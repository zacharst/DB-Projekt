# components/filter_panel.py
import streamlit as st
import pandas as pd 

def build_filters(df: pd.DataFrame) -> dict:
    """
    Erzeugt Filter in der Sidebar für jede Spalte eines DataFrames.

    Für numerische Spalten werden Min/Max-Number-Inputs erstellt,
    für Datums-Spalten Start-/End-Dates,
    für andere Spalten Multi-Selects.

    Args:
        df (pd.DataFrame): Das DataFrame, für das Filter erzeugt werden sollen.

    Returns:
        dict: Jeder Schlüssel ist eine Spalte ist und
              der Wert das Filterkriterium.
    """
    filters = {}

    for col in df.columns:
        with st.sidebar.expander(f"Filter für {col}", expanded=False):
            active_key = f"{col}_active"
            active = st.checkbox("Aktivieren", value=False, key=active_key)

            nunique = df[col].nunique()

            # Numerische Spalten
            if pd.api.types.is_numeric_dtype(df[col]) and nunique > 1:
                mn, mx = float(df[col].min()), float(df[col].max())
                default_min = min(0, mn)

                min_key, max_key = f"{col}_min", f"{col}_max"

                if min_key not in st.session_state:
                    st.session_state[min_key] = default_min
                if max_key not in st.session_state:
                    st.session_state[max_key] = mx

                st.number_input(f"Min {col}", key=min_key, format="%.4f")
                st.number_input(f"Max {col}", key=max_key, format="%.4f")

                if active:
                    filters[col] = (st.session_state[min_key], st.session_state[max_key])

            # Datumsspalten
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                mn, mx = df[col].min(), df[col].max()

                start_key, end_key = f"{col}_start", f"{col}_end"

                if start_key not in st.session_state:
                    st.session_state[start_key] = mn
                if end_key not in st.session_state:
                    st.session_state[end_key] = mx

                st.date_input(f"Von (inkl.) {col}", key=start_key)
                st.date_input(f"Bis (inkl.) {col}", key=end_key)

                if active:
                    filters[col] = (pd.to_datetime(st.session_state[start_key]),
                                    pd.to_datetime(st.session_state[end_key]))
            # Andere Spalten
            else:
                multi_key = f"{col}_multi"

                if multi_key not in st.session_state:
                    st.session_state[multi_key] = []

                st.multiselect(f"Werte für {col}",
                               options=list(df[col].dropna().unique()),
                               key=multi_key)

                if active:
                    filters[col] = st.session_state[multi_key]

    return filters


def apply_filters(df: pd.DataFrame, filters: dict, limit: int = 1000) -> pd.DataFrame:
    """
    Wendet die angegebenen Filter auf ein DataFrame an.

    Numerische und Datums-Filter werden als Tuple (min, max) übergeben,
    andere Spalten als Liste von erlaubten Werten.
    Das Limit als numerischer Wert.

    Args:
        df (pd.DataFrame): Das zu filternde DataFrame.
        filters (dict): Schlüssel sind Spaltennamen, Werte sind Filterkriterien.
        limit (int, optional): Maximale Anzahl der zurückgegebenen Zeilen.

    Returns:
        pd.DataFrame: Gefiltertes DataFrame, auf maximal `limit` Zeilen begrenzt.
    """
    filtered = df.copy()
    for col, val in filters.items():
        if isinstance(val, tuple):
            filtered = filtered[(filtered[col] >= val[0]) & (filtered[col] <= val[1])]
        elif isinstance(val, list) and val:
            filtered = filtered[filtered[col].isin(val)]
    if limit:
        return filtered.head(limit)
    return filtered
