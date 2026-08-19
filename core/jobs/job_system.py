"""Background Job Queue & Task Execution System."""

import time
import uuid
import threading
from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from core.events.event_bus import event_bus
from core.events.events import BackgroundJobCompleted
from core.logger import get_logger

logger = get_logger("core.jobs.system")


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Job:
    """Represents a background execution job."""

    def __init__(self, job_type: str, payload: Dict[str, Any], max_retries: int = 3):
        self.id = str(uuid.uuid4())[:8]
        self.job_type = job_type
        self.payload = payload
        self.status = JobStatus.PENDING
        self.progress = 0.0
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.retries = 0
        self.max_retries = max_retries
        self.created_at = time.time()
        self.updated_at = time.time()

    def update_progress(self, progress: float):
        self.progress = min(max(progress, 0.0), 100.0)
        self.updated_at = time.time()


class JobQueue:
    """Asynchronous background job worker queue."""

    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._handlers: Dict[str, Callable[[Job], Any]] = {}

    def register_handler(self, job_type: str, handler: Callable[[Job], Any]):
        """Register worker callback for a specific job type."""
        self._handlers[job_type] = handler
        logger.info(f"Registered job worker handler for '{job_type}'")

    def submit_job(self, job_type: str, payload: Dict[str, Any], max_retries: int = 3) -> Job:
        """Enqueue a background job and trigger async background worker."""
        job = Job(job_type, payload, max_retries)
        self._jobs[job.id] = job

        # Execute in background thread
        thread = threading.Thread(target=self._run_job, args=(job,), daemon=True)
        thread.start()

        logger.info(f"Submitted background job '{job_type}' (ID: {job.id})")
        return job

    def _run_job(self, job: Job):
        job.status = JobStatus.RUNNING
        job.updated_at = time.time()
        handler = self._handlers.get(job.job_type)

        if not handler:
            job.status = JobStatus.FAILED
            job.error = f"No registered handler for job_type '{job.job_type}'"
            return

        try:
            res = handler(job)
            job.result = res
            job.progress = 100.0
            job.status = JobStatus.COMPLETED
            job.updated_at = time.time()
            event_bus.publish(BackgroundJobCompleted(payload={"job_id": job.id, "job_type": job.job_type, "status": "completed"}))
            logger.info(f"Background job '{job.id}' completed successfully.")
        except Exception as e:
            logger.error(f"Error executing background job '{job.id}': {e}", exc_info=True)
            if job.retries < job.max_retries:
                job.retries += 1
                logger.info(f"Retrying background job '{job.id}' (Attempt {job.retries}/{job.max_retries})")
                self._run_job(job)
            else:
                job.status = JobStatus.FAILED
                job.error = str(e)
                job.updated_at = time.time()

    def get_job(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def list_jobs(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": j.id,
                "type": j.job_type,
                "status": j.status.value,
                "progress": j.progress,
                "retries": j.retries,
                "error": j.error,
                "created_at": j.created_at,
            }
            for j in self._jobs.values()
        ]


# Global singleton instance
job_queue = JobQueue()
