import re

import pandas as pd
import streamlit as st

from modules.formatting import format_brl


def extract_mbps(row: pd.Series) -> float:
    text = " ".join(
        str(value)
        for value in row.values
        if pd.notna(value)
    ).upper()

    text = (
        text.replace(",", ".")
        .replace("GBPS", "G")
        .replace("GB", "G")
        .replace("MBPS", "M")
        .replace("MB", "M")
    )

    matches = re.findall(r"(\d+(?:\.\d+)?)\s*(G|M)", text)

    total = 0.0

    for value, unit in matches:
        speed = float(value)
        if unit == "G":
            speed *= 1000
        total += speed

    return total


def add_mbps_column(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["MBPS"] = result.apply(extract_mbps, axis=1)
    return result


def classify_services(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    if "SERVICO" not in result.columns:
        result["TIPO"] = "OUTROS"
        return result

    service = result["SERVICO"].astype(str).str.upper()
    result["TIPO"] = "OUTROS"

    result.loc[service.str.contains("INTERNET", regex=False, na=False), "TIPO"] = "INTERNET"
    result.loc[service.str.contains("FIBRA", regex=False, na=False), "TIPO"] = "FIBRA"
    result.loc[service.str.contains(r"RADIO|RÁDIO", regex=True, na=False), "TIPO"] = "RADIO"

    return result


def split_service_types(df: pd.DataFrame):
    if "TIPO" not in df.columns:
        empty = df.iloc[0:0].copy()
        return empty, empty.copy(), empty.copy()

    return (
        df[df["TIPO"] == "INTERNET"],
        df[df["TIPO"] == "FIBRA"],
        df[df["TIPO"] == "RADIO"],
    )


def sum_money(df: pd.DataFrame, column: str = "VALOR GLOBAL") -> float:
    if column not in df.columns:
        return 0.0

    return pd.to_numeric(df[column], errors="coerce").fillna(0).sum()


def render_summary(df: pd.DataFrame):
    internet_df, fibra_df, radio_df = split_service_types(df)

    cards = [
        ("🌐 Internet", internet_df),
        ("🧵 Link Dados Fibra", fibra_df),
        ("📡 Link Dados Rádio", radio_df),
    ]

    columns = st.columns(3)

    for column, (title, data) in zip(columns, cards):
        with column:
            st.metric(
                title,
                f"{data['MBPS'].sum():,.0f} Mbps".replace(",", "."),
            )
            st.caption(
                f"Valor Global: {format_brl(sum_money(data))}"
            )

    return internet_df, fibra_df, radio_df


def render_bandwidth_distribution(internet_df, fibra_df, radio_df):
    st.subheader("📶 Distribuição de Banda")

    chart = pd.DataFrame(
        {
            "Tipo": ["Internet", "Fibra", "Rádio"],
            "Mbps": [
                internet_df["MBPS"].sum(),
                fibra_df["MBPS"].sum(),
                radio_df["MBPS"].sum(),
            ],
        }
    )

    st.bar_chart(chart.set_index("Tipo"), use_container_width=True)


def build_group_summary(
    df: pd.DataFrame,
    group_column: str,
) -> pd.DataFrame:
    if group_column not in df.columns:
        return pd.DataFrame()

    result = (
        df.groupby([group_column, "TIPO"], dropna=False)["MBPS"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )

    result = result.rename(
        columns={
            "INTERNET": "INTERNET_Mbps",
            "FIBRA": "FIBRA_Mbps",
            "RADIO": "RADIO_Mbps",
        }
    )

    for column in ["INTERNET_Mbps", "FIBRA_Mbps", "RADIO_Mbps"]:
        if column not in result.columns:
            result[column] = 0

    return result[
        [group_column, "INTERNET_Mbps", "FIBRA_Mbps", "RADIO_Mbps"]
    ]


def render_region_analysis(df: pd.DataFrame):
    if "REGIÃO" not in df.columns:
        return

    st.subheader("🗺️ Mbps por Região")

    summary = build_group_summary(df, "REGIÃO")
    st.dataframe(summary, use_container_width=True)

    if not summary.empty:
        st.bar_chart(summary.set_index("REGIÃO"), use_container_width=True)


def render_municipality_analysis(df: pd.DataFrame):
    if "MUNICIPIO" not in df.columns:
        return

    st.subheader("📍 Mbps por Município")

    summary = build_group_summary(df, "MUNICIPIO")
    st.dataframe(summary, use_container_width=True)

    if not summary.empty:
        st.bar_chart(
            summary.head(20).set_index("MUNICIPIO"),
            use_container_width=True,
        )


def build_client_summary(df: pd.DataFrame) -> pd.DataFrame:
    if "SIGLA" not in df.columns:
        return pd.DataFrame()

    base = df.copy()

    if "VALOR GLOBAL" not in base.columns:
        base["VALOR GLOBAL"] = 0.0

    if "MBPS" not in base.columns:
        base["MBPS"] = 0.0

    base["VALOR_GLOBAL_NUM"] = pd.to_numeric(
        base["VALOR GLOBAL"],
        errors="coerce",
    ).fillna(0)

    summary = (
        base.groupby(["SIGLA", "TIPO"], dropna=False)
        .agg(
            MBPS=("MBPS", "sum"),
            VALOR_GLOBAL_NUM=("VALOR_GLOBAL_NUM", "sum"),
        )
        .reset_index()
    )

    pivot = summary.pivot_table(
        index="SIGLA",
        columns="TIPO",
        values=["MBPS", "VALOR_GLOBAL_NUM"],
        fill_value=0,
    )

    if pivot.empty:
        return pd.DataFrame()

    pivot.columns = [
        f"{metric}_{service_type}"
        for metric, service_type in pivot.columns
    ]

    pivot = pivot.reset_index()

    value_columns = [
        column for column in pivot.columns
        if column.startswith("VALOR_GLOBAL_")
    ]

    mbps_columns = [
        column for column in pivot.columns
        if column.startswith("MBPS_")
    ]

    pivot["VALOR_TOTAL"] = pivot[value_columns].sum(axis=1) if value_columns else 0.0
    pivot["MBPS_TOTAL"] = pivot[mbps_columns].sum(axis=1) if mbps_columns else 0.0

    return pivot


def render_client_analysis(df: pd.DataFrame):
    st.subheader("🏢 Mbps e Valores por Cliente")

    summary = build_client_summary(df)

    if summary.empty:
        st.info("Nenhum dado de cliente disponível para os filtros selecionados.")
        return

    display_summary = summary.copy()

    value_columns = [
        column for column in display_summary.columns
        if "VALOR" in column
    ]

    for column in value_columns:
        display_summary[column] = display_summary[column].apply(format_brl)

    st.dataframe(display_summary, use_container_width=True)

    mbps_columns = [
        column for column in summary.columns
        if column.startswith("MBPS_")
        and column != "MBPS_TOTAL"
    ]

    if mbps_columns:
        st.subheader("📊 Mbps por Cliente")
        st.bar_chart(
            summary.head(20).set_index("SIGLA")[mbps_columns],
            use_container_width=True,
        )

    value_chart_columns = [
        column for column in summary.columns
        if column.startswith("VALOR_GLOBAL_")
    ]

    if value_chart_columns:
        st.subheader("💰 Valor por Cliente")
        st.bar_chart(
            summary.head(20).set_index("SIGLA")[value_chart_columns],
            use_container_width=True,
        )


def render_analysis(df: pd.DataFrame):
    st.divider()
    st.header("📊 Análise dos Dados Filtrados")

    analysis_df = add_mbps_column(df)
    analysis_df = classify_services(analysis_df)

    internet_df, fibra_df, radio_df = render_summary(analysis_df)

    render_bandwidth_distribution(
        internet_df,
        fibra_df,
        radio_df,
    )

    render_region_analysis(analysis_df)
    render_municipality_analysis(analysis_df)
    render_client_analysis(analysis_df)
