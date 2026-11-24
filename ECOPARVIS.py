"""
ST-ECOPARVIS — Pavés écologiques · Bénin
Fichier principal : il assemble les pages. Les prix et contacts sont dans config.py.
"""
import hmac

import streamlit as st

import database
import styles
import vue_accueil
import vue_admin
import vue_calculateur
import vue_contact
import vue_galerie
import vue_historique
import vue_temoignages
from outils import secret
from traductions import TRADUCTIONS

st.set_page_config(page_title="ST-Ecoparvis", page_icon="♻️", layout="wide",
                   initial_sidebar_state="collapsed")

database.init_db()
styles.appliquer()

# ─── État de la session ──────────────────────────────────────────────────────
st.session_state.setdefault("etape", 0)
st.session_state.setdefault("admin_connecte", False)
st.session_state.setdefault("menu_idx", 0)
st.session_state.setdefault("commande", None)


def aller(i):
    """Utilisée par les boutons de l'accueil pour ouvrir une page."""
    st.session_state.menu_idx = i


LOGO_HTML = """
<div style="display:flex;justify-content:center;margin-bottom:8px;">
  <div class="logo-box">
    <span style="font-size:40px;">♻️</span>
    <div>
      <div class="logo-brand"><span>ST-</span>ECOPARVIS</div>
      <div class="logo-tag">Pavés Écologiques · Bénin</div>
    </div>
  </div>
</div>
"""

# ─── Zone du logo (remplie plus bas, une fois la langue connue) ──────────────
zone_logo = st.container()

# ─── Langue et menu (en haut de page, pratique sur téléphone) ────────────────
colonne_langue, colonne_menu = st.columns([1, 2])
langue = colonne_langue.selectbox("🌍 Langue / Language", list(TRADUCTIONS.keys()))
T = TRADUCTIONS[langue]
nav = T["nav"]  # 0 Accueil, 1 Calculateur, 2 Galerie, 3 Contact, 4 Historique, 5 Témoignages, 6 Admin

with zone_logo:
    st.markdown(LOGO_HTML, unsafe_allow_html=True)
    st.markdown(f'<div class="slogan">"{T["slogan"]}"</div>', unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;color:#777;font-size:13px;'>{T['sous_titre']}</p>", unsafe_allow_html=True)

menu = colonne_menu.selectbox("📍 Menu", list(range(6)), format_func=lambda i: nav[i], key="menu_idx")

# L'admin n'apparaît pas dans le menu : on y accède par l'adresse ?admin=CLE
cle_admin = secret("ADMIN_URL_KEY")
cle_url = st.query_params.get("admin")
if cle_admin and cle_url and hmac.compare_digest(str(cle_url).encode(), str(cle_admin).encode()):
    menu = 6

# ─── Pages ───────────────────────────────────────────────────────────────────
if menu == 0:
    vue_accueil.afficher(T, aller)
elif menu == 1:
    vue_calculateur.afficher(T)
elif menu == 2:
    vue_galerie.afficher(T)
elif menu == 3:
    vue_contact.afficher(T)
elif menu == 4:
    vue_historique.afficher(T)
elif menu == 5:
    vue_temoignages.afficher(T)
else:
    vue_admin.afficher(T)