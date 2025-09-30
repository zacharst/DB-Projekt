# app.py
import streamlit as st
from utils.database import get_connection
from components.sidebar import show_sidebar
from components.table_view import display_dataframe
from components.filter_panel import apply_filters
from components.sql_runner_simple import run_custom_query
from components.sql_filter_runner import run_sql_filter
from setup import test_connection

from components.table_editor import table_editor

# 2 Nutzer:
# verwaltung (pw:1234)
# kursleiter (pw:12345)

def main():
    """
    Startet die Streamlit-App mit einem Tab:
    1. Tabelle anzeigen: Zeigt eine ausgewählte Tabelle mit optionalen Filtern per Pandas an. 
       Joins mithilfe von join_config.json möglich.
    
    Bietet Login an
    2. SQL-Abfrage: Führt freie SQL-Queries aus.
    3. SQL-Filter: Wendet Sidebar-Filter parametriert auf die Datenbank an.
    
    Liest Tabellen und Filter aus der Sidebar, verwaltet Limits und gibt
    Ergebnisse als DataFrame oder CSV aus.
    """
    st.title("Hochschulsport")

    if "default_view" not in st.session_state:
        st.session_state["default_view"] = True
        st.session_state["show_login"] = False
        st.session_state["logged_in"] = False
        st.session_state["sql_user"] = None
        st.session_state["sql_password"] = None

    with st.sidebar:
        st.subheader("Nutzerzugang")

        #Default View - Ansicht für Kursteilnehmer
        if st.session_state["default_view"]:
            if st.button("Login für Nutzer"):
                st.session_state["show_login"] = True
                st.session_state["default_view"] = False
                st.rerun()

        # Show-Login - Sobald Loginbutton gedrückt wurde
        if st.session_state["show_login"]:
            st.session_state["default_view"] = False
            user = st.text_input("Nutzername")
            password = st.text_input("Passwort", type = "password")
            if st.button("Login", disabled = not(user and password)):
                if test_connection(user, password) and user is not None:
                    st.session_state["sql_user"] = user
                    st.session_state["sql_password"] = password
                    st.session_state["show_login"] = False
                    st.session_state["logged_in"] = True
                    st.rerun()
                else:
                    st.error("Login fehlgeschlagen. Prüfen Sie Benutzername/Passwort.")

        #Show-Logout: Nutzer ist eingelogged (Verwaltung oder Kursleiter)
        if st.session_state["logged_in"]:
            st.success(f"Erfolgreich als {st.session_state['sql_user']} verbunden!")
            if st.button("Abmelden"):
                st.session_state["default_view"] = True
                st.session_state["logged_in"] = False
                st.session_state["sql_user"] = None
                st.session_state["sql_password"] = None
                st.rerun()

    conn = get_connection(
            user=st.session_state["sql_user"],
            password=st.session_state["sql_password"]
        )

    ## Nur Verwaltung und Kursleiter kriegen SQL-Abfrage und SQL-Filter angezeigt
    if st.session_state["logged_in"]:
        tabs = ["Tabelle anzeigen", "SQL-Abfrage","Tabelle bearbeiten"]
        active_tab = st.radio("Wähle einen Tab", tabs, index=0)
    else:
        tabs = ["Tabelle anzeigen"]
        active_tab = st.radio("Wähle einen Tab", tabs, index=0)
        

    with st.sidebar:
        selected_table, filters, limit_active, default_limit, df_for_filters = show_sidebar(conn, active_tab)


    if active_tab == "SQL-Abfrage":
        st.title("Freie SQL-Abfrage")
        run_custom_query()

    elif active_tab == "Tabelle anzeigen":
        limit_to_use = default_limit if limit_active else None
        show_table_title = f"Tabelle anzeigen: {selected_table}" if selected_table else "Tabelle anzeigen"
        st.title(show_table_title)
        if df_for_filters is None or selected_table is None:
            st.info("Bitte wähle eine Tabelle in der Sidebar.")
        else:
            with st.spinner("Führe parametrisierten SQL-Filter aus..."):
                run_sql_filter(conn, selected_table, filters, limit=limit_to_use)

    elif active_tab == "Tabelle bearbeiten":
        if selected_table is None:
            st.info("Bitte wähle eine Tablle in der Sidebar aus.")
        else:
            table_editor(conn,selected_table)

if __name__ == "__main__":
    main()
