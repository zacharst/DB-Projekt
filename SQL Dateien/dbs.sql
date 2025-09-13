/*
* 1. Erstellen der Datenbank
*/ 

CREATE DATABASE hochschulsport; 
USE hochschulsport;
/*
* 2. Entitäten
*/ 

CREATE TABLE Kursteilnehmer (
teilnehmer_id INT PRIMARY KEY AUTO_INCREMENT,
teilnehmer_name VARCHAR(100),
teilnehmer_mail VARCHAR(100),
teilnehmer_adresse VARCHAR(100)
);

CREATE TABLE Studierende (
teilnehmer_id INT NOT NULL,
FOREIGN KEY (teilnehmer_id) REFERENCES Kursteilnehmer(teilnehmer_id), 
matrikelnummer INT
);

CREATE TABLE Beschäftigte (
teilnehmer_id INT NOT NULL,
FOREIGN KEY (teilnehmer_id) REFERENCES Kursteilnehmer(teilnehmer_id), 
personalnummer INT,
abteilung VARCHAR(100)
);

CREATE TABLE Externe_Alumni (
teilnehmer_id INT NOT NULL,
FOREIGN KEY (teilnehmer_id) REFERENCES Kursteilnehmer(teilnehmer_id), 
mitgliedsnummer INT
);

CREATE TABLE Verwaltungsangestellter (
angestellten_id INT PRIMARY KEY AUTO_INCREMENT,
angestellten_name VARCHAR(100),
berechtigung VARCHAR(100)
);

CREATE TABLE Kursleiter (
kursleiter_id INT PRIMARY KEY AUTO_INCREMENT, 
kursleiter_name VARCHAR(100), 
qualifikation VARCHAR(100), 
e_mail VARCHAR(100)
);

CREATE TABLE Termin (
termin_id INT PRIMARY KEY AUTO_INCREMENT,
datum DATETIME
);

CREATE TABLE Ort (
ort_id INT PRIMARY KEY AUTO_INCREMENT,
kapazität INT,
adresse VARCHAR(100),
ort_name VARCHAR (100)
);

CREATE TABLE Sportkategorie(
kategorie_id INT PRIMARY KEY AUTO_INCREMENT,
kategorie_name VARCHAR(100)
);

CREATE TABLE Sportangebot (
angebot_id INT PRIMARY KEY AUTO_INCREMENT,
angebot_name VARCHAR (100),
angebot_beschreibung VARCHAR(2000),
kategorie_id INT NOT NULL,
FOREIGN KEY (kategorie_id) REFERENCES Sportkategorie(kategorie_id)
);

CREATE TABLE Veranstaltung (
veranstaltungs_id INT PRIMARY KEY AUTO_INCREMENT,
dauer INT,
voraussetzungen VARCHAR(100),
buchungsfrist DATETIME,
schwierigkeitslevel VARCHAR(2),
CHECK (schwierigkeitslevel IN('A1','A2','F1','F2')),
preis_beschäftigte DECIMAL(5,2),
preis_externe_alumni DECIMAL(5,2),
preis_student DECIMAL(5,2),
verfügbare_plätze INT,
kursleiter_id INT,
FOREIGN KEY (kursleiter_id) REFERENCES Kursleiter(kursleiter_id),
angebot_id INT NOT NULL,
FOREIGN KEY (angebot_id) REFERENCES Sportangebot(angebot_id),
ort_id INT NOT NULL,
FOREIGN KEY (ort_id) REFERENCES Ort(ort_id)
);

CREATE TABLE Buchung (
buchungs_id INT PRIMARY KEY AUTO_INCREMENT, 
datum TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
betrag INT, 
teilnehmer_id INT NOT NULL,
FOREIGN KEY (teilnehmer_id) REFERENCES Kursteilnehmer(teilnehmer_id), 
veranstaltungs_id INT NOT NULL,
FOREIGN KEY (veranstaltungs_id) REFERENCES Veranstaltung(veranstaltungs_id), 
buchung_status ENUM('bezahlt', 'storniert', 'offen', 'wartend') NOT NULL DEFAULT 'offen'
);

CREATE TABLE Rechnung (
rechnungs_id INT PRIMARY KEY AUTO_INCREMENT,
sender VARCHAR(50),
empfänger VARCHAR(50), ## sinnhaftigkeit von sender und empfänger fraglich, ggf. als optionales feld falls adresse abweicht
angestellten_id INT NOT NULL,
FOREIGN KEY(angestellten_id) REFERENCES Verwaltungsangestellter(angestellten_id),
buchungs_id INT NOT NULL,
FOREIGN KEY(buchungs_id) REFERENCES Buchung(buchungs_id) 
);

