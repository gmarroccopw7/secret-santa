import os
from flask import Flask, render_template, redirect, session, url_for
import json, random, tempfile, traceback

app = Flask(__name__)
app.secret_key = "supersecretkey123"

app.debug = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.before_request
def log_request_info():
    print(f"🔥 PATH RICHIESTO: {os.getcwd()}")
    print(f"🔥 LISTA TEMPLATES: {os.listdir(os.path.join(BASE_DIR, 'templates'))}")

# --- Percorsi file ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERSONE_FILE = os.path.join(BASE_DIR, "data", "persone.json")
ESTRATTI_FILE = os.path.join(tempfile.gettempdir(), "estratti.json")

# --- Logging globale per errori ---
@app.errorhandler(Exception)
def handle_exception(e):
    print("🔥 ERRORE INTERNO FLASK:")
    traceback.print_exc()
    return "Internal server error", 500

# --- Caricamento persone ---
with open(PERSONE_FILE, encoding="utf-8") as f:
    PERSONE = json.load(f)["persone"]

# --- ICONE ASSOCIATE ---
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

# --- Creazione automatica estratti.json se non esiste ---
if not os.path.exists(ESTRATTI_FILE):
    print(f"⚠ estratti.json non trovato, lo creo in {ESTRATTI_FILE}")
    with open(ESTRATTI_FILE, "w", encoding="utf-8") as f:
        json.dump({"estratti": []}, f, ensure_ascii=False, indent=4)

# --- Caricamento estratti ---
with open(ESTRATTI_FILE, encoding="utf-8") as f:
    ESTRATTI = json.load(f)["estratti"]

# --- Funzione per salvare estratti ---
def salva_estratti():
    with open(ESTRATTI_FILE, "w", encoding="utf-8") as f:
        json.dump({"estratti": ESTRATTI}, f, ensure_ascii=False, indent=4)

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

# --- ROUTE ESTRAZIONE ---
@app.route("/estrazione")
def estrazione():
    if "utente" not in session:
        return redirect("/")
    utente = session["utente"]
    try:
        with open(ESTRATTI_FILE) as f:
            estratti = json.load(f)
    except:
        estratti = {}
    gia_estratto = estratti.get(utente)
    return render_template("estrazione.html", utente=utente, gia_estratto=gia_estratto)

@app.route("/fai_estrazione", methods=["POST"])
def fai_estrazione():
    utente = session.get("utente")
    if not utente:
        return redirect("/")

    candidati = [p for p in PERSONE if p != utente]

    try:
        with open(ESTRATTI_FILE) as f:
            estratti = json.load(f)
    except:
        estratti = {}

    # evitare duplicati
    disponibili = [p for p in candidati if p not in estratti.values()]
    if not disponibili:
        risultato = random.choice(candidati)  # fallback se esauriti
    else:
        risultato = random.choice(disponibili)

    estratti[utente] = risultato
    with open(ESTRATTI_FILE, "w", encoding="utf-8") as f:
        json.dump(estratti, f, indent=4)

    return render_template("risultato.html", utente=utente, estratto=risultato)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)










