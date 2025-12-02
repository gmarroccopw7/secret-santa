from flask import Flask, render_template, redirect, session, url_for
import json, os, random

app = Flask(__name__)
app.secret_key = "supersecretkey123"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERSONE_FILE = os.path.join(BASE_DIR, "data", "persone.json")
#ESTRATTI_FILE = os.path.join(BASE_DIR, "estratti.json")
# Directory scrivibile su Railway/Render
ESTRATTI_FILE = "/tmp/estratti.json"
print(">>> PATH ESTRATTI:", ESTRATTI_FILE)
print(">>> ESISTE?:", os.path.exists(ESTRATTI_FILE))

# --- CARICAMENTO PERSONE ---
with open(PERSONE_FILE, encoding="utf-8") as f:
    PERSONE = json.load(f)["persone"]

# --- CREAZIONE AUTOMATICA DI estratti.json SE NON ESISTE ---
if not os.path.exists(ESTRATTI_FILE):
    print("⚠ estratti.json non trovato, lo creo...")
    with open(ESTRATTI_FILE, "w", encoding="utf-8") as f:
        json.dump({"estratti": []}, f, ensure_ascii=False, indent=4)

# --- CARICAMENTO ESTRATTI (ora il file esiste sicuramente) ---
with open(ESTRATTI_FILE, encoding="utf-8") as f:
    ESTRATTI = json.load(f)["estratti"]

# --- ICONE ASSOCIATE ---
ICONE = [
    "renna.png",
    "babbo_natale.png",
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
    app.run(debug=True)


