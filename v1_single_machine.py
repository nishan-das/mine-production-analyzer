"""
=================================================================
 MINE PRODUCTION & EQUIPMENT PERFORMANCE ANALYZER
 Version 1 - one machine, one day, typed in by hand
=================================================================
 NOTE: All data used with this program is SYNTHETIC (made up for
 practice). It does not represent any real mine or real company.

 Python concepts used here:
   variables, data types, input(), type conversion,
   arithmetic, if / elif / else, f-strings
=================================================================
"""

# -----------------------------------------------------------------
# STEP 1 - INPUT
# input() always gives us TEXT (a string), even if we type a number.
# So we wrap it in float() or int() to turn it into a number we can
# do maths with.
# -----------------------------------------------------------------

print("=" * 58)
print("  MINE EQUIPMENT DAILY PERFORMANCE REPORT  (v1)")
print("=" * 58)

equipment_id = input("Equipment ID (e.g. HT-01)          : ")
equipment_type = input("Equipment type (e.g. Haul Truck)   : ")

scheduled_hours = float(input("Scheduled hours for the day        : "))
downtime_hours = float(input("Downtime hours (breakdown + maint) : "))
operating_hours = float(input("Operating hours (actually working) : "))
production_tonnes = float(input("Production (tonnes)                : "))
number_of_cycles = int(input("Number of cycles / trips           : "))
fuel_consumed_litres = float(input("Fuel consumed (litres)             : "))


# -----------------------------------------------------------------
# STEP 2 - VALIDATE THE INPUT
# Never trust data. In a real mine the shift clerk types this in at
# 6 a.m. after a 12-hour shift. Mistakes happen.
# -----------------------------------------------------------------

data_is_valid = True

if scheduled_hours <= 0:
    print("\nERROR: scheduled hours must be greater than zero.")
    data_is_valid = False

if operating_hours < 0 or downtime_hours < 0 or production_tonnes < 0:
    print("\nERROR: hours and tonnes cannot be negative.")
    data_is_valid = False

if operating_hours + downtime_hours > scheduled_hours:
    print("\nWARNING: operating + downtime is MORE than scheduled hours.")
    print("         The shift log is probably wrong. Check it.")


# -----------------------------------------------------------------
# STEP 3 - SPLIT THE DAY INTO TIME BUCKETS
# This is the heart of equipment performance analysis in mining.
# Every scheduled hour of a machine's day is in exactly one bucket:
#
#   SCHEDULED = DOWNTIME  +  OPERATING  +  IDLE
#               (broken)     (working)     (fine, but not working)
# -----------------------------------------------------------------

available_hours = scheduled_hours - downtime_hours
idle_hours = available_hours - operating_hours


# -----------------------------------------------------------------
# STEP 4 - CALCULATE THE METRICS
# Notice the repeated "if bottom > 0" pattern. That is us protecting
# against ZeroDivisionError. It is ugly and repetitive on purpose -
# in Version 2 we replace all of it with ONE function.
# -----------------------------------------------------------------

# Physical Availability: of the time we PLANNED to run it, how much
# was the machine mechanically fit to run?
if scheduled_hours > 0:
    physical_availability = (available_hours / scheduled_hours) * 100
else:
    physical_availability = 0.0

# Utilisation of Availability: when the machine WAS fit to run,
# how much of that time did we actually use it?
if available_hours > 0:
    utilisation_of_availability = (operating_hours / available_hours) * 100
else:
    utilisation_of_availability = 0.0

# Effective Utilisation: of the whole scheduled day, how much was
# real productive work? This is the honest bottom-line number.
if scheduled_hours > 0:
    effective_utilisation = (operating_hours / scheduled_hours) * 100
else:
    effective_utilisation = 0.0

# Downtime percentage: how much of the scheduled day was lost to
# breakdowns and maintenance?
if scheduled_hours > 0:
    downtime_percentage = (downtime_hours / scheduled_hours) * 100
else:
    downtime_percentage = 0.0

# Productivity: tonnes moved per hour of ACTUAL operating time.
# This measures the machine + operator when they are working.
if operating_hours > 0:
    productivity_tph = production_tonnes / operating_hours
else:
    productivity_tph = 0.0

# Specific fuel consumption: litres burnt per tonne moved.
# LOWER IS BETTER. This is the efficiency number a mine manager
# actually cares about, because diesel is a huge operating cost.
if production_tonnes > 0:
    fuel_per_tonne = fuel_consumed_litres / production_tonnes
else:
    fuel_per_tonne = 0.0


# -----------------------------------------------------------------
# STEP 5 - OUTPUT THE REPORT
# f-strings let us drop a variable straight into text.
# {value:>8.2f}  means: right-align in 8 spaces, 2 decimal places.
# -----------------------------------------------------------------

if data_is_valid:
    print()
    print("-" * 58)
    print(f" Equipment : {equipment_id}   ({equipment_type})")
    print("-" * 58)
    print(" TIME BREAKDOWN")
    print(f"   Scheduled hours        : {scheduled_hours:>8.2f} h")
    print(f"   Downtime hours         : {downtime_hours:>8.2f} h")
    print(f"   Available hours        : {available_hours:>8.2f} h")
    print(f"   Operating hours        : {operating_hours:>8.2f} h")
    print(f"   Idle / standby hours   : {idle_hours:>8.2f} h")
    print("-" * 58)
    print(" PERFORMANCE METRICS")
    print(f"   Physical availability  : {physical_availability:>8.1f} %")
    print(f"   Utilisation of avail.  : {utilisation_of_availability:>8.1f} %")
    print(f"   Effective utilisation  : {effective_utilisation:>8.1f} %")
    print(f"   Downtime percentage    : {downtime_percentage:>8.1f} %")
    print("-" * 58)
    print(" PRODUCTION & FUEL")
    print(f"   Production             : {production_tonnes:>8.1f} t")
    print(f"   Productivity           : {productivity_tph:>8.1f} t/h")
    print(f"   Fuel consumed          : {fuel_consumed_litres:>8.1f} L")
    print(f"   Specific fuel consump. : {fuel_per_tonne:>8.3f} L/t")
    print("-" * 58)

    # -------------------------------------------------------------
    # STEP 6 - TURN NUMBERS INTO A DECISION
    # A number on its own is not useful. A supervisor wants to know
    # "do I need to do something about this machine today?"
    #
    # IMPORTANT: the thresholds below are ILLUSTRATIVE ONLY. Every
    # mine sets its own targets from its own historical data, its
    # equipment class and its haul profile. Do not treat 70 / 15 as
    # industry standards - they are placeholders for the logic.
    # -------------------------------------------------------------
    print(" SUPERVISOR FLAGS (thresholds are illustrative, set your own)")

    if effective_utilisation < 50:
        print("   [!] Less than half the scheduled day was productive.")
    elif effective_utilisation < 70:
        print("   [~] Moderate utilisation - room to improve.")
    else:
        print("   [OK] Utilisation is healthy against the set target.")

    if downtime_percentage > 15:
        print("   [!] High downtime - raise with the maintenance team.")

    if idle_hours > downtime_hours and idle_hours > 2:
        print("   [!] Idle time exceeds downtime. The machine was FIT to")
        print("       work but was not working - look at operator")
        print("       availability, truck-shovel matching or shift changes.")

    print("=" * 58)
