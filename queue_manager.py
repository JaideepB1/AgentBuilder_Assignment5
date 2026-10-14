import threading
import uuid
import json
from db import get_alerted_accounts
from agent import (
    investigate_account,
    get_total_token_usage,
    reset_token_usage,
)
from langchain_core.tools import tool


jobs = {}
jobs_lock = threading.Lock()

def start_sweep():
    job_id = str(uuid.uuid4())

    with jobs_lock:
        jobs[job_id] = {
            "status": "pending",
            "completed": 0,
            "failed": 0,
            "total": 0,
            "results": [],
            "error": None,
        }

    thread = threading.Thread(
        target=run_sweep,
        args=(job_id,),
        daemon=True,
    )
    thread.start()

    return job_id

@tool
def start_queue_sweep() -> str:
    """Start the fraud investigation queue sweep in the background and return its job ID."""
    return start_sweep()

def run_sweep(job_id):
    reset_token_usage()
    
    accounts = get_alerted_accounts()

    with jobs_lock:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["total"] = len(accounts)

    for account_id in accounts:
        try:
            result = investigate_account(account_id)

            with jobs_lock:
                jobs[job_id]["results"].append(result)

        except Exception as error:
            with jobs_lock:
                jobs[job_id]["results"].append(
                    {
                        "account_id": account_id,
                        "error": str(error),
                    }
                )
                jobs[job_id]["failed"] += 1

        finally:
            with jobs_lock:
                jobs[job_id]["completed"] += 1

        if jobs[job_id]["completed"] % 10 == 0:
            print(
                f'Sweep progress: {jobs[job_id]["completed"]}/{len(accounts)}'
            )

            with jobs_lock:
                checkpoint_job = jobs[job_id].copy()
                checkpoint_job["results"] = [
                    result.model_dump() if hasattr(result, "model_dump") else result
                    for result in jobs[job_id]["results"]
                ]

            with open("sweep_results_checkpoint.json", "w") as file:
                json.dump(checkpoint_job, file, indent=2)

    token_usage = get_total_token_usage()

    with jobs_lock:
        jobs[job_id]["token_usage"] = token_usage
        jobs[job_id]["status"] = "completed"

    with jobs_lock:
        saved_job = jobs[job_id].copy()
        saved_job["results"] = [
            result.model_dump() if hasattr(result, "model_dump") else result
            for result in jobs[job_id]["results"]
        ]

    with open("sweep_results.json", "w") as file:
        json.dump(saved_job, file, indent=2)

def get_sweep_status(job_id):
    with jobs_lock:
        job = jobs.get(job_id)

        if job is None:
            return None

        return {
            "job_id": job_id,
            "status": job["status"],
            "completed": job["completed"],
            "failed": job["failed"],
            "total": job["total"],
            "error": job["error"],
            "token_usage": job.get("token_usage"),
        }

@tool
def check_queue_status(job_id: str) -> dict:
    """Check the current status and progress of a fraud investigation queue sweep."""
    status = get_sweep_status(job_id)

    if status is None:
        return {
            "error": f"Job {job_id} was not found."
        }

    return status

def collect_sweep_results(job_id):
    with jobs_lock:
        job = jobs.get(job_id)

        if job is None:
            return None

        return {
            "job_id": job_id,
            "status": job["status"],
            "completed": job["completed"],
            "failed": job["failed"],
            "total": job["total"],
            "results": job["results"].copy(),
            "error": job["error"],
        }


@tool
def collect_queue_results(job_id: str) -> dict:
    """Collect the available results from a fraud investigation queue sweep."""
    results = collect_sweep_results(job_id)

    if results is None:
        return {
            "error": f"Job {job_id} was not found."
        }

    return results