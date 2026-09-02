import pandas as pd
import streamlit as st

from modules.config import FILTER_COLUMNS


def get_filter_options(df: pd.DataFrame, column: str) -> list[str]:
    if column not in df.columns:
        return []

    return sorted(
        df[column]
        .dropna()
        .astype(str)
        .loc[lambda series: series.ne("")]
        .unique()
        .tolist()
    )


def render_sidebar(df: pd.DataFrame) -> dict:
    """Renderiza somente a barra lateral e devolve os filtros escolhidos."""
    total_records = len(df)

    automatic_siglas = (
        int(df["_SIGLA_AUTOMATICA"].sum())
        if "_SIGLA_AUTOMATICA" in df.columns
        else 0
    )

    with st.sidebar:
        st.markdown("# 🎯 Filtros")
        st.caption(f"📊 Total: {total_records} registros")

        if automatic_siglas:
            st.caption(
                f"⚠️ {automatic_siglas} registros sem SIGLA original "
                "(preenchidos automaticamente)"
            )

        if st.button("🔄 Limpar Todos os Filtros", use_container_width=True):
            st.cache_data.clear()

            # Remove os valores dos widgets da sidebar.
            for column, _ in FILTER_COLUMNS:
                st.session_state.pop(f"filtro_{column}", None)

            st.rerun()

        st.divider()

        filters = {}

        for column, label in FILTER_COLUMNS:
            options = get_filter_options(df, column)

            if not options:
                continue

            selected = st.multiselect(
                label,
                options=options,
                key=f"filtro_{column}",
            )

            if selected:
                filters[column] = selected

    return filters


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    filtered = df.copy()

    for column, values in filters.items():
        if column in filtered.columns:
            filtered = filtered[filtered[column].isin(values)]

    return filtered
