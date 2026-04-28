"""Tests for agent.tools - verifies the retail LangChain tools."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from agent.tools import build_tools
from services.analytics import AnalyticsService


@pytest.fixture
def tools(sample_df: pd.DataFrame, analytics: AnalyticsService) -> list:
    return build_tools(sample_df, analytics)


@pytest.fixture
def tool_map(tools: list) -> dict:
    return {t.name: t for t in tools}


class TestToolCount:
    def test_has_13_tools(self, tools: list):
        assert len(tools) == 13


class TestToolOutputFormat:
    ANALYTICS_TOOLS = [
        "dataset_overview",
        "top_products_by_quantity",
        "top_locations_by_quantity",
        "top_products_by_revenue",
        "top_locations_by_revenue",
        "total_sales_in_period",
        "monthly_sales_summary",
        "top_categories_by_sales",
        "top_states_by_sales",
        "top_cities_by_sales",
        "top_customers_by_sales",
        "sales_by_segment",
    ]

    @pytest.mark.parametrize("tool_name", ANALYTICS_TOOLS)
    def test_returns_valid_json(self, tool_map: dict, tool_name: str):
        result = tool_map[tool_name].invoke("")
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    @pytest.mark.parametrize("tool_name", ANALYTICS_TOOLS)
    def test_has_metric_key(self, tool_map: dict, tool_name: str):
        result = tool_map[tool_name].invoke("")
        parsed = json.loads(result)
        assert "metric" in parsed


class TestToolSpecificBehavior:
    def test_top_products_respects_n(self, tool_map: dict):
        result = json.loads(tool_map["top_products_by_quantity"].invoke("2"))
        assert len(result["data"]) == 2

    def test_total_sales_with_period(self, tool_map: dict):
        result = json.loads(
            tool_map["total_sales_in_period"].invoke("01/01/2018,31/01/2018")
        )
        assert result["num_transactions"] > 0

    def test_total_sales_empty_period(self, tool_map: dict):
        result = json.loads(
            tool_map["total_sales_in_period"].invoke("01/01/2025,31/12/2025")
        )
        assert result["num_transactions"] == 0

    def test_python_repl_exists(self, tool_map: dict):
        assert "python_repl" in tool_map

    def test_python_repl_can_access_df(self, tool_map: dict):
        repl = tool_map["python_repl"]
        result = repl.invoke("print(len(df))")
        assert "8" in result
