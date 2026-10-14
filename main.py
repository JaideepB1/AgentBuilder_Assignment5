import sys
import time
import uuid

from agent import investigate_single_case, resume_approval
from queue_manager import (
    start_sweep,
    get_sweep_status,
    collect_sweep_results,
)


def run_single_case(account_id: str):
    thread_id = str(uuid.uuid4())

    result = investigate_single_case(account_id, thread_id)
    investigation = result["investigation"]
    approval = result["approval"]

    print("\nINVESTIGATION:")
    print(investigation.model_dump())

    if "__interrupt__" in approval:
        interrupt_data = approval["__interrupt__"][0].value

        print("\nHUMAN APPROVAL REQUIRED:")
        print("Proposed action:", interrupt_data["proposed_action"])
        print("Reasoning:", interrupt_data["reasoning"])

        while True:
            decision = input("\nApprove action? (yes/no): ").strip().lower()

            if decision in ["yes", "y"]:
                decision = "approved"
                break

            if decision in ["no", "n"]:
                decision = "rejected"
                break

            print("Please enter yes or no.")

        final_result = resume_approval(thread_id, decision)

        print("\nAPPROVAL RESULT:")
        print(final_result["approval_status"])

    else:
        print("\nAPPROVAL RESULT:")
        print(approval["approval_status"])


def run_queue_sweep():
    job_id = start_sweep()
    print("JOB ID:", job_id)

    while True:
        status = get_sweep_status(job_id)

        print(
            "STATUS:",
            status["status"],
            f'{status["completed"]}/{status["total"]}',
        )

        if status["status"] == "completed":
            break

        time.sleep(10)

    results = collect_sweep_results(job_id)

    print("\nFINAL STATUS:")
    print(get_sweep_status(job_id))

    print("\nRESULT COUNT:")
    print(len(results["results"]))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_single_case(sys.argv[1])
    else:
        run_queue_sweep()