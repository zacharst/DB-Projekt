# app.py
import streamlit as st
from utils.database import get_connection
from components.sidebar import show_sidebar
from components.table_view import display_dataframe
from components.filter_panel import apply_filters
from components.sql_runner_simple import run_custom_query
from components.sql_filter_runner import run_sql_filter


def main():
    """
    Startet die Streamlit-App mit drei Tabs:
    1. Tabelle anzeigen: Zeigt eine ausgewählte Tabelle mit optionalen Filtern per Pandas an. 
       Joins mithilfe von join_config.json möglich.
    2. SQL-Abfrage: Führt freie SQL-Queries aus.
    3. SQL-Filter: Wendet Sidebar-Filter parametriert auf die Datenbank an.

    Liest Tabellen und Filter aus der Sidebar, verwaltet Limits und gibt
    Ergebnisse als DataFrame oder CSV aus.
    """
    conn = get_connection()

    tabs = ["Tabelle anzeigen", "SQL-Abfrage", "SQL-Filter"]
    active_tab = st.radio("Wähle einen Tab", tabs, index=0)

    with st.sidebar:
        selected_table, filters, limit_active, default_limit, df_for_filters = show_sidebar(conn, active_tab)

    if active_tab == "Tabelle anzeigen":
        st.title("Tabelle anzeigen")
        if df_for_filters is None:
            st.info("Bitte wähle eine Tabelle in der Sidebar.")
        else:
            limit_to_use = default_limit if limit_active else None
            filtered_df = apply_filters(df_for_filters, filters, limit=limit_to_use if limit_to_use else len(df_for_filters))
            display_dataframe(filtered_df)

    elif active_tab == "SQL-Abfrage":
        st.title("Freie SQL-Abfrage")
        run_custom_query()

    elif active_tab == "SQL-Filter":
        st.title("SQL-Filter")
        if df_for_filters is None or selected_table is None:
            st.info("Bitte wähle eine Tabelle in der Sidebar.")
        else:
            with st.spinner("Führe parametrisierten SQL-Filter aus..."):
                run_sql_filter(conn, selected_table, filters, limit=default_limit)


if __name__ == "__main__":
    main()

