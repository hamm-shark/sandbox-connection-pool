from pathlib import Path

import pandas as pd


async def build_connections_summary(input_file: Path, output_file: Path) -> None:
    df = pd.read_csv(input_file)

    SAMPLES_PER_RUN = 32

    full_rows = (len(df) // SAMPLES_PER_RUN) * SAMPLES_PER_RUN
    df = df.iloc[:full_rows]

    if df.empty:
        return

    df["run"] = df.index // SAMPLES_PER_RUN
    summary = df.groupby("run", as_index=False).agg(
        test=("test", "first"),
        samples=("active", "count"),
        avg_total=("total_connections", "mean"),
        avg_active=("active", "mean"),
        avg_idle=("idle", "mean"),
        avg_idle_tx=("idle_in_transaction", "mean"),
        max_active=("active", "max"),
        max_idle=("idle", "max"),
        max_idle_tx=("idle_in_transaction", "max"),
        min_active=("active", "min"),
        min_idle=("idle", "min"),
        min_idle_tx=("idle_in_transaction", "min"),
    )

    summary = summary.round(2)

    summary.to_csv(output_file, index=False)


async def build_hold_times_summary(input_file: Path, output_file: Path) -> None:
    df = pd.read_csv(input_file, header=0, names=["hold_time_ms"])

    summary = pd.DataFrame(
        {
            "samples": [len(df)],
            "avg_hold_time_ms": [df["hold_time_ms"].mean()],
            "min_hold_time_ms": [df["hold_time_ms"].min()],
            "max_hold_time_ms": [df["hold_time_ms"].max()],
        }
    ).round(2)

    summary.to_csv(output_file, index=False)
