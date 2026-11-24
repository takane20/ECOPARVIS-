"""
Enregistrement des devis.

- Si les secrets SUPABASE_URL et SUPABASE_KEY sont configurés : base en ligne,
  durable (les devis ne disparaissent jamais).
- Sinon : fichier SQLite local (temporaire sur Streamlit Cloud : il peut être
  effacé à chaque redémarrage de l'application).
"""
import re
import secrets
import sqlite3
from datetime import timedelta
from collections import Counter, defaultdict

import requests
import streamlit as st

import config
from outils import cle_contact, maintenant, secret

DB_PATH = "ecoparvis.db"
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sans O/0/I/1 pour éviter les confusions

CHAMPS = ["numero_commande", "date", "date_expiration", "nom", "contact", "contact_cle",
          "type_pave", "surface", "zone", "couleur", "forme", "motif",
          "montant_total", "plastique_kg", "economie", "statut"]


# ─── Choix de la base ────────────────────────────────────────────────────────
def _supabase():
    url, cle = secret("SUPABASE_URL"), secret("SUPABASE_KEY")
    if url and cle:
        return url.rstrip("/"), cle
    return None


def backend():
    return "en ligne (Supabase)" if _supabase() else "local (temporaire)"


def _rest(methode, params=None, json=None, prefer=None):
    url, cle = _supabase()
    entetes = {"apikey": cle, "Authorization": f"Bearer {cle}", "Content-Type": "application/json"}
    if prefer:
        entetes["Prefer"] = prefer
    return requests.request(methode, f"{url}/rest/v1/devis", headers=entetes,
                            params=params, json=json, timeout=10)


# ─── SQLite (local / secours) ────────────────────────────────────────────────
def _sqlite():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@st.cache_resource(show_spinner=False)
def init_db():
    conn = _sqlite()
    conn.execute("""CREATE TABLE IF NOT EXISTS devis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_commande TEXT, date TEXT, date_expiration TEXT,
        nom TEXT, contact TEXT, contact_cle TEXT, type_pave TEXT, surface REAL,
        zone TEXT, couleur TEXT, forme TEXT, motif TEXT,
        montant_total REAL, plastique_kg REAL, economie REAL, statut TEXT)""")
    colonnes = [r["name"] for r in conn.execute("PRAGMA table_info(devis)")]
    if "contact_cle" not in colonnes:  # ancienne base : on ajoute la colonne
        conn.execute("ALTER TABLE devis ADD COLUMN contact_cle TEXT")
    try:
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_numero ON devis(numero_commande)")
    except sqlite3.DatabaseError:
        pass  # anciens doublons éventuels : on laisse l'ancienne base telle quelle
    conn.commit()
    conn.close()
    return True


def _sqlite_inserer(ligne):
    conn = _sqlite()
    try:
        conn.execute(f"INSERT INTO devis ({','.join(CHAMPS)}) VALUES ({','.join('?' * len(CHAMPS))})",
                     [ligne[c] for c in CHAMPS])
        conn.commit()
    finally:
        conn.close()


def _sqlite_lire(clause="", params=()):
    conn = _sqlite()
    try:
        return [dict(r) for r in conn.execute(f"SELECT * FROM devis {clause}", params)]
    finally:
        conn.close()


# ─── Fonctions utilisées par l'application ───────────────────────────────────
def generer_numero_commande():
    suite = "".join(secrets.choice(ALPHABET) for _ in range(6))
    return f"STE-{maintenant().strftime('%Y%m%d')}-{suite}"


def creer_devis(nom, contact, type_pave, surface, zone, couleur, forme, motif,
                montant_total, plastique_kg, economie):
    """Enregistre un devis et renvoie son numéro unique."""
    maintenant_ = maintenant()
    ligne = {
        "date": maintenant_.strftime("%d/%m/%Y %H:%M"),
        "date_expiration": (maintenant_ + timedelta(hours=config.VALIDITE_HEURES)).strftime("%d/%m/%Y %H:%M"),
        "nom": nom, "contact": contact, "contact_cle": cle_contact(contact),
        "type_pave": type_pave, "surface": surface, "zone": zone, "couleur": couleur,
        "forme": forme, "motif": motif, "montant_total": montant_total,
        "plastique_kg": plastique_kg, "economie": economie, "statut": "En attente",
    }
    for _ in range(8):
        ligne["numero_commande"] = generer_numero_commande()
        try:
            if _supabase():
                try:
                    r = _rest("POST", json=ligne, prefer="return=minimal")
                    if r.status_code == 409:
                        continue  # numéro déjà pris : on en tire un autre
                    r.raise_for_status()
                    return ligne["numero_commande"]
                except requests.RequestException:
                    pass  # base en ligne injoignable : on enregistre en local
            _sqlite_inserer(ligne)
            return ligne["numero_commande"]
        except sqlite3.IntegrityError:
            continue
    raise RuntimeError("Impossible de créer un numéro de commande unique.")


def _lire(params, clause, valeurs):
    if _supabase():
        try:
            r = _rest("GET", params=params)
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            pass
    return _sqlite_lire(clause, valeurs)


def get_devis_par_numero(numero):
    numero = re.sub(r"[^A-Z0-9\-]", "", (numero or "").upper())
    lignes = _lire({"select": "*", "numero_commande": f"eq.{numero}", "limit": 1},
                   "WHERE numero_commande=? LIMIT 1", (numero,))
    return lignes[0] if lignes else None


def get_devis_du_contact(cle, limite=10):
    return _lire({"select": "*", "contact_cle": f"eq.{cle}", "order": "id.desc", "limit": limite},
                 "WHERE contact_cle=? ORDER BY id DESC LIMIT ?", (cle, limite))


def get_all_devis(limite=2000):
    return _lire({"select": "*", "order": "id.desc", "limit": limite},
                 "ORDER BY id DESC LIMIT ?", (limite,))


def changer_statut(numero, statut):
    if statut not in config.STATUTS:
        return False
    if _supabase():
        try:
            r = _rest("PATCH", params={"numero_commande": f"eq.{numero}"},
                      json={"statut": statut}, prefer="return=minimal")
            r.raise_for_status()
            return True
        except requests.RequestException:
            pass
    conn = _sqlite()
    try:
        conn.execute("UPDATE devis SET statut=? WHERE numero_commande=?", (statut, numero))
        conn.commit()
        return True
    finally:
        conn.close()


def statistiques(devis):
    """Totaux et répartitions pour le tableau de bord admin."""
    s = {"nb": len(devis),
         "ca": sum(d.get("montant_total") or 0 for d in devis),
         "plastique": sum(d.get("plastique_kg") or 0 for d in devis),
         "economie": sum(d.get("economie") or 0 for d in devis),
         "par_zone": Counter(d.get("zone") for d in devis),
         "par_type": Counter(d.get("type_pave") for d in devis),
         "par_statut": Counter(d.get("statut") for d in devis)}
    par_jour = defaultdict(float)
    for d in devis:
        jour = (d.get("date") or "")[:10]  # jj/mm/aaaa
        if len(jour) == 10:
            par_jour[f"{jour[6:]}-{jour[3:5]}-{jour[:2]}"] += d.get("montant_total") or 0
    s["par_jour"] = dict(sorted(par_jour.items()))
    return s