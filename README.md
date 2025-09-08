# DB Projekt – Hochschulsport

Dieses Projekt erstellt und verwaltet eine **Hochschulsport-Datenbank** mit einer Streamlit-Oberfläche.

---

## Installation

1. **Benötigte Pakete installieren**

   ```bash
   pip install -r requirements.txt
   ```

2. **Setup ausführen**

   * Startskript:

     ```bash
     python setup.py
     ```
   * Aufgaben des Setups:

     * Login in die Datenbank
     * Speichern der Zugangsdaten
     * Automatisches Erstellen der Datenbank *Hochschulsport*

   ### 🔧 Alternative (manuell)

   * Datenbankzugangsdaten in `.streamlit/secrets.toml` eintragen:

     ```toml
     [mysql]
     host = "localhost"
     port = 3306
     user = "root"
     password = "dein_passwort"
     database = "hochschulsport"
     ```
   * SQL-Datei manuell ausführen, um die Datenbank zu erstellen.

3. **Streamlit App starten**

   ```bash
   streamlit run app.py
   ```

   Danach öffnet sich die Oberfläche automatisch im Browser.

