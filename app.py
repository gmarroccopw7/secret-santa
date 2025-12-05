import os
import json
import random
import tempfile
import traceback
from flask import Flask, render_template, redirect, session, request
from db import init_db, db_get_estratti, db_set_estratto, db_reset_estrazioni


app = Flask(__name__)
init_db()
app.secret_key = "supersecretkey123"
app.debug = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

def calcola_assegnazione_figli(figli, associazioni, esclusioni):
    """
    figli: lista di tutti i figli (FIGLI)
    associazioni: dict famiglia -> [figli]
    esclusioni: dict figlio -> [altri figli da escludere (fratelli, ecc.)]
    """
    # Mappa figlio -> famiglia di appartenenza
    figlio_to_famiglia = {}
    for famiglia, lista_figli in associazioni.items():
        for f in lista_figli:
            figlio_to_famiglia[f] = famiglia

    # Precalcolo dei candidati validi per ogni figlio (senza considerare ancora i 'già usati')
    candidati_possibili = {}
    for f in figli:
        famiglia_f = figlio_to_famiglia[f]
        fratelli = set(esclusioni.get(f, []))
        possibili = []
        for target in figli:
            if target == f:
                continue  # non può estrarre sé stesso
            # niente figli della stessa famiglia
            if figlio_to_famiglia[target] == famiglia_f:
                continue
            # niente fratelli/sorelle
            if target in fratelli:
                continue
            possibili.append(target)
        candidati_possibili[f] = possibili

    assegnazione = {}
    usati = set()

    # Ordiniamo i figli per quelli con meno opzioni, così il backtracking è più efficiente
    figli_ordinati = sorted(figli, key=lambda x: len(candidati_possibili[x]))

    def backtrack(idx):
        if idx == len(figli_ordinati):
            return True  # tutti assegnati

        f = figli_ordinati[idx]
        for candidato in candidati_possibili[f]:
            if candidato in usati:
                continue
            assegnazione[f] = candidato
            usati.add(candidato)
            if backtrack(idx + 1):
                return True
            # backtrack
            usati.remove(candidato)
            del assegnazione[f]

        return False

    ok = backtrack(0)
    if not ok:
        # Qui puoi decidere cosa fare: raise, loggare, ecc.
        raise RuntimeError("Impossibile trovare una assegnazione valida per tutti i figli")

    return assegnazione

# --- Percorsi file ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERSONE_FILE = os.path.join(BASE_DIR, "data", "persone.json")
ASSOCIAZIONE_FILE = os.path.join(BASE_DIR, "data", "associazioni.json")
ESCLUSIONI_FILE = os.path.join(BASE_DIR, "data", "esclusioni.json")

# File dell'estrazione persistente
ESTRATTI_FILE = os.path.join(BASE_DIR, "data", "estratti.json")

print("ESTRATTI FILE:", ESTRATTI_FILE)


# --- Carica famiglie ---
with open(PERSONE_FILE, encoding="utf-8") as f:
    PERSONE = json.load(f)["persone"]

# --- Carica associazioni famiglia → figli ---
with open(ASSOCIAZIONE_FILE, encoding="utf-8") as f:
    ASSOCIAZIONI = json.load(f)

# --- Ricava lista globale FIGLI ---
FIGLI = []
for figli in ASSOCIAZIONI.values():
    FIGLI.extend(figli)

# --- Carica esclusioni (figlio → fratelli) ---
with open(ESCLUSIONI_FILE, encoding="utf-8") as f:
    ESCLUSIONI = json.load(f)

# -------------------------
# Icone e mappa
# -------------------------
ICONE = [
    "babbo_natale.png",
    "renna.png",
    "pupazzo_neve.png",
    "pan_zenzero.png",
    "albero_natale.png",
    "palla_natale.png",
    "pacco_regalo.png",
    "panettone.png",
    "stella.png"
]

# costruiamo una mappa icone per famiglie + figli
ICON_MAP = {}
tutti = PERSONE + FIGLI  # famiglie + figli

for i, nome in enumerate(tutti):
    ICON_MAP[nome] = ICONE[i % len(ICONE)]

# Ricrea il file estratti a ogni avvio (come nel tuo attuale comportamento)
# if os.path.exists(ESTRATTI_FILE):
#     os.remove(ESTRATTI_FILE)

# with open(ESTRATTI_FILE, "w", encoding="utf-8") as f:
#     json.dump({}, f)

#if not os.path.exists(ESTRATTI_FILE):
    #with open(ESTRATTI_FILE, "w", encoding="utf-8") as f:
    #    json.dump({}, f, indent=4)

    #db_set_estratto(estrattore, valore)


