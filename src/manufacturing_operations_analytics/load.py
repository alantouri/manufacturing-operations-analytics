import re
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"


def _norm(col: str) -> str:
    """Lowercase and strip everything except letters and digits."""
    return re.sub(r"[^a-z0-9]", "", str(col).lower())


OEE_MAP = {
    "shiftdate": "shift_date",
    "oee": "oee",
    "availability": "availability",
    "performance": "performance",
    "quality": "quality",
    "sumofgoodproductiontimesec": "good_prod_time",
    "sumofgoodprodction": "good_prod_time",
    "sumofgoodproduction": "good_prod_time",
    "sumofslowproductiontimesec": "slow_prod_time",
    "sumofslowproduction": "slow_prod_time",
    "sumofplannedtime": "planned_time",
    "sumofidealproductionquantity": "ideal_qty",
    "sumofidealqty": "ideal_qty",
    "sumofplannedstopstimesec": "planned_stops_time",
    "sumofunplannedstopstimesec": "unplanned_stops_time",
    "sumofgoodqty": "good_qty",
    "sumoftotalqty": "total_qty",
}

DOWNTIME_MAP = {
    "date": "date",
    "productcode": "product_code",
    "stopgroup": "stop_group",
    "stop": "stop_reason",
    "stopreason": "stop_reason",
    "stoptype": "stop_type",
    "stoplocation": "stop_location",
    "extratext": "extra_text",
    "stopstarttime": "stop_start",
    "stopendtime": "stop_end",
    "stopdurationmin": "duration_min",
    "stopdurationminttr": "duration_min",
}


def _read(filename: str, period: str) -> pd.DataFrame:
    df = pd.read_csv(RAW / filename, low_memory=False)
    df = df.dropna(axis=1, how="all").dropna(how="all")
    return df.assign(period=period)


def _coalesce(df: pd.DataFrame) -> pd.DataFrame:
    """Merge columns that share a name into one, taking the first non-null value."""
    out = {}
    for name in dict.fromkeys(df.columns):
        out[name] = df.loc[:, df.columns == name].bfill(axis=1).iloc[:, 0]
    return pd.DataFrame(out)


def _clean_oee(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=lambda c: OEE_MAP.get(_norm(c), c))
    return _coalesce(df)


def load_oee() -> pd.DataFrame:
    parts = [
        _clean_oee(_read("OEEdataset.csv", "before_LSS")),
        _clean_oee(_read("OEEdataset_afterLSS.csv", "after_LSS")),
    ]
    df = pd.concat(parts, ignore_index=True)
    df["shift_date"] = pd.to_datetime(df["shift_date"], format="mixed", errors="coerce")
    return df


def load_downtime() -> pd.DataFrame:
    parts = []
    for filename, period in [
        ("DowntimeDataset.csv", "before_LSS"),
        ("DowntimeDataset_afterLSS.csv", "after_LSS"),
    ]:
        df = _read(filename, period)
        df = df.rename(columns=lambda c: DOWNTIME_MAP.get(_norm(c), c))
        parts.append(_coalesce(df))
    df = pd.concat(parts, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    for col in ["stop_start", "stop_end"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df
