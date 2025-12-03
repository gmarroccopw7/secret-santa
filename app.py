from flask import Flask, render_template, redirect, session, url_for, request
import json, os, random, tempfile, traceback

app = Flask(__name__)
app.secret_key = "supersecretkey123"

# --- Percorsi ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERSONE_FILE = os.path.join(BASE_DIR, "data", "persone.json")
ESCLUSIONI_FILE = os.path.join(BASE_DIR, "data", "esclusioni.json")

# File estrazioni dinamico → in /tmp (compatibile con Railway/Render)
ESTRATTI_FILE = os.path.join(tempfile.gettempdir(), "estratti.json")
ESTRATTI_GIOCATTOLI_FILE = os.path.join(tempfile.gettempdir(), "estratti_giocattoli.json")

def init_file(path):
    """Ricrea sempre i file a ogni avvio (richiesto da te)."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
        print(f"[INIT] Ricreato file: {path}")
    except Exception as e:
        print(f"[ERRORE INIT] {e}")

# Ricreo i file a ogni deploy/riavvio
init_file(ESTRATTI_FILE)
init_file(ESTRATTI_GIOCATTOLI_FILE)

# --- Caricamento persone ---
with open(PERSONE_FILE, encoding="utf-8") as f:
    PERSONE = json.load(f)["persone"]

# --- Caricamento esclusioni ---
if os.path.exists(ESCLUSIONI_FILE):
    with open(ESCLUSIONI_FILE, encoding="utf-8") as f:
        ESCLUSIONI = json.load(f)
else:
    ESCLUSIONI = {p: [] for p in PERSONE}

# --- Icone utenti ---
ICONE = [
    "babbo_natale.png",
    "renna.png",
    "pupazzo_neve.png",
    "pan_zenzero.png",
    "albero_natale.png",
    "palla_natale.png",
    "pacco_regalo.png",
    "panettone.jpg",
    "stella.png"
]
ICON_MAP = {p: ICONE[i % len(ICONE)] for i, p in enumerate(PERSONE)}

# --- ROUTE LOGIN ---
@app.route("/")
def login():
    return render_template("login.html", persone=PERSONE, icone=ICON_MAP)

@app.route("/login/<nome>")
def do_login(nome):
    if nome not in PERSONE:
        return "Utente non valido", 400
    session["utente"] = nome
    return redirect("/estrazione")

# --- ROUTE ESTRAZIONI ---
@app.route("/estrazione")
def estrazione():
    if "utente" not in session:
        return redirect("/")
    utente = session["utente"]

    # Carica estrazioni
    with open(ESTRATTI_FILE) as f:
        estratti1 = json.load(f)

    with open(ESTRATTI_GIOCATTOLI_FILE) as f:
        estratti2 = json.load(f)

    return render_template(
        "estrazione.html",
        utente=utente,
        gia1=estratti1.get(utente),
        gia2=estratti2.get(utente)
    )

# --- ESTRAZIONE 1: Secret Santa ---
@app.route("/fai_estrazione1", methods=["POST"])
def fai_estrazione1():
    utente = session.get("utente")
    if not utente:
        return redirect("/")

    with open(ESTRATTI_FILE) as f:
        estratti = json.load(f)

    if utente in estratti:
        risultato = estratti[utente]
    else:
        candidati = [p for p in PERSONE if p != utente]
        disponibili = [x for x in candidati if x not in estratti.values()]
        risultato = random.choice(disponibili if disponibili else candidati)
        estratti[utente] = risultato
        with open(ESTRATTI_FILE, "w") as f:
            json.dump(estratti, f, indent=4)

    return render_template("risultato.html", utente=utente, estratto=risultato, tipo="Secret Santa")

# --- ESTRAZIONE 2: Giocattoli con esclusioni ---
GIOCATTOLI = [
    "orsetto di peluche",
    "trenino di legno",
    "cavallo a dondolo",
    "pacco regalo",
    "costruzioni",
    "un libro",
    "piatto di biscotti",
    "bicchiere di latte",
    "stella cometa"
]

@app.route("/fai_estrazione2", methods=["POST"])
def fai_estrazione2():
    utente = session.get("utente")
    if not utente:
        return redirect("/")

    with open(ESTRATTI_GIOCATTOLI_FILE) as f:
        estratti = json.load(f)

    if utente in estratti:
        risultato = estratti[utente]
    else:
        esclusi = ESCLUSIONI.get(utente, [])
        candidati = [g for g in GIOCATTOLI if g not in esclusi]
        disponibili = [g for g in candidati if g not in estratti.values()]
        pool = disponibili if disponibili else candidati
        risultato = random.choice(pool)
        estratti[utente] = risultato
        with open(ESTRATTI_GIOCATTOLI_FILE, "w") as f:
            json.dump(estratti, f, indent=4)

    return render_template("risultato.html", utente=utente, estratto=risultato, tipo="Giocattolo")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
