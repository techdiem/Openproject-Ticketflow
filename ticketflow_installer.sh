#!/bin/bash

APP_DIR="/opt/ticketflow"
TEMPFILE_DIR="/tmp/ticketflow_updates"
SETTINGS_FILE="${APP_DIR}/settings.conf"
TEMP_SETTINGS_FILE="${TEMPFILE_DIR}/settings_temp_backup.conf"
VENV_PATH="${APP_DIR}/venv"
USER="ticketflow"
CRON_FILE="/etc/cron.d/ticketflow"
LOGROTATE_FILE="/etc/logrotate.d/ticketflow"
FLOW_LOGFILE="/var/log/ticketflow.log" #Log location from settings.conf


GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

COMMAND="$1"
UPDATE_ZIP="$2"

cat << "EOF"
  _______ _      _        _    __ _               
 |__   __(_)    | |      | |  / _| |              
    | |   _  ___| | _____| |_| |_| | _____      __
    | |  | |/ __| |/ / _ \ __|  _| |/ _ \ \ /\ / /
    | |  | | (__|   <  __/ |_| | | | (_) \ V  V / 
    |_|  |_|\___|_|\_\___|\__|_| |_|\___/ \_/\_/     

EOF

case "$COMMAND" in
    install)
        if [ -d "$APP_DIR" ]; then
            echo -e "${RED}Fehler: Anwendungsverzeichnis '$APP_DIR' bereits vorhanden.${NC}"
            echo -e "${RED}Für Updates verwenden Sie den Befehl \"update\".${NC}"
            exit 1
        fi

        if [ -z "$UPDATE_ZIP" ]; then
            echo -e "${RED}Fehler: Bitte geben Sie den Pfad zur Installations-ZIP-Datei an.${NC}"
            echo -e "${RED}Verwendung: $0 install /pfad/zur/version.zip${NC}"
            exit 1
        fi
        
        if [ ! -f "$UPDATE_ZIP" ]; then
            echo -e "${RED}Fehler: ZIP-Datei nicht gefunden: $UPDATE_ZIP${NC}"
            exit 1
        fi

        echo -e "${GREEN}Starte Installation...${NC}"
        echo -e "${GREEN}Installiere Systempakete 'python3-pip' und 'python3-venv'...${NC}"
        apt-get update && apt-get install -y python3-pip python3-venv

        echo -e "${GREEN}Erstelle Benutzer '$USER'...${NC}"
        if ! id -u "$USER" >/dev/null 2>&1; then
            useradd -r "$USER"
        fi
        
        echo -e "${GREEN}Erstelle Anwendungsverzeichnisse...${NC}"
        mkdir -p "$APP_DIR"
        
        echo -e "${GREEN}Extrahiere Anwendungsdateien...${NC}"
        unzip -q -o "$UPDATE_ZIP" -d "$APP_DIR"
        
        echo -e "${GREEN}Passe Berechtigungen an...${NC}"
        chown -R "$USER":"$USER" "$APP_DIR"
        chmod -R 770 "$APP_DIR"

        echo -e "${GREEN}Erstelle virtuelle Umgebung und installiere Abhängigkeiten...${NC}"
        python3 -m venv "$VENV_PATH"
        chown -R "$USER":"$USER" "$VENV_PATH"
        chmod -R 770 "$VENV_PATH"
        if [ -f "${APP_DIR}/requirements.txt" ]; then
            su -s /bin/bash "$USER" -c "source \"$VENV_PATH/bin/activate\" && pip install -r \"${APP_DIR}/requirements.txt\""
        fi

        echo -e "${GREEN}Erstelle Logfile...${NC}"
        touch $FLOW_LOGFILE
        chown ticketflow:ticketflow $FLOW_LOGFILE

        echo -e "${GREEN}Erstelle Cron-Job-Datei...${NC}"
        echo "# Cron Job für Ticketflow-Bot, legt Polling-Intervall für Mail und Benachrichtigungen fest" > "$CRON_FILE"
        echo "HOME=$APP_DIR" > "$CRON_FILE"
        echo "*/5 6-19 * * 1-5 $USER $VENV_PATH/bin/python3 $APP_DIR/ticketflow.py > /dev/null 2>&1" >> "$CRON_FILE"
        chmod 600 $CRON_FILE

        echo -e "${GREEN}Erstelle Logrotate-Config...${NC}"
        cat << EOF > $LOGROTATE_FILE
