import urllib.parse
import requests
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def is_capital_raid_day(dt: datetime) -> bool:
    """
    Returns True if capital raids data should be fetched.
    We skip Tuesday (1), Wednesday (2), and Thursday (3) in UTC.
    """
    return dt.weekday() not in (1, 2, 3)

class CocApiClient:
    def __init__(self, api_key: str, clan_tag: str):
        self.api_key = api_key
        # URL encode the clan tag, e.g. #2PP becomes %232PP
        self.clan_tag = urllib.parse.quote(clan_tag)
        self.base_url = "https://api.clashofclans.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }

    def _get(self, endpoint: str) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, headers=self.headers)
        if not response.ok:
            logger.error(
                "Failed to fetch data from Clash of Clans API",
                extra={
                    "url": url,
                    "status_code": response.status_code,
                    "response_text": response.text
                }
            )
            response.raise_for_status()
        return response.json()

    def fetch_clan(self) -> Dict[str, Any]:
        return self._get(f"clans/{self.clan_tag}")

    def fetch_members(self) -> Dict[str, Any]:
        return self._get(f"clans/{self.clan_tag}/members")

    def fetch_current_war(self) -> Optional[Dict[str, Any]]:
        """
        Fetches current war details. Returns None if state is 'notInWar'.
        """
        data = self._get(f"clans/{self.clan_tag}/currentwar")
        if data.get("state") == "notInWar":
            logger.info(
                "Clan is not currently in war. Skipping current war extraction.",
                extra={"clan_tag": self.clan_tag, "state": "notInWar"}
            )
            return None
        return data

    def fetch_capital_raids(self) -> Dict[str, Any]:
        return self._get(f"clans/{self.clan_tag}/capitalraidseasons")