CREATE TABLE Feedback (
feedback_id INT PRIMARY KEY AUTO_INCREMENT,
veranstaltungs_id INT,
FOREIGN KEY (veranstaltungs_id) REFERENCES Veranstaltung(veranstaltungs_id),
teilnehmer_id INT,
FOREIGN KEY (teilnehmer_id) REFERENCES Kursteilnehmer(teilnehmer_id),
kursleiter_id INT,
FOREIGN KEY (kursleiter_id) REFERENCES Kursleiter(kursleiter_id),
bewertung INT NOT NULL,
CHECK (bewertung BETWEEN 1 AND 5),
kommentar VARCHAR (1000)
);

CREATE TABLE Warteliste(
warteliste_id INT PRIMARY KEY AUTO_INCREMENT,
veranstaltungs_id INT,
FOREIGN KEY (veranstaltungs_id) REFERENCES Veranstaltung(veranstaltungs_id),
teilnahme_möglich BOOL DEFAULT 1);

CREATE TABLE Geräte(
geräte_id INT PRIMARY KEY AUTO_INCREMENT,
typ VARCHAR(100),
zustand ENUM('gut', 'schlecht', 'fehlt') DEFAULT 'gut' 
);

CREATE TABLE Sportevent(
event_id INT PRIMARY KEY AUTO_INCREMENT,
event_name VARCHAR(100),
event_teilnahme_bedingungen VARCHAR(200)
);

CREATE TABLE Prüfung(
veranstaltungs_id INT NOT NULL,
FOREIGN KEY (veranstaltungs_id) REFERENCES Veranstaltung(Veranstaltungs_id),
prüfungsform VARCHAR(50),
passwort VARCHAR(50)
);

CREATE TABLE Gym_mitgliedschaft(
veranstaltungs_id INT NOT NULL,
FOREIGN KEY (veranstaltungs_id) REFERENCES Veranstaltung(Veranstaltungs_id),
berechtigungen VARCHAR(50)
);

CREATE TABLE Onlinekurs(
veranstaltungs_id INT NOT NULL,
FOREIGN KEY (veranstaltungs_id) REFERENCES Veranstaltung(Veranstaltungs_id),
zugangslink VARCHAR(50),
plattform VARCHAR(50)
);

CREATE TABLE Offlinekurs(
veranstaltungs_id INT NOT NULL,
FOREIGN KEY (veranstaltungs_id) REFERENCES Veranstaltung(Veranstaltungs_id),
wetterabhängig BOOL
);

CREATE TABLE Exkursion(
veranstaltungs_id INT NOT NULL,
FOREIGN KEY (veranstaltungs_id) REFERENCES Veranstaltung(Veranstaltungs_id),
exkursion_name VARCHAR(50),
zielort VARCHAR(50),
teilnahmebedingungen VARCHAR(50)
);

/*
* 3. N zu M Relationships
* 1:1 sowie 1:M müssen nicht modeliert werden 
* N:M müssen als Entitäten modelliert werden
*/ 

CREATE TABLE Verwaltete_Veranstaltungen(
angestellten_id INT,
veranstaltungs_id INT,
PRIMARY KEY (angestellten_id, veranstaltungs_id),
FOREIGN KEY (angestellten_id) REFERENCES Verwaltungsangestellter (angestellten_id),
FOREIGN KEY (veranstaltungs_id) REFERENCES Veranstaltung(veranstaltungs_id)
);

CREATE TABLE Wartende_Kursteilnehmer(
teilnehmer_id INT,
warteliste_id INT,
PRIMARY KEY (teilnehmer_id, warteliste_id),
FOREIGN KEY (teilnehmer_id) REFERENCES Kursteilnehmer(teilnehmer_id),
FOREIGN KEY (warteliste_id) REFERENCES Warteliste(warteliste_id)
);

CREATE TABLE Veranstaltung_Orte(
veranstaltungs_id INT,
ort_id INT,
PRIMARY KEY (veranstaltungs_id, ort_id),
FOREIGN KEY (veranstaltungs_id) REFERENCES Veranstaltung(veranstaltungs_id),
FOREIGN KEY (ort_id) REFERENCES Ort(ort_id)
);

