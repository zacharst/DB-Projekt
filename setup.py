# setup.py
import os
import mysql.connector
import tkinter as tk
from tkinter import simpledialog, messagebox
import toml
import re

SCHEMA_FILE = os.path.join("SQL Dateien","dbs_2.sql")
SECRETS_FILE = os.path.join(".streamlit", "secrets.toml")



def _remove_multiline_comments(sql):
    """ Entfernt alle Kommentare"""
    sql_no_comments = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    sql_no_comments = re.sub(r"^\s*(--|#).*?$", "", sql_no_comments, flags=re.MULTILINE)
    return sql_no_comments

def ask_credentials():
    """Öffnet Tkinter GUI-Dialog für DB-Login"""
    root = tk.Tk()
    root.withdraw()  # Kein Hauptfenster
    user = simpledialog.askstring("Login", "MySQL Benutzername:")
    pwd = simpledialog.askstring("Login", "MySQL Passwort:", show="*")
    return user, pwd

def test_connection(user, pwd, host="localhost"):
    """Testet Verbindung mit den angegebenen Zugangsdaten"""
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=pwd
        )
        conn.close()
        return True
    except mysql.connector.Error as e:
        messagebox.showerror("Fehler", f"Login fehlgeschlagen:\n{e}")
        return False


def run_sql(user, pwd, host="localhost"):
    """Liest schema.sql ein, entfernt DELIMITER-Zeilen, extrahiert Trigger und führt SQL-Statements aus."""
    conn = mysql.connector.connect(
        host=host,
        user=user,
        password=pwd
    )
    cursor = conn.cursor()

    with open(SCHEMA_FILE, encoding="utf-8") as f:
        sql = f.read()

    sql = _remove_multiline_comments(sql)
    # Entferne alle Zeilen mit DELIMITER
    sql = re.sub(r"^\s*DELIMITER.*\n", "", sql, flags=re.MULTILINE)

    # Extrahiere Trigger mit regulärem Ausdruck
    trigger_pattern = re.compile(r"CREATE TRIGGER.*?END\s*\$\$*", re.DOTALL)
    triggers = trigger_pattern.findall(sql)

    # Entferne Trigger aus dem SQL-Code
    sql_without_triggers = trigger_pattern.sub("", sql)

    # Führe alle anderen SQL-Statements aus
    statements = [stmt.strip() for stmt in sql_without_triggers.split(";") if stmt.strip()]
    for stmt in statements:
        cursor.execute(stmt)
        try:
            cursor.fetchall()  # Für Statements, die Ergebnisse liefern
        except mysql.connector.errors.InterfaceError:
            pass  # Für Statements, die keine Ergebnisse liefern

    # Führe die extrahierten Trigger separat aus
    for trigger in triggers:
        trigger = trigger.replace("$$", ";")  # Ersetze $$ durch ;
        cursor.execute(trigger)

    conn.commit()
    cursor.close()
    conn.close()
    messagebox.showinfo("Erfolg", "Datenbank erfolgreich erstellt!")

def update_secrets(user, pwd, host="localhost"):
    # Wenn die Datei existiert -> laden, sonst Defaultwerte setzen
    if os.path.exists(SECRETS_FILE):
        data = toml.load(SECRETS_FILE)
    else:
        os.makedirs(os.path.dirname(SECRETS_FILE), exist_ok=True)
        data = {
            "mysql": {
                "host": "localhost",
                "port": 3306,
                "username": "deinuser",
                "password": "deinpasswort",
                "database": "hochschulsport",
            }
        }

    # sicherstellen, dass mysql-Abschnitt vorhanden ist
    if "mysql" not in data:
        data["mysql"] = {}

    # user & password aktualisieren
    data["mysql"]["host"] = host
    data["mysql"]["username"] = user
    data["mysql"]["password"] = pwd

    with open(SECRETS_FILE, "w", encoding="utf-8") as f:
        toml.dump(data, f)

    #messagebox.showinfo("Gespeichert", f"Zugangsdaten in {SECRETS_FILE} gespeichert.")

def main():
    host = "localhost"  # ggf. anpassen
    while True:
        user, pwd = ask_credentials()
        if not user or not pwd:
            messagebox.showwarning("Abbruch", "Keine Zugangsdaten eingegeben.")
            return
        if test_connection(user, pwd, host):
            run_sql(user, pwd, host)
            update_secrets(user, pwd, host)
            break  # Setup war erfolgreich

if __name__ == "__main__":
    main()
