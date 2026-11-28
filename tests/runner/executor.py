import asyncio

from tests.runner.evidence import now
from tests.runner.resources import Resources, ResourceBlocked
from tests.support.privacy import redact
from tests.tasks.catalog import no_work_reason


def cases_for(jobs):
    return [{"case_id": f"case-{j:03d}-{i:03d}", "config_id": job.config_id, "task_id": task,
             "status": "not_run", "review": "pending", "reason": "", "evidence": [],
             "evidence_dropped": 0, "timeout_seconds": job.timeout_seconds}
            for j, job in enumerate(jobs, 1) for i, task in enumerate(job.tasks, 1)]


class Executor:
    def __init__(self, jobs, targets, backend, recorder, cancel, emit, config_reader):
        self.jobs, self.targets, self.backend, self.recorder = jobs, targets, backend, recorder
        self.cancel, self.emit, self.config_reader = cancel, emit, config_reader
        self.resources = Resources()

    def update(self, case, **values):
        with self.recorder.lock:
            case.update(values)
        self.emit({"type": "case" if "status" in values or "reason" in values else "case_details", "case_id": case["case_id"], "config_id": case["config_id"],
                   "task_id": case["task_id"], "status": case["status"], "reason": case.get("reason", "")})

    async def run(self):
        await asyncio.gather(*(self.run_job(job) for job in self.jobs))

    async def run_job(self, job):
        target = self.targets[job.config_id]
        cases = [c for c in self.recorder.cases.values() if c["config_id"] == job.config_id]
        halted = False
        for case in cases:
            if halted or self.cancel.is_set():
                self.update(case, status="not_run", reason="An earlier task failed or the batch was cancelled")
                continue
            if not target.ready:
                self.update(case, status="blocked", reason=target.reason)
                halted = True
                continue
            acquired = []
            try:
                acquired = await self.resources.acquire(target.resources)
                if self.cancel.is_set():
                    self.update(case, status="not_run", reason="Batch cancelled")
                    continue
                before = self.config_reader(job.config_id)
                self.recorder.bind(job.config_id, case["case_id"])
                self.update(case, status="running", started_at=now(), target=target.data())
                outcome = await self.backend.run_case(job, case, self.cancel)
                self.update(case, status=outcome["status"], reason=outcome.get("reason", ""), ended_at=now())
                if not outcome.get("quiescent", True):
                    self.resources.poison(target.resources, "The previous task has not exited; this device cannot be reused")
                with self.recorder.lock:
                    messages = list(self.recorder.messages[case["case_id"]])
                reason = no_work_reason(case["task_id"], messages)
                if case["status"] == "completed" and reason:
                    self.update(case, status="unexecuted", reason=reason)
                after = self.config_reader(job.config_id)
                changes = {k: {"before": before.get(k), "after": after.get(k)}
                           for k in sorted(before.keys() | after.keys()) if before.get(k) != after.get(k)}
                self.update(case, config_changes=redact(changes, self.recorder.secrets))
                halted = case["status"] in {"failed", "timeout", "cancelled", "blocked"}
            except ResourceBlocked as exc:
                self.update(case, status="blocked", reason=str(exc), ended_at=now())
                halted = True
            except Exception as exc:
                self.update(case, status="failed", reason=redact(str(exc), self.recorder.secrets), ended_at=now())
                halted = True
            finally:
                self.recorder.unbind(job.config_id)
                self.resources.release(acquired)
