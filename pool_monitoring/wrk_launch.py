import asyncio
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any
from pool_monitoring.monitoring_settings import RESULTS_BASE_DIR

RUNS = 5
DURATION = "30s"

DURATION_MAPPING = {
    20: "20s",
    30: "30s",
    60: "60s",
    120: "120s",
}

THREADS = 2
CONNECTIONS = 50

RESULTS_DIR = RESULTS_BASE_DIR / Path("wrk_results")
RESULTS_DIR.mkdir(exist_ok=True)

SUMMARY_FILE = RESULTS_DIR / "summary.log"


async def run_wrk(run_number: int, config: dict[str, Any], body: str | None) -> None:
    print(f"Starting run {run_number}/{RUNS}")

    LUA_TEMPLATE = """
    wrk.method = "POST"
    wrk.body = [[{body}]]

    wrk.headers["Content-Type"] = "application/json"
    """

    threads = config.get("threads", THREADS)
    connections = config.get("connections", CONNECTIONS)
    duration = config.get("duration", DURATION)
    url = config["url"]

    cmd = [
        "wrk",
        "-t",
        str(threads),
        "-c",
        str(connections),
        "-d",
        duration,
    ]

    if body is not None:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".lua",
            delete=False,
        ) as lua_file:
            lua_file.write(LUA_TEMPLATE.format(body=body))
            lua_path = Path(lua_file.name)
        cmd.extend(["-s", str(lua_path)])

    cmd.append(url)

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    stdout, _ = await process.communicate()
    output = stdout.decode()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    run_file = RESULTS_DIR / f"run_{run_number}.txt"
    run_file.write_text(output)

    with SUMMARY_FILE.open("a") as f:
        f.write("=" * 80 + "\n")
        f.write(f"Run #{run_number}\n")
        f.write(f"Time: {timestamp}\n")
        f.write(output)
        f.write("\n\n")

    if body is not None:
        lua_path.unlink(missing_ok=True)
    print(f"Finished run {run_number}")


async def main():
    SUMMARY_FILE.write_text("")
    threads = 2
    connections = 50
    duration = 30
    config = {
        "threads": threads,
        "connections": connections,
        "duration": DURATION_MAPPING[duration],
        # "url": "http://127.0.0.1:8000/api/book-payments/in-session/no-transaction/",
        # "url": "http://127.0.0.1:8000/api/book-payments/out-session/no-transaction/",
        # "url": "http://127.0.0.1:8000/api/book-payments/in-session/no-transaction/sequential",
        # "url": "http://127.0.0.1:8000/api/book-payments/out-session/no-transaction/sequential",
        # "url": "http://127.0.0.1:8000/api/book-payments/in-session/no-transaction/parallel",
        # "url": "http://127.0.0.1:8000/api/book-payments/out-session/no-transaction/parallel",
        #
        # "url": "http://127.0.0.1:8000/api/book-payments/in-session/transaction/",
        # "url": "http://127.0.0.1:8000/api/book-payments/out-session/transaction/",
        # "url": "http://127.0.0.1:8000/api/book-payments/in-session/transaction/sequential",
        # "url": "http://127.0.0.1:8000/api/book-payments/out-session/transaction/sequential",
        # "url": "http://127.0.0.1:8000/api/book-payments/in-session/transaction/parallel",
        "url": "http://127.0.0.1:8000/api/book-payments/out-session/transaction/parallel",
    }

    body = """
    """
    # body = None

    for run in range(1, RUNS + 1):
        await run_wrk(run, config, body)
        await asyncio.sleep(1)

    print("All tests finished.")


if __name__ == "__main__":
    asyncio.run(main())
