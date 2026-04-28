from __future__ import annotations

import logging
import re
from functools import lru_cache
from pathlib import Path

import pandas as pd

from config.settings import get_settings

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {
    "row_id",
    "order_id",
    "order_date",
    "ship_date",
    "ship_mode",
    "customer_id",
    "customer_name",
    "segment",
    "country",
    "city",
    "state",
    "postal_code",
    "region",
    "product_id",
    "category",
    "sub_category",
    "product_name",
    "sales",
}


def _snake_case(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^0-9a-z]+", "_", value)
    return re.sub(r"_+", "_", value).strip("_")


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [_snake_case(col) for col in df.columns]
    return df


def _read_csv_with_fallbacks(csv_path: Path, settings) -> pd.DataFrame:
    separators: list[str] = []
    if settings.csv_separator:
        separators.append(settings.csv_separator)
    separators.extend([",", ";", "\t", "|"])

    seen: set[str] = set()
    last_error: Exception | None = None

    for sep in separators:
        if sep in seen:
            continue
        seen.add(sep)

        try:
            candidate = pd.read_csv(
                csv_path,
                sep=sep,
                encoding=settings.csv_encoding,
                low_memory=False,
            )
            normalised = _normalise_columns(candidate)
            if REQUIRED_COLUMNS.issubset(set(normalised.columns)):
                logger.info("Detected CSV separator '%s' for retail dataset", sep)
                return normalised
        except Exception as exc:
            last_error = exc

    if last_error is not None:
        raise last_error

    raise ValueError(
        "Could not detect the retail dataset schema. Check the file path, "
        "delimiter and column names."
    )


def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = _normalise_columns(df)

    missing = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing:
        raise ValueError(f"Retail dataset is missing required columns: {missing}")

    df = df.copy()
    df["date"] = pd.to_datetime(df["order_date"], dayfirst=True, errors="coerce")
    if df["date"].isna().any():
        invalid = int(df["date"].isna().sum())
        raise ValueError(f"Could not parse {invalid} order_date values in retail dataset")

    df["row_id"] = pd.to_numeric(df["row_id"], errors="coerce").fillna(0).astype(int)
    df["postal_code"] = pd.to_numeric(df["postal_code"], errors="coerce").fillna(0).astype(int)
    df["sales"] = pd.to_numeric(df["sales"], errors="coerce").fillna(0.0)

    df["product_id"] = df["product_id"].astype(str).str.strip()
    df["product_name"] = df["product_name"].astype(str).str.strip()
    df["customer_id"] = df["customer_id"].astype(str).str.strip()
    df["customer_name"] = df["customer_name"].astype(str).str.strip()
    df["segment"] = df["segment"].astype(str).str.strip()
    df["country"] = df["country"].astype(str).str.strip()
    df["city"] = df["city"].astype(str).str.strip()
    df["state"] = df["state"].astype(str).str.strip()
    df["region"] = df["region"].astype(str).str.strip()
    df["local"] = df["region"]

    df["actual_quantity"] = 1
    df["actual_revenue"] = df["sales"]
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%B")
    df["quarter"] = df["date"].dt.quarter

    df.attrs["dataset_kind"] = "retail"
    df.attrs["dataset_display_name"] = "Retail Sales"
    df.attrs["location_column"] = "region"

    logger.info("Retail DataFrame loaded: %d rows x %d columns", len(df), len(df.columns))
    return df


@lru_cache(maxsize=1)
def load_sales_data(path: Path | None = None) -> pd.DataFrame:
    """Load, validate and enrich the retail sales CSV into a pandas DataFrame."""
    settings = get_settings()
    csv_path = Path(path) if path else settings.csv_path

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    logger.info("Loading retail CSV from %s", csv_path)
    df = _read_csv_with_fallbacks(csv_path, settings)
    return _clean_dataframe(df)
