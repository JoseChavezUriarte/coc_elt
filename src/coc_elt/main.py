import logging
from datetime import datetime, timezone

from coc_elt.config import settings
from coc_elt.api_client import CocApiClient, is_capital_raid_day
from coc_elt.bq_client import BigQueryIngester
from coc_elt.logging_config import setup_logging

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

    api_client = CocApiClient(api_key=settings.coc_apikey, clan_tag=settings.clan_tag)
    ingester = BigQueryIngester(project_id=settings.data_project_id, dataset_id=settings.dataset_id)

    try:
        logger.info("Fetching clan details", extra={"step": "fetch_clan"})
        clan_data = api_client.fetch_clan()
        ingester.ingest_record("clan", clan_data, now_utc)

        logger.info("Fetching members details", extra={"step": "fetch_members"})
        members_data = api_client.fetch_members()
        ingester.ingest_record("members", members_data, now_utc)

        logger.info("Fetching current war details", extra={"step": "fetch_current_war"})
        war_data = api_client.fetch_current_war()
        if war_data is not None:
            ingester.ingest_record("current_war", war_data, now_utc)
        else:
            logger.info(
                "Skipping Current War ingestion as clan is not in war.",
                extra={"step": "fetch_current_war", "reason": "notInWar"}
            )

        if is_capital_raid_day(now_utc):
            logger.info("Fetching capital raids details", extra={"step": "fetch_capital_raids"})
            raids_data = api_client.fetch_capital_raids()
            ingester.ingest_record("capital_raids", raids_data, now_utc)
        else:
            logger.info(
                "Skipping Capital Raids extraction (Tuesday/Wednesday/Thursday in UTC).",
                extra={"step": "fetch_capital_raids", "reason": "weekday_schedule", "weekday": now_utc.weekday()}
            )

        logger.info(
            "ELT pipeline completed successfully.",
            extra={"finished_at": datetime.now(timezone.utc).isoformat()}
        )

    except Exception as e:
        logger.error(
            "Pipeline execution failed",
            exc_info=True,
            extra={
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "error_message": str(e)
            }
        )
        raise e

if __name__ == "__main__":
    run_pipeline()

if __name__ == "__main__":
    run_pipeline()
