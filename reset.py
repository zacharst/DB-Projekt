# reset.py
import mysql.connector
import tkinter as tk
from tkinter import simpledialog, messagebox

HOST = "localhost"
ROLES = ["rolle_verwaltung", "rolle_kursleiter"]
USERS = ["verwaltung", "kursleiter"]
DATABASE = "hochschulsport"

def ask_credentials():
    root = tk.Tk()
    root.withdraw()
    user = simpledialog.askstring("Login", "MySQL Benutzername:")
    pwd = simpledialog.askstring("Login", "MySQL Passwort:", show="*")
    return user, pwd

def confirm_reset():
    root = tk.Tk()
    root.withdraw()
    return messagebox.askyesno(
        "Achtung!",
        "Willst du wirklich alle Rollen, Benutzer und die Datenbank löschen?"
    )

def reset_db(user: str, password: str, host: str = HOST):
    try:
        conn = mysql.connector.connect(host=host, user=user, password=password)
        cursor = conn.cursor()

        # Rollen löschen
        for role in ROLES:
            cursor.execute(f"DROP ROLE IF EXISTS `{role}`;")
            #print(f"Rolle {role} gelöscht (falls vorhanden).")

        # Benutzer löschen
        for u in USERS:
            cursor.execute(f"DROP USER IF EXISTS '{u}'@'localhost';")
            #print(f"Benutzer {u} gelöscht (falls vorhanden).")

        # Datenbank löschen
        cursor.execute(f"DROP DATABASE IF EXISTS `{DATABASE}`;")
        #print(f"Datenbank {DATABASE} gelöscht (falls vorhanden).")

        conn.commit()
        cursor.close()
        conn.close()
        messagebox.showinfo("Erfolg", "Rollen, Benutzer und Datenbank wurden gelöscht!")
    except mysql.connector.Error as e:
        messagebox.showerror("Fehler", f"Fehler bei der Datenbankoperation:\n{e}")

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

def main():
    user, pwd = ask_credentials()
    if not user or not pwd:
        messagebox.showwarning("Abbruch", "Keine Zugangsdaten eingegeben.")
        return
    if not test_connection(user,pwd):
        return
    if confirm_reset():
        reset_db(user, pwd)
    else:
        messagebox.showinfo("Abbruch", "Löschen abgebrochen.")

if __name__ == "__main__":
    main()
