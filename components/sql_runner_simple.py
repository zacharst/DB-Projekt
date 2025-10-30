# components/sql_runner_simple.py
import streamlit as st
import pandas as pd
from utils.database import get_connection
import mysql.connector as mysql

def _execute_sql(conn, cursor, sql, params=None):
    """Führt die SQL-Query aus und zeigt Ergebnisse/Status in Streamlit an."""
    sql_upper = sql.strip().upper()
    try:
        if sql_upper.startswith("SELECT") or sql_upper.startswith("SHOW"):
            if params:
                cursor.execute(sql, params)
            else:
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
            if params:
                cursor.execute(sql, params)
            else:
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
    """Streamlit-Komponente zum Ausführen eigener SQL-Queries mit Beispiel-Queries."""
    st.subheader("SQL-Abfrage ausführen")

    conn = get_connection(
        user=st.session_state["sql_user"],
        password=st.session_state["sql_password"]
    )

    # Standardwert für parametrierten Ort setzen
    if "ort_param" not in st.session_state:
        st.session_state["ort_param"] = "Yogastudio"

    # Beispiel-Queries
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
""",
        "11: Verwaltungsangestellte die für Gesellschaftstanz verantwortlich sind": """
SELECT vw.angestellten_name
FROM Verwaltungsangestellter vw
WHERE angestellten_id IN (
    SELECT angestellten_id
    FROM Verwaltete_veranstaltungen
    WHERE veranstaltungs_id IN (
        SELECT veranstaltungs_id
        FROM Veranstaltung
        WHERE angebot_id IN (
            SELECT angebot_id
            FROM Sportangebot sa
            WHERE sa.angebot_name = "Gesellschaftstanz"
        )
    )
);
""",
        "12: Veranstaltungen an bestimmtem Ort (parametrisiert)": """
SELECT v.veranstaltungs_id, sa.angebot_name, o.ort_name, v.verfügbare_plätze
FROM Veranstaltung v
JOIN Sportangebot sa ON v.angebot_id = sa.angebot_id
JOIN Ort o ON v.ort_id = o.ort_id
WHERE o.ort_name = %s;
"""
    }

    # Anzeigen der Beispiele
    with st.expander("Beispiel-Queries anzeigen"):
        st.write("Klicke auf einen Button, um die Query als Beispiel auszuführen.")
        for label, query in example_queries.items():
            if st.button(label):
                st.session_state["sql_text"] = query.strip()
                st.session_state["selected_query"] = label

    # Wenn Query 12 gewählt wurde, Eingabefeld für Parameter anzeigen
    if st.session_state.get("selected_query") == "12: Veranstaltungen an bestimmtem Ort (parametrisiert)":
        st.session_state["ort_param"] = st.text_input("Ort eingeben:", st.session_state["ort_param"])

    # Textarea für freie Eingabe
    if "sql_text" not in st.session_state:
        st.session_state["sql_text"] = ""

    sql = st.text_area("SQL", height=240, key="sql_text")

    # Ausführen Button 
    if st.button("Ausführen"):
        try:
            conn = get_connection()
            cursor = conn.cursor()

            if st.session_state.get("selected_query") == "12: Veranstaltungen an bestimmtem Ort (parametrisiert)":
                params = (st.session_state["ort_param"],)
            else:
                params = None

            _execute_sql(conn, cursor, st.session_state["sql_text"], params)
            cursor.close()
            conn.close()
        except Exception as e:
            st.error(f"Fehler bei der Ausführung: {e}")

    conn.close()
