# rules.py

def map_issue_to_root_cause(failure: str):
    failure = failure.lower()

    if "overheat" in failure:
        return "Cooling system inefficiency / blocked airflow"

    if "brake" in failure:
        return "Friction material wear / hydraulic inconsistency"

    if "battery" in failure:
        return "Cell degradation or charge imbalance"

    if "noise" in failure:
        return "Component looseness / mechanical friction"

    if "oil" in failure:
        return "Lubrication leakage or pump weakness"

    return "General mechanical anomaly"


def climate_factor(climate: str, failure: str):
    climate = (climate or "").lower()
    failure = failure.lower()

    if "hot" in climate and "overheat" in failure:
        return 0.2
    if "cold" in climate and "battery" in failure:
        return 0.1

    return 0.0
