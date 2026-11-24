"""Page Contact et questions fréquentes."""
import streamlit as st

import config


def afficher(T):
    st.markdown(f'<div class="section-title">📞 {T["contact_page"]}</div>', unsafe_allow_html=True)
    paiements = "".join(f"<p>📱 <b>{p['nom']} :</b> {p['numero']}</p>" for p in config.PAIEMENTS)
    st.markdown(f"""
    <div class="contact-card">
        <h4>♻️ ST-Ecoparvis — Bénin</h4>
        <p><i>"Chaque déchet est une brique d'avenir"</i></p><br>
        <p>💬 <b>WhatsApp :</b> {config.WHATSAPP_AFFICHAGE}</p>
        {paiements}
        <p>📧 <b>Email :</b> {config.EMAIL_CONTACT}</p>
        <p>📍 <b>Localisation :</b> {T.get('localisation', 'Bénin')}</p>
    </div>""", unsafe_allow_html=True)

    st.markdown(f'<div class="section-title">{T.get("faq_titre", "❓ Questions Fréquentes")}</div>',
                unsafe_allow_html=True)
    with st.expander(T.get("faq1_q", "⏱️ Combien de temps pour la livraison ?")):
        st.write(T.get("faq1_r", "Livraison sous 3 à 7 jours ouvrables."))
    with st.expander(T.get("faq2_q", "🌧️ Les pavés résistent-ils à la pluie et à la chaleur ?")):
        st.write(T.get("faq2_r", "Oui ! Nos pavés résistent aux fortes chaleurs."))
    with st.expander(T.get("faq3_q", "🧱 Puis-je voir un échantillon avant de commander ?")):
        st.write(T.get("faq3_r", f"Oui ! Contactez-nous sur WhatsApp au {config.WHATSAPP_AFFICHAGE}."))
    with st.expander(T.get("faq4_q", "💰 Les prix affichés sont-ils définitifs ?")):
        st.write(T.get("faq4_r", "Les prix sont des estimations. Le montant définitif est confirmé sous 24h."))