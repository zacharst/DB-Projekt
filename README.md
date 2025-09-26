# DB Projekt – Hochschulsport

Dieses Projekt erstellt und verwaltet eine **Hochschulsport-Datenbank** mit einer Streamlit-Oberfläche.

---

## Installation

### 1. **Benötigte Pakete installieren**

```bash
pip install -r requirements.txt
```

### 2. **Setup ausführen**

* Startskript:

```bash
python setup.py
```

* Aufgaben des Setups:

  * Login in die Datenbank
  * Speichern der Zugangsdaten
  * Automatisches Erstellen der Datenbank *Hochschulsport*

#### Alternative (manuell)

* Datenbankzugangsdaten in `.streamlit/secrets.toml` eintragen:

```toml
[mysql]
host = "localhost"
port = 3306
username = "enterusername"
password = "enterpassword"
database = "databasename"
```

* SQL-Datei manuell ausführen, um die Datenbank zu erstellen.

### 3. **Streamlit App starten**

```bash
streamlit run app.py
```

Danach öffnet sich die Oberfläche automatisch im Browser.

### 4. **Nutzerkonten**

* `verwaltung` (pw: 1234) – kann:

  * Einträge in allen Tabellen hinzufügen, bearbeiten und löschen
  * Datenbankinhalte verwalten und überwachen
  * Fehlerberichte zu Datenbankoperationen einsehen
* `kursleiter` (pw: 12345) – kann:

  * Kursinformationen einsehen und verwalten (abhängig von Berechtigungen)

### 5. **Reset der Datenbank**

Das Skript `reset.py`, führt folgende Aktionen aus:

* Löschen aller Rollen (`rolle_verwaltung`, `rolle_kursleiter`)
* Löschen der Benutzer (`verwaltung`, `kursleiter`)
* Löschen der Datenbank `hochschulsport`
* Skript prüft zunächst die Zugangsdaten und fragt nach einer Bestätigung, bevor alles gelöscht wird

```bash
python reset.py
```
---

