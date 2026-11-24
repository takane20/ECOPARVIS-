"""Page Calculateur & Devis : simulation, commande, reçu PDF, paiement, WhatsApp."""
import base64
import json
import math
import urllib.parse
from importlib.util import find_spec

import streamlit as st
import streamlit.components.v1 as components

import calcul
import config
import database
from notifications import envoyer_email_notification
from outils import contact_valide, fcfa
from recu_pdf import generer_recu_pdf
from styles import motif_icon_html

COULEUR_KEYS = ["rouge", "vert", "jaune", "gris", "violet", "bleu", "noir", "blanc", "orange"]
COULEUR_CSS = {"rouge": "#8B2500", "vert": "#2E7D32", "jaune": "#F9A825", "gris": "#424242",
               "violet": "#6A1B9A", "bleu": "#1565C0", "noir": "#212121", "blanc": "#F5F5F5",
               "orange": "#E65100", "naturel": "#5D4037", "melange": "#5D4037"}
CARTE_DISPONIBLE = all(find_spec(m) for m in ("folium", "streamlit_folium", "shapely"))


def _lien_whatsapp(texte):
    return f"https://wa.me/{config.WHATSAPP_LIEN}?text={urllib.parse.quote(texte)}"


def _drainage(T, type_pave, pluie):
    if type_pave == "drainant":
        return {"faible": T["drain_faible"], "moderee": T["drain_moderate"], "forte": T["drain_forte"]}[pluie]
    if type_pave == "autobloquant":
        return {"faible": T["auto_faible"], "moderee": T["auto_moderate"], "forte": T["auto_forte"]}[pluie]
    return T["haute_drain"]


def _surface_depuis_carte(T):
    """Dessin d'une zone sur une carte (seulement si folium est installé)."""
    from folium import Map
    from folium.plugins import Draw
    from shapely.geometry import Polygon
    from streamlit_folium import st_folium

    m = Map(location=[6.3654, 2.4183], zoom_start=13)
    Draw(export=False, draw_options={"polygon": True, "rectangle": True, "circle": False, "marker": False,
                                     "polyline": False, "circlemarker": False}).add_to(m)
    resultat = st_folium(m, height=300, width=None)
    if resultat and resultat.get("last_active_drawing"):
        coords = resultat["last_active_drawing"]["geometry"]["coordinates"][0]
        poly = Polygon([(c[0], c[1]) for c in coords])
        surface = poly.area * 111132.92 * 111132.92 * math.cos(math.radians(6.3654))
        st.success(f"Superficie : **{surface:,.1f} m²**")
        return max(surface, 1.0)
    return None


def _bouton_partage_pdf(pdf_bytes, nom_fichier, texte):
    """Ouvre le partage du téléphone avec le PDF (WhatsApp apparaît dans la liste)."""
    b64 = base64.b64encode(pdf_bytes).decode()
    texte_js = json.dumps(texte).replace("</", "<\\/")
    components.html(f"""
    <button id="b" style="width:100%;padding:14px;border:0;border-radius:10px;background:#25D366;color:white;
        font-size:16px;font-weight:700;font-family:sans-serif;cursor:pointer;">📲 Partager le PDF sur WhatsApp</button>
    <p id="m" style="font:13px sans-serif;color:#555;margin:8px 0 0;"></p>
    <script>
    const msg = document.getElementById('m');
    document.getElementById('b').onclick = async () => {{
      try {{
        const bin = atob("{b64}"); const arr = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
        const f = new File([arr], "{nom_fichier}", {{type: "application/pdf"}});
        if (navigator.canShare && navigator.canShare({{files: [f]}})) {{
          await navigator.share({{files: [f], text: {texte_js}}});
        }} else {{
          msg.innerText = "Partage direct indisponible ici : téléchargez le PDF puis joignez-le dans WhatsApp.";
        }}
      }} catch (e) {{
        msg.innerText = "Partage annulé ou indisponible : téléchargez le PDF puis joignez-le dans WhatsApp.";
      }}
    }};
    </script>""", height=120)


def _nouvelle_commande():
    st.session_state.commande = None
    st.session_state.etape = 1


