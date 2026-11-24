"""Page d'accueil : carrousel, cartes de navigation, chiffres clés."""
import streamlit as st
import streamlit.components.v1 as components

from outils import image_b64, liste_images

LEGENDES = [
    "Visuel d'inspiration — finition",
    "Visuel d'inspiration — mélange turquoise & or",
    "Visuel d'inspiration — motif hexagonal",
    "Visuel d'inspiration — gamme colorée",
    "Visuel d'inspiration — texture haute performance",
    "Visuel d'inspiration — dalles",
]


def _carrousel():
    chemins = liste_images("carousel")
    if not chemins:
        st.warning("🖼️ Aucune image carousel_*.jpg trouvée dans le dépôt : le carrousel s'affichera dès qu'elles y seront ajoutées.")
        return
    n = len(chemins)
    duree = n * 4  # 4 secondes par image
    diapos = ""
    for i, chemin in enumerate(chemins):
        legende = LEGENDES[i] if i < len(LEGENDES) else "Visuel d'inspiration"
        diapos += f"""
        <div class="carousel-slide" style="animation-delay:{i * 4}s;">
            <img src="data:image/jpeg;base64,{image_b64(chemin)}" />
            <div class="carousel-caption">{legende}</div>
        </div>"""
    html = f"""
    <div class="carousel-wrap">
      <style>
        body {{ margin:0; }}
        .carousel-wrap {{ position:relative; width:100%; height:280px; border-radius:16px; overflow:hidden;
                          box-shadow:0 6px 24px rgba(0,0,0,0.2); font-family:sans-serif; }}
        .carousel-slide {{ position:absolute; inset:0; opacity:0; animation-name:carouselFade;
                           animation-duration:{duree}s; animation-iteration-count:infinite;
                           animation-timing-function:ease-in-out; }}
        .carousel-slide img {{ width:100%; height:100%; object-fit:cover; }}
        .carousel-caption {{ position:absolute; bottom:0; left:0; right:0; text-align:center;
                             background:rgba(0,0,0,0.45); color:white; font-size:13px; padding:8px; }}
        @keyframes carouselFade {{
          0% {{ opacity:0; }}
          3% {{ opacity:1; }}
          {round(100 / n - 3)}% {{ opacity:1; }}
          {round(100 / n)}% {{ opacity:0; }}
          100% {{ opacity:0; }}
        }}
      </style>
      {diapos}
    </div>"""
    components.html(html, height=300)
    st.caption("🔎 Visuels d'inspiration en défilement automatique — projet en phase de prototype.")


def afficher(T, aller):
    """aller(i) ouvre directement la page numéro i du menu."""
    _carrousel()

    st.markdown(f"<h3 style='text-align:center;color:#1B5E20;'>{T.get('que_faire', 'Que souhaitez-vous faire ?')}</h3>",
                unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""<div class="nav-card">
            <div class="nav-icon">🌱</div>
            <div class="nav-title">{T['decouvrir']}</div>
            <div class="nav-desc">Notre concept, nos valeurs, nos engagements</div>
        </div>""", unsafe_allow_html=True)
        if st.button("→", key="btn_decouvrir"):
            st.info(T.get("decouvrir_info", "ST-Ecoparvis transforme les déchets plastiques en pavés écologiques."))

    cartes = [
        (c2, "🧮", T["commander"], "Simulez, personnalisez et commandez", "Commander →", "btn_commander", 1),
        (c3, "📸", T["galerie_btn"], "Inspirez-vous de nos réalisations", "Voir galerie →", "btn_galerie", 2),
        (c4, "📞", T["contact_btn"], "On vous répond sous 24h", "Contacter →", "btn_contact", 3),
    ]
    for colonne, icone, titre, desc, bouton, cle, page in cartes:
        with colonne:
            st.markdown(f"""<div class="nav-card">
                <div class="nav-icon">{icone}</div>
                <div class="nav-title">{titre}</div>
                <div class="nav-desc">{desc}</div>
            </div>""", unsafe_allow_html=True)
            st.button(bouton, key=cle, on_click=aller, args=(page,))

    st.markdown("---")

    st.markdown(f"<h3 style='text-align:center;color:#1B5E20;'>{T['chiffres']}</h3>", unsafe_allow_html=True)
    chiffres = [
        ("12-18 kg", T.get("plastique_recycle", "♻️ Plastique recyclé par m²")),
        ("30-55 MPa", T.get("resistance_meca", "💪 Résistance mécanique")),
        ("5 zones", T.get("zones_livraison", "🚚 Livraison au Bénin")),
        ("5 langues", T.get("interface_multi", "🌍 Interface multilingue")),
    ]
    for colonne, (nombre, libelle) in zip(st.columns(4), chiffres):
        with colonne:
            st.markdown(f'<div class="stat-card"><div class="stat-number">{nombre}</div>'
                        f'<div class="stat-label">{libelle}</div></div>', unsafe_allow_html=True)