from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

PGBOUNCER_PORT = 6432
TOTAL_CONN_MIN = 10
SAMPLES_PER_RUN = 30

RESULTS_BASE_DIR = BASE_DIR / Path("results")
RESULTS_BASE_DIR.mkdir(exist_ok=True)

CSV_FILE = RESULTS_BASE_DIR / Path("connections.csv")
SUMMARY_FILE = RESULTS_BASE_DIR / Path("summary.csv")
HEADERS = "test,total_connections,active,idle,idle_in_transaction\n"
POOL_MONITOR_FILE = RESULTS_BASE_DIR / Path("hold_ms.csv")
SUMMARY_POOL_MONITOR_FILE = RESULTS_BASE_DIR / Path("summary_hold_ms.csv")
