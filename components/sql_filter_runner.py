# components/sql_filter_runner.py
import streamlit as st
import pandas as pd





def build_where_clause(filters: dict, allowed_cols: list) -> tuple:
    """
    Erzeugt die WHERE-Klausel mit zugehörige Parameter aus den angegebenen Filtern.

    Args:
        filters (dict): Filter im Format {col: (min,max) | [v1,v2,...]}.
        allowed_cols (list): Liste der erlaubten Spalten.

    Returns:
        tuple: (where_sql, params_list)
    """
    clauses = []
    params = []

    for col, val in filters.items():

        if isinstance(val, tuple):
            clauses.append(f"`{col}` BETWEEN %s AND %s")
            params.extend([val[0], val[1]])
        elif isinstance(val, list):
            if not val:
                continue
            placeholders = ", ".join(["%s"] * len(val))
            clauses.append(f"`{col}` IN ({placeholders})")
            params.extend(val)

    where_sql = " AND ".join(clauses) if clauses else ""
    return where_sql, params


def _get_table_columns(conn, table_name: str) -> list:
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


def run_sql_filter(conn, table_name: str, filters: dict, limit: int = 1000):
    """
    Baut eine parametrisierte SELECT-Abfrage aus Filtern.
    Führt diese aus und zeigt das Ergebnis an.

    Args:
        conn: Datenbankverbindung
        table_name (str): Tabelle, auf die die Filter angewendet werden.
        filters (dict): Filter wie von build_filters() erzeugt.
        limit (int, optional): Maximale Anzahl Zeilen.

    Zeigt die SQL-Abfrage, das Ergebnis als DataFrame und einen CSV-Download-Button in Streamlit.
    """
    allowed_cols = _get_table_columns(conn, table_name)
    if not allowed_cols:
        st.error("Konnte Spalten der Tabelle nicht ermitteln.")
        return

    where_sql, params = build_where_clause(filters, allowed_cols)

    sql = f"SELECT * FROM `{table_name}`"
    if where_sql:
        sql += " WHERE " + where_sql
    if "LIMIT" not in sql.upper():
        sql += f" LIMIT {int(limit)}"

    st.subheader("Ausgeführte SQL-Abfrage:")
    st.code(sql, language="sql", line_numbers=True, wrap_lines=True)
    st.write(f"Parameter: {params}")

    cursor = None
    try:
        cursor = conn.cursor(buffered=True)
        cursor.execute(sql, tuple(params))
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
