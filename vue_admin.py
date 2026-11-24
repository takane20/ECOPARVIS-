"""Page Admin : statistiques, graphiques, suivi des commandes."""
import hmac
from html import escape

import pandas as pd
import streamlit as st

import config
import database
from outils import fcfa, secret


def _connexion(T):
    essais = st.session_state.get("admin_tentatives", 0)
    if essais >= 5:
        st.error("🔒 Trop de tentatives incorrectes. Recharge la page dans quelques minutes pour réessayer.")
        return
    mdp = st.text_input(T.get("mdp_label", "Mot de passe :"), type="password")
    if st.button("Se connecter"):
        # Mot de passe lu dans les Secrets de Streamlit Cloud : ADMIN_PASSWORD = "..."
        attendu = secret("ADMIN_PASSWORD")
        if attendu and hmac.compare_digest(mdp.encode(), str(attendu).encode()):
            st.session_state.admin_connecte = True
            st.session_state.admin_tentatives = 0
            st.rerun()
        else:
            st.session_state.admin_tentatives = essais + 1
            st.error(T.get("mdp_incorrect", "❌ Mot de passe incorrect."))


def _tableau_de_bord(T):
    st.success(T.get("connecte", "✅ Connecté"))
    if st.button(T.get("deconnecter", "Se déconnecter")):
        st.session_state.admin_connecte = False
        st.rerun()

    if "Supabase" not in database.backend():
        st.warning("⚠️ Stockage local temporaire : les devis peuvent disparaître au redémarrage de l'application. "
                   "Configurez Supabase (voir LISEZMOI.md) pour les conserver définitivement.")

    devis = database.get_all_devis()
    s = database.statistiques(devis)

    a, b = st.columns(2)
    a.metric(T.get("devis_label", "📋 Devis"), s["nb"])
    b.metric(T.get("ca_label", "💰 CA Estimé"), fcfa(s["ca"]))
    c, d = st.columns(2)
    c.metric(T.get("plastique_label2", "🌿 Plastique Recyclé"), f"{s['plastique']:,.1f} kg")
    d.metric(T.get("economie_label2", "💡 Économies Clients"), fcfa(s["economie"]))

    if devis:
        st.markdown("---")
        st.markdown("### 📈 Statistiques")
        g1, g2 = st.columns(2)
        with g1:
            st.caption("Chiffre d'affaires estimé par jour (FCFA)")
            st.line_chart(pd.Series(s["par_jour"], name="FCFA"))
        with g2:
            st.caption("Commandes par zone de livraison")
            st.bar_chart(pd.Series(dict(s["par_zone"]), name="Commandes"))
        g3, g4 = st.columns(2)
        with g3:
            st.caption("Commandes par type de pavé")
            st.bar_chart(pd.Series(dict(s["par_type"]), name="Commandes"))
        with g4:
            st.caption("Commandes par statut")
            st.bar_chart(pd.Series(dict(s["par_statut"]), name="Commandes"))

        st.markdown("---")
        st.markdown("### ✏️ Mettre à jour une commande")
        numeros = [d["numero_commande"] for d in devis]
        choix = st.selectbox("Commande", numeros)
        statut = st.selectbox("Nouveau statut", config.STATUTS)
        if st.button("Enregistrer le statut"):
            if database.changer_statut(choix, statut):
                st.success(f"✅ {choix} → {statut}")
                st.rerun()
            else:
                st.error("Statut non enregistré.")

        st.download_button("⬇️ Exporter toutes les commandes (CSV)",
                           data=pd.DataFrame(devis).to_csv(index=False).encode("utf-8-sig"),
                           file_name="commandes_ecoparvis.csv", mime="text/csv")

    st.markdown("---")
    st.markdown(T.get("toutes_commandes", "### 📋 Toutes les commandes"))
    if not devis:
        st.info(T.get("aucune_commande", "Aucune commande encore enregistrée."))
        return
    for d in devis[:200]:
        st.markdown(f"""
        <div class="historique-card">
            🔖 <b>{escape(str(d['numero_commande']))}</b> | 📅 {escape(str(d['date']))} | 👤 {escape(str(d['nom']))} | 📞 {escape(str(d['contact']))}<br>
            🧱 {escape(str(d['type_pave']))} | 📐 {d['surface']} m² | 📍 {escape(str(d['zone']))}<br>
            🎨 {escape(str(d['couleur']))} | 🔷 {escape(str(d['forme']))} | 🎭 {escape(str(d['motif']))}<br>
            🌿 {d['plastique_kg']:,.1f} kg | 💰 <b>{fcfa(d['montant_total'])}</b> | Statut : {escape(str(d.get('statut') or ''))}
        </div>""", unsafe_allow_html=True)


def afficher(T):
    st.markdown(f'<div class="section-title">{T.get("admin_titre", "🔐 Tableau de Bord Admin")}</div>',
                unsafe_allow_html=True)
    if not st.session_state.get("admin_connecte", False):
        _connexion(T)
    else:
        _tableau_de_bord(T)