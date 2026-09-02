import streamlit as st
import pandas as pd

from modules.config import DATE_COLUMNS, MONEY_COLUMNS
from modules.formatting import format_brl, format_date


def prepare_display_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara uma cópia para a tela.
    O DataFrame original continua numérico para os cálculos.
    """
    display_df = df.drop(
        columns=["_SIGLA_AUTOMATICA"],
        errors="ignore",
    ).copy()

    for column in MONEY_COLUMNS:
        if column in display_df.columns:
            display_df[column] = display_df[column].apply(format_brl)

    for column in DATE_COLUMNS:
        if column in display_df.columns:
            display_df[column] = display_df[column].apply(format_date)

    return display_df


def render_main_table(df: pd.DataFrame):
    display_df = prepare_display_dataframe(df)

    st.dataframe(
        display_df,
        use_container_width=True,
        height=min(600, max(120, len(display_df) * 35 + 50)),
    )

    if not display_df.empty:
        csv = display_df.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            "📥 Baixar CSV",
            data=csv,
            file_name="dados_filtrados.csv",
            mime="text/csv",
            use_container_width=True,
        )
