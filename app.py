import streamlit as st
from utils.database import get_connection
from components.sidebar import show_sidebar
from components.table_view import display_dataframe
from components.filter_panel import apply_filters
from components.sql_runner_simple import run_custom_query
from components.sql_filter_runner import run_sql_filter
from setup import test_connection

# 2 Nutzer:
# verwaltung (pw:1234)
# kursleiter (pw:12345)

def main():
    st.title("Hochschulsport")

    if "default_view" not in st.session_state:
        st.session_state["default_view"] = True
        st.session_state["show_login"] = False
        st.session_state["show_logout"] = False
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
                    st.session_state["show_logout"] = True
                    st.rerun()
                else:
                    st.error("Login fehlgeschlagen. Prüfen Sie Benutzername/Passwort.")

        #Show-Logout: Nutzer ist eingelogged (Verwaltung oder Kursleiter)
        if st.session_state["show_logout"]:
            st.success(f"Erfolgreich als {st.session_state['sql_user']} verbunden!")
            if st.button("Abmelden"):
                st.session_state["default_view"] = True
                st.session_state["show_logout"] = False
                st.session_state["sql_user"] = None
                st.session_state["sql_password"] = None
                st.rerun()

    conn = get_connection(
            user=st.session_state["sql_user"],
            password=st.session_state["sql_password"]
        )

    ## Nur Verwaltung und Kursleiter kriegen SQL-Abfrage und SQL-Filter angezeigt
    if st.session_state["show_logout"]:
        tabs = ["Tabelle anzeigen", "SQL-Abfrage", "SQL-Filter"]
        active_tab = st.radio("Wähle einen Tab", tabs, index=0)
    else:
        active_tab = "Tabelle anzeigen"

    with st.sidebar:
        selected_table, filters, limit_active, default_limit, df_for_filters = show_sidebar(conn, active_tab)

    if active_tab == "Tabelle anzeigen":
        st.title("Tabelle anzeigen")
        if df_for_filters is None:
            st.info("Bitte wähle eine Tabelle in der Sidebar.")
        else:
            limit_to_use = default_limit if limit_active else None
            filtered_df = apply_filters(
                df_for_filters, filters, limit=limit_to_use if limit_to_use else len(df_for_filters)
            )
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
