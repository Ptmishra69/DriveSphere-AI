# rules.py

def map_issue_to_root_cause(failure: str):
    failure = failure.lower()

    if "overheat" in failure:
        return "Cooling system inefficiency or airflow blockage"

    if "brake" in failure:
        return "Friction material degradation or rotor wear"

    if "battery" in failure:
        return "Cell degradation or alternator undercharging"

    if "oil" in failure:
        return "Lubrication system leak or worn pump"

    return "Unknown, requires technician review"


def climate_factor(climate: str, failure: str):
    climate = (climate or "").lower()
    failure = failure.lower()

    if "hot" in climate and "overheat" in failure:
        return 0.15  # boost confidence
    return 0.0
