import os
import psycopg2

# -------------------------------------------------
# Connessione al DB PostgreSQL
# -------------------------------------------------

def get_db():
    """
    Se DATABASE_URL esiste → usa PostgreSQL
    Se non esiste → usa SQLite locale (data/estratti.db)
    """
    if "DATABASE_URL" in os.environ:
        # Render → PostgreSQL
        return psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")
    else:
        # Locale → SQLite
        import sqlite3
        db_path = os.path.join(os.path.dirname(__file__), "data", "estratti.db")
        return sqlite3.connect(db_path)



# -------------------------------------------------
# Creazione iniziale tabella
# -------------------------------------------------

def init_db():
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS estrazioni (
                nome TEXT PRIMARY KEY,
                estratto TEXT
            )
        """)
    except Exception as e:
        print("Errore init_db:", e)

    conn.commit()
    conn.close()


# -------------------------------------------------
# Funzioni CRUD
# -------------------------------------------------

def db_get_estratti():
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT nome, estratto FROM estrazioni")
        rows = cur.fetchall()
        conn.close()

        # PostgreSQL restituisce tuple normali
        return {nome: estratto for (nome, estratto) in rows}

    except Exception as e:
        print("Errore db_get_estratti:", e)
        conn.close()
        return {}



def db_set_estratto(nome, estratto):
    conn = get_db()
    cur = conn.cursor()

    try:
        # PostgreSQL
        cur.execute("""
            INSERT INTO estrazioni (nome, estratto)
            VALUES (%s, %s)
            ON CONFLICT (nome) DO UPDATE SET estratto = EXCLUDED.estratto
        """, (nome, estratto))
    except:
        try:
            # SQLite
            cur.execute("""
                INSERT INTO estrazioni (nome, estratto)
                VALUES (?, ?)
                ON CONFLICT(nome) DO UPDATE SET estratto = excluded.estratto
            """, (nome, estratto))
        except:
            # Fallback SQLite (per versioni vecchie)
            cur.execute("DELETE FROM estrazioni WHERE nome = ?", (nome,))
            cur.execute("INSERT INTO estrazioni (nome, estratto) VALUES (?, ?)", (nome, estratto))

    conn.commit()
    conn.close()



def db_reset_estrazioni():
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM estrazioni")
    except:
        cur.execute("DELETE FROM estrazioni")

    conn.commit()
    conn.close()