# --- Calcola mappa globale dei figli (figlio -> figlio_estratto) ---
MAPPA_FIGLI = calcola_assegnazione_figli(FIGLI, ASSOCIAZIONI, ESCLUSIONI)
print("Mappa figli calcolata:", MAPPA_FIGLI)

# --- ROUTE LOGIN ---
@app.route("/")
def login():
    return render_template("login.html", persone=PERSONE, icone=ICON_MAP)

@app.route("/login/<nome>")
def do_login(nome):
    if nome not in PERSONE:
        return "Famiglia non valida", 400
    session["utente"] = nome
    return redirect("/estrazione")

@app.route("/estrazione")
def estrazione():
    if "utente" not in session:
        return redirect("/")

    utente = session["utente"]

    # Carica estratti attuali
    try:
        #with open(ESTRATTI_FILE) as f:
            #estratti = json.load(f)
         estratti = db_get_estratti()
    except:
        estratti = {}

    return render_template(
        "estrazione.html",
        utente=utente,
        estratti=estratti,
        ASSOCIAZIONI=ASSOCIAZIONI,
        icone=ICON_MAP,
    )


@app.route("/fai_estrazione", methods=["POST"])
def fai_estrazione():
    if "utente" not in session:
        return redirect("/")

    estrattore = request.form.get("estrattore")

    # Carica estratti attuali
    try:
        #with open(ESTRATTI_FILE) as f:
            #estratti = json.load(f)
        estratti = db_get_estratti()
    except:
        estratti = {}

    # Blocca chi ha già estratto
    if estrattore in estratti:
        return redirect("/estrazione")

    # --- FAMIGLIA ---
    if estrattore in PERSONE:

        # Tutte le altre famiglie
        candidati = [f for f in PERSONE if f != estrattore]

        # Escludi famiglie già estratte
        gia_estratti = set(estratti.values())
        disponibili = [f for f in candidati if f not in gia_estratti]

        # fallback se necessario
        if not disponibili:
            disponibili = candidati

        #estratti[estrattore] = random.choice(disponibili)
        
        estratto_finale = random.choice(disponibili)
        db_set_estratt o(estrattore, estratto_finale)



    # --- FIGLIO ---
    elif estrattore in FIGLI:

        # Usa l’assegnazione globale calcolata all’avvio
        if estrattore not in MAPPA_FIGLI:
            return "Errore: nessuna assegnazione valida trovata", 500

        #estratti[estrattore] = MAPPA_FIGLI[estrattore]
        valore_figlio = MAPPA_FIGLI[estrattore]
        db_set_estratto(estrattore, valore_figlio)



    else:
        return "Errore: estrattore sconosciuto", 400

    # Salva gli estratti
    #with open(ESTRATTI_FILE, "w", encoding="utf-8") as f:
    #    json.dump(estratti, f, indent=4)
    
    db_set_estratto(estrattore, valore)

    
    return redirect("/estrazione")


@app.route("/admin_login")
def admin_login():
    return render_template("login.html", persone=PERSONE, show_admin_form=True, icone=ICON_MAP)

@app.route("/do_admin_login", methods=["POST"])
def do_admin_login():
    username = request.form.get("username")
    password = request.form.get("password")

    if username == "admin" and password == "estrazione":
        session["admin"] = True
        return redirect("/admin")
    else:
        return render_template(
            "login.html",
            persone=PERSONE,
            show_admin_form=True,
            error="Credenziali errate"
        )

@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/")

    # carica estrazioni aggiornate
    try:
        #with open(ESTRATTI_FILE) as f:
            #estratti = json.load(f)
        estratti = db_get_estratti()
    except:
        estratti = {}

    # costruiamo la struttura per la tabella
    tabella = []
    for famiglia in PERSONE:
        figli = ASSOCIAZIONI.get(famiglia, [])
        
        # estratto della famiglia
        estratto_famiglia = estratti.get(famiglia, None)

        # estratti figli
        estratti_figli = []
        for figlio in figli:
            if figlio in estratti:
                estratti_figli.append(f"{figlio} → {estratti[figlio]}")
            else:
                estratti_figli.append(f"{figlio} → ❌ Non ancora")

        tabella.append({
            "famiglia": famiglia,
            "estratto_famiglia": estratto_famiglia,
            "figli": figli,
            "stato_figli": estratti_figli
        })

    return render_template("admin.html", tabella=tabella)

@app.route("/admin_reset", methods=["POST"])
def admin_reset():
    if not session.get("admin"):
        return redirect("/")

    # reset estratti.json
    #with open(ESTRATTI_FILE, "w", encoding="utf-8") as f:
    #    json.dump({}, f)
    
    db_set_estratto(estrattore, valore)
    db_reset_estrazioni()

    
    return redirect("/admin")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

