from __future__ import annotations

from typing import Any

import pandas as pd


class AnalyticsService:
    """Retail analytics built on top of the normalized sales DataFrame."""

    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df
        self._dataset_kind = "retail"

    def _unavailable(self, metric: str, message: str) -> dict[str, Any]:
        return {
            "metric": metric,
            "dataset_kind": self._dataset_kind,
            "available": False,
            "message": message,
        }

    def _product_ranking(self, sort_column: str, n: int) -> list[dict[str, Any]]:
        ranking = (
            self._df.groupby("product_id", as_index=False)
            .agg(
                product_name=("product_name", "first"),
                units_sold=("actual_quantity", "sum"),
                revenue=("actual_revenue", "sum"),
            )
            .sort_values(sort_column, ascending=False)
            .head(n)
        )
        return ranking.to_dict(orient="records")

    def _group_ranking(self, column: str, n: int) -> list[dict[str, Any]]:
        ranking = (
            self._df.groupby(column, as_index=False)["actual_revenue"]
            .sum()
            .sort_values("actual_revenue", ascending=False)
            .head(n)
        )
        return ranking.to_dict(orient="records")

    def top_products_by_quantity(self, n: int = 10) -> dict[str, Any]:
        return {
            "metric": "top_products_by_quantity",
            "dataset_kind": self._dataset_kind,
            "data": self._product_ranking("units_sold", n),
        }

    def top_locations_by_quantity(self, n: int = 10) -> dict[str, Any]:
        ranking = (
            self._df.groupby("region", as_index=False)["actual_quantity"]
            .sum()
            .sort_values("actual_quantity", ascending=False)
            .head(n)
        )
        ranking = ranking.rename(columns={"region": "local"})
        return {
            "metric": "top_locations_by_quantity",
            "dataset_kind": self._dataset_kind,
            "data": ranking.to_dict(orient="records"),
        }

    def top_products_by_revenue(self, n: int = 10) -> dict[str, Any]:
        return {
            "metric": "top_products_by_revenue",
            "dataset_kind": self._dataset_kind,
            "data": self._product_ranking("revenue", n),
        }

    def top_locations_by_revenue(self, n: int = 10) -> dict[str, Any]:
        ranking = (
            self._df.groupby("region", as_index=False)["actual_revenue"]
            .sum()
            .sort_values("actual_revenue", ascending=False)
            .head(n)
        )
        ranking = ranking.rename(columns={"region": "local"})
        return {
            "metric": "top_locations_by_revenue",
            "dataset_kind": self._dataset_kind,
            "data": ranking.to_dict(orient="records"),
        }

    def top_categories_by_sales(self, n: int = 10) -> dict[str, Any]:
        return {
            "metric": "top_categories_by_sales",
            "dataset_kind": self._dataset_kind,
            "data": self._group_ranking("category", n),
        }

    def top_states_by_sales(self, n: int = 10) -> dict[str, Any]:
        return {
            "metric": "top_states_by_sales",
            "dataset_kind": self._dataset_kind,
            "data": self._group_ranking("state", n),
        }

    def top_cities_by_sales(self, n: int = 10) -> dict[str, Any]:
        return {
            "metric": "top_cities_by_sales",
            "dataset_kind": self._dataset_kind,
            "data": self._group_ranking("city", n),
        }

    def top_customers_by_sales(self, n: int = 10) -> dict[str, Any]:
        ranking = (
            self._df.groupby("customer_name", as_index=False)["actual_revenue"]
            .sum()
            .sort_values("actual_revenue", ascending=False)
            .head(n)
        )
        return {
            "metric": "top_customers_by_sales",
            "dataset_kind": self._dataset_kind,
            "data": ranking.to_dict(orient="records"),
        }

    def sales_by_segment(self) -> dict[str, Any]:
        summary = (
            self._df.groupby("segment", as_index=False)
            .agg(
                total_sales=("actual_revenue", "sum"),
                avg_sales=("actual_revenue", "mean"),
                num_transactions=("product_id", "count"),
            )
            .sort_values("total_sales", ascending=False)
        )
        return {
            "metric": "sales_by_segment",
            "dataset_kind": self._dataset_kind,
            "data": summary.to_dict(orient="records"),
        }

    def total_sales_in_period(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        df = self._df.copy()
        if start_date:
            df = df[df["date"] >= pd.to_datetime(start_date, dayfirst=True)]
        if end_date:
            df = df[df["date"] <= pd.to_datetime(end_date, dayfirst=True)]

        return {
            "metric": "total_sales_in_period",
            "dataset_kind": self._dataset_kind,
            "start_date": start_date,
            "end_date": end_date,
            "total_actual_quantity": int(df["actual_quantity"].sum()),
            "total_actual_revenue": float(df["actual_revenue"].sum()),
            "num_transactions": len(df),
        }

    def monthly_sales_summary(self) -> dict[str, Any]:
        summary = (
            self._df.groupby(["year", "month", "month_name"], as_index=False)
            .agg(
                total_sales=("actual_revenue", "sum"),
                avg_sales=("actual_revenue", "mean"),
                num_transactions=("product_id", "count"),
            )
            .sort_values(["year", "month"])
        )
        return {
            "metric": "monthly_sales_summary",
            "dataset_kind": self._dataset_kind,
            "data": summary.to_dict(orient="records"),
        }

    def planned_vs_actual_summary(self) -> dict[str, Any]:
        return self._unavailable(
            "planned_vs_actual_summary",
            "The retail dataset does not include planned quantities or prices, so planned-vs-actual analysis is not available.",
        )

    def planned_vs_actual_by_product(self, n: int = 10) -> dict[str, Any]:
        return self._unavailable(
            "planned_vs_actual_by_product",
            "The retail dataset does not include planned quantities, so the comparison by product is not available.",
        )

    def promotion_impact(self) -> dict[str, Any]:
        return self._unavailable(
            "promotion_impact",
            "The retail dataset does not include promotion columns, so promotion analysis is not available.",
        )

    def service_level_stats(self) -> dict[str, Any]:
        return self._unavailable(
            "service_level_statistics",
            "The retail dataset does not include service level values.",
        )

    def service_level_by_location(self) -> dict[str, Any]:
        return self._unavailable(
            "service_level_by_location",
            "The retail dataset does not include service level values.",
        )

    def dataset_overview(self) -> dict[str, Any]:
        df = self._df
        return {
            "metric": "dataset_overview",
            "dataset_kind": self._dataset_kind,
            "total_rows": len(df),
            "unique_products": int(df["product_id"].nunique()),
            "unique_orders": int(df["order_id"].nunique()),
            "unique_regions": int(df["region"].nunique()),
            "unique_states": int(df["state"].nunique()),
            "unique_cities": int(df["city"].nunique()),
            "unique_categories": int(df["category"].nunique()),
            "unique_sub_categories": int(df["sub_category"].nunique()),
            "unique_segments": int(df["segment"].nunique()),
            "unique_customers": int(df["customer_name"].nunique()),
            "date_range": {
                "min": str(df["date"].min().date()),
                "max": str(df["date"].max().date()),
            },
            "columns": df.columns.tolist(),
        }
