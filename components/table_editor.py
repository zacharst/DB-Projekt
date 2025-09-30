# components/table_editor.py
import streamlit as st
import pandas as pd
from utils.database import load_dataframe
import mysql.connector as mysql
import numpy as np
from typing import List, Dict, Any

def get_table_schema(conn, table_name: str) -> List[Dict[str, Any]]:
    """
    Liefert DESCRIBE-Ergebnis als Liste von Dicts mit:
    name, type (raw), null, key, default, extra
    """
    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE `{table_name}`;")
    rows = cursor.fetchall()
    cursor.close()
    schema = []

    for row in rows:
        schema.append({
            "name": row[0],
            "type": row[1],     
            "null": row[2],
            "key": row[3],
            "default": row[4],
            "extra": row[5],
        })
    return schema

def _parse_enum_options(type_str: str):
    """Wenn type_str ein enum(...) ist, liefert eine Liste der Optionen, sonst None"""
    if isinstance(type_str, str) and type_str.lower().startswith("enum("):
        inner = type_str[type_str.find("(")+1:type_str.rfind(")")]
        opts = []
        cur = ""
        in_quote = False
        for ch in inner:
            if ch == "'" and not in_quote:
                in_quote = True
                cur = ""
            elif ch == "'" and in_quote:
                in_quote = False
                opts.append(cur)
            elif in_quote:
                cur += ch
            else:
                continue
        return opts
    return None

def _format_db_error(e: Exception) -> str:
    """
    Formatiert häufige MySQL-Fehler als kurze, verständliche Nachricht.
    Details kann der Admin im Expander sehen.
    """
    errno = getattr(e, "errno", None)
    msg = getattr(e, "msg", None) or str(e)

    if errno == 1062:
        return "Duplikateintrag: Ein Eintrag mit diesem Primärschlüssel existiert bereits."
    if errno in (1216, 1217):
        return "Foreign Key-Verstoß: Ein referenziertes Element existiert nicht."
    if errno in (1451, 1452):
        return "Foreign Key-Constraint verhindert die Aktion (abhängige Zeilen vorhanden oder fehlende Referenz)."
    if errno == 3819:
        return "Check-Constraint verletzt: Ein eingegebener Wert ist nicht erlaubt."
    if errno in (1142, 1143):
        return "Berechtigungsfehler: Dein Datenbankbenutzer hat nicht die nötigen Rechte für diese Aktion."
    if errno == 1048:
        return "NOT NULL-Verstoß: Ein Pflichtfeld wurde leer gelassen."
    if errno:
        return f"Datenbankfehler ({errno}): {msg}"
    return f"Datenbankfehler: {msg}"

def insert_entry(conn, table_name: str, data: dict):
    """Fügt einen neuen Eintrag ein (DB-Operation)."""
    columns = ", ".join(f"`{c}`" for c in data.keys())
    placeholders = ", ".join(["%s"] * len(data))
    values = list(data.values())
    query = f"INSERT INTO `{table_name}` ({columns}) VALUES ({placeholders});"
    cursor = conn.cursor()
    cursor.execute(query, values)
    conn.commit()
    cursor.close()

def update_entry(conn, table_name: str, data: dict, pk_cols: List[str], pk_vals: list):
    """Aktualisiert einen bestehenden Eintrag basierend auf zusammengesetztem Primärschlüssel (DB-Operation)."""
    clean_data_vals = [_to_python_value(v) for v in data.values()]
    clean_pk_vals = [_to_python_value(v) for v in pk_vals]

    assignments = ", ".join([f"`{k}`=%s" for k in data.keys()])
    where_clause = " AND ".join([f"`{col}`=%s" for col in pk_cols])
    query = f"UPDATE `{table_name}` SET {assignments} WHERE {where_clause};"

    cursor = conn.cursor()
    cursor.execute(query, clean_data_vals + clean_pk_vals)
    conn.commit()
    cursor.close()


def delete_entry(conn, table_name: str, pk_cols: List[str], pk_vals: list):
    """Löscht einen Eintrag basierend auf zusammengesetztem Primärschlüssel (DB-Operation)."""
    clean_pk_vals = [_to_python_value(v) for v in pk_vals]
    where_clause = " AND ".join([f"`{col}`=%s" for col in pk_cols])
    query = f"DELETE FROM `{table_name}` WHERE {where_clause};"

    cursor = conn.cursor()
    cursor.execute(query, clean_pk_vals)
    conn.commit()
    cursor.close()

def _to_python_value(val):
    """Hilfsfunktion: numpy und andere Spezialtypen -> Standard Python"""
    if isinstance(val, np.integer):
        return int(val)
    if isinstance(val, np.floating):
        return float(val)
    return val

 
