import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import requests
from coc_elt.api_client import CocApiClient, is_capital_raid_day

def test_is_capital_raid_day():
    # Tuesday (1) - UTC
    dt_tue = datetime(2026, 7, 14, tzinfo=timezone.utc)
    assert is_capital_raid_day(dt_tue) is False

    # Wednesday (2) - UTC
    dt_wed = datetime(2026, 7, 15, tzinfo=timezone.utc)
    assert is_capital_raid_day(dt_wed) is False

    # Thursday (3) - UTC
    dt_thu = datetime(2026, 7, 16, tzinfo=timezone.utc)
    assert is_capital_raid_day(dt_thu) is False

    # Friday (4) - UTC
    dt_fri = datetime(2026, 7, 17, tzinfo=timezone.utc)
    assert is_capital_raid_day(dt_fri) is True

    # Monday (0) - UTC
    dt_mon = datetime(2026, 7, 13, tzinfo=timezone.utc)
    assert is_capital_raid_day(dt_mon) is True

@patch("requests.get")
def test_fetch_current_war_active(mock_get):
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.return_value = {"state": "inWar", "opponent": {}}
    mock_get.return_value = mock_response

    client = CocApiClient(api_key="test-key", clan_tag="#TESTCLAN")
    war_data = client.fetch_current_war()
    
    assert war_data is not None
    assert war_data["state"] == "inWar"
    mock_get.assert_called_once_with(
        "https://api.clashofclans.com/v1/clans/%23TESTCLAN/currentwar",
        headers={"Authorization": "Bearer test-key", "Accept": "application/json"}
    )

@patch("requests.get")
def test_fetch_current_war_not_in_war(mock_get):
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.return_value = {"state": "notInWar"}
    mock_get.return_value = mock_response

    client = CocApiClient(api_key="test-key", clan_tag="#TESTCLAN")
    war_data = client.fetch_current_war()
    
    assert war_data is None

@patch("requests.get")
def test_fetch_error_handling(mock_get):
    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.status_code = 403
    mock_response.text = "Access denied"
    mock_response.raise_for_status.side_effect = requests.HTTPError("403 Forbidden")
    mock_get.return_value = mock_response

    client = CocApiClient(api_key="invalid-key", clan_tag="#TEST")
    with pytest.raises(requests.HTTPError):
        client.fetch_clan()
