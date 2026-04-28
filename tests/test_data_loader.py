"""Tests for services.data_loader."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest


class TestLoadSalesData:
    def test_load_from_csv_file(self, sample_csv_path: Path, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        from services.data_loader import load_sales_data

        load_sales_data.cache_clear()
        df = load_sales_data(path=sample_csv_path)

        assert len(df) == 8
        assert df.attrs["dataset_kind"] == "retail"
        assert "actual_revenue" in df.columns
        assert "date" in df.columns
        assert pd.api.types.is_datetime64_any_dtype(df["date"])
        assert (df["actual_quantity"] == 1).all()
        assert (df["local"] == df["region"]).all()

    def test_file_not_found_raises(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        from services.data_loader import load_sales_data

        load_sales_data.cache_clear()
        with pytest.raises(FileNotFoundError):
            load_sales_data(path=Path("/nonexistent/path/dataset.csv"))

    def test_required_columns_are_normalized(self, sample_df: pd.DataFrame):
        required = {
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
        assert required.issubset(set(sample_df.columns))
