# DB Projekt – Hochschulsport

Dieses Projekt erstellt und verwaltet eine **Hochschulsport-Datenbank** mit einer Streamlit-Oberfläche.

**Hinweis:** Alle Funktionen basieren auf **MySQL** als Datenbankmanagementsystem.

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

### 4. **Nutzung**

* #### **4.1 Ohne Login**

  * Über den Tab **Tabelle anzeigen**, könenn Nutzer die Datenbank vollständig einsehen und die Tabellen filtern.
  * Für jedes Attribut der Tabelle, kann eingestellt werden wie und ob es gefiltert werden soll. Zusätzlich kann ein Limit eingestellt werden.
  * Durch einen Button auf dem Streamlit UI können die parametrisierten Queries, die durch die vom User gesetzten Filter erstellt werden, angezeigt werden.

  * Zusätzlich ist eine View **veranstaltung_auslastung** einsehbar, die angibt, wie stark die Sportangebote ausgebucht sind.

* #### **4.2 Mit Login** (über die vorgegebenen Nutzerkonten `verwaltung` / `kursleiter`)

  * Es besteht die Möglichkeit, sich mit verschiedenen Rollen einzuloggen. Dies ist notwendig, um alle Funktionalitäten nutzen zu können.
  * 1. `verwaltung` (Passwort: `1234`)
  * 2. `kursleiter` (Passwort: `12345`)


  * Nach erfolgreichem Login erscheinen zwei zusätzliche Tabs:

  * #### **4.2.1 SQL-Abfrage**

     * Hier können beliebige SQL-Abfragen auf der Datenbank ausgeführt werden.
     * Zusätzlich stehen 10 Beispielabfragen zur Verfügung. Inklusive Join, Aggregation, Sub-Anfrage, Sum, Group by, Order by.

  *  #### **4.2.2 Tabelle bearbeiten**

     * Berechtigungen hängen von der Rolle ab:

     * `verwaltung` (Passwort: `1234`)

       * Hat **VOLLE RECHTE** auf alle Tabellen: SELECT, INSERT, UPDATE, DELETE
       * Kann Views anzeigen

     * `kursleiter` (Passwort: `12345`)

       * Hat Lesezugriff auf die gesamte Datenbank (SELECT)
       * Kann **NUR** in den Tabellen `Buchung` und `Feedback` Datensätze aktualisieren (UPDATE) oder löschen (DELETE)
       * **KEINE** Berechtigung zum Einfügen neuer Datensätze in andere Tabellen

### 5. **Reset der Datenbank**

Das Skript `reset.py` führt folgende Aktionen aus:

* Löschen aller Rollen (`rolle_verwaltung`, `rolle_kursleiter`)
* Löschen der Benutzer (`verwaltung`, `kursleiter`)
* Löschen der Datenbank `hochschulsport`
* Das Skript prüft zunächst die Zugangsdaten und fragt nach einer Bestätigung, bevor alles gelöscht wird

```bash
python reset.py
```
