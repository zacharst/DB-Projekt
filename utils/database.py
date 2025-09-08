# utils/database.py
import toml
from mysql.connector import connect
import pandas as pd
import json
import os

JOIN_CONFIG_PATH = os.path.join("utils","join_config.json")
SECRETS_PATH = os.path.join(".streamlit","secrets.toml")


def get_connection():
    """
    Stellt eine Verbindung zur MySQL-Datenbank her.

    Liest Zugangsdaten aus .streamlit/secrets.toml und gibt eine offene Verbindung zurück.

    Returns:
        mysql.connector.connection_cext.CMySQLConnection: Datenbankverbindung
    """
    secrets = toml.load(SECRETS_PATH)
    conn = connect(
        host=secrets["mysql"]["host"],
        user=secrets["mysql"]["username"],
        password=secrets["mysql"]["password"],
        database=secrets["mysql"]["database"]
    )
    return conn


def load_dataframe(conn, table_name, apply_joins=False):
    """
    Lädt eine Tabelle als Pandas DataFrame aus der Datenbank.

    Optional können vordefinierte Joins aus `join_config.json` angewendet werden.

    Args:
        conn: MySQL Datenbankverbindung.
        table_name (str): Name der Tabelle.
        apply_joins (bool, optional): Ob definierte Joins angewendet werden sollen.
    Returns:
        pd.DataFrame: DataFrame mit den geladenen Daten.
    """
    with open(JOIN_CONFIG_PATH, "r", encoding="utf-8") as f:
        join_config = json.load(f)

    cursor = conn.cursor()
    if apply_joins and table_name in join_config:
        joins = join_config[table_name]
        select_parts = ["t.*"]
        join_clauses = []

        for j in joins:
            jt = j["join_table"]
            join_ons = j["join_on"]
            display_cols = j["display_columns"]

            select_parts.extend([f"{jt}.{col}" for col in display_cols])
            join_condition = " AND ".join([f"t.{col} = {jt}.{col}" for col in join_ons])
            join_clauses.append(f"LEFT JOIN {jt} ON {join_condition}")

        select_clause = ", ".join(select_parts)
        join_clause = " ".join(join_clauses)
        query = f"SELECT {select_clause} FROM {table_name} t {join_clause};"
    else:
        query = f"SELECT * FROM `{table_name}`;"

    cursor.execute(query)
    data = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    cursor.close()
    df = pd.DataFrame(data, columns=columns)
    return df
