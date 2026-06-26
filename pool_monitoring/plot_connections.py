from pathlib import Path
import csv
import matplotlib.pyplot as plt


async def get_plot(file: Path, base_dir: Path, is_avg: bool = False) -> None:
    rows = []

    if is_avg:
        columns = {
            "total": "avg_total",
            "active": "avg_active",
            "idle": "avg_idle",
            "idle_tx": "avg_idle_tx",
        }
    else:
        columns = {
            "total": "total_connections",
            "active": "active",
            "idle": "idle",
            "idle_tx": "idle_in_transaction",
        }

    with file.open() as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            rows.append(
                {
                    "sample": i,
                    "test": row["test"],
                    "total": float(row[columns["total"]]),
                    "active": float(row[columns["active"]]),
                    "idle": float(row[columns["idle"]]),
                    "idle_tx": float(row[columns["idle_tx"]]),
                }
            )

    if not rows:
        raise SystemExit("CSV is empty")

    tests = sorted({r["test"] for r in rows})

    for test in tests:
        data = [r for r in rows if r["test"] == test]
        x = [r["sample"] for r in data]

        plt.figure(figsize=(10, 5))
        plt.plot(x, [r["active"] for r in data], label="Active")
        plt.plot(x, [r["idle"] for r in data], label="Idle")
        plt.plot(x, [r["idle_tx"] for r in data], label="Idle in transaction")
        plt.plot(x, [r["total"] for r in data], label="Total")

        plt.title(f"PostgreSQL connections ({test})")
        plt.xlabel("Sample")
        plt.ylabel("Connections")
        plt.grid(True)
        plt.legend()

        if is_avg:
            test = f"AVG_{test}"

        out = Path(f"{base_dir}/{test}.png")
        plt.tight_layout()
        plt.savefig(out)
        plt.close()
