import streamlit as st

from modules.analysis import render_analysis
from modules.config import PAGE_TITLE
from modules.data_loader import load_data
from modules.sidebar import apply_filters, render_sidebar
from modules.table_view import render_main_table


def main():
    st.set_page_config(page_title=PAGE_TITLE, layout="wide")
    st.markdown("## 📡 Consulta de Links de Dados e Internet")

    df = load_data()

    if df.empty:
        st.stop()

    filters = render_sidebar(df)
    filtered_df = apply_filters(df, filters)

    render_main_table(filtered_df)
    render_analysis(filtered_df)


if __name__ == "__main__":
    main()
