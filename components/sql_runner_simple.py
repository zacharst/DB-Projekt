# components/sql_runner_simple.py
import streamlit as st
import pandas as pd
from utils.database import get_connection


def run_custom_query():
    """
    Zeigt ein Textfeld für eine benutzerdefinierte SQL-Abfrage an und führt diese aus.

    - SELECT-Abfragen: SQL Abfrage wird ausgeführt. Ergebnisse werden als DataFrame angezeigt.
    - SQL-Befehle wie INSERT, UPDATE, DELETE werden ausgeführt und Änderungen übernommen.
    """
    st.subheader("SQL-Abfrage ausführen")

    sql = st.text_area("SQL", height=120)

    if st.button("Ausführen"):
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Überprüfen, ob es sich um eine SELECT-Anweisung oder eien SHOW-Anweisung handelt
            if sql.strip().upper().startswith("SELECT") or sql.strip().upper().startswith("SHOW"):
                cursor.execute(sql)
                data = cursor.fetchall()

                if cursor.description is None:
                    st.warning("Keine Spaltenbeschreibung verfügbar. Keine Ergebnisse.")
                    df = pd.DataFrame()  # leeres DataFrame
                else:
                    cols = [c[0] for c in cursor.description]
                    df = pd.DataFrame(data, columns=cols)
                    st.dataframe(df)
                    st.download_button(
                        "CSV herunterladen",
                        data=df.to_csv(index=False),
                        file_name="result.csv",
                        mime="text/csv"
                    )
            else:
                # Für INSERT, UPDATE, DELETE
                cursor.execute(sql)
                conn.commit()
                st.success(f"Operation erfolgreich durchgeführt. {cursor.rowcount} Zeilen betroffen.")
                
            cursor.close()
            conn.close()
        except Exception as e:
            st.error(f"Fehler bei der Ausführung: {e}")

