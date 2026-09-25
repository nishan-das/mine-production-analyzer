"""
=================================================================
 MINE PRODUCTION & EQUIPMENT PERFORMANCE ANALYZER  -  VERSION 2
=================================================================
 Version 1 (v1_single_machine.py) handled one machine, one day,
 typed in by hand. Version 2 reads a whole month of shift logs for
 a 10-machine fleet from CSV, using pandas.

 What it does:
   1. loads data/shift_logs.csv and reports data-quality problems
   2. computes fleet KPIs per machine:
        physical availability, utilisation of availability,
        effective utilisation, downtime %, productivity (t/h),
        specific fuel consumption (L/t)
   3. flags underperforming machines against targets you set
   4. saves a KPI table (CSV) and two charts to outputs/

 Run:   python generate_shift_logs.py    (once, makes the data)
        python fleet_analyzer.py

 *** ALL DATA IS SYNTHETIC. It does not represent any real mine. ***
=================================================================
"""

import os

import matplotlib
matplotlib.use("Agg")                      # save charts without opening a window
import matplotlib.pyplot as plt
import pandas as pd

INPUT = os.path.join("data", "shift_logs.csv")
OUTPUT_DIR = "outputs"

# ILLUSTRATIVE targets only. Every mine sets its own from its own
# history, equipment class and haul profile.
TARGETS = {
    "physical_availability_pct": 85.0,
    "effective_utilisation_pct": 70.0,
    "downtime_pct_max": 15.0,
}


def safe_divide(numerator, denominator):
    """The ONE function that replaces all the 'if bottom > 0' blocks
    from Version 1. Works on single numbers and on pandas columns."""
    if isinstance(denominator, pd.Series):
        return (numerator / denominator).where(denominator > 0, 0.0)
    return numerator / denominator if denominator > 0 else 0.0


def load_and_check(path):
    """Load shift logs and report (not hide) data-quality problems."""
    df = pd.read_csv(path, parse_dates=["date"])
    print(f"Loaded {len(df)} shift records for {df['equipment_id'].nunique()} machines.")

    missing = df[["production_tonnes", "fuel_litres"]].isna().sum()
    print(f"  Blank production cells : {missing['production_tonnes']}")
    print(f"  Blank fuel cells       : {missing['fuel_litres']}")

    over = df["operating_hours"] + df["downtime_hours"] > df["scheduled_hours"]
    print(f"  Shifts where operating + downtime > scheduled: {over.sum()}  (flagged, excluded)")
    df = df[~over].copy()

    # A blank tonnes/fuel cell means "not recorded", NOT zero. We drop
    # those rows from the tonnes-based and fuel-based ratios only.
    return df


def fleet_kpis(df):
    """Aggregate the month per machine, then compute ratios from totals
    (averaging per-shift percentages would give the wrong answer)."""
    g = df.groupby(["equipment_id", "equipment_type"])
    totals = g.agg(
        scheduled_h=("scheduled_hours", "sum"),
        downtime_h=("downtime_hours", "sum"),
        operating_h=("operating_hours", "sum"),
    )
    # tonnes and fuel only from shifts where BOTH were recorded
    complete = df.dropna(subset=["production_tonnes", "fuel_litres"])
    gc = complete.groupby(["equipment_id", "equipment_type"])
    totals["tonnes"] = gc["production_tonnes"].sum()
    totals["fuel_L"] = gc["fuel_litres"].sum()
    totals["op_h_recorded"] = gc["operating_hours"].sum()

    available = totals["scheduled_h"] - totals["downtime_h"]
    totals["physical_availability_pct"] = safe_divide(available, totals["scheduled_h"]) * 100
    totals["utilisation_of_availability_pct"] = safe_divide(totals["operating_h"], available) * 100
    totals["effective_utilisation_pct"] = safe_divide(totals["operating_h"], totals["scheduled_h"]) * 100
    totals["downtime_pct"] = safe_divide(totals["downtime_h"], totals["scheduled_h"]) * 100
    totals["productivity_tph"] = safe_divide(totals["tonnes"], totals["op_h_recorded"])
    totals["fuel_L_per_t"] = safe_divide(totals["fuel_L"], totals["tonnes"])

    # Dozers push material and log no tonnes, so t/h and L/t do not apply.
    totals.loc[totals["tonnes"] == 0, ["productivity_tph", "fuel_L_per_t"]] = float("nan")

    return totals.drop(columns=["op_h_recorded"]).round(2).reset_index()


def flag_machines(kpis):
    """Turn numbers into a decision: which machines need attention?"""
    flags = []
    for _, m in kpis.iterrows():
        reasons = []
        if m["physical_availability_pct"] < TARGETS["physical_availability_pct"]:
            reasons.append("low availability - maintenance issue")
        if m["downtime_pct"] > TARGETS["downtime_pct_max"]:
            reasons.append("high downtime")
        if (m["effective_utilisation_pct"] < TARGETS["effective_utilisation_pct"]
                and m["physical_availability_pct"] >= TARGETS["physical_availability_pct"]):
            reasons.append("fit to work but under-used - check dispatch/operators")
        flags.append("; ".join(reasons) if reasons else "OK")
    kpis["flag"] = flags
    return kpis


def save_charts(df, kpis):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    daily = df.dropna(subset=["production_tonnes"]).groupby("date")["production_tonnes"].sum()
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(daily.index, daily.values / 1000, marker="o", markersize=3)
    ax.set_ylabel("Production ('000 t)")
    ax.set_title("Daily fleet production (synthetic data)")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "daily_production.png"), dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4))
    x = range(len(kpis))
    ax.bar([i - 0.2 for i in x], kpis["physical_availability_pct"], width=0.4, label="Physical availability %")
    ax.bar([i + 0.2 for i in x], kpis["effective_utilisation_pct"], width=0.4, label="Effective utilisation %")
    ax.axhline(TARGETS["effective_utilisation_pct"], linestyle="--", linewidth=1, color="grey")
    ax.set_xticks(list(x))
    ax.set_xticklabels(kpis["equipment_id"])
    ax.set_ylabel("%")
    ax.set_title("Availability vs utilisation by machine (synthetic data)")
    ax.legend(loc="lower left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "equipment_comparison.png"), dpi=120)
    plt.close(fig)


def main():
    if not os.path.exists(INPUT):
        print(f"{INPUT} not found. Run:  python generate_shift_logs.py")
        return

    df = load_and_check(INPUT)
    kpis = flag_machines(fleet_kpis(df))

    pd.set_option("display.width", 160)
    cols = ["equipment_id", "physical_availability_pct", "effective_utilisation_pct",
            "downtime_pct", "productivity_tph", "fuel_L_per_t", "flag"]
    print("\nFLEET KPIs - June 2026 (synthetic data)")
    print(kpis[cols].to_string(index=False))

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    kpis.to_csv(os.path.join(OUTPUT_DIR, "fleet_kpis.csv"), index=False)
    save_charts(df, kpis)
    print(f"\nSaved: {OUTPUT_DIR}/fleet_kpis.csv, daily_production.png, equipment_comparison.png")


if __name__ == "__main__":
    main()