CREATE TABLE Veranstaltung_Termine(
veranstaltungs_id INT,
termin_id INT,
PRIMARY KEY (veranstaltungs_id, termin_id),
FOREIGN KEY (veranstaltungs_id) REFERENCES Veranstaltung(veranstaltungs_id),
FOREIGN KEY (termin_id) REFERENCES Termin(termin_id)
);

CREATE TABLE Benötigte_Geräte(
angebot_id INT,
geräte_id INT,
PRIMARY KEY (angebot_id, geräte_id),
FOREIGN KEY (angebot_id) REFERENCES Sportangebot(angebot_id),
FOREIGN KEY (geräte_id) REFERENCES Geräte(geräte_id)
);

CREATE TABLE Events_für_Sportkategorie(
kategorie_id INT,
event_id INT,
PRIMARY KEY (kategorie_id, event_id),
FOREIGN KEY (kategorie_id) REFERENCES Sportkategorie(kategorie_id),
FOREIGN KEY (event_id) REFERENCES Sportevent(event_id)
);

/*
* 5. Trigger
* 1. Falls Veranstaltung die gebucht wurde voll ist --> Eintrag in Warteliste
* 2. Falls Veranstaltung storniert --> nachrücken
*/
DELIMITER $$

CREATE TRIGGER check_teilnahme_moeglich
BEFORE INSERT ON Buchung
FOR EACH ROW
BEGIN
    DECLARE aktuelle INT;
    DECLARE maxplaetze INT;
    SELECT COUNT(*) INTO aktuelle
    FROM Buchung
    WHERE veranstaltungs_id = NEW.veranstaltungs_id
      AND buchung_status IN ('offen','bezahlt');
    SELECT verfügbare_plätze INTO maxplaetze
    FROM Veranstaltung
    WHERE veranstaltungs_id = NEW.veranstaltungs_id;
    IF aktuelle >= maxplaetze THEN
        SET NEW.buchung_status = 'wartend';
        UPDATE Warteliste
        SET teilnahme_möglich = 0
        WHERE veranstaltungs_id = NEW.veranstaltungs_id;
    ELSE
        UPDATE Warteliste
        SET teilnahme_möglich = 1
        WHERE veranstaltungs_id = NEW.veranstaltungs_id;
    END IF;
END$$


CREATE TRIGGER handle_storno
AFTER UPDATE ON Buchung
FOR EACH ROW
BEGIN
    DECLARE nachruecker_id INT;
    IF NEW.buchung_status = 'storniert' AND OLD.buchung_status <> 'storniert' THEN
        -- Warteliste öffnen
        UPDATE Warteliste
        SET teilnahme_möglich = 1
        WHERE veranstaltungs_id = NEW.veranstaltungs_id;
        SELECT buchungs_id INTO nachruecker_id
        FROM Buchung
        WHERE veranstaltungs_id = NEW.veranstaltungs_id
          AND buchung_status = 'wartend'
        ORDER BY datum ASC
        LIMIT 1;
        IF nachruecker_id IS NOT NULL THEN
            UPDATE Buchung
            SET buchung_status = 'offen'
            WHERE buchungs_id = nachruecker_id;
        END IF;
    END IF;
END$$

DELIMITER ;

/*
* 5.1 Beispieldaten: Entitäten
*/ 

INSERT INTO Kursteilnehmer (teilnehmer_name, teilnehmer_mail, teilnehmer_adresse)
VALUES
('Johann Wolfgang von Goethe', 'goethe@mail.de', 'Frauenplan 1, 99423 Weimar'),
('Friedrich Schiller', 'schiller@mail.de', 'Schillerstraße 12, 99423 Weimar'),
('Heinrich Heine', 'heine@mail.de', 'Düsseldorfer Straße 7, 40213 Düsseldorf'),
('Thomas Mann', 'mann@mail.de', 'Budapester Straße 5, 10787 Berlin'),
('Hermann Hesse', 'hesse@mail.de', 'Calwweg 3, 75365 Calw'),
('Franz Kafka', 'kafka@mail.de', 'Prager Allee 10, 11000 Prag'),
('Bertolt Brecht', 'brecht@mail.de', 'Berliner Straße 15, 10117 Berlin'),
('Rainer Maria Rilke', 'rilke@mail.de', 'Wiener Straße 20, 1010 Wien'),
('Theodor Fontane', 'fontane@mail.de', 'Neuruppiner Straße 8, 16816 Neuruppin'),
('Gottfried Keller', 'keller@mail.de', 'Zürcher Straße 11, 8001 Zürich');

