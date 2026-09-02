import re
import pandas as pd


def format_brl(value) -> str:
    """Formata número no padrão brasileiro: R$ 1.234,56."""
    if pd.isna(value):
        return ""

    try:
        value = float(value)
    except (TypeError, ValueError):
        return ""

    negative = value < 0
    value = abs(value)

    formatted = f"{value:,.2f}"
    formatted = formatted.replace(",", "_").replace(".", ",").replace("_", ".")

    return f"-R$ {formatted}" if negative else f"R$ {formatted}"


def parse_money(value):
    """
    Converte valores monetários para float.

    Aceita:
    R$ 1.234,56 | 1.234,56 | 1234,56 | 1234.56 | 1,234.56
    """
    if pd.isna(value):
        return float("nan")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)

    text = (
        str(value)
        .strip()
        .replace("R$", "")
        .replace("r$", "")
        .replace('"', "")
        .replace(" ", "")
    )

    if not text:
        return float("nan")

    if "," in text and "." in text:
        # O separador que aparece por último é considerado decimal.
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(".", "").replace(",", ".")
    elif "." in text:
        # 1.234 -> milhar; 1.23 -> decimal
        if re.fullmatch(r"-?\d+\.\d{3}", text):
            text = text.replace(".", "")

    try:
        return float(text)
    except ValueError:
        return float("nan")


def format_date(value) -> str:
    if pd.isna(value):
        return ""

    parsed = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed):
        return ""

    return parsed.strftime("%d/%m/%y")
