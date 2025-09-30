# components/sql_runner_simple.py
import streamlit as st
import pandas as pd
from utils.database import get_connection
import mysql.connector as mysql

def _execute_sql(conn, cursor, sql):
    """Führt die SQL-Query aus und zeigt Ergebnisse/Status in Streamlit an."""
    sql_upper = sql.strip().upper()
    try:
        if sql_upper.startswith("SELECT") or sql_upper.startswith("SHOW"):
            cursor.execute(sql)
            data = cursor.fetchall()
            if cursor.description is None:
                st.warning("Keine Spaltenbeschreibung verfügbar. Keine Ergebnisse.")
                df = pd.DataFrame()
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
            # INSERT, UPDATE, DELETE
            cursor.execute(sql)
            conn.commit()
            st.success(f"Operation erfolgreich durchgeführt. {cursor.rowcount} Zeilen betroffen.")
    except mysql.Error as e:
        errno = getattr(e, "errno", None)
        msg = getattr(e, "msg", None) or str(e)
        if errno in (1142, 1143):
            st.error("Berechtigungsfehler: Dein Datenbankbenutzer hat nicht die nötigen Rechte für diese Aktion.")
        else:
            st.error(f"Datenbankfehler ({errno}): {msg}")

def run_custom_query():
    """
    Zeigt ein Textfeld für eine benutzerdefinierte SQL-Abfrage an und führt diese aus.

    - SELECT-Abfragen: SQL Abfrage wird ausgeführt. Ergebnisse werden als DataFrame angezeigt.
    - SQL-Befehle wie INSERT, UPDATE, DELETE werden ausgeführt und Änderungen übernommen.

    Zusätzlich: bietet Beispiel-Queries an, die per Button geklickt und sofort ausgeführt werden.
    """
    st.subheader("SQL-Abfrage ausführen")


    conn = get_connection(
        user=st.session_state["sql_user"],
        password=st.session_state["sql_password"]
    )

    # Beispiel-Queries nach Projektbeschreibung
    example_queries = {
        "1: Anzeigen aller Studenten": """
SELECT k.*, s.matrikelnummer
FROM Kursteilnehmer k
INNER JOIN Studierende s
  ON k.teilnehmer_id = s.teilnehmer_id;
""",
        "2: Anzahl Veranstaltungen pro Angebot": """
SELECT s.angebot_id, s.angebot_name, COUNT(v.veranstaltungs_id) AS anzahl_veranstaltungen
FROM Sportangebot s
LEFT JOIN Veranstaltung v ON s.angebot_id = v.angebot_id
GROUP BY s.angebot_id, s.angebot_name;
""",
        "3: Teilnehmerliste und Sportangebote, die sie gebucht haben": """
SELECT k.teilnehmer_id, k.teilnehmer_name, s.angebot_name
FROM Kursteilnehmer k
JOIN Buchung b ON k.teilnehmer_id = b.teilnehmer_id
JOIN Veranstaltung v ON b.veranstaltungs_id = v.veranstaltungs_id
JOIN Sportangebot s ON v.angebot_id = s.angebot_id;
""",
        "4: Alle Teilnehmer die auf Anmeldelisten stehen": """
SELECT k.teilnehmer_id, k.teilnehmer_name AS teilnehmer_name, v.veranstaltungs_id, sa.angebot_name
FROM Buchung b
JOIN Kursteilnehmer k ON b.teilnehmer_id = k.teilnehmer_id
JOIN Veranstaltung v ON b.veranstaltungs_id = v.veranstaltungs_id
JOIN Sportangebot sa ON v.angebot_id = sa.angebot_id
WHERE b.buchung_status = 'wartend'
ORDER BY v.veranstaltungs_id, b.datum;
""",
        "5: Prozentuelle Auslastung aller Kurse (nur bezahlte Buchung)": """
SELECT sa.angebot_name AS veranstaltungsname, v.verfügbare_plätze,
COUNT(b.buchungs_id) AS belegte_plaetze,
ROUND(COUNT(b.buchungs_id) / v.verfügbare_plätze * 100, 1) AS auslastung_prozent
FROM Veranstaltung v
JOIN Sportangebot sa ON v.angebot_id = sa.angebot_id
LEFT JOIN Buchung b 
ON v.veranstaltungs_id = b.veranstaltungs_id
AND b.buchung_status = 'bezahlt' 
GROUP BY sa.angebot_name, v.verfügbare_plätze
ORDER BY auslastung_prozent DESC;
""",
        "6: Kurse die in bestimmten Ort stattfinden (Yogastudio)": """
SELECT v.veranstaltungs_id, sa.angebot_name, o.ort_name
FROM Veranstaltung v
JOIN Sportangebot sa ON v.angebot_id = sa.angebot_id
JOIN Ort o ON v.ort_id = o.ort_id
WHERE o.ort_name = 'Yogastudio';
""",
        "7: Teilnehmer mit den meisten Buchungen": """
SELECT k.teilnehmer_id, k.teilnehmer_name, COUNT(b.buchungs_id) AS buchungen
FROM Kursteilnehmer k
JOIN Buchung b ON k.teilnehmer_id = b.teilnehmer_id
GROUP BY k.teilnehmer_id, k.teilnehmer_name
ORDER BY buchungen DESC
LIMIT 1;
""",
        "8: Einnahmen pro Angebot": """
SELECT sa.angebot_name, SUM(b.betrag) AS gesamt_einnahmen
FROM Buchung b
JOIN Veranstaltung v ON b.veranstaltungs_id = v.veranstaltungs_id
JOIN Sportangebot sa ON v.angebot_id = sa.angebot_id
WHERE b.buchung_status = 'bezahlt'
GROUP BY sa.angebot_name
ORDER BY gesamt_einnahmen DESC;
""",
        "9: Veranstaltungen mit mehr als 5 verfügbaren Plätzen": """
SELECT sa.angebot_name, v.verfügbare_plätze
FROM Veranstaltung v
JOIN Sportangebot sa ON v.angebot_id = sa.angebot_id
WHERE v.verfügbare_plätze > 5;
""",
"10: Veranstaltungen mit freien Plätzen in Sporthalle": """
SELECT v.veranstaltungs_id, sa.angebot_name, o.ort_name, v.verfügbare_plätze
FROM Veranstaltung v
JOIN Sportangebot sa ON v.angebot_id = sa.angebot_id
JOIN Ort o ON v.ort_id = o.ort_id
WHERE o.ort_name = "Sporthalle";
""" 
    }

    # Anzeigen der Beispiele
    with st.expander("Beispiel-Queries anzeigen"):
        st.write("Klicke auf einen Button, um die Query als Beispiel auszuführen.")
        for label, query in example_queries.items():
            if st.button(label):
                # Setze die Textarea (session state) und führe die Query sofort aus
                st.session_state["sql_text"] = query.strip()
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    _execute_sql(conn, cursor, query)
                    cursor.close()
                    conn.close()
                except Exception as e:
                    st.error(f"Fehler bei der Ausführung des Beispiels: {e}")

    # Textarea für freie Eingabe
    if "sql_text" not in st.session_state:
        st.session_state["sql_text"] = ""

    # Wir benötigt, um die SQL Abfrage als Text anzuzeigen
    sql = st.text_area("SQL", height=240, key="sql_text")

    # Ausführen Button 
    if st.button("Ausführen"):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            _execute_sql(conn, cursor, st.session_state["sql_text"])
            cursor.close()
            conn.close()
        except Exception as e:
            st.error(f"Fehler bei der Ausführung: {e}")
    conn.close()
