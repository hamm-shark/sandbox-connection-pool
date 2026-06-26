from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

CSV_FILE = BASE_DIR / Path("connections.csv")
SUMMARY_FILE = BASE_DIR / Path("summary.csv")
HEADERS = "test,total_connections,active,idle,idle_in_transaction\n"