$FLOW_LOGFILE {
        rotate 4
        daily
        missingok
        notifempty
        compress
        delaycompress
        sharedscripts
}
EOF
        chmod 644 $LOGROTATE_FILE

        echo -e "${GREEN}Installation erfolgreich abgeschlossen.${NC}"
        echo -e "${GREEN}Passe bei Bedarf das Polling Intervall in \"$CRON_FILE\" an, Standard ist Werktags 6-19 Uhr alle 5min.${NC}"
        read -p "Möchtest du eine neue Konfigurationsdatei anlegen? (y/n): " confirm
        if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
            su -s /bin/bash "$USER" -c "cp $APP_DIR/settings.example.conf $SETTINGS_FILE"
            echo -e "${GREEN}Datei angelegt.${NC}"
            exit 0
        else
            echo -e "Ok, falls du eine bestehende Konfiguration rüberkopierst, passe die Berechtigungen an, da in der Datei API-Schlüssel und Kennwörter enthalten sind."
        fi
        ;;

    update)
        if [ ! -d "$APP_DIR" ]; then
            echo -e "${RED}Fehler: Anwendungsverzeichnis '$APP_DIR' nicht gefunden.${NC}"
            echo -e "${RED}Bitte führen Sie zuerst die Installation aus.${NC}"
            exit 1
        fi

        if [ -z "$UPDATE_ZIP" ]; then
            echo -e "${RED}Fehler: Bitte geben Sie den Pfad zur Update-ZIP-Datei an.${NC}"
            echo -e "${RED}Verwendung: $0 update /pfad/zur/neuen/version.zip${NC}"
            exit 1
        fi

        if [ ! -f "$UPDATE_ZIP" ]; then
            echo -e "${RED}Fehler: ZIP-Datei nicht gefunden: $UPDATE_ZIP${NC}"
            exit 1
        fi

        echo -e "${GREEN}Starte Update-Prozess für die Anwendung...${NC}"
        mkdir -p "$TEMPFILE_DIR"

        if [ -f "$SETTINGS_FILE" ]; then
            echo -e "${GREEN}Sichere bestehende settings.conf nach: $TEMP_SETTINGS_FILE${NC}"
            cp "$SETTINGS_FILE" "$TEMP_SETTINGS_FILE"
        else
            echo -e "${GREEN}settings.conf nicht gefunden, überspringe Sicherung.${NC}"
        fi

        echo -e "${GREEN}Lösche alte Anwendungsdateien...${NC}"
        find "$APP_DIR" -mindepth 1 -maxdepth 1 \
            -not -name "venv" \
            -not -name "$(basename "$SETTINGS_FILE")" \
            -exec rm -rf {} +

        echo -e "${GREEN}Alte Anwendungsdateien gelöscht.${NC}"

        echo -e "${GREEN}Extrahiere neue Anwendungsdateien...${NC}"
        unzip -q -o "$UPDATE_ZIP" -d "$APP_DIR"
        if [ $? -ne 0 ]; then
            echo -e "${RED}Fehler beim Extrahieren der ZIP-Datei. Update abgebrochen.${NC}"
            exit 1
        fi
        echo -e "${GREEN}Extraktion abgeschlossen.${NC}"

        if [ -f "$TEMP_SETTINGS_FILE" ]; then
            echo -e "${GREEN}Stelle settings.conf von $TEMP_SETTINGS_FILE nach $SETTINGS_FILE wieder her.${NC}"
            cp "$TEMP_SETTINGS_FILE" "$SETTINGS_FILE"
            rm "$TEMP_SETTINGS_FILE"
        else
            echo -e "${GREEN}Keine settings.conf Sicherung zum Wiederherstellen gefunden.${NC}"
        fi

        echo -e "${GREEN}Passe Besitzrechte und Berechtigungen an...${NC}"
        chown -R "$USER":"$USER" "$APP_DIR"
        chmod -R 770 "$APP_DIR"

        echo -e "${GREEN}Aktualisiere virtuelle Umgebung...${NC}"
        if [ -d "$VENV_PATH" ]; then
            if [ -f "${APP_DIR}/requirements.txt" ]; then
                su -s /bin/bash "$USER" -c "source \"$VENV_PATH/bin/activate\" && pip install --upgrade -r \"${APP_DIR}/requirements.txt\""
            else
                echo -e "${GREEN}requirements.txt nicht gefunden. Überspringe Venv-Aktualisierung.${NC}"
            fi
        else
            echo -e "${GREEN}Achtung: Virtuelle Python-Umgebung nicht gefunden, überspringe Aktualisierung.${NC}"
        fi

        echo -e "${GREEN}Update erfolgreich abgeschlossen.${NC}"
        ;;
    
    uninstall)
        if [ ! -d "$APP_DIR" ]; then
            echo -e "${RED}Fehler: Anwendungsverzeichnis '$APP_DIR' nicht gefunden.${NC}"
            echo -e "${RED}Anwendung scheint nicht installiert zu sein.${NC}"
            exit 1
        fi

        if [ -f "$SETTINGS_FILE" ]; then
            echo -e "${RED}Achtung: Die Konfigurationsdatei '$SETTINGS_FILE' existiert und wird gelöscht.${NC}"
            read -p "Möchten Sie fortfahren? (y/n): " confirm
            if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
                echo -e "${RED}Deinstallation abgebrochen.${NC}"
                exit 1
            fi
        fi

        echo -e "${GREEN}Starte Deinstallations-Prozess...${NC}"
        echo -e "${GREEN}Lösche Anwendungsverzeichnis '$APP_DIR'...${NC}"
        rm -rf "$APP_DIR"
        
        echo -e "${GREEN}Lösche Benutzer '$USER'...${NC}"
        userdel "$USER"

        echo -e "${GREEN}Lösche Cron-Job...${NC}"
        rm -f "$CRON_FILE"

        echo -e "${GREEN}Lösche Logrotate-Config...${NC}"
        rm -f "$LOGROTATE_FILE"

        echo -e "${GREEN}Lösche Logfile...${NC}"
        rm -f "$FLOW_LOGFILE"

        echo -e "${GREEN}Deinstallation erfolgreich abgeschlossen.${NC}"
        ;;

    run)
        if [ ! -d "$APP_DIR" ]; then
            echo -e "${RED}Fehler: Anwendungsverzeichnis '$APP_DIR' nicht gefunden.${NC}"
            echo -e "${RED}Anwendung scheint nicht installiert zu sein.${NC}"
            exit 1
        fi
        su -s /bin/bash "$USER" -c "cd $APP_DIR && $VENV_PATH/bin/python3 $APP_DIR/ticketflow.py"
        ;;

    *)
        echo -e "${RED}Unbekannter Befehl: $COMMAND${NC}"
        echo -e "${RED}Verwendung: $0 {install|update|uninstall|run} [ZIP-Datei]${NC}

install [Zip-Pfad]: Software neu installieren
update [Zip-Pfad]: Software und Python-Umgebung aktualisieren
uninstall: Software entfernen
run: Synchronisation manuell ausführen
"

        exit 1
        ;;
esac

