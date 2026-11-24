"""Page Galerie : toutes les images galerie_*.jpg du dépôt."""
import re

import streamlit as st

from outils import image_b64, liste_images

LEGENDES = {
    1: "Visuel d'inspiration — finition", 2: "Visuel d'inspiration — turquoise & or",
    3: "Visuel d'inspiration — hexagones bleus", 4: "Visuel d'inspiration — gamme colorée",
    5: "Visuel d'inspiration — texture", 6: "Référence — équipement de production",
    7: "Référence — équipement de production", 8: "Visuel d'inspiration — dalles",
    9: "Référence — équipement de production", 10: "Référence — équipement de production",
    11: "Visuel d'inspiration — motifs", 12: "Visuel d'inspiration — motifs posés",
}


def afficher(T):
    st.markdown(f'<div class="section-title">📸 {T["galerie_titre"]}</div>', unsafe_allow_html=True)
    st.write(T["galerie_sous"])
    st.caption("🔎 Projet en phase de prototype — les visuels ci-dessous illustrent la direction esthétique "
               "visée, ce ne sont pas encore des pavés fabriqués par Ecoparvis.")
    chemins = liste_images("galerie")
    if not chemins:
        st.info("Aucune image galerie_*.jpg trouvée dans le dépôt.")
        return
    colonnes = st.columns(3)
    for i, chemin in enumerate(chemins):
        m = re.search(r"galerie_(\d+)", chemin)
        legende = LEGENDES.get(int(m.group(1)) if m else 0, "Visuel d'inspiration")
        colonnes[i % 3].markdown(f"""
        <div style="margin-bottom:14px;">
            <img src="data:image/jpeg;base64,{image_b64(chemin)}"
                 style="width:100%;border-radius:10px;object-fit:cover;height:180px;
                        box-shadow:0 4px 12px rgba(0,0,0,0.1);" />
            <p style="text-align:center;font-size:12px;color:#555;margin-top:4px;">{legende}</p>
        </div>""", unsafe_allow_html=True)