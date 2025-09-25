# components/table_editor.py
import streamlit as st
import pandas as pd
from utils.database import load_dataframe
from mysql.connector import errors
import numpy as np

def get_table_schema(conn, table_name: str):
    """Gibt eine Liste von Spalten mit Typ zurück"""
    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE `{table_name}`;")
    schema = cursor.fetchall()
    cursor.close()
    return [{"name": row[0], "type": row[1]} for row in schema]

def insert_entry(conn, table_name: str, data: dict):
    """Fügt einen neuen Eintrag ein"""
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["%s"] * len(data))
    values = list(data.values())
    query = f"INSERT INTO `{table_name}` ({columns}) VALUES ({placeholders});"
    cursor = conn.cursor()
    cursor.execute(query, values)
    conn.commit()
    cursor.close()

def update_entry(conn, table_name: str, data: dict, pk_col: str, pk_val):
    """Aktualisiert einen bestehenden Eintrag basierend auf Primärschlüssel"""
    if isinstance(pk_val, np.integer):
        pk_val = pk_val.item()
    assignments = ", ".join([f"{k}=%s" for k in data.keys()])
    values = list(data.values())
    values.append(pk_val)
    query = f"UPDATE `{table_name}` SET {assignments} WHERE {pk_col}=%s;"
    cursor = conn.cursor()
    cursor.execute(query, values)
    conn.commit()
    cursor.close()

def delete_entry(conn, table_name: str, pk_col: str, pk_val):
    """Löscht einen Eintrag basierend auf Primärschlüssel"""
    if isinstance(pk_val, np.integer):
        pk_val = pk_val.item()
    query = f"DELETE FROM `{table_name}` WHERE {pk_col}=%s;"
    cursor = conn.cursor()
    cursor.execute(query, (pk_val,))
    conn.commit()
    cursor.close()

def table_editor(conn, table_name: str):
    """Zeigt die Bearbeitungsschnittstelle für eine Tabelle"""
    if not table_name:
        st.info("Bitte wähle eine Tabelle.")
        return

    st.header(f"Tabelle bearbeiten: {table_name}")

    # Tabelle laden
    df = load_dataframe(conn, table_name)
    schema = get_table_schema(conn, table_name)
    pk_col = schema[0]["name"]  # Annahme: erste Spalte = Primärschlüssel

    if df.empty:
        st.warning("Die Tabelle ist leer.")

    # Auswahl der aktiven Aktion
    action = st.radio("Aktion auswählen", ["Eintrag hinzufügen", "Eintrag löschen", "Eintrag bearbeiten"])

    if action == "Eintrag hinzufügen":
        st.subheader("Neuen Eintrag hinzufügen")
        new_data = {}
        for col in schema:
            name, typ = col["name"], col["type"]
            if "int" in typ or "decimal" in typ or "float" in typ:
                new_data[name] = st.number_input(f"{name} ({typ})", value=0)
            elif "date" in typ and "datetime" not in typ:
                new_data[name] = st.date_input(f"{name} ({typ})")
            elif "datetime" in typ:
                new_data[name] = st.date_input(f"{name} ({typ})")
            else:
                new_data[name] = st.text_input(f"{name} ({typ})")

        if st.button("Eintrag hinzufügen"):
            try:
                insert_entry(conn, table_name, new_data)
                st.success("Eintrag hinzugefügt!")
                st.rerun()
            except errors.ProgrammingError as e:
                st.error(f"Fehler beim Hinzufügen: {e}")

    elif action == "Eintrag löschen":
        st.subheader("Eintrag löschen")
        pk_input = st.text_input(f"Gib den Wert für {pk_col} ein, der gelöscht werden soll")
        
        if pk_input:
            try:
                # Typ der Primärschlüssel-Spalte korrekt behandeln
                pk_type = type(df[pk_col].iloc[0])
                pk_val = pk_type(pk_input)
                
                # Prüfen, ob die ID existiert
                if pk_val in df[pk_col].values:
                    selected_row = df[df[pk_col] == pk_val]
                    st.table(selected_row)  # Zeige die ausgewählte Zeile
                    
                    # Button zum Löschen der angezeigten Zeile
                    if st.button("Eintrag endgültig löschen"):
                        delete_entry(conn, table_name, pk_col, pk_val)
                        st.success("Eintrag gelöscht!")
                        st.rerun()
                else:
                    st.warning(f"Keine Zeile mit {pk_col} = {pk_val} gefunden.")
            except ValueError:
                st.error(f"Ungültiger Wert für {pk_col}. Bitte den richtigen Typ eingeben.")
            except errors.ProgrammingError as e:
                st.error(f"Fehler beim Löschen: {e}")

    elif action == "Eintrag bearbeiten":
        st.subheader("Eintrag bearbeiten")
        pk_input = st.text_input(f"Gib den Wert für {pk_col} ein, der bearbeitet werden soll", key="edit_pk_input")
        
        if pk_input:
            try:
                pk_type = type(df[pk_col].iloc[0])
                pk_val = pk_type(pk_input)

                if pk_val in df[pk_col].values:
                    selected_row = df[df[pk_col] == pk_val]
                    st.table(selected_row)  # Zeige die ausgewählte Zeile

                    # Eingabefelder für die Werte der Zeile
                    row = selected_row.iloc[0]
                    updated_data = {}
                    for col in schema:
                        name, typ = col["name"], col["type"]
                        current_value = row[name]
                        if "int" in typ or "decimal" in typ or "float" in typ:
                            updated_data[name] = st.number_input(f"{name} ({typ})", value=float(current_value), key=f"edit_{name}")
                        elif "date" in typ and "datetime" not in typ:
                            updated_data[name] = st.date_input(f"{name} ({typ})", value=current_value, key=f"edit_{name}")
                        elif "datetime" in typ:
                            updated_data[name] = st.date_input(f"{name} ({typ})", value=current_value, key=f"edit_{name}")
                        else:
                            updated_data[name] = st.text_input(f"{name} ({typ})", value=str(current_value), key=f"edit_{name}")

                    if st.button("Eintrag aktualisieren"):
                        update_entry(conn, table_name, updated_data, pk_col, pk_val)
                        st.success("Eintrag aktualisiert!")
                        st.rerun()
                else:
                    st.warning(f"Keine Zeile mit {pk_col} = {pk_val} gefunden.")
            except ValueError:
                st.error(f"Ungültiger Wert für {pk_col}. Bitte den richtigen Typ eingeben.")
            except errors.ProgrammingError as e:
                st.error(f"Fehler beim Aktualisieren: {e}")