INSERT INTO Studierende VALUES (1,123456), (2,444444), (3,565656);
INSERT INTO Beschäftigte VALUES (4, 999999, "Mathematik"), (5,661233, "Informatik"), (6,333123,"Philosophie");
INSERT INTO Externe_Alumni VALUES (7, 234), (8, 555), (9, 123), (10, 909);

INSERT INTO Verwaltungsangestellter (angestellten_name, berechtigung)
VALUES
('Max Mustermann', 'Admin'), 
('Maria Musterfrau', 'Admin');

INSERT INTO Termin (datum) VALUES
('2025-09-01 10:00:00'),
('2025-09-08 10:00:00'),
('2025-09-15 10:00:00'),
('2025-09-22 10:00:00'),
('2025-09-29 10:00:00'),
('2025-10-06 10:00:00'),
('2025-10-13 10:00:00'),
('2025-10-20 10:00:00'),
('2025-10-27 10:00:00'),
('2025-11-03 10:00:00'),
('2025-11-10 10:00:00'),
('2025-11-17 10:00:00');

INSERT INTO Ort (kapazität, adresse, ort_name)
VALUES
(50, 'Rudower Chaussee 35', 'Sporthalle'),
(100, 'Karl Marx Straße 15', 'Martial Arts Schule'),
(25, 'Oststraße 24', 'Yogastudio'),
(NULL, 'Seestraße 10', 'Fitness Studio'),
(NULL, NULL, 'Online');

INSERT INTO Kursleiter (kursleiter_name, qualifikation, e_mail)
VALUES
('Joseph Gibbs', 'Boxweltmeister', 'gibbs@email.com'),
('Marylin Mercado', 'Fußballspielerin', 'mercardo@email.com'),
('Remi Rosales', 'Tennisspieler', 'rosales@mail.com'),
('Brendon Lloyd', 'Yogalehrer', 'lloyd@email.com'),
('Zack Moreno', 'Tanzlehrer', 'morenotanz@email.com'),
('Lee Parsons', 'MMA-Lehrer', 'gibbs@email.com')
;

INSERT INTO Sportkategorie (kategorie_name)
VALUES
('Yoga'), ('Kampfsport'),('Ballsport'),('Tanz'),('Gym-Membership');

INSERT INTO Sportangebot (angebot_name, angebot_beschreibung, kategorie_id)
VALUES
('Yin-Yoga', 'Ruhiger passiver Yoga-Stil', 1),
('Hatha Yoga', 'Verbindung körperlicher Übungen, Atemübungen und Meditation', 1),
('MMA', 'Vollkontakt-Kampfsportat, die sich verschiedenen Kampfkünsten bedient', 2),
('Boxen', 'Kampfsport, der nur mit Fäusten ausgeführt wird', 2),
('Tennis', 'Wer Tennis lernen will, ist hier richtig. A1 für Anfänger, F1 für Fortgeschrittene.', 3),
('Basketball', 'Dieses Jahr nur F2 für stark Fortgeschrittene.', 3),
('Gesellschaftstanz', 'Kann nur mit einem Partner belegt werden, bitte nutzen Sie ggf. die Partnerbörse.', 4), 
('Gym-Mitgliedschaft - 1 Jahr', 'Mitgliedschaft im Unigym für 1 Jahr. Wird nicht automatisch verlängert.', 5),
('Online Yoga-Einzelkurs', 'Exklusiver Einzel-Yogakurs für nur 1 Person', 1); 

INSERT INTO Veranstaltung (dauer, voraussetzungen, buchungsfrist, schwierigkeitslevel, preis_beschäftigte, 
preis_externe_alumni, preis_student, verfügbare_plätze, kursleiter_id, angebot_id, ort_id)
VALUES
(12, NULL, '2025-09-30 23:59:59', 'A1', 25.00, 16.00, 15.00, 50, 4, 1, 3),
(12, NULL, '2025-09-30 23:59:59', 'A1', 25.00, 16.00, 15.00, 50, 4, 2, 3),
(12, NULL, '2025-09-30 23:59:59', 'A1', 25.00, 16.00, 15.00, 50, 1, 3, 2),
(12, NULL, '2025-09-30 23:59:59', 'A1', 25.00, 16.00, 15.00, 20, 6, 4, 2),
(12, NULL, '2025-09-30 23:59:59', 'A1', 30.00, 16.00, 15.00, 50, 3, 5, 1),
(12, "Tennisprüfung A1 bestanden", '2025-09-30 23:59:59', 'F1', 35.00, 30.00, 25.00, 50, 3, 5, 1),
(12, NULL, '2025-09-30 23:59:59', 'F2', 25.00, 16.00, 15.00, 50, 2, 6, 1),
(12, NULL, '2025-09-30 23:59:59', 'A2', 55.00, 35.00, 25.00, 70, 6, 7, 1),
(12, NULL, '2025-09-30 23:59:59', 'A2', 55.00, 35.00, 25.00, 70, 6, 7, 1),
(53, NULL, '2025-09-30 23:59:59', NULL, 10.00, 20.00, 30.00, NULL, NULL, 8, 4),
(12, NULL, '2025-09-30 23:59:59', NULL, 100.00, 200.00, 300.00, 1, 1, 9, 5);


