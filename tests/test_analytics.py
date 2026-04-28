"""Tests for services.analytics.AnalyticsService."""

from __future__ import annotations

from services.analytics import AnalyticsService


class TestTopProducts:
    def test_top_products_by_quantity_order(self, analytics: AnalyticsService):
        result = analytics.top_products_by_quantity(n=3)
        units = [row["units_sold"] for row in result["data"]]
        assert units == sorted(units, reverse=True)

    def test_top_product_by_quantity(self, analytics: AnalyticsService):
        result = analytics.top_products_by_quantity(n=1)
        top = result["data"][0]
        assert top["product_name"] == "Chair B"
        assert top["units_sold"] == 3

    def test_top_products_by_revenue(self, analytics: AnalyticsService):
        result = analytics.top_products_by_revenue(n=2)
        assert result["metric"] == "top_products_by_revenue"
        assert len(result["data"]) == 2
        assert result["data"][0]["revenue"] >= result["data"][1]["revenue"]


class TestTopLocations:
    def test_top_locations_by_quantity(self, analytics: AnalyticsService):
        result = analytics.top_locations_by_quantity(n=2)
        assert len(result["data"]) == 2
        assert all("local" in row for row in result["data"])

    def test_top_locations_by_revenue(self, analytics: AnalyticsService):
        result = analytics.top_locations_by_revenue(n=2)
        assert len(result["data"]) == 2


class TestRetailAnalysis:
    def test_categories_by_sales(self, analytics: AnalyticsService):
        result = analytics.top_categories_by_sales(n=1)
        assert result["data"][0]["category"] == "Furniture"

    def test_customers_by_sales(self, analytics: AnalyticsService):
        result = analytics.top_customers_by_sales(n=1)
        assert "customer_name" in result["data"][0]

    def test_segment_summary(self, analytics: AnalyticsService):
        result = analytics.sales_by_segment()
        assert result["metric"] == "sales_by_segment"
        assert len(result["data"]) > 0


class TestPeriodAnalysis:
    def test_total_sales_no_filter(self, analytics: AnalyticsService):
        result = analytics.total_sales_in_period()
        assert result["num_transactions"] == 8
        assert result["total_actual_quantity"] == 8
        assert result["total_actual_revenue"] == 1270.0

    def test_total_sales_with_date_filter(self, analytics: AnalyticsService):
        result = analytics.total_sales_in_period(
            start_date="01/02/2018",
            end_date="28/02/2018",
        )
        assert result["num_transactions"] == 3
        assert result["total_actual_revenue"] == 450.0

    def test_monthly_sales_summary(self, analytics: AnalyticsService):
        result = analytics.monthly_sales_summary()
        assert result["metric"] == "monthly_sales_summary"
        assert len(result["data"]) == 3
        first_month = result["data"][0]
        assert "total_sales" in first_month
        assert "avg_sales" in first_month


class TestUnavailableMetrics:
    def test_planned_vs_actual_is_unavailable(self, analytics: AnalyticsService):
        result = analytics.planned_vs_actual_summary()
        assert result["available"] is False

    def test_promotion_impact_is_unavailable(self, analytics: AnalyticsService):
        result = analytics.promotion_impact()
        assert result["available"] is False

    def test_service_level_is_unavailable(self, analytics: AnalyticsService):
        result = analytics.service_level_stats()
        assert result["available"] is False


class TestDatasetOverview:
    def test_overview_values(self, analytics: AnalyticsService):
        result = analytics.dataset_overview()
        assert result["total_rows"] == 8
        assert result["unique_products"] == 4
        assert result["unique_orders"] == 8
        assert result["unique_regions"] == 4

    def test_columns_list(self, analytics: AnalyticsService):
        result = analytics.dataset_overview()
        assert "product_id" in result["columns"]
        assert "actual_revenue" in result["columns"]

