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

    # DESCRIBE returns: Field, Type, Null, Key, Default, Extra
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
        # inner: "'opt1','opt2'"
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

def update_entry(conn, table_name: str, data: dict, pk_col: str, pk_val):
    """Aktualisiert einen bestehenden Eintrag basierend auf Primärschlüssel (DB-Operation)."""
    if isinstance(pk_val, np.integer):
        pk_val = pk_val.item()
    assignments = ", ".join([f"`{k}`=%s" for k in data.keys()])
    values = list(data.values())
    values.append(pk_val)
    query = f"UPDATE `{table_name}` SET {assignments} WHERE `{pk_col}`=%s;"
    cursor = conn.cursor()
    cursor.execute(query, values)
    conn.commit()
    cursor.close()

def delete_entry(conn, table_name: str, pk_col: str, pk_val):
    """Löscht einen Eintrag basierend auf Primärschlüssel (DB-Operation)."""
    if isinstance(pk_val, np.integer):
        pk_val = pk_val.item()
    query = f"DELETE FROM `{table_name}` WHERE `{pk_col}`=%s;"
    cursor = conn.cursor()
    cursor.execute(query, (pk_val,))
    conn.commit()
    cursor.close()

def _to_python_value(val):
    """Hilfsfunktion: numpy -> Standard Python"""
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

    # Tabelle und Schema laden
    df = load_dataframe(conn, table_name)
    schema = get_table_schema(conn, table_name)

    # Bestimme Primärschlüssel, falls vorhanden (falls nicht, nehme erste Spalte) Bei dieser DB ist erste Spalte immer PK
    pk_cols = [col["name"] for col in schema if col["key"] == "PRI"]
    pk_col = pk_cols[0] if pk_cols else schema[0]["name"]

    if df.empty:
        st.warning("Die Tabelle ist leer.")

    # Aktion wählen: immer nur eine aktiv
    action = st.radio("Aktion auswählen", ["Eintrag hinzufügen", "Eintrag löschen", "Eintrag bearbeiten"])

    if action == "Eintrag hinzufügen":
        st.subheader("Neuen Eintrag hinzufügen")
        new_data = {}
        # Erzeuge passende Inputs basierend auf Schema
        for col in schema:
            name = col["name"]
            typ = col["type"]
            extra = col["extra"] or ""
            enum_opts = _parse_enum_options(typ)

            # Wenn auto_increment (z. B. PRIMARY KEY AUTO_INCREMENT), wird das Feld beim Hinzufügen übersprungen
            if "auto_increment" in extra.lower():
                st.markdown(f"*{name} wird automatisch gesetzt (AUTO_INCREMENT)*")
                continue

            if enum_opts:
                # Enum -> Selectbox
                new_data[name] = st.selectbox(f"{name} (enum)", options=[""] + enum_opts, key=f"add_{name}")
                if new_data[name] == "":
                    new_data[name] = None
            elif any(x in typ.lower() for x in ("int", "decimal", "float", "double")):
                if "int" in typ.lower():
                    new_data[name] = st.number_input(f"{name} ({typ})", value=0, format="%d", step=1, key=f"add_{name}")
                else:
                    new_data[name] = st.number_input(f"{name} ({typ})", value=0.0, key=f"add_{name}")
            # Streamlit date_input für Daten
            elif "date" in typ.lower() and "datetime" not in typ.lower():
                new_data[name] = st.date_input(f"{name} ({typ})", key=f"add_{name}")
            elif "datetime" in typ.lower() or "timestamp" in typ.lower():
                new_data[name] = st.date_input(f"{name} ({typ})", key=f"add_{name}")
            else:
                # Freies Textfeld
                new_data[name] = st.text_input(f"{name} ({typ})", key=f"add_{name}")

        if st.button("Eintrag hinzufügen"):
            try:
                # Konvertiere numpy-Typen in native Python
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
        pk_input = st.text_input(f"Gib den Wert für {pk_col} ein, der gelöscht werden soll", key="del_pk_input")

        if pk_input:
            if df.empty:
                st.warning("Die Tabelle ist leer. Keine IDs vorhanden zum Löschen.")
            else:
                try:
                    first_val = df[pk_col].iloc[0]
                    pk_type = type(first_val)

                    # Versuche Konvertierung; handle numpy numeric types
                    if issubclass(pk_type, (np.integer, np.floating)):
                        # numeric string zu numeric numpy type
                        pk_val = pk_type(pk_input)
                    else:
                        pk_val = pk_type(pk_input)

                    if pk_val in df[pk_col].values:
                        selected_row = df[df[pk_col] == pk_val]
                        st.table(selected_row)

                        if st.button("Eintrag endgültig löschen"):
                            try:
                                delete_entry(conn, table_name, pk_col, pk_val)
                                st.success("Eintrag gelöscht!")
                                st.rerun()
                            except mysql.Error as e:
                                st.error(_format_db_error(e))
                                with st.expander("Fehlerdetails"):
                                    st.text(str(e))
                            except Exception as e:
                                st.error("Fehler beim Löschen.")
                                with st.expander("Fehlerdetails"):
                                    st.text(str(e))
                    else:
                        st.warning(f"Keine Zeile mit {pk_col} = {pk_val} gefunden.")
                except ValueError:
                    st.error(f"Ungültiger Wert für {pk_col}. Bitte den richtigen Typ eingeben.")
                except mysql.Error as e:
                    st.error(_format_db_error(e))
                    with st.expander("Fehlerdetails"):
                        st.text(str(e))
                except Exception as e:
                    st.error("Fehler beim Verarbeiten der Eingabe.")
                    with st.expander("Fehlerdetails"):
                        st.text(str(e))

    elif action == "Eintrag bearbeiten":
        st.subheader("Eintrag bearbeiten")
        pk_input = st.text_input(f"Gib den Wert für {pk_col} ein, der bearbeitet werden soll", key="edit_pk_input")

        if pk_input:
            if df.empty:
                st.warning("Die Tabelle ist leer. Keine IDs vorhanden zum Bearbeiten.")
            else:
                try:
                    first_val = df[pk_col].iloc[0]
                    pk_type = type(first_val)
                    if issubclass(pk_type, (np.integer, np.floating)):
                        pk_val = pk_type(pk_input)
                    else:
                        pk_val = pk_type(pk_input)

                    if pk_val in df[pk_col].values:
                        selected_row = df[df[pk_col] == pk_val]
                        st.table(selected_row)

                        row = selected_row.iloc[0]
                        updated_data = {}
                        for col in schema:
                            name = col["name"]
                            typ = col["type"]
                            extra = col["extra"] or ""
                            enum_opts = _parse_enum_options(typ)
                            current_value = row[name]

                            # Wenn PK auto_increment, nutze disabled/display only
                            if col["key"] == "PRI" and "auto_increment" in (extra or "").lower():
                                st.markdown(f"*{name} (Primärschlüssel, AUTO_INCREMENT): {current_value}*")
                                continue

                            if enum_opts:
                                # zeige momentane Auswahl
                                options = [""] + enum_opts
                                val = current_value if pd.notna(current_value) else ""
                                sel = st.selectbox(f"{name} (enum)", options=options, index=options.index(val) if val in options else 0, key=f"edit_{name}")
                                updated_data[name] = sel if sel != "" else None
                            elif any(x in typ.lower() for x in ("int", "decimal", "float", "double")):
                                if pd.isna(current_value):
                                    # setzte default
                                    if "int" in typ.lower():
                                        cur = 0
                                    else:
                                        cur = 0.0
                                else:
                                    cur = float(current_value) if not isinstance(current_value, (int, float, np.integer, np.floating)) else float(_to_python_value(current_value))
                                if "int" in typ.lower():
                                    # zahlen input bei integer Format
                                    updated_data[name] = int(st.number_input(f"{name} ({typ})", value=int(cur), format="%d", step=1, key=f"edit_{name}"))
                                else:
                                    updated_data[name] = st.number_input(f"{name} ({typ})", value=cur, key=f"edit_{name}")
                            elif "date" in typ.lower() and "datetime" not in typ.lower():
                                if pd.notna(current_value):
                                    try:
                                        cur = pd.to_datetime(current_value).date()
                                    except Exception:
                                        cur = pd.Timestamp.today().date()
                                else:
                                    cur = pd.Timestamp.today().date()
                                updated_data[name] = st.date_input(f"{name} ({typ})", value=cur, key=f"edit_{name}")
                            elif "datetime" in typ.lower() or "timestamp" in typ.lower():
                                if pd.notna(current_value):
                                    try:
                                        cur = pd.to_datetime(current_value)
                                        cur_date = cur.date()
                                    except Exception:
                                        cur_date = pd.Timestamp.now().date()
                                else:
                                    cur_date = pd.Timestamp.now().date()
                                updated_data[name] = st.date_input(f"{name} ({typ})", value=cur_date, key=f"edit_{name}")
                            else:
                                updated_data[name] = st.text_input(f"{name} ({typ})", value=str(current_value) if pd.notna(current_value) else "", key=f"edit_{name}")

                        if st.button("Eintrag aktualisieren"):
                            try:
                                # konvertiere numpy/pandas Typen zu standard Python Typen
                                prepared = {k: (_to_python_value(v) if v is not None else None) for k, v in updated_data.items()}
                                update_entry(conn, table_name, prepared, pk_col, pk_val)
                                st.success("Eintrag aktualisiert!")
                                st.rerun()
                            except mysql.Error as e:
                                st.error(_format_db_error(e))
                                with st.expander("Fehlerdetails"):
                                    st.text(str(e))
                            except Exception as e:
                                st.error("Fehler beim Aktualisieren.")
                                with st.expander("Fehlerdetails"):
                                    st.text(str(e))
                    else:
                        st.warning(f"Keine Zeile mit {pk_col} = {pk_val} gefunden.")
                except ValueError:
                    st.error(f"Ungültiger Wert für {pk_col}. Bitte den richtigen Typ eingeben.")
                except mysql.Error as e:
                    st.error(_format_db_error(e))
                    with st.expander("Fehlerdetails"):
                        st.text(str(e))
                except Exception as e:
                    st.error("Fehler beim Verarbeiten der Eingabe.")
                    with st.expander("Fehlerdetails"):
                        st.text(str(e))
