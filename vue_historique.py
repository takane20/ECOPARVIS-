"""Page Historique : accessible seulement avec le n° de commande ET le numéro WhatsApp."""
from html import escape

import streamlit as st

import database
from outils import cle_contact, fcfa, numero_commande_valide

MAX_ESSAIS = 6


def afficher(T):
    st.markdown(f'<div class="section-title">📋 {T["historique_label"]}</div>', unsafe_allow_html=True)
    st.caption("🔒 Pour protéger vos données, indiquez le n° de commande figurant sur votre reçu "
               "et le numéro WhatsApp utilisé pour la commande.")

    essais = st.session_state.get("hist_essais", 0)
    if essais >= MAX_ESSAIS:
        st.error("🔒 Trop de tentatives. Rechargez la page dans quelques minutes pour réessayer.")
        return

    numero = st.text_input("🔖 N° de commande", placeholder="STE-20261124-K7M2QX").strip().upper()
    contact = st.text_input(T.get("entrez_numero", "Entrez votre numéro WhatsApp :"))
    if not (numero and contact):
        return

    if not numero_commande_valide(numero):
        st.error("Le n° de commande a le format STE-AAAAMMJJ-XXXXXX (voir votre reçu).")
        return

    cle = cle_contact(contact)
    devis = database.get_devis_par_numero(numero)
    if not devis or not cle or devis.get("contact_cle") != cle:
        st.session_state.hist_essais = essais + 1
        st.info(T.get("aucun_devis", "Aucun devis trouvé pour ce numéro."))
        return

    st.session_state.hist_essais = 0
    for d in database.get_devis_du_contact(cle):
        st.markdown(f"""
        <div class="historique-card">
            📅 <b>{escape(str(d['date']))}</b> | 🔖 N° {escape(str(d['numero_commande']))} | ⏱️ Expire : {escape(str(d.get('date_expiration') or 'N/A'))}<br>
            🧱 {escape(str(d['type_pave']))} | 📐 {d['surface']} m² | 📍 {escape(str(d['zone']))}<br>
            🎨 {escape(str(d['couleur']))} | 🔷 {escape(str(d['forme']))} | 🎭 {escape(str(d['motif']))}<br>
            🌿 {d['plastique_kg']:,.1f} kg recyclés | 💰 <b>{fcfa(d['montant_total'])}</b> | Statut : {escape(str(d.get('statut') or ''))}
        </div>""", unsafe_allow_html=True)