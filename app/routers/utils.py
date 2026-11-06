from typing import Any, Dict, List, Union

import pandas as pd


def clean_value(v: Any) -> Any:
    """pandas NA / NaN -> None, numpy scalars -> plain Python (JSON can't encode NaN)."""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(v, "item"):
        return v.item()
    return v


def records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """DataFrame -> list of JSON-safe dicts."""
    return [{k: clean_value(v) for k, v in row.items()} for row in df.to_dict(orient="records")]


def unique_values(series: pd.Series) -> List[Any]:
    """Distinct non-empty values, sorted."""
    return sorted(clean_value(v) for v in series.dropna().unique())


def as_json(obj: Union[pd.DataFrame, pd.Series, List], title: str = "items") -> Any:
    if isinstance(obj, pd.DataFrame):
        return records(obj)
    if isinstance(obj, pd.Series):
        return [clean_value(v) for v in obj.tolist()]
    if isinstance(obj, list):
        return {title: [clean_value(v) for v in obj]}
    return obj


def matches(series: pd.Series, value: str) -> pd.Series:
    """Case-insensitive, whitespace-tolerant equality (works for 'mark evans', 'McArthur', 'DJ', ...)."""
    return series.astype(str).str.strip().str.casefold() == value.strip().casefold()
