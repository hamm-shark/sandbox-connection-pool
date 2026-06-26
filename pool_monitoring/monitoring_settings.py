from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

CSV_FILE = BASE_DIR / Path("connections.csv")
HEADERS = "test,total_connections,active,idle,idle_in_transaction\n"
