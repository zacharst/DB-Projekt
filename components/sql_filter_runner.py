import json
from pypika import Query
from pypika.terms import Field
import streamlit as st
import pandas as pd

JOIN_CONFIG_PATH = "utils/join_config.json"

def load_join_config():
    """Lädt die Join-Konfiguration aus der JSON-Datei."""
    with open(JOIN_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def build_where_clause(filters, allowed_cols):
    """
    Erstellt PyPika-Terms für WHERE-Klausel.
    """
    clauses = []
    params = []
    for col, val in filters.items():
        if col not in allowed_cols:
            continue
        field = Field(col)
        if isinstance(val, tuple):  # min/max
            clauses.append(field.between(val[0], val[1]))
            params.extend([val[0], val[1]])
        elif isinstance(val, list) and val:
            clauses.append(field.isin(val))
            params.extend(val)
    # Kombiniere alle Klauseln mit AND
    if clauses:
        term = clauses[0]
        for c in clauses[1:]:
            term &= c
        return term, params
    else:
        return None, params
    

def get_table_columns(conn, table_name: str) -> list:
    """
    Holt die Spaltennamen einer Tabelle mit LIMIT 0 SELECT.

    Args:
        conn: Datenbankverbindung
        table_name (str): Name der Tabelle.

    Returns:
        list: Liste der Spaltennamen.
    """
    cursor = None
    try:
        cursor = conn.cursor(buffered=True)
        cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 0;")
        _ = cursor.fetchall()
        if cursor.description:
            cols = [c[0] for c in cursor.description]
        else:
            cols = []
        return cols
    finally:
        if cursor:
            cursor.close()

def build_sql_query(conn, table_name, filters, limit):
    """Erstellt die SQL-Abfrage basierend auf den Filtern und dem Limit."""
    allowed_cols = get_table_columns(conn, table_name)
    where_sql, params = build_where_clause(filters, allowed_cols)
    query = Query.from_(table_name).select("*")
    if where_sql:
        query = query.where(where_sql)
    if limit:
        query = query.limit(limit)
    sql = str(query)
    # Ersetze doppelte Anführungszeichen durch Backticks für MySQL
    sql = sql.replace('"', "`")
    return sql, params

def run_sql_filter(conn, table_name, filters, limit):
    """
    Baut eine parametrisierte SELECT-Abfrage aus Filtern.
    Führt diese aus und zeigt das Ergebnis an.
    """
    allowed_cols = get_table_columns(conn, table_name)
    if not allowed_cols:
        return

    term, params = build_where_clause(filters, allowed_cols)

    query = Query.from_(table_name).select("*")
    if term:
        query = query.where(term)
    if limit: #limit deaktiviert -> limit = None
        query = query.limit(limit)

    sql = str(query)
    sql = sql.replace('"',"`")  # MySQL Backticks

    if "show_sql" not in st.session_state:
        st.session_state.show_sql = False

    
    def toggle_sql():
        st.session_state.show_sql = not st.session_state.show_sql
    st.button("SQL Query anzeigen/ausblenden", on_click=toggle_sql)

    if st.session_state.show_sql:
        st.subheader("Ausgeführte SQL-Abfrage:")
        st.code(sql, language="sql", line_numbers=True, wrap_lines=True)
    #st.write(f"Parameter: {params}")

    cursor = None
    try:
        cursor = conn.cursor(buffered=True)
        cursor.execute(sql)
        rows = cursor.fetchall()
        if cursor.description:
            cols = [c[0] for c in cursor.description]
            df = pd.DataFrame(rows, columns=cols)
        else:
            df = pd.DataFrame()
        st.dataframe(df)
        st.download_button(
            "CSV herunterladen",
            data=df.to_csv(index=False),
            file_name="sql_filter_result.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"Fehler bei SQL-Filter-Ausführung: {e}")
    finally:
        if cursor:
            cursor.close()
