"""
=================================================================
 MINE PRODUCTION ANALYZER  -  SYNTHETIC SHIFT-LOG GENERATOR
=================================================================
 Creates data/shift_logs.csv: 30 days x 3 shifts x 10 machines of
 made-up shift records for a fictional opencast mine.

 *** ALL DATA IS SYNTHETIC. It does not represent any real mine. ***

 A few problems are planted on purpose, because real shift logs
 are messy and the analyzer must cope with them:
   - some blank cells (clerk forgot to fill them in)
   - one machine with chronic breakdowns (DT-04)
   - one machine that is healthy but sits idle a lot (DT-07)
   - a few shifts where operating + downtime > scheduled hours

 Run:   python generate_shift_logs.py
=================================================================
"""

import csv
import os
import random
from datetime import date, timedelta

random.seed(7)                     # fixed seed = same data every run

OUTPUT = os.path.join("data", "shift_logs.csv")
SHIFT_HOURS = 8.0
START = date(2026, 6, 1)
DAYS = 30

# equipment_id, type, typical t/h when working, typical L/h fuel burn
FLEET = [
    ("SH-01", "Hydraulic Shovel", 900, 95),
    ("SH-02", "Hydraulic Shovel", 880, 98),
    ("DT-01", "Dumper 100 t", 310, 60),
    ("DT-02", "Dumper 100 t", 300, 62),
    ("DT-03", "Dumper 100 t", 305, 61),
    ("DT-04", "Dumper 100 t", 295, 64),   # breaks down a lot
    ("DT-05", "Dumper 100 t", 310, 60),
    ("DT-06", "Dumper 100 t", 300, 63),
    ("DT-07", "Dumper 100 t", 305, 61),   # fit to work, but often idle
    ("DZ-01", "Dozer", 0, 45),             # dozers push material, no tonnes logged
]


def one_shift(equipment_id, tph, fuel_lph):
    """Return downtime, operating hours, tonnes, cycles, fuel for one shift."""
    if equipment_id == "DT-04":
        downtime = round(random.uniform(1.5, 4.5), 1)
    else:
        downtime = round(random.choice([0, 0, 0, 0.5, 1.0, random.uniform(0, 2)]), 1)

    idle = random.uniform(1.5, 3.5) if equipment_id == "DT-07" else random.uniform(0.3, 1.2)
    operating = round(max(SHIFT_HOURS - downtime - idle, 0), 1)

    tonnes = round(operating * tph * random.uniform(0.85, 1.1), 0)
    cycles = int(tonnes / 100) if equipment_id.startswith("DT") else 0
    fuel = round(operating * fuel_lph * random.uniform(0.9, 1.15) + idle * 8, 0)
    return downtime, operating, tonnes, cycles, fuel


def main():
    os.makedirs("data", exist_ok=True)
    rows = []
    for d in range(DAYS):
        day = START + timedelta(days=d)
        for shift in ("A", "B", "C"):
            for equipment_id, eq_type, tph, fuel_lph in FLEET:
                downtime, operating, tonnes, cycles, fuel = one_shift(equipment_id, tph, fuel_lph)
                rows.append([day.isoformat(), shift, equipment_id, eq_type,
                             SHIFT_HOURS, downtime, operating, tonnes, cycles, fuel])

    # --- plant realistic mistakes -------------------------------
    for row in random.sample(rows, 12):
        row[random.choice([7, 9])] = ""          # blank tonnes or fuel
    for row in random.sample(rows, 4):
        row[6] = row[4] - row[5] + 1.5           # operating + downtime > scheduled

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "shift", "equipment_id", "equipment_type",
                         "scheduled_hours", "downtime_hours", "operating_hours",
                         "production_tonnes", "cycles", "fuel_litres"])
        writer.writerows(rows)

    print(f"Wrote {len(rows)} shift records to {OUTPUT} (synthetic data)")


if __name__ == "__main__":
    main()
