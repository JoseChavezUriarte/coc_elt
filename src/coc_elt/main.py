import logging
from datetime import datetime, timezone
from pydantic import ValidationError

from coc_elt.config import settings
from coc_elt.api_client import CocApiClient, is_capital_raid_day
from coc_elt.bq_client import BigQueryIngester
from coc_elt.logging_config import setup_logging
from coc_elt.models import ClanRecord, MemberRecord, MemberListResponse, WarRecord, CapitalRaidListResponse, LeagueGroupRecord, WarLeagueWarRecord

setup_logging(logging.INFO)
logger = logging.getLogger("coc_elt.main")

def run_pipeline() -> None:
    now_utc = datetime.now(timezone.utc)
    logger.info(
        "Starting ELT pipeline execution",
        extra={
            "started_at": now_utc.isoformat(),
            "data_project_id": settings.data_project_id,
            "dataset_id": settings.dataset_id,
            "clan_tag": settings.clan_tag
        }
    )

    try:
        api_client = CocApiClient(api_key=settings.coc_apikey, clan_tag=settings.clan_tag)
        ingester = BigQueryIngester(project_id=settings.data_project_id, dataset_id=settings.dataset_id)
    except Exception as e:
        logger.error(
            "Pipeline initialization failed",
            exc_info=True,
            extra={
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "error_message": str(e)
            }
        )
        raise e

    clan_raw = None

    # 1. Clan Domain
    try:
        logger.info("Processing Clan domain", extra={"step": "domain_clan"})
        clan_raw = api_client.fetch_clan()
        clan_val = ClanRecord.model_validate(clan_raw)
        ingester.ingest_batch("coc_clan", [clan_val.model_dump(mode="json")], now_utc)
    except ValidationError as e:
        logger.error("Validation failed for Clan domain. Skipping ingestion.", exc_info=e)
    except Exception as e:
        logger.error("Error processing Clan domain. Skipping ingestion.", exc_info=e)

    # 2. Members Domain
    try:
        logger.info("Processing Members domain", extra={"step": "domain_members"})
        current_clan_raw = clan_raw if clan_raw is not None else api_client.fetch_clan()
        member_list = current_clan_raw.get("memberList", [])
        validated_members = []
        for member in member_list:
            tag = member["tag"]
            player_raw = api_client.fetch_player(tag)
            player_val = MemberRecord.model_validate(player_raw)
            validated_members.append(player_val.model_dump(mode="json"))
        ingester.ingest_batch("coc_members", validated_members, now_utc)
    except ValidationError as e:
        logger.error("Validation failed for Members domain. Skipping ingestion.", exc_info=e)
    except Exception as e:
        logger.error("Error processing Members domain. Skipping ingestion.", exc_info=e)

    # 3. Current War Domain
    try:
        logger.info("Processing Current War domain", extra={"step": "domain_war"})
        war_raw = api_client.fetch_current_war()
        if war_raw is not None:
            war_val = WarRecord.model_validate(war_raw)
            ingester.ingest_batch("coc_current_war", [war_val.model_dump(mode="json")], now_utc)
        else:
            logger.info(
                "Skipping Current War ingestion as clan is not in war.",
                extra={"step": "domain_war", "reason": "notInWar"}
            )
    except ValidationError as e:
        logger.error("Validation failed for Current War domain. Skipping ingestion.", exc_info=e)
    except Exception as e:
        logger.error("Error processing Current War domain. Skipping ingestion.", exc_info=e)

    # 4. Capital Raids Domain
    if is_capital_raid_day(now_utc):
        try:
            logger.info("Processing Capital Raids domain", extra={"step": "domain_raids"})
            raids_raw = api_client.fetch_capital_raids()
            raids_val = CapitalRaidListResponse.model_validate(raids_raw)
            raids_records = [r.model_dump(mode="json") for r in raids_val.items]
            ingester.ingest_batch("coc_capital_raids", raids_records, now_utc)
        except ValidationError as e:
            logger.error("Validation failed for Capital Raids domain. Skipping ingestion.", exc_info=e)
        except Exception as e:
            logger.error("Error processing Capital Raids domain. Skipping ingestion.", exc_info=e)
    else:
        logger.info(
            "Skipping Capital Raids extraction (Tuesday/Wednesday/Thursday in UTC).",
            extra={"step": "domain_raids", "reason": "weekday_schedule", "weekday": now_utc.weekday()}
        )

    # 5. League Group & War League Domain
    try:
        logger.info("Processing League Group & War League domain", extra={"step": "domain_league_group"})
        league_group_raw = api_client.fetch_league_group()
        if league_group_raw is not None and "rounds" in league_group_raw:
            league_group_val = LeagueGroupRecord.model_validate(league_group_raw)
            ingester.ingest_batch("coc_league_group", [league_group_val.model_dump(mode="json")], now_utc)

            validated_wars = []
            for round_obj in league_group_raw.get("rounds", []):
                for war_tag in round_obj.get("warTags", []):
                    if war_tag == "#0":
                        continue
                    war_raw = api_client.fetch_warleague_war(war_tag)
                    war_val = WarLeagueWarRecord.model_validate(war_raw)
                    validated_wars.append(war_val.model_dump(mode="json"))
            
            if validated_wars:
                ingester.ingest_batch("coc_warleague_war", validated_wars, now_utc)
        else:
            logger.info(
                "Skipping League Group & War League ingestion as no active league group or rounds found.",
                extra={"step": "domain_league_group"}
            )
    except ValidationError as e:
        logger.error("Validation failed for League Group & War League domain. Skipping ingestion.", exc_info=e)
    except Exception as e:
        logger.error("Error processing League Group & War League domain. Skipping ingestion.", exc_info=e)

    logger.info(
        "ELT pipeline completed execution.",
        extra={"finished_at": datetime.now(timezone.utc).isoformat()}
    )

if __name__ == "__main__":
    run_pipeline()
