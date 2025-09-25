# components/sidebar.py
import streamlit as st
from utils.database import load_dataframe
from components.filter_panel import build_filters

def show_sidebar(conn, active_tab: str, apply_joins: bool = False):
    """
    Zeigt die Sidebar mit Tabellen-Auswahl, Limit und Filtern an 
    (nur in den Tabs 'Tabelle anzeigen' und 'SQL-Filter').

    Args:
        conn: Datenbankverbindung.
        active_tab (str): Der aktuell aktive Tab.
        apply_joins (bool, optional): Ob Joins beim Laden des DataFrames angewendet werden sollen. Default False.

    Returns:
        tuple: (selected_table, filters, limit_active, default_limit, df_for_filters)
    """
    if active_tab not in ("Tabelle anzeigen","Tabelle bearbeiten"):
        return None, {}, False, 1000, None
    


    st.header("Navigation / Auswahl")

    # Tabellen laden
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES;")
    tables = [t[0] for t in cursor.fetchall()]
    cursor.close()

    selected_table = st.selectbox("Wähle eine Tabelle", tables)

    if active_tab == "Tabelle bearbeiten":
        return selected_table,{}, False, None, None

    st.markdown("---")
    st.write("Einstellungen")

    # Limit Checkbox und Number Input per Textfeld
    limit_active = st.checkbox("Limit aktivieren", value=True)
    default_limit = st.number_input(
        "Setze ein LIMIT für die SQL-Abfragen",
        min_value=1, value=1000, step=100
    )

    if selected_table:
        if active_tab == "Tabelle anzeigen":
            apply_joins = True
        # DataFrame laden und Filter bauen
        df_for_filters = load_dataframe(conn, selected_table, apply_joins=apply_joins)
        filters = build_filters(df_for_filters)
    else:
        df_for_filters = None
        filters = {}

    return selected_table, filters, limit_active, default_limit, df_for_filters
