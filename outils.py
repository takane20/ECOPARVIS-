"""Petits outils partagés : images, numéros de téléphone, formats."""
import base64
import glob
import os
import re
from datetime import datetime, timedelta, timezone

import streamlit as st

BASE = os.path.dirname(os.path.abspath(__file__))
DOSSIERS_IMAGES = [BASE, os.path.join(BASE, "images")]
FUSEAU_BENIN = timezone(timedelta(hours=1))  # heure du Bénin (UTC+1, sans changement d'heure)


def maintenant():
    return datetime.now(FUSEAU_BENIN)


def secret(nom, defaut=None):
    """Lit un secret Streamlit sans planter s'il n'est pas configuré."""
    try:
        return st.secrets.get(nom, defaut)
    except Exception:
        return defaut


def fcfa(montant):
    return f"{montant:,.0f}".replace(",", " ") + " FCFA"


def liste_images(prefixe):
    """Trouve prefixe_1.jpg, prefixe_2.jpg… à la racine du dépôt ou dans images/."""
    trouvees = {}
    for dossier in DOSSIERS_IMAGES:
        for chemin in glob.glob(os.path.join(dossier, f"{prefixe}_*.jpg")):
            trouvees.setdefault(os.path.basename(chemin), chemin)

    def numero(nom):
        m = re.search(r"_(\d+)", nom)
        return int(m.group(1)) if m else 0

    return [trouvees[n] for n in sorted(trouvees, key=lambda n: (numero(n), n))]


@st.cache_data(show_spinner=False)
def image_b64(chemin):
    with open(chemin, "rb") as f:
        return base64.b64encode(f.read()).decode()


def cle_contact(contact):
    """Clé de comparaison d'un numéro : ses 8 derniers chiffres.
    Ainsi +229 01 92 62 41 33, 0192624133 et 92624133 sont reconnus comme le même numéro."""
    chiffres = re.sub(r"\D", "", contact or "")
    return chiffres[-8:]


def contact_valide(contact):
    propre = re.sub(r"[\s\-\.]", "", contact or "")
    return bool(re.fullmatch(r"\+?\d{8,15}", propre))


def numero_commande_valide(numero):
    return bool(re.fullmatch(r"STE-\d{8}-[A-Z0-9]{4,10}", numero or ""))