INSERT INTO Buchung (datum, betrag, teilnehmer_id, veranstaltungs_id, buchung_status)
VALUES
('2025-08-01 12:14:59', 15.00, 1, 1, 'bezahlt'),
('2025-08-01 12:13:22', 15.00, 2, 2, 'bezahlt'),
('2025-08-01 11:11:59', 15.00, 3, 3, 'bezahlt'),
('2025-08-01 10:11:29', 16.00, 4, 4, 'storniert'),
('2025-08-02 10:15:29', 16.00, 4, 1, 'bezahlt'),
('2025-08-02 10:15:29', 100, 1, 11, 'bezahlt'),
('2025-08-02 10:25:29', 100, 2, 11, 'offen'),
('2025-08-02 10:25:29', 100, 3, 11, 'offen');

INSERT INTO Rechnung (angestellten_id, buchungs_id)
VALUES
(1,1),(1,2),(1,3),(2,4),(2,5);

INSERT INTO Warteliste (veranstaltungs_id) ### TODO: Boolwert über Trigger machen
VALUES
(1),(2),(3),(4),(5),(6),(7),(8),(9),(10),(11);

INSERT INTO Geräte(typ, zustand)
VALUES
("Boxhandschuhe","gut"),
("Yogamatten","gut");

INSERT INTO Sportevent (event_name)
VALUES
("Kampfsportfest");

INSERT INTO Prüfung (veranstaltungs_id, prüfungsform, passwort)
VALUES
(5, "Tennisprüfung A1", "tennis2025");

INSERT INTO Gym_mitgliedschaft(veranstaltungs_id, berechtigungen)
VALUES
(8, "default");

INSERT INTO Offlinekurs(veranstaltungs_id, wetterabhängig)
VALUES
(1,0),(2,0),(3,0),(4,0),(5,0),(6,0),(7,0),(8,0),(9,0),(10,0);

INSERT INTO Onlinekurs(veranstaltungs_id)
VALUES (11);



INSERT INTO Feedback (veranstaltungs_id, teilnehmer_id, kursleiter_id, bewertung, kommentar)
VALUES
(1,1,1,5,"alles top");

-- NOCH LEERE ENTITÄTEN:
-- EXKURSION

/*
* 5.2 Beispieldaten für M:N Beziehungen
*/ 

INSERT INTO benötigte_geräte(angebot_id, geräte_id)
VALUES
(3,1),(1,2),(2,2);


INSERT INTO veranstaltung_orte(veranstaltungs_id, ort_id)
VALUES
(1, 3),
(2, 3),
(3, 2),
(4, 2),
(5, 1),
(6, 1),
(7, 1),
(8, 1),
(9, 1),
(10, 4);

#
INSERT INTO veranstaltung_termine (veranstaltungs_id, termin_id)
SELECT v.veranstaltungs_id, t.termin_id
FROM veranstaltung v
CROSS JOIN termin t
WHERE v.veranstaltungs_id BETWEEN 1 AND 9
  AND t.termin_id BETWEEN 1 AND 12;

INSERT INTO events_für_sportkategorie(kategorie_id, event_id)
VALUES
(2,1);

INSERT INTO verwaltete_veranstaltungen(angestellten_id, veranstaltungs_id)
VALUES
(1,1),(1,2),(1,3),(1,4),(1,5),(2,6),(2,7),(2,8),(2,9),(2,10),(2,11);

-- NOCH LEERE RELATION:
-- wartende_kursteilnehmer

/*
* 5. View
*/ 

