"""
Phase 1 / Step 2 - Explore the AIOps Challenge (KPI Anomaly Detection) dataset.

Run:
    python scripts/explore_dataset.py
"""
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "KPI-Anomaly-Detection" / "Preliminary_dataset"
TRAIN_PATH = DATA_DIR / "train.csv"
TEST_PATH = DATA_DIR / "test.csv"


def load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")
    return df


def explore(df: pd.DataFrame, name: str) -> None:
    print(f"\n{'='*60}\n{name}\n{'='*60}")
    print(f"Rows: {len(df):,}")
    print(f"Unique KPI IDs (services): {df['KPI ID'].nunique()}")
    print(f"Date range: {df['datetime'].min()} -> {df['datetime'].max()}")
    if "label" in df.columns:
        anomaly_rate = df["label"].mean()
        print(f"Overall anomaly rate: {anomaly_rate:.2%}")

    print("\nPer-KPI breakdown (first 10):")
    grouped = df.groupby("KPI ID")
    for i, (kpi_id, g) in enumerate(grouped):
        if i >= 10:
            print(f"  ... and {df['KPI ID'].nunique() - 10} more KPIs")
            break
        interval = g["timestamp"].diff().median()
        line = f"  {kpi_id[:12]}...  points={len(g):>7,}  interval={interval:>5.0f}s"
        if "label" in g.columns:
            line += f"  anomaly_rate={g['label'].mean():.2%}"
        print(line)


if __name__ == "__main__":
    print("Loading train.csv (has labels)...")
    train = load(TRAIN_PATH)
    explore(train, "TRAIN SET")

    print("\nLoading test.csv (no labels - this is what you'd predict on)...")
    test = load(TEST_PATH)
    explore(test, "TEST SET")

    # Save a small parquet copy for fast reloading in later steps
    out_dir = Path(__file__).resolve().parent.parent / "data"
    train.to_parquet(out_dir / "train.parquet", index=False)
    test.to_parquet(out_dir / "test.parquet", index=False)
    print(f"\nSaved fast-loading parquet copies to {out_dir}/train.parquet and test.parquet")