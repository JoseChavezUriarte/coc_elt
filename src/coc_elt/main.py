import logging
from datetime import datetime, timezone
from pydantic import ValidationError

from coc_elt.config import settings
from coc_elt.api_client import CocApiClient, is_capital_raid_day
from coc_elt.bq_client import BigQueryIngester
from coc_elt.logging_config import setup_logging
from coc_elt.models import ClanRecord, MemberListResponse, WarRecord, CapitalRaidListResponse

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
        members_raw = api_client.fetch_members()
        members_val = MemberListResponse.model_validate(members_raw)
        members_records = [m.model_dump(mode="json") for m in members_val.items]
        ingester.ingest_batch("coc_members", members_records, now_utc)
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

    logger.info(
        "ELT pipeline completed execution.",
        extra={"finished_at": datetime.now(timezone.utc).isoformat()}
    )

if __name__ == "__main__":
    run_pipeline()