def _confirmation(T, c):
    """Affichée après la commande, et conservée même si la page se recharge."""
    st.success(T.get("commande_confirmee", "✅ Commande confirmée !").replace("Commande", f"Commande {c['numero']}"))
    st.info(T.get("repondrons", "📬 Nous vous répondrons sous 24h."))
    st.download_button(T.get("telecharger_recu", "📄 Télécharger mon reçu PDF"), data=c["pdf"],
                       file_name=f"Recu_ST_Ecoparvis_{c['numero']}.pdf", mime="application/pdf")
    _bouton_partage_pdf(c["pdf"], f"Recu_ST_Ecoparvis_{c['numero']}.pdf",
                        f"Mon reçu ST-Ecoparvis N° {c['numero']} — {fcfa(c['montant_total'])}")

    st.markdown(f"### 💳 Procédez au paiement de **{fcfa(c['montant_total'])}**")
    for colonne, p in zip(st.columns(len(config.PAIEMENTS)), config.PAIEMENTS):
        with colonne:
            st.markdown(f"""<div style="background:{p['fond']};padding:16px;border-radius:12px;text-align:center;margin-bottom:8px;">
                <h4 style="color:{p['texte']};margin:0;">📱 {p['nom']}</h4>
                <p style="font-size:22px;font-weight:900;color:{p['texte']};margin:8px 0;">{p['numero']}</p>
                <p style="color:{p['texte']};font-size:12px;margin:0;">Montant exact : <b>{fcfa(c['montant_total'])}</b></p>
            </div>""", unsafe_allow_html=True)
    st.warning(T.get("apres_paiement", "⚠️ Après paiement, envoyez votre capture de reçu sur WhatsApp.")
               + " Le nom du titulaire affiché peut être différent de celui d'ST-Ecoparvis : "
                 "demandez-nous confirmation sur WhatsApp avant d'envoyer.")

    texte_wa = (
        f"♻️ *COMMANDE ST-ECOPARVIS — {c['numero']}*\n\n"
        f"👤 *Nom :* {c['nom']}\n📞 *Contact :* {c['contact']}\n📍 *Zone :* {c['zone']}\n"
        f"🏛️ *Type de projet :* {c['type_projet']}\n\n"
        f"🧱 *Détails :*\n- Type : {c['type_pave']}\n- Forme : {c['forme']}\n"
        f"- Motif : {c['motif']}\n- Couleur : {c['couleur']}\n- Surface : {c['surface']} m²\n"
        f"- 🌿 {c['plastique']:,.1f} kg recyclés !\n\n"
        f"💵 Pavés : {fcfa(c['montant_paves'])} | Transport : {fcfa(c['frais'])}\n"
        f"💰 *TOTAL : {fcfa(c['montant_total'])}*\n\n📎 Je joins mon reçu PDF."
    )
    st.markdown(f"[{T.get('envoyer_wa', '➡️ Envoyer aussi sur WhatsApp')}]({_lien_whatsapp(texte_wa)})")
    texte_partage = (f"J'ai reçu un devis ST-Ecoparvis pour {c['surface']} m² — Montant : "
                     f"{fcfa(c['montant_total'])}. N° commande : {c['numero']}")
    st.markdown(f"[📤 {T['partager']}](https://wa.me/?text={urllib.parse.quote(texte_partage)})")
    st.caption(f"🔖 Gardez votre n° de commande **{c['numero']}** : il sert à retrouver votre devis dans « Mon historique ».")
    st.button("🔄 Nouvelle commande", on_click=_nouvelle_commande)


