from pathlib import Path
import csv
import matplotlib.pyplot as plt

CSV_FILE = Path("connections.csv")

rows = []

with CSV_FILE.open() as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        rows.append(
            {
                "sample": i,
                "test": row["test"],
                "total": int(row["total_connections"]),
                "active": int(row["active"]),
                "idle": int(row["idle"]),
                "idle_tx": int(row["idle_in_transaction"]),
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

    out = Path(f"{test}.png")
    plt.tight_layout()
    plt.savefig(out)
    plt.close()

    print(f"Saved {out}")

print("Done.")
