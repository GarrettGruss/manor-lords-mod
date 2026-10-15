"""Shared helpers to read exported data table JSON in compact form (spec 18, issue #104)."""

JSON_PATH = "C:/Users/garre/development/manor-lords-mod/modtools/work/json/ManorLords/Content/NotStronghold/Data/buildingStats.json"
SKIP_FIELDS = {"panelImage", "panelImageV2", "buildingImage", "purposeIcon", "SFX", "gatheringSpot", "range", "rangeType"}


def value_of(item):
    if isinstance(item, dict) and "Value" in item:
        value = item["Value"]
        if isinstance(value, list):
            if value and all(isinstance(s, dict) and "Name" in s for s in value):
                return {s["Name"]: value_of(s) for s in value}
            return [value_of(s) if isinstance(s, dict) else [value_of(t) for t in s] for s in value]
        return value
    return item


def short(value):
    if isinstance(value, dict) and "AssetPath" in value:
        return value["AssetPath"]["PackageName"].rsplit("/", 1)[-1] + ":" + str(value["AssetPath"]["AssetName"])
    if isinstance(value, dict):
        return {k: short(v) for k, v in value.items() if k != "$type"}
    if isinstance(value, list):
        return [short(v) for v in value]
    return value


def row_of(raw_row):
    return {item["Name"]: short(value_of(item)) for item in raw_row["Value"] if item["Name"] not in SKIP_FIELDS}