CREATE VIEW Veranstaltung_Auslastung AS
SELECT 
    v.veranstaltungs_id,
    a.angebot_name,
    COUNT(b.teilnehmer_id) AS teilnehmerzahl,
    v.verfügbare_plätze
FROM Veranstaltung v
JOIN Sportangebot a ON v.angebot_id = a.angebot_id
LEFT JOIN Buchung b ON v.veranstaltungs_id = b.veranstaltungs_id
GROUP BY v.veranstaltungs_id, a.angebot_name, v.verfügbare_plätze;

/*
* 6. Indexes
*/ 
CREATE INDEX idx_angebot_name ON Sportangebot(angebot_name);
CREATE INDEX idx_ort_name ON Ort(ort_name);

/*
* 7. Queries
*/ 

# 7.1 Anzeigen aller Studenten
SELECT * FROM Kursteilnehmer INNER JOIN Studierende
ON Kursteilnehmer.teilnehmer_id = Studierende.teilnehmer_id; 

#7.2 Anzahl Veranstaltungen pro Angebot
SELECT s.angebot_id, s.angebot_name, COUNT(v.veranstaltungs_id) AS anzahl_veranstaltungen
FROM Sportangebot s
LEFT JOIN Veranstaltung v ON s.angebot_id = v.angebot_id
GROUP BY s.angebot_id, s.angebot_name;

#7.3 Teilnehmerliste und Sportangebote, die sie gebucht haben
SELECT k.teilnehmer_id, k.teilnehmer_name, s.angebot_name
FROM Kursteilnehmer k
JOIN Buchung b ON k.teilnehmer_id = b.teilnehmer_id
JOIN Veranstaltung v ON b.veranstaltungs_id = v.veranstaltungs_id
JOIN Sportangebot s ON v.angebot_id = s.angebot_id;

#7.4 Alle Teilnehmer die auf Wartelisten stehen
SELECT k.teilnehmer_id, k.teilnehmer_name AS teilnehmer_name, v.veranstaltungs_id, sa.angebot_name
FROM Buchung b
JOIN Kursteilnehmer k ON b.teilnehmer_id = k.teilnehmer_id
JOIN Veranstaltung v ON b.veranstaltungs_id = v.veranstaltungs_id
JOIN Sportangebot sa ON v.angebot_id = sa.angebot_id
WHERE b.buchung_status = 'wartend'
ORDER BY v.veranstaltungs_id, b.datum;

#7.5 Prozentuelle Auslastung aller Kurse (nur bezahlte Buchung)
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

#7.6 Kurse die in bestimmten Ort stattfinden
SELECT v.veranstaltungs_id, sa.angebot_name, o.ort_name
FROM Veranstaltung v
JOIN Sportangebot sa ON v.angebot_id = sa.angebot_id
JOIN Ort o ON v.ort_id = o.ort_id
WHERE o.ort_name = 'Yogastudio'; 

#7.7 Teilnehmer mit den meisten Buchungen
SELECT k.teilnehmer_id, k.teilnehmer_name, COUNT(b.buchungs_id) AS buchungen
FROM Kursteilnehmer k
JOIN Buchung b ON k.teilnehmer_id = b.teilnehmer_id
GROUP BY k.teilnehmer_id, k.teilnehmer_name
ORDER BY buchungen DESC
LIMIT 1;

#7.8 Einnahmen pro Angebot
SELECT sa.angebot_name, SUM(b.betrag) AS gesamt_einnahmen
FROM Buchung b
JOIN Veranstaltung v ON b.veranstaltungs_id = v.veranstaltungs_id
JOIN Sportangebot sa ON v.angebot_id = sa.angebot_id
WHERE b.buchung_status = 'bezahlt'
GROUP BY sa.angebot_name
ORDER BY gesamt_einnahmen DESC;

#7.9 Veranstaltungen mit mehr als 50 verfügbaren Plätzen
SELECT sa.angebot_name, v.verfügbare_plätze
FROM Veranstaltung v
JOIN Sportangebot sa ON v.angebot_id = sa.angebot_id
WHERE v.verfügbare_plätze > 5;

/* #7.10 Parameterized Query
* benötigt connector
SELECT v.veranstaltungs_id, sa.angebot_name, o.ort_name, v.verfügbare_plätze
FROM Veranstaltung v
JOIN Sportangebot sa ON v.angebot_id = sa.angebot_id
JOIN Ort o ON v.ort_id = o.ort_id
WHERE o.ort_name = ?; 
*/