def table_editor(conn, table_name: str):
    """
    Zeigt ein UI, mit der ein eingeloggter Benutzer Tabelleninhalte:
      - hinzufügen,
      - löschen,
      - bearbeiten
    kann.

    - Hinzufügen: für jede Spalte wird ein passendes Eingabefeld erzeugt
        (AUTO_INCREMENT PKs werden beim Hinzufügen übersprungen; ENUM -> Selectbox;
        int/decimal/float -> number_input; date/datetime -> date_input; sonst text_input).
    - Löschen: freie ID-Eingabe; falls vorhanden, wird die Zeile angezeigt
    - Bearbeiten: freie ID-Eingabe, falls vorhanden, wird die Zeile angezeigt. Die
        Felder folgen dem Spaltentyp; AUTO_INCREMENT PKs können nicht
        bearbeitet werden
    - DB-Fehler (Duplicate Key, Foreign Key, Check-Constraint, Permission, NOT NULL)
        werden abgefangen und als Meldung an den Nutzer ausgegeben.

    Args:
        conn: Offene MySQL-Verbindung (mysql.connector)
        table_name: Name der Tabelle, die bearbeitet werden soll

    Returns:
        None  (gibt Ergebnisse direkt mithilfe von Streamlit aus)
    """
    if not table_name:
        st.info("Bitte wähle eine Tabelle.")
        return

    st.header(f"Tabelle bearbeiten: {table_name}")

    df = load_dataframe(conn, table_name)
    schema = get_table_schema(conn, table_name)

    pk_cols = [col["name"] for col in schema if col["key"] == "PRI"]
    if not pk_cols:
        st.warning("Keine Primärschlüssel in der Tabelle gefunden.")
        return

    if df.empty:
        st.warning("Die Tabelle ist leer.")

    action = st.radio("Aktion auswählen", ["Eintrag hinzufügen", "Eintrag löschen", "Eintrag bearbeiten"])

    if action == "Eintrag hinzufügen":
        st.subheader("Neuen Eintrag hinzufügen")
        new_data = {}
        for col in schema:
            name = col["name"]
            typ = col["type"]
            extra = col["extra"] or ""
            enum_opts = _parse_enum_options(typ)

            if "auto_increment" in extra.lower():
                st.markdown(f"*{name} wird automatisch gesetzt (AUTO_INCREMENT)*")
                continue

            if enum_opts:
                new_data[name] = st.selectbox(f"{name} (enum)", options=[""] + enum_opts, key=f"add_{name}")
                if new_data[name] == "":
                    new_data[name] = None
            elif any(x in typ.lower() for x in ("int", "decimal", "float", "double")):
                if "int" in typ.lower():
                    new_data[name] = st.number_input(f"{name} ({typ})", value=0, format="%d", step=1, key=f"add_{name}")
                else:
                    new_data[name] = st.number_input(f"{name} ({typ})", value=0.0, key=f"add_{name}")
            elif "date" in typ.lower() and "datetime" not in typ.lower():
                new_data[name] = st.date_input(f"{name} ({typ})", key=f"add_{name}")
            elif "datetime" in typ.lower() or "timestamp" in typ.lower():
                new_data[name] = st.date_input(f"{name} ({typ})", key=f"add_{name}")
            else:
                new_data[name] = st.text_input(f"{name} ({typ})", key=f"add_{name}")

        if st.button("Eintrag hinzufügen"):
            try:
                prepared = {k: (_to_python_value(v) if v is not None else None) for k, v in new_data.items()}
                insert_entry(conn, table_name, prepared)
                st.success("Eintrag hinzugefügt!")
                st.rerun()
            except mysql.Error as e:
                st.error(_format_db_error(e))
                with st.expander("Fehlerdetails"):
                    st.text(str(e))
            except Exception as e:
                st.error("Fehler beim Hinzufügen.")
                with st.expander("Fehlerdetails"):
                    st.text(str(e))

    elif action == "Eintrag löschen":
        st.subheader("Eintrag löschen")
        
        if df.empty:
            st.warning("Die Tabelle ist leer. Keine Einträge zum Löschen vorhanden.")
        else:
            pk_inputs = {col: st.text_input(f"Gib den Wert für {col} ein", key=f"del_{col}") for col in pk_cols}

            if all(pk_inputs.values()):
                try:
                    pk_vals = [_to_python_value(type(df[col].iloc[0])(pk_inputs[col])) for col in pk_cols]
                    selected_row = df.copy()
                    for col, val in zip(pk_cols, pk_vals):
                        selected_row = selected_row[selected_row[col] == val]
                    if not selected_row.empty:
                        st.table(selected_row)
                        if st.button("Eintrag endgültig löschen"):
                            delete_entry(conn, table_name, pk_cols, pk_vals)
                            st.success("Eintrag gelöscht!")
                            st.rerun()
                    else:
                        st.warning("Keine Zeile mit den angegebenen Primärschlüssel-Werten gefunden.")
                except ValueError:
                    st.error("Ungültiger Wert für einen Primärschlüssel. Bitte den richtigen Typ eingeben.")
                except Exception as e:
                    st.error("Fehler beim Löschen.")
                    with st.expander("Fehlerdetails"):
                        st.text(str(e))

    elif action == "Eintrag bearbeiten":
        st.subheader("Eintrag bearbeiten")
        
        if df.empty:
            st.warning("Die Tabelle ist leer. Keine Einträge zum Bearbeiten vorhanden.")
        else:
            pk_inputs = {col: st.text_input(f"Gib den Wert für {col} ein", key=f"edit_{col}") for col in pk_cols}

            if all(pk_inputs.values()):
                try:
                    # Typkonvertierung für PKs
                    pk_vals = [_to_python_value(type(df[col].iloc[0])(pk_inputs[col])) for col in pk_cols]

                    # Zeilen filtern
                    mask = pd.Series(True, index=df.index)
                    for col, val in zip(pk_cols, pk_vals):
                        mask &= df[col] == val

                    if mask.any():
                        selected_row = df[mask]
                        st.table(selected_row)
                        row = selected_row.iloc[0]

                        updated_data = {}
                        for col in schema:
                            name = col["name"]
                            typ = col["type"]
                            extra = col["extra"] or ""
                            enum_opts = _parse_enum_options(typ)

                            current_value = row[name]
                            if isinstance(current_value, pd.Series):
                                current_value = current_value.iloc[0] if not current_value.empty else None

                            # AUTO_INCREMENT PK nur anzeigen
                            if col["key"] == "PRI" and "auto_increment" in extra.lower():
                                st.markdown(f"*{name} (Primärschlüssel, AUTO_INCREMENT): {current_value}*")
                                continue

                            input_key = f"edit_{name}_{'_'.join(str(v) for v in pk_vals)}"

                            # ENUM
                            if enum_opts:
                                options = [""] + enum_opts
                                val = current_value if pd.notna(current_value) else ""
                                sel = st.selectbox(
                                    f"{name} (enum)",
                                    options=options,
                                    index=options.index(val) if val in options else 0,
                                    key=input_key
                                )
                                updated_data[name] = sel if sel != "" else None

                            # Zahlen
                            elif any(x in typ.lower() for x in ("int", "decimal", "float", "double")):
                                cur = 0 if pd.isna(current_value) and "int" in typ.lower() else 0.0 if pd.isna(current_value) else float(_to_python_value(current_value))
                                if "int" in typ.lower():
                                    updated_data[name] = int(st.number_input(f"{name} ({typ})", value=int(cur), format="%d", step=1, key=input_key))
                                else:
                                    updated_data[name] = st.number_input(f"{name} ({typ})", value=cur, key=input_key)

                            # Date
                            elif "date" in typ.lower() and "datetime" not in typ.lower():
                                cur = pd.to_datetime(current_value).date() if pd.notna(current_value) else pd.Timestamp.today().date()
                                updated_data[name] = st.date_input(f"{name} ({typ})", value=cur, key=input_key)

                            # DateTime / Timestamp
                            elif "datetime" in typ.lower() or "timestamp" in typ.lower():
                                cur = pd.to_datetime(current_value) if pd.notna(current_value) else pd.Timestamp.now()
                                updated_data[name] = st.date_input(f"{name} ({typ})", value=cur, key=input_key)

                            # Text
                            else:
                                val = str(current_value) if pd.notna(current_value) else ""
                                updated_data[name] = st.text_input(f"{name} ({typ})", value=val, key=input_key)

                        if st.button("Eintrag aktualisieren"):
                            try:
                                prepared = {k: (_to_python_value(v) if v is not None else None) for k, v in updated_data.items()}
                                update_entry(conn, table_name, prepared, pk_cols, pk_vals)
                                st.success("Eintrag aktualisiert!")
                                st.rerun()
                            except Exception as e:
                                st.error("Fehler beim Aktualisieren.")
                                with st.expander("Fehlerdetails"):
                                    st.text(str(e))
                    else:
                        st.warning("Keine Zeile mit den angegebenen Primärschlüssel-Werten gefunden.")
                except Exception as e:
                    st.error("Fehler beim Bearbeiten.")
                    with st.expander("Fehlerdetails"):
                        st.text(str(e))
