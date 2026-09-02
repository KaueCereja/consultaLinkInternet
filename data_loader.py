from pathlib import Path

import pandas as pd
import streamlit as st

from modules.config import DATE_COLUMNS, GOOGLE_SHEETS_URL, LOCAL_CSV, MONEY_COLUMNS
from modules.formatting import parse_money


def extract_sigla_from_client(client) -> str:
    if pd.isna(client) or not isinstance(client, str):
        return ""

    words = client.strip().split()

    if not words:
        return ""

    if len(words) >= 2:
        sigla = "".join(word[0] for word in words if len(word) > 2)[:10]
        return sigla.upper() if sigla else words[0][:8].upper()

    return client[:8].upper()


def normalize_sigla(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "SIGLA" not in df.columns:
        df["_SIGLA_AUTOMATICA"] = False
        return df

    original_empty = (
        df["SIGLA"].isna()
        | df["SIGLA"].astype(str).str.strip().str.upper().isin(
            {"", "NAN", "NONE", "N/A", "NULL"}
        )
    )

    df["SIGLA"] = df["SIGLA"].fillna("").astype(str).str.strip().str.upper()
    df["SIGLA"] = df["SIGLA"].replace(["NAN", "NONE", "N/A", "NULL"], "")

    if "CLIENTE" in df.columns:
        mask = df["SIGLA"].eq("")
        if mask.any():
            df.loc[mask, "SIGLA"] = df.loc[mask, "CLIENTE"].apply(
                extract_sigla_from_client
            )

    df["_SIGLA_AUTOMATICA"] = original_empty
    return df


def normalize_money_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for column in MONEY_COLUMNS:
        if column in df.columns:
            df[column] = df[column].apply(parse_money)

    return df


def normalize_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for column in DATE_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_datetime(
                df[column],
                errors="coerce",
                dayfirst=True,
            )

    return df


@st.cache_data(ttl=3600)
def load_data() -> pd.DataFrame:
    try:
        df = pd.read_csv(GOOGLE_SHEETS_URL)
    except Exception as google_error:
        st.warning(f"⚠️ Erro ao carregar do Google Sheets: {google_error}")

        local_file = Path(LOCAL_CSV)

        if not local_file.exists():
            st.error("❌ Não foi possível carregar os dados.")
            return pd.DataFrame()

        try:
            df = pd.read_csv(local_file, encoding="utf-8")
        except Exception as local_error:
            st.error(f"❌ Erro ao carregar o arquivo local: {local_error}")
            return pd.DataFrame()

    df.columns = [str(column).strip() for column in df.columns]
    df = normalize_sigla(df)
    df = normalize_money_columns(df)
    df = normalize_date_columns(df)

    return df
