"""LangChain tools that wrap retail analytics service methods."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
from langchain_core.tools import tool
from langchain_experimental.tools.python.tool import PythonAstREPLTool

from services.analytics import AnalyticsService


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _safe_int(value: str, default: int = 10) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def build_tools(df: pd.DataFrame, analytics: AnalyticsService) -> list:
    """Build the retail-only set of LangChain tools used by the agent."""

    @tool
    def dataset_overview(query: str = "") -> str:
        """Get a high-level overview of the retail dataset."""
        return _json(analytics.dataset_overview())

    @tool
    def top_products_by_quantity(n: str = "10") -> str:
        """Return the top N products ranked by total units sold."""
        return _json(analytics.top_products_by_quantity(_safe_int(n)))

    @tool
    def top_locations_by_quantity(n: str = "10") -> str:
        """Return the top N regions ranked by total units sold."""
        return _json(analytics.top_locations_by_quantity(_safe_int(n)))

    @tool
    def top_products_by_revenue(n: str = "10") -> str:
        """Return the top N products ranked by total revenue."""
        return _json(analytics.top_products_by_revenue(_safe_int(n)))

    @tool
    def top_locations_by_revenue(n: str = "10") -> str:
        """Return the top N regions ranked by total revenue."""
        return _json(analytics.top_locations_by_revenue(_safe_int(n)))

    @tool
    def total_sales_in_period(period: str = "") -> str:
        """Get total sales for a date range.
        Input: 'start_date,end_date' in DD/MM/YYYY format.
        Either date can be empty. Examples: '01/01/2012,31/12/2012' or ',31/12/2012'."""
        parts = [p.strip() for p in period.split(",")]
        start = parts[0] if len(parts) > 0 and parts[0] else None
        end = parts[1] if len(parts) > 1 and parts[1] else None
        return _json(analytics.total_sales_in_period(start, end))

    @tool
    def monthly_sales_summary(query: str = "") -> str:
        """Get a monthly breakdown of total revenue, average revenue and number of transactions."""
        return _json(analytics.monthly_sales_summary())

    @tool
    def top_categories_by_sales(n: str = "10") -> str:
        """Return the top N product categories ranked by sales revenue."""
        return _json(analytics.top_categories_by_sales(_safe_int(n)))

    @tool
    def top_states_by_sales(n: str = "10") -> str:
        """Return the top N states ranked by sales revenue."""
        return _json(analytics.top_states_by_sales(_safe_int(n)))

    @tool
    def top_cities_by_sales(n: str = "10") -> str:
        """Return the top N cities ranked by sales revenue."""
        return _json(analytics.top_cities_by_sales(_safe_int(n)))

    @tool
    def top_customers_by_sales(n: str = "10") -> str:
        """Return the top N customers ranked by sales revenue."""
        return _json(analytics.top_customers_by_sales(_safe_int(n)))

    @tool
    def sales_by_segment(query: str = "") -> str:
        """Summarize sales by customer segment."""
        return _json(analytics.sales_by_segment())

    tools = [
        dataset_overview,
        top_products_by_quantity,
        top_locations_by_quantity,
        top_products_by_revenue,
        top_locations_by_revenue,
        total_sales_in_period,
        monthly_sales_summary,
        top_categories_by_sales,
        top_states_by_sales,
        top_cities_by_sales,
        top_customers_by_sales,
        sales_by_segment,
    ]

    python_repl = PythonAstREPLTool(
        locals={"df": df},
        name="python_repl",
        description=(
            "Execute Python/pandas code on the DataFrame `df` for custom "
            "analysis that the other tools cannot handle. Always print() "
            "results so they appear in the output."
        ),
    )

    tools.append(python_repl)
    return tools
