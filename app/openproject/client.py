"""HTTP client for the OpenProject REST API v3.

Encapsulates all HTTP operations (GET / POST / PATCH) including auth,
base URL, TLS verification, and session reuse (connection pooling).
The module-level singleton `op_client` is used by the domain modules
of this package.
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import config


class OpenProjectClient:
    def __init__(self) -> None:
        self._base_url: str = config.get("OpenProject", "base_url")
        self._session = requests.Session()
        self._session.auth = ("apikey", config.get("OpenProject", "api_key"))
        self._session.verify = config.getboolean("OpenProject", "https_verification")

        retry_strategy = Retry(
            total=3,
            connect=3,                      # Versuche bei ConnectionError (kein Server erreichbar)
            read=3,                         # Versuche bei ReadTimeout
            backoff_factor=2,               # Wartezeit: 0s, 2s, 4s, 8s, 16s
            backoff_max=30,                 # max. 30s zwischen Versuchen
            status_forcelist=[500, 502, 503, 504],  # bei diesen HTTP-Codes wiederholen
            allowed_methods=["GET", "POST", "PATCH"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    def get(
        self,
        path: str,
        headers: dict | None = None,
        params: dict | None = None,
    ) -> requests.Response:
        return self._session.get(
            f"{self._base_url}{path}",
            headers=headers,
            params=params,
            timeout=30,
        )

    def post(
        self,
        path: str,
        data: bytes | str | None = None,
        files: dict | None = None,
        headers: dict | None = None,
    ) -> requests.Response:
        return self._session.post(
            f"{self._base_url}{path}",
            data=data,
            files=files,
            headers=headers,
            timeout=30,
        )

    def patch(
        self,
        path: str,
        headers: dict | None = None,
        data: bytes | str | None = None,
    ) -> requests.Response:
        return self._session.patch(
            f"{self._base_url}{path}",
            headers=headers,
            data=data,
            timeout=30,
        )


# Module-level singleton – instantiated once on first import
op_client = OpenProjectClient()