def afficher(T):
    # ── Barre de progression
    etape_active = st.session_state.get("etape", 0)
    html = '<div class="progress-bar">'
    for i, e in enumerate(T["progression"]):
        cls, ico = ("done", "✅") if i < etape_active else (("active", "🔵") if i == etape_active else ("inactive", "⚪"))
        html += f'<div class="prog-step {cls}">{ico}<br>{e}</div>'
    st.markdown(html + "</div>", unsafe_allow_html=True)

    st.markdown(f'<div class="section-title">{T.get("simulateur_titre", "🧮 Simulateur de Commande")}</div>',
                unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    # ── Colonne de gauche : les choix du client
    with col1:
        st.subheader(T.get("parametres", "🧱 Paramètres"))

        st.markdown(f"#### {T['superficie_titre']}")
        surface = None
        if CARTE_DISPONIBLE:
            mode = st.radio(T["superficie_titre"], [T["manuelle"], T["carte"]], horizontal=True,
                            label_visibility="collapsed")
            if mode == T["carte"]:
                st.info(T["carte_info"])
                try:
                    surface = _surface_depuis_carte(T)
                except Exception:
                    surface = None
        if surface is None:
            surface = st.number_input(T["surface_label"], min_value=1.0, value=10.0, step=1.0)
        st.session_state.etape = max(st.session_state.etape, 1)

        types_pave = {"drainant": T["pave_drainant"], "autobloquant": T["pave_autobloquant"],
                      "haute_res": T["pave_haute_res"]}
        type_pave = st.selectbox(T["type_pave_label"], list(types_pave), format_func=lambda k: types_pave[k])

        projet_touristique = T.get("projet_touristique", "Site touristique / Patrimoine")
        type_projet = st.selectbox(T.get("type_projet_label", "🏛️ Type de projet"),
                                   [T.get("projet_residentiel", "Résidentiel / Particulier"),
                                    projet_touristique,
                                    T.get("projet_municipal", "Voirie municipale")])
        if type_projet == projet_touristique:
            st.markdown(f'<div class="color-notice">🏛️ {T.get("suggestion_touristique", "Pour un site touristique, nous recommandons un motif personnalisé inspiré du patrimoine local.")}</div>',
                        unsafe_allow_html=True)

        # Forme
        st.markdown(f"#### {T['forme_titre']}")
        formes = {"carre": T["carré"], "rectangle": T["rectangle"], "hexagone": T["hexagone"],
                  "hisz": T["hisz"], "perso": T["perso_forme"]}
        forme_choisie = st.selectbox(T["forme_titre"], list(formes), format_func=lambda k: formes[k],
                                     label_visibility="collapsed")
        supplement_forme = config.SUPPL_FORMES[forme_choisie]
        forme_label = formes[forme_choisie].split("(")[0].strip()

        # Motif
        st.markdown(f"#### {T['motif_titre']}")

        def _motif_label(k):
            cle_trad, prix = config.MOTIFS[k]
            return T[cle_trad] + (f" (+{prix} FCFA/m²)" if prix else "")

        option_motif = st.radio(T["motif_titre"], [T["motif_std"], T["motif_perso"]], label_visibility="collapsed")
        if option_motif == T["motif_std"]:
            motif_choisi = st.selectbox(T["motif_titre"], list(config.MOTIFS), format_func=_motif_label,
                                        label_visibility="collapsed")
            supplement_motif = config.MOTIFS[motif_choisi][1]
            motif_label = _motif_label(motif_choisi)
            st.markdown(f'<div style="display:flex;align-items:center;gap:8px;margin:-6px 0 8px 4px;">{motif_icon_html(motif_choisi)}<span style="font-size:12px;color:#777;">{motif_label}</span></div>',
                        unsafe_allow_html=True)
        else:
            motif_choisi = "perso"
            supplement_motif = config.SUPPL_MOTIF_PERSO
            motif_label = T["motif_perso"]
            st.markdown(f'<div class="color-notice">{T["motif_perso_info"]}</div>', unsafe_allow_html=True)
            photo_motif = st.file_uploader("📸 Téléchargez votre photo de motif (optionnel)",
                                           type=["jpg", "jpeg", "png", "webp"], key="photo_motif")
            if photo_motif:
                st.image(photo_motif, caption="Votre motif personnalisé", width=200)
                st.success("✅ Photo reçue ! Envoyez-la aussi sur WhatsApp avec votre commande.")

        # Couleur
        st.markdown(f"#### {T['couleur_titre']}")
        couleur_labels = {k: T[f"couleur_{k}"] for k in COULEUR_KEYS}
        option_couleur = st.radio(T["couleur_q"], [T["naturel"], T["couleur_unie"], T["melange"]])
        supplement_couleur, couleur_choisie, couleur_label, nb_couleurs = 0, "naturel", T["naturel"], 0
        if option_couleur == T["couleur_unie"]:
            supplement_couleur = config.SUPPL_COULEUR_UNIE
            couleur_choisie = st.selectbox(T["couleurs_dispo"], COULEUR_KEYS, format_func=lambda k: couleur_labels[k])
            couleur_label = couleur_labels[couleur_choisie]
            st.markdown(f'<div class="color-notice">⚠️ Supplément : <b>+{supplement_couleur} FCFA/m²</b></div>',
                        unsafe_allow_html=True)
        elif option_couleur == T["melange"]:
            nb_couleurs = st.slider(T["nb_couleurs"], 2, 5, 2)
            supplement_couleur = nb_couleurs * config.SUPPL_PAR_COULEUR_MELANGE
            choisies = st.multiselect(T["couleurs_dispo"], COULEUR_KEYS, format_func=lambda k: couleur_labels[k],
                                      max_selections=nb_couleurs)
            couleur_choisie = choisies[0] if choisies else "melange"
            couleur_label = " + ".join(couleur_labels[c] for c in choisies) if choisies else T["melange"]
            st.markdown(f'<div class="color-notice">🎨 {nb_couleurs} couleurs → <b>+{supplement_couleur} FCFA/m²</b></div>',
                        unsafe_allow_html=True)

        # Livraison et pluie
        zones = {"cotonou": T["cotonou"], "porto": T["porto"], "abomey": T["abomey"],
                 "parakou": T["parakou"], "retrait": T["retrait"]}
        zone = st.selectbox(T["zone_label"], list(zones), format_func=lambda k: zones[k])
        zone_label = zones[zone]
        pluies = {"faible": T["faible"], "moderee": T["moderee"], "forte": T["forte"]}
        pluie = st.select_slider(T["pluie_label"], options=list(pluies), format_func=lambda k: pluies[k])

    # ── Calcul (une seule fois, règles dans config.py)
    r = calcul.calculer(type_pave, surface, supplement_couleur, supplement_forme, supplement_motif, zone)
    montant_total, montant_paves = r["montant_total"], r["montant_paves"]
    frais, economie, total_plastique = r["frais_livraison"], r["economie"], r["total_plastique"]

    # ── Colonne de droite : le résultat
    with col2:
        st.subheader(f"📊 {T['specs_label']}")
        st.markdown(f"""
        <div class="eco-badge">
            🎉 Grâce à cette commande :<br>
            <span style="font-size:26px;color:#1B5E20;">{total_plastique:,.1f} kg</span><br>
            <span style="font-size:13px;">{T['plastique_label']}</span>
        </div>""", unsafe_allow_html=True)

        couleur_hex = COULEUR_CSS.get(couleur_choisie, "#5D4037")
        forme_css = "50%" if forme_choisie == "hexagone" else ("30% 70% 70% 30%" if forme_choisie == "hisz" else "8px")
        st.markdown(f"""
        <div class="apercu-pave">
            <p style="font-size:13px;color:#777;margin-bottom:10px;">{T['apercu_pave']}</p>
            <div style="width:100px;height:100px;background:{couleur_hex};border-radius:{forme_css};
                        margin:0 auto 10px;box-shadow:0 4px 12px rgba(0,0,0,0.3);
                        display:flex;align-items:center;justify-content:center;color:white;font-size:11px;">
                {motif_icon_html(motif_choisi, color="white", size=40)}
            </div>
            <p style="font-size:12px;color:#555;">{forme_label} · {couleur_label[:20]}</p>
        </div>""", unsafe_allow_html=True)

        def _sans_icone(titre):
            return titre.split(" ", 1)[-1] if " " in titre else titre

        st.markdown(f"""
        <div class="card">
            <p><b>{T['resistance_label']} :</b> {r['resistance']}</p>
            <p><b>{_sans_icone(T['forme_titre'])} :</b> {forme_label}</p>
            <p><b>{_sans_icone(T['motif_titre'])} :</b> {motif_label}</p>
            <p><b>{_sans_icone(T['couleur_titre'])} :</b> {couleur_label[:30]}</p>
            <p><b>{T['simulation_label']} ({pluies[pluie]}) :</b> {_drainage(T, type_pave, pluie)}</p>
            <p><b>{T['paves_estimes']} :</b> ~{int(r['nb_paves'])} unités</p>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"#### {T['suggestions_ia']}")
        suggestions = []
        if surface > 50:
            suggestions.append(T["sug_grande_surface"])
        if zone == "parakou":
            suggestions.append(T["sug_parakou"])
        if option_couleur == T["melange"] and nb_couleurs >= 4:
            suggestions.append(T["sug_melange"])
        if pluie == "forte":
            suggestions.append(T["sug_pluie"])
        for s in suggestions or [T["config_ok"]]:
            st.info(s)

    # ── Montants
    st.markdown("---")
    m1, m2 = st.columns(2)
    with m1:
        st.markdown(f'<div style="color:#ffffff;background:linear-gradient(135deg,#1B5E20,#2E7D32);padding:16px;border-radius:12px;margin-bottom:8px;"><span style="font-size:20px;font-weight:900;">{T["montant_label"]} : {fcfa(montant_total)}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color:#4CAF50;font-size:12px;">Pavés : {fcfa(montant_paves)} | Transport : {fcfa(frais)}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color:#4CAF50;font-weight:bold;margin-top:6px;">⏱️ {T["validite"]}</div>', unsafe_allow_html=True)
    with m2:
        if economie > 0:
            st.markdown(f'<div style="color:#ffffff;background:linear-gradient(135deg,#2E7D32,#4CAF50);padding:16px;border-radius:12px;"><span style="font-size:18px;font-weight:900;">{T["economie_label"]} : {fcfa(economie)} 🎉</span></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="color:#ffffff;background:linear-gradient(135deg,#2E7D32,#4CAF50);padding:16px;border-radius:12px;"><span style="font-size:16px;font-weight:700;">{T["economie_label"]} : Prix compétitif ✅</span></div>', unsafe_allow_html=True)
    st.session_state.etape = max(st.session_state.etape, 2)

    # ── Commande
    st.markdown(f'<div class="section-title">📩 {T["commander_label"]}</div>', unsafe_allow_html=True)
    if st.session_state.get("commande"):
        _confirmation(T, st.session_state.commande)
    else:
        c1, c2 = st.columns(2)
        nom_client = c1.text_input(T["nom_label"])
        contact = c2.text_input(T["contact_label"])
        if st.button(T["btn_wa"]):
            if not nom_client or not contact:
                st.error(T.get("nom_contact_requis", "Veuillez remplir votre nom et votre contact."))
            elif not contact_valide(contact):
                st.error("📞 Le numéro de contact ne semble pas valide — utilisez uniquement des chiffres (8 à 15), avec ou sans indicatif (+229...).")
            else:
                nom_client, contact = nom_client.strip(), contact.strip()
                numero = database.creer_devis(nom_client, contact, types_pave[type_pave], surface, zone_label,
                                              couleur_label, forme_label, motif_label, montant_total,
                                              total_plastique, max(economie, 0))
                envoyer_email_notification(nom_client, contact, types_pave[type_pave], surface,
                                           montant_total, zone_label, numero)
                pdf = generer_recu_pdf(numero, nom_client, contact, types_pave[type_pave], surface, zone_label,
                                       couleur_label, forme_label, motif_label, montant_total, total_plastique,
                                       max(economie, 0), frais, montant_paves).getvalue()
                st.session_state.commande = {
                    "numero": numero, "nom": nom_client, "contact": contact, "zone": zone_label,
                    "type_projet": type_projet, "type_pave": types_pave[type_pave], "forme": forme_label,
                    "motif": motif_label, "couleur": couleur_label, "surface": surface,
                    "plastique": total_plastique, "montant_paves": montant_paves, "frais": frais,
                    "montant_total": montant_total, "pdf": pdf}
                st.session_state.etape = 3
                st.rerun()

    # ── Devis sur mesure
    st.markdown("---")
    with st.expander(f"📋 {T['devis_complexe']}"):
        st.write(T["devis_complexe_info"])
        description = st.text_area(T.get("decrire_projet", "Décrivez votre projet :"),
                                   placeholder=T.get("placeholder_projet", "Ex: Route courbe 200m..."))
        if st.button(T["devis_complexe_btn"]):
            if description:
                msg = f"📋 *DEMANDE DEVIS SUR MESURE — ST-ECOPARVIS*\n\n📝 *Description du projet :*\n{description}"
                st.success(T.get("envoyer_demande", "✅ Demande prête !"))
st.markdown(f"[➡️ Envoyer la demande sur WhatsApp]({_lien_whatsapp(msg)})")
            else:
                st.error(T.get("desc_vide", "Veuillez décrire votre projet."))