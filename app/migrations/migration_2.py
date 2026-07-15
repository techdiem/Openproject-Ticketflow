from commentedconfigparser import CommentedConfigParser

# Migration script for config file version 2.

# Adds the following to the OpenProject-section:

# #Use displayID instead of internal ID for ticket references in mails, if available (OpenProject 17.5+) (true | false)
# use_display_id = true

# --------------------------

def migrate(config: CommentedConfigParser) -> None:
    config.set("General", "config_version", "2")

    section = "OpenProject"
    if not config.has_section(section):
        config.add_section(section)

    comment_key = "__comment_1"
    comment_value = (
        "#Use displayID instead of internal ID for ticket references in mails, if available (OpenProject 17.5+) (true | false)"
    )
    if not config.has_option(section, comment_key):
        config.set(section, comment_key, comment_value)

    if not config.has_option(section, "use_display_id"):
        config.set(section, "use_display_id", "true")
