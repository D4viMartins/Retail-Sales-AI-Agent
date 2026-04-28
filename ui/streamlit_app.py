"""Streamlit chat interface for the Retail Sales AI Agent."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.csv_agent import SalesAgent
from services.data_loader import load_sales_data


st.set_page_config(
    page_title="Retail Sales AI Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; }
    .metric-box {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 16px 20px;
        text-align: center;
    }
    .metric-box .label {
        font-size: 0.8rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin: 0;
    }
    .metric-box .value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #212529;
        margin: 4px 0 0 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

PLOTLY_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=12),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(showgrid=False),
    yaxis=dict(gridcolor="rgba(128,128,128,0.15)", gridwidth=1),
    colorway=["#228be6", "#40c057", "#fab005", "#fa5252", "#7950f2", "#20c997"],
)


def _format_currency(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@st.cache_resource(show_spinner="Carregando dados de vendas...")
def get_dataframe() -> pd.DataFrame:
    return load_sales_data()


@st.cache_resource(show_spinner="Inicializando agente de IA...")
def get_agent() -> SalesAgent:
    return SalesAgent(get_dataframe())


RETAIL_SUGGESTIONS = [
    "Qual categoria teve maior faturamento?",
    "Quais foram as 3 categorias que mais venderam?",
    "Qual região teve maior faturamento?",
    "Mostre os 5 estados com maior receita",
    "Qual cidade teve maior receita?",
    "Quais clientes compraram mais?",
    "Mostre as vendas por segmento",
    "Qual foi a receita total por mês?",
    "Quais foram os 3 produtos mais vendidos?",
]


def _format_trace_caption(trace: dict) -> str:
    return (
        f"Tempo {trace['total_duration_ms']:.0f}ms | "
        f"Tools {len(trace['tool_calls'])} | "
        f"Tokens {trace['tokens']['total']:,} | "
        f"Custo ${trace['estimated_cost_usd']:.4f}"
    )


with st.sidebar:
    st.title("Retail Sales AI Agent")
    st.caption("Análise com IA")
    st.divider()

    df = get_dataframe()
    st.markdown("**Dataset:** Retail Sales")
    st.markdown(f"**{len(df):,}** registros")
    st.markdown(f"**{df['product_id'].nunique():,}** produtos")
    st.markdown(f"**{df['order_id'].nunique():,}** pedidos únicos")
    st.markdown(f"**{df['category'].nunique():,}** categorias")
    st.markdown(f"**{df['region'].nunique():,}** regiões")
    st.markdown(f"**{df['customer_name'].nunique():,}** clientes")
    st.markdown(f"**{df['date'].min().date()}** → **{df['date'].max().date()}**")

    st.divider()
    st.markdown("##### Perguntas sugeridas")
    for suggestion in RETAIL_SUGGESTIONS:
        if st.button(suggestion, key=f"sug_{suggestion}", type="tertiary"):
            st.session_state["pending_question"] = suggestion

    st.divider()
    st.markdown("##### Sessão")
    agent = get_agent()
    tracker = agent.tracker
    st.markdown(f"Perguntas: **{tracker.total_queries}**")
    st.markdown(f"Tokens: **{tracker.total_tokens_used:,}**")
    st.markdown(f"Custo: **${tracker.total_cost_usd:.4f}**")

    st.divider()
    st.caption("Powered by LangChain + OpenAI")


st.title("Retail Sales AI Agent")
st.caption("Faça perguntas sobre os dados em linguagem natural")


tab_chat, tab_dashboard, tab_trace = st.tabs(["Chat", "Dashboard", "Tracking"])


with tab_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = None
    if "pending_query" not in st.session_state:
        st.session_state.pending_query = None
    if "traces" not in st.session_state:
        st.session_state.traces = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("trace"):
                st.caption(_format_trace_caption(msg["trace"]))

    if st.session_state.pending_query:
        query = st.session_state.pending_query
        st.session_state.pending_query = None
        with st.chat_message("assistant"):
            with st.spinner("Analisando..."):
                agent = get_agent()
                result = agent.ask(
                    question=query,
                    conversation_id=st.session_state.conversation_id,
                )
                answer = result["answer"]
                trace_dict = result["trace"].to_dict()
                st.session_state.conversation_id = result["conversation_id"]
            st.markdown(answer)
            st.caption(_format_trace_caption(trace_dict))
        st.session_state.messages.append({"role": "assistant", "content": answer, "trace": trace_dict})
        st.session_state.traces.append(trace_dict)

    pending = st.session_state.pop("pending_question", None)
    prompt = st.chat_input("Faça uma pergunta sobre os dados...") or pending

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.pending_query = prompt
        st.rerun()


with tab_dashboard:
    df = get_dataframe()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f'<div class="metric-box"><p class="label">Receita Total</p>'
            f'<p class="value">{_format_currency(df["actual_revenue"].sum())}</p></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="metric-box"><p class="label">Pedidos Únicos</p>'
            f'<p class="value">{df["order_id"].nunique():,}</p></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="metric-box"><p class="label">Produtos</p>'
            f'<p class="value">{df["product_id"].nunique():,}</p></div>',
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f'<div class="metric-box"><p class="label">Clientes</p>'
            f'<p class="value">{df["customer_name"].nunique():,}</p></div>',
            unsafe_allow_html=True,
        )

    st.markdown("")
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("##### Top 10 Produtos por Receita")
        top_prod = (
            df.groupby("product_name", as_index=False)["actual_revenue"]
            .sum()
            .sort_values(ascending=True, by="actual_revenue")
            .tail(10)
        )
        fig1 = px.bar(
            top_prod,
            x="actual_revenue",
            y="product_name",
            orientation="h",
            color_discrete_sequence=["#228be6"],
        )
        fig1.update_layout(**PLOTLY_LAYOUT, yaxis_title="", xaxis_title="Receita (R$)")
        st.plotly_chart(fig1, width="stretch")

    with col_r:
        st.markdown("##### Top 10 Estados por Receita")
        top_states = (
            df.groupby("state", as_index=False)["actual_revenue"]
            .sum()
            .sort_values(ascending=True, by="actual_revenue")
            .tail(10)
        )
        fig2 = px.bar(
            top_states,
            x="actual_revenue",
            y="state",
            orientation="h",
            color_discrete_sequence=["#40c057"],
        )
        fig2.update_layout(**PLOTLY_LAYOUT, yaxis_title="", xaxis_title="Receita (R$)")
        st.plotly_chart(fig2, width="stretch")

    col_l2, col_r2 = st.columns(2)

    with col_l2:
        st.markdown("##### Receita Mensal")
        monthly = (
            df.groupby(df["date"].dt.to_period("M"), as_index=False)
            .agg(total_rev=("actual_revenue", "sum"))
        )
        monthly["date"] = monthly["date"].astype(str)
        fig3 = px.line(monthly, x="date", y="total_rev", markers=True, color_discrete_sequence=["#228be6"])
        fig3.update_layout(**PLOTLY_LAYOUT, xaxis_title="Mês", yaxis_title="Receita (R$)")
        st.plotly_chart(fig3, width="stretch")

    with col_r2:
        st.markdown("##### Vendas por Categoria")
        cats = (
            df.groupby("category", as_index=False)["actual_revenue"]
            .sum()
            .sort_values(ascending=True, by="actual_revenue")
        )
        fig4 = px.bar(cats, x="actual_revenue", y="category", orientation="h", color_discrete_sequence=["#fab005"])
        fig4.update_layout(**PLOTLY_LAYOUT, yaxis_title="", xaxis_title="Receita (R$)")
        st.plotly_chart(fig4, width="stretch")

    st.markdown("##### Vendas por Segmento")
    segment = (
        df.groupby("segment", as_index=False)
        .agg(total_sales=("actual_revenue", "sum"), avg_sales=("actual_revenue", "mean"))
    )
    fig5 = px.bar(segment, x="segment", y="total_sales", color_discrete_sequence=["#7950f2"])
    fig5.update_layout(**PLOTLY_LAYOUT, xaxis_title="Segmento", yaxis_title="Receita (R$)")
    st.plotly_chart(fig5, width="stretch")


with tab_trace:
    traces = st.session_state.get("traces", [])

    if not traces:
        st.info("Nenhum trace ainda. Faça uma pergunta no Chat para ver os dados de observabilidade.")
    else:
        agent = get_agent()
        tk = agent.tracker

        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            st.metric("Total de Perguntas", tk.total_queries)
        with tc2:
            st.metric("Total de Tokens", f"{tk.total_tokens_used:,}")
        with tc3:
            st.metric("Custo Estimado", f"${tk.total_cost_usd:.4f}")

        st.divider()

        for i, trace in enumerate(reversed(traces)):
            idx = len(traces) - i
            with st.expander(f"#{idx} - {trace['question'][:80]}", expanded=(i == 0)):
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Tempo", f"{trace['total_duration_ms']:.0f}ms")
                m2.metric("Tokens", f"{trace['tokens']['total']:,}")
                m3.metric("Custo", f"${trace['estimated_cost_usd']:.4f}")
                m4.metric("Modelo", trace["model"])

                if trace["tool_calls"]:
                    st.markdown("**Tools utilizadas:**")
                    for tool_call in trace["tool_calls"]:
                        st.markdown(
                            f"- `{tool_call['name']}` -> input: `{tool_call['input'][:100]}` "
                            f"-> output: `{tool_call['output'][:100]}`"
                        )
                else:
                    st.markdown("*Nenhuma tool utilizada (resposta direta do LLM)*")

                st.markdown("**Breakdown de tokens:**")
                st.markdown(
                    f"- Prompt: {trace['tokens']['prompt']:,} -> Completion: {trace['tokens']['completion']:,}"
                )
