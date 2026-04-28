"""Shared fixtures for the retail-only test suite."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import pandas as pd
import pytest

from services.analytics import AnalyticsService


SAMPLE_CSV = """\
row_id,order_id,order_date,ship_date,ship_mode,customer_id,customer_name,segment,country,city,state,postal_code,region,product_id,category,sub_category,product_name,sales
1,CA-2018-1,01/01/2018,03/01/2018,Standard Class,C-1,Ana,Consumer,United States,New York,New York,10001,East,P-1,Technology,Phones,Phone A,100.00
2,CA-2018-2,02/01/2018,04/01/2018,Second Class,C-2,Beto,Corporate,United States,Los Angeles,California,90001,West,P-1,Technology,Phones,Phone A,150.00
3,CA-2018-3,03/01/2018,05/01/2018,First Class,C-1,Ana,Consumer,United States,New York,New York,10001,East,P-2,Furniture,Chairs,Chair B,200.00
4,CA-2018-4,15/02/2018,17/02/2018,Standard Class,C-3,Carlos,Home Office,United States,Austin,Texas,73301,Central,P-2,Furniture,Chairs,Chair B,180.00
5,CA-2018-5,20/02/2018,22/02/2018,Same Day,C-4,Diana,Consumer,United States,Seattle,Washington,98101,West,P-2,Furniture,Chairs,Chair B,220.00
6,CA-2018-6,21/02/2018,24/02/2018,Standard Class,C-5,Elisa,Corporate,United States,Miami,Florida,33101,South,P-3,Office Supplies,Binders,Binder C,50.00
7,CA-2018-7,01/03/2018,03/03/2018,Standard Class,C-6,Fabio,Consumer,United States,Miami,Florida,33101,South,P-3,Office Supplies,Binders,Binder C,70.00
8,CA-2018-8,10/03/2018,12/03/2018,Second Class,C-7,Gabi,Consumer,United States,Dallas,Texas,73301,Central,P-4,Technology,Accessories,Accessory D,300.00
"""


@pytest.fixture
def sample_csv_path(tmp_path: Path) -> Path:
    csv_file = tmp_path / "retail_sample.csv"
    csv_file.write_text(SAMPLE_CSV, encoding="utf-8")
    return csv_file


@pytest.fixture
def sample_df() -> pd.DataFrame:
    df = pd.read_csv(StringIO(SAMPLE_CSV))
    df.columns = df.columns.str.strip().str.lower()
    df["date"] = pd.to_datetime(df["order_date"], dayfirst=True)
    df["row_id"] = df["row_id"].astype(int)
    df["postal_code"] = df["postal_code"].astype(int)
    df["sales"] = df["sales"].astype(float)
    df["local"] = df["region"].astype(str).str.strip()
    df["actual_quantity"] = 1
    df["actual_revenue"] = df["sales"]
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%B")
    df["quarter"] = df["date"].dt.quarter
    df.attrs["dataset_kind"] = "retail"
    df.attrs["dataset_display_name"] = "Retail Sales"
    return df


@pytest.fixture
def analytics(sample_df: pd.DataFrame) -> AnalyticsService:
    return AnalyticsService(sample_df)
