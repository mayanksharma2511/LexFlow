"""Auto-healing service for stalled background processing tasks and orphaned DB records."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.document import Document

logger = logging.getLogger(__name__)

STALLED_THRESHOLD_MINUTES = 10


class TaskHealingService:
    """Enterprise self-healing manager for stuck or orphaned document analysis tasks."""

    def heal_stalled_documents(self, db: Session, threshold_minutes: int = STALLED_THRESHOLD_MINUTES) -> int:
        """Query documents stuck in PROCESSING or ANALYSIS_PENDING for longer than threshold_minutes.

        Automatically transitions stuck records to FAILED_QUOTA / RETRY_REQUIRED with a clear error message.

        Args:
            db: SQLAlchemy database session context.
            threshold_minutes: Timeout window in minutes (defaults to 10 minutes).

        Returns:
            Count of auto-healed document records.
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=threshold_minutes)

        try:
            # Match records stuck in pending/processing states
            stalled_docs = (
                db.query(Document)
                .filter(
                    Document.status.in_(["PROCESSING", "ANALYSIS_PENDING"]),
                    Document.uploaded_at <= cutoff_time,
                )
                .all()
            )

            if not stalled_docs:
                return 0

            healed_count = 0
            for doc in stalled_docs:
                doc.status = "FAILED_QUOTA"
                doc.error_message = (
                    f"Task execution timed out (exceeded {threshold_minutes} minutes). "
                    "Status auto-healed to FAILED_QUOTA."
                )
                healed_count += 1

            db.commit()
            logger.info("Auto-healing routine repaired %d stalled document task(s)", healed_count)
            return healed_count

        except Exception as exc:
            db.rollback()
            logger.exception("Error executing auto-healing routine: %s", exc)
            return 0


healing_service = TaskHealingService()
