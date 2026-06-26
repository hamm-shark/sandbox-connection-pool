from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

CSV_FILE = BASE_DIR / Path("connections.csv")
SUMMARY_FILE = BASE_DIR / Path("summary.csv")
HEADERS = "test,total_connections,active,idle,idle_in_transaction\n"
POOL_MONITOR_FILE = BASE_DIR / Path("hold_ms.csv")
SUMMARY_POOL_MONITOR_FILE = BASE_DIR / Path("summary_hold_ms.csv")
