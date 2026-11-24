"""Page Témoignages."""
import streamlit as st


def afficher(T):
    st.markdown(f'<div class="section-title">{T.get("temoignages_titre", "⭐ Témoignages Clients")}</div>', unsafe_allow_html=True)
    st.caption("🔎 Exemples illustratifs — le projet est en phase de prototype et n'a pas encore de clients réels. Ces témoignages montrent le type de retour attendu, pas de vraies commandes livrées.")
    temoignages = [
        {"nom": "Kouassi A.", "ville": "Cotonou", "note": "⭐⭐⭐⭐⭐",
         "texte": "Des pavés d'une qualité exceptionnelle ! Ma cour est magnifique et plus aucune flaque d'eau après la pluie."},
        {"nom": "Fatou M.", "ville": "Porto-Novo", "note": "⭐⭐⭐⭐⭐",
         "texte": "Service rapide et professionnel. Les pavés colorés sont exactement comme je les voulais."},
        {"nom": "Rodrigue K.", "ville": "Abomey", "note": "⭐⭐⭐⭐⭐",
         "texte": "Résistance excellente même sous le trafic lourd. Et en plus on contribue à l'écologie !"},
        {"nom": "Marie-Claire D.", "ville": "Calavi", "note": "⭐⭐⭐⭐⭐",
         "texte": "L'application est très facile à utiliser. J'ai fait mon devis en 2 minutes !"},
        {"nom": "Ibrahim S.", "ville": "Parakou", "note": "⭐⭐⭐⭐⭐",
         "texte": "Le mélange de couleurs est superbe. Mes voisins me demandent tous où j'ai trouvé ces pavés !"},
    ]
    for t in temoignages:
        st.markdown(f"""
        <div class="temoignage-card">
            <p style="font-size:20px;margin:0;">{t['note']}</p>
            <p style="font-style:italic;color:#444;margin:8px 0;">"{t['texte']}"</p>
            <p style="color:#2E7D32;font-weight:bold;margin:0;">— {t['nom']}, {t['ville']}</p>
        </div>""", unsafe_allow_html=True)