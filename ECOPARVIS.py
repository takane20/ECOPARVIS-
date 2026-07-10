import streamlit as st
import urllib.parse
import base64
import sqlite3
import os
import json
import smtplib
import time
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT
# Mise à jour

# ─── Configuration ───────────────────────────────────────────────────────────
st.set_page_config(page_title="ST-Ecoparvis", page_icon="♻️", layout="wide")

# ─── Base de données ─────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("ecoparvis.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS devis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_commande TEXT, date TEXT, date_expiration TEXT,
        nom TEXT, contact TEXT, type_pave TEXT, surface REAL,
        zone TEXT, couleur TEXT, forme TEXT, motif TEXT,
        montant_total REAL, plastique_kg REAL, economie REAL, statut TEXT
    )""")
    conn.commit()
    conn.close()

def generer_numero_commande():
    return "STE-" + datetime.now().strftime("%Y%m%d") + "-" + ''.join(random.choices(string.digits, k=4))

def sauvegarder_devis(numero, nom, contact, type_pave, surface, zone, couleur, forme, motif, montant_total, plastique_kg, economie):
    conn = sqlite3.connect("ecoparvis.db")
    c = conn.cursor()
    date_exp = (datetime.now() + timedelta(hours=48)).strftime("%d/%m/%Y %H:%M")
    c.execute("""INSERT INTO devis (numero_commande,date,date_expiration,nom,contact,type_pave,surface,zone,couleur,forme,motif,montant_total,plastique_kg,economie,statut)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
              (numero, datetime.now().strftime("%d/%m/%Y %H:%M"), date_exp,
               nom, contact, type_pave, surface, zone, couleur, forme, motif,
               montant_total, plastique_kg, economie, "En attente"))
    conn.commit()
    conn.close()

def get_historique(contact):
    conn = sqlite3.connect("ecoparvis.db")
    c = conn.cursor()
    c.execute("SELECT * FROM devis WHERE contact=? ORDER BY id DESC LIMIT 10", (contact,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_devis():
    conn = sqlite3.connect("ecoparvis.db")
    c = conn.cursor()
    c.execute("SELECT * FROM devis ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

init_db()

# ─── Génération PDF reçu ─────────────────────────────────────────────────────
def generer_recu_pdf(numero, nom, contact, type_pave, surface, zone, couleur, forme, motif, montant_total, plastique_kg, economie, frais_livraison, montant_paves):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    VERT = colors.HexColor("#1B5E20")
    VERT_CLAIR = colors.HexColor("#E8F5E9")
    story = []
    styles = getSampleStyleSheet()
    titre = ParagraphStyle("t", fontSize=20, fontName="Helvetica-Bold", textColor=VERT, alignment=TA_CENTER, spaceAfter=4)
    sous = ParagraphStyle("s", fontSize=11, textColor=colors.HexColor("#2E7D32"), alignment=TA_CENTER, spaceAfter=16)
    body = ParagraphStyle("b", fontSize=10, spaceAfter=6)

    story.append(Paragraph("♻ ST-ECOPARVIS", titre))
    story.append(Paragraph('"Chaque déchet est une brique d\'avenir"', sous))
    story.append(Paragraph(f"REÇU DE COMMANDE N° {numero}", ParagraphStyle("r", fontSize=14, fontName="Helvetica-Bold", textColor=VERT, alignment=TA_CENTER, spaceAfter=4)))
    story.append(Paragraph(f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')} | Valable 48h", ParagraphStyle("d", fontSize=9, alignment=TA_CENTER, textColor=colors.grey, spaceAfter=16)))
    story.append(Spacer(1, 0.3*cm))

    data = [
        ["DÉTAILS CLIENT", ""],
        ["Nom / Entreprise", nom],
        ["Contact WhatsApp", contact],
        ["Zone de livraison", zone],
        ["", ""],
        ["DÉTAILS COMMANDE", ""],
        ["Type de pavé", type_pave],
        ["Surface", f"{surface} m²"],
        ["Forme", forme],
        ["Motif", motif],
        ["Couleur", couleur],
        ["Pavés estimés", f"~{int(surface*20)} unités"],
        ["Plastique recyclé", f"{plastique_kg:,.1f} kg"],
        ["", ""],
        ["DÉTAIL FINANCIER", ""],
        ["Coût des pavés", f"{montant_paves:,.0f} FCFA"],
        ["Frais de livraison", f"{frais_livraison:,.0f} FCFA"],
        ["Économie vs béton classique", f"- {economie:,.0f} FCFA"],
        ["TOTAL À PAYER", f"{montant_total:,.0f} FCFA"],
    ]
    t = Table(data, colWidths=[7*cm, 9.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), VERT), ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("SPAN", (0,0), (-1,0)),
        ("BACKGROUND", (0,5), (-1,5), VERT), ("TEXTCOLOR", (0,5), (-1,5), colors.white),
        ("FONTNAME", (0,5), (-1,5), "Helvetica-Bold"), ("SPAN", (0,5), (-1,5)),
        ("BACKGROUND", (0,14), (-1,14), VERT), ("TEXTCOLOR", (0,14), (-1,14), colors.white),
        ("FONTNAME", (0,14), (-1,14), "Helvetica-Bold"), ("SPAN", (0,14), (-1,14)),
        ("BACKGROUND", (0,18), (-1,18), colors.HexColor("#FFD700")),
        ("FONTNAME", (0,18), (-1,18), "Helvetica-Bold"), ("FONTSIZE", (0,18), (-1,18), 12),
        ("FONTNAME", (0,1), (0,-1), "Helvetica-Bold"), ("TEXTCOLOR", (0,1), (0,-1), VERT),
        ("BACKGROUND", (0,1), (-1,-1), VERT_CLAIR),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#BDBDBD")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, VERT_CLAIR]),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    paiement_data = [
        ["MODE DE PAIEMENT", "NUMÉRO", "NOM DU COMPTE"],
        ["📱 MTN Mobile Money", "+229 69 71 06 23", "ST-Ecoparvis"],
        ["📱 Celtiis", "+229 92 62 41 33", "ST-Ecoparvis"],
    ]
    tp = Table(paiement_data, colWidths=[6*cm, 5.5*cm, 5*cm])
    tp.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), VERT), ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("BACKGROUND", (0,1), (-1,1), colors.HexColor("#FFF9C4")),
        ("BACKGROUND", (0,2), (-1,2), colors.HexColor("#E3F2FD")),
        ("FONTNAME", (0,1), (-1,-1), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#BDBDBD")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 8), ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(tp)
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("⚠️ Ce devis est valable 48h. Après paiement, envoyez votre reçu sur WhatsApp.", ParagraphStyle("n", fontSize=9, textColor=colors.grey, alignment=TA_CENTER)))
    story.append(Paragraph("📞 +229 69 71 06 23 | ✉️ eloisemable17@gmail.com", ParagraphStyle("c", fontSize=9, textColor=VERT, alignment=TA_CENTER)))
    doc.build(story)
    buffer.seek(0)
    return buffer

# ─── Email notification ───────────────────────────────────────────────────────
def envoyer_email_notification(nom, contact, type_pave, surface, montant_total, zone, numero):
    try:
        msg = MIMEMultipart()
        msg['From'] = 'eloisemable17@gmail.com'
        msg['To'] = 'eloisemable17@gmail.com'
        msg['Subject'] = f'🌱 Commande {numero} — {nom}'
        body = f'''Nouvelle commande ST-Ecoparvis !

N° Commande : {numero}
👤 Client : {nom}
📞 Contact : {contact}
🧱 Type : {type_pave}
📐 Surface : {surface} m²
📍 Zone : {zone}
💰 Montant : {montant_total:,.0f} FCFA

— ST-Ecoparvis'''
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('eloisemable17@gmail.com', 'VOTRE_MOT_DE_PASSE_APP')
        server.sendmail('eloisemable17@gmail.com', 'eloisemable17@gmail.com', msg.as_string())
        server.quit()
        return True
    except:
        return False

# ─── Traductions ─────────────────────────────────────────────────────────────
TRADUCTIONS = {
    "Français": {
        "titre": "ST-ECOPARVIS", "slogan": "Chaque déchet est une brique d'avenir",
        "sous_titre": "Pavés écologiques recyclés — zéro résidu, haute performance",
        "nav": ["🏠 Accueil", "🧮 Calculateur & Devis", "📸 Galerie", "📞 Contact", "📋 Mon Historique", "⭐ Témoignages", "🔐 Admin"],
        "que_faire": "Que souhaitez-vous faire ?",
        "nos_engagements": "nos_engagements, Notre concept, nos valeurs, nos engagements",
        "simulez": "simulez Simulez, personnalisez et commandez",
        "inspirez": "inspirez Inspirez-vous de nos réalisations",
        "repond": "repond, On vous répond sous 24h",
        "decouvrir_info": "**ST-Ecoparvis** transforme les déchets plastiques en pavés écologiques.\n\n✅ Zéro résidu · ✅ Haute résistance · ✅ Éco-drainant · ✅ Made in Bénin",
        "aller_calc": "👈 Allez dans **Calculateur & Devis** dans le menu de gauche.",
        "aller_gal": "👈 Allez dans **Galerie** dans le menu de gauche.",
        "aller_contact": "👈 Allez dans **Contact** dans le menu de gauche.",
        "plastique_recycle": "♻️ Plastique recyclé par m²",
        "resistance_meca": "💪 Résistance mécanique",
        "zones_livraison": "🚚 Livraison au Bénin",
        "interface_multi": "🌍 Interface multilingue",
        "desc_accueil": "Notre concept, valeurs et engagements",
        "simulateur_titre": "🧮 Simulateur de Commande",
        "parametres": "🧱 Paramètres",
        "confirmer_cmd": "📩 Confirmer ma commande",
        "telecharger_recu": "📄 Télécharger mon reçu PDF",
        "apres_paiement": "⚠️ Après paiement, envoyez votre capture de reçu sur WhatsApp pour confirmer.",
        "envoyer_wa": "➡️ Envoyer aussi sur WhatsApp",
        "decrire_projet": "Décrivez votre projet ici :",
        "placeholder_projet": "Ex: Route courbe de 200m, carrefour avec rayons différents...",
        "entrez_numero": "Entrez votre numéro WhatsApp :",
        "aucun_devis": "Aucun devis trouvé pour ce numéro.",
        "connecte": "✅ Connecté",
        "deconnecter": "Se déconnecter",
        "mdp_label": "Mot de passe :",
        "se_connecter": "Se connecter",
        "mdp_incorrect": "❌ Mot de passe incorrect.",
        "toutes_commandes": "### 📋 Toutes les commandes",
        "aucune_commande": "Aucune commande encore enregistrée.",
        "faq_titre": "❓ Questions Fréquentes",
        "faq1_q": "⏱️ Combien de temps pour la livraison ?",
        "faq1_r": "Livraison sous **3 à 7 jours ouvrables**. Cotonou/Calavi : 3 jours. Parakou : 5-7 jours.",
        "faq2_q": "🌧️ Les pavés résistent-ils à la pluie et à la chaleur ?",
        "faq2_r": "Oui ! Nos pavés intègrent un **traitement UV** et résistent aux fortes chaleurs.",
        "faq3_q": "🧱 Puis-je voir un échantillon avant de commander ?",
        "faq3_r": "Oui ! Contactez-nous sur WhatsApp au **+229 69 71 06 23**.",
        "faq4_q": "💰 Les prix affichés sont-ils définitifs ?",
        "faq4_r": "Les prix sont des **estimations**. Le montant définitif est confirmé sous 24h.",
        "commande_confirmee": "✅ Commande confirmée ! Voici votre reçu :",
        "repondrons": "📬 Nous vous répondrons sous **24h**. Merci de votre confiance !",
        "proceder_paiement": "### 💳 Procédez au paiement de",
        "localisation": "Bénin (adresse en cours de finalisation)",
        "temoignages_titre": "⭐ Témoignages Clients",
        "admin_titre": "🔐 Tableau de Bord Admin",
        "devis_label": "📋 Devis",
        "ca_label": "💰 CA Estimé",
        "plastique_label2": "🌿 Plastique Recyclé",
        "economie_label2": "💡 Économies Clients",
        "expire_label": "⏱️ Expire",
        "statut_label": "Statut",
        "placeholder_desc": "Décrivez votre projet complexe...",
        "envoyer_demande": "✅ Demande prête !",
        "desc_vide": "Veuillez décrire votre projet.",
        "nom_contact_requis": "Veuillez remplir votre nom et votre contact.",
        "superficie_calculee": "Superficie calculée",
        "module_indispo": "Module carte non disponible. Saisie manuelle activée.",
        "suggestions_titre": "#### 🤖 Suggestions intelligentes",
        "config_ok": "✅ Votre configuration est équilibrée et adaptée !",
        "sug_grande_surface": "💡 Grande surface : le Pavé Haute Résistance est recommandé.",
        "sug_parakou": "🚚 Livraison Parakou : commandez en grande quantité pour optimiser.",
        "sug_melange": "🎨 Mélange riche : pensez à la Spirale/Rosace comme motif.",
        "sug_pluie": "🌧️ Zone pluvieuse : le Pavé Drainant (Éco) est fortement recommandé.",
        "montant_detail": "Pavés | Transport",
        "pave_drainant": "Pavé Drainant (Éco)",
        "pave_autobloquant": "Pavé Autobloquant Classique",
        "pave_haute_res": "Pavé Haute Résistance",
        "drain_faible": "🟢 Absorption totale instantanée.",
        "drain_moderate": "🟢 Évacuation fluide.",
        "drain_forte": "🟡 Absorption maximale activée.",
        "auto_faible": "🟢 Légère infiltration.",
        "auto_moderate": "🟡 Ruissellement standard.",
        "auto_forte": "🔴 Risque de stagnation.",
        "haute_drain": "❌ Structure étanche haute densité.",
        "faible": "Faible", "moderee": "Modérée", "forte": "Forte (Saison des pluies)",
        "retrait": "Retrait sur place (Gratuit)",
        "cotonou": "Cotonou / Calavi", "porto": "Porto-Novo",
        "abomey": "Abomey / Bohicon", "parakou": "Parakou",
        "saisie_manuelle_label": "Saisie manuelle", "via_carte_label": "Via carte (OpenStreetMap)",
        "carré": "Carré ⬛", "rectangle": "Rectangle ▬",
        "hexagone": "Hexagone ⬡ (+300 FCFA/m²)", "hisz": "Forme H/I/S/Z (+500 FCFA/m²)",
        "perso_forme": "Forme personnalisée (+1000 FCFA/m²)",
        "lisse": "Lisse (sans motif)", "briques": "Briques classiques 🧱",
        "motif_detail": "Supplément couleur",
        "paves_estimes": "Pavés estimés",
        "devis_sur_mesure_desc": "Votre projet ne rentre pas dans nos options ? Décrivez-le nous !",
        "decouvrir": "Découvrir ST-Ecoparvis", "commander": "Passer Commande",
        "galerie_btn": "Nos Réalisations", "contact_btn": "Nous Contacter",
        "chiffres": "Nos Chiffres Clés",
        "vision": "Notre Vision", "pourquoi": "Pourquoi nous choisir ?",
        "surface_label": "Surface à couvrir (m²)", "type_pave_label": "Type de pavé",
        "zone_label": "Zone de livraison", "pluie_label": "Intensité de pluie simulée",
        "couleur_titre": "🎨 Personnalisation couleur",
        "couleur_q": "Choisissez votre option couleur",
        "naturel": "Naturel (sans supplément)",
        "couleur_unie": "Couleur unie (+500 FCFA/m²)",
        "melange": "Mélange de couleurs (prix variable)",
        "nb_couleurs": "Nombre de couleurs",
        "couleurs_dispo": "Choisissez vos couleurs",
        "forme_titre": "🔷 Forme du pavé",
        "motif_titre": "🎭 Motif sur le pavé",
        "motif_std": "Motif standard",
        "motif_perso": "Motif personnalisé",
        "motif_perso_info": "📸 Vous ne trouvez pas votre motif ? Envoyez une photo de votre motif sur WhatsApp (+229 69 71 06 23) après confirmation de commande. Supplément : +1000 FCFA/m²",
        "superficie_titre": "📐 Comment saisir votre superficie ?",
        "manuelle": "Saisie manuelle",
        "carte": "Via carte (OpenStreetMap)",
        "carte_info": "Dessinez votre terrain sur la carte pour calculer automatiquement.",
        "montant_label": "💰 Montant Total Estimé",
        "economie_label": "💡 Économie vs béton classique",
        "validite": "⏱️ Ce devis est valable 48h",
        "commander_label": "📩 Confirmer ma commande",
        "nom_label": "Votre Nom / Entreprise",
        "contact_label": "Numéro WhatsApp",
        "btn_wa": "✅ Confirmer et recevoir mon reçu",
        "partager": "📤 Partager ce devis",
        "historique_label": "📋 Mon Historique de Devis",
        "contact_page": "Contactez-nous",
        "plastique_label": "kg de déchets plastiques retirés !",
        "resistance_label": "Résistance mécanique",
        "simulation_label": "Simulation pluie",
        "specs_label": "⚙️ Spécifications & Simulation",
        "galerie_titre": "Galerie ST-Ecoparvis",
        "galerie_sous": "Aperçu de nos pavés et réalisations",
        "progression": ["Simulation", "Personnalisation", "Confirmation", "Paiement"],
        "devis_complexe": "📋 Projet complexe ? Demandez un devis sur mesure",
        "devis_complexe_info": "Votre projet ne rentre pas dans nos options standards ? Décrivez-le nous directement !",
        "devis_complexe_btn": "Envoyer ma demande de devis sur mesure",
        "apercu_pave": "👁️ Aperçu de votre pavé",
        "galerie_lien": "Voir la galerie pour plus d'inspiration",
        "suggestions_ia": "🤖 Suggestions intelligentes",
    },
    "English": {
        "titre": "ST-ECOPARVIS", "slogan": "Every waste is a brick for the future",
        "sous_titre": "Recycled ecological paving — zero waste, high performance",
        "nav": ["🏠 Home", "🧮 Calculator & Quote", "📸 Gallery", "📞 Contact", "📋 My History", "⭐ Testimonials", "🔐 Admin"],
        "que_faire": "What would you like to do?",
        "nos_engagements": "Our concept, values and commitments",
        "simulez": "Simulate, customize and order",
        "inspirez": "Get inspired by our achievements",
        "repond": "We reply within 24h",
        "decouvrir_info": "**ST-Ecoparvis** transforms plastic waste into high-performance ecological paving.\n\n✅ Zero waste · ✅ High resistance · ✅ Eco-draining · ✅ Made in Benin",
        "aller_calc": "👈 Go to **Calculator & Quote** in the left menu.",
        "aller_gal": "👈 Go to **Gallery** in the left menu.",
        "aller_contact": "👈 Go to **Contact** in the left menu.",
        "plastique_recycle": "♻️ Recycled plastic per m²",
        "resistance_meca": "💪 Mechanical resistance",
        "zones_livraison": "🚚 Delivery in Benin",
        "interface_multi": "🌍 Multilingual interface",
        "simulateur_titre": "🧮 Order Simulator",
        "parametres": "🧱 Parameters",
        "confirmer_cmd": "📩 Confirm my order",
        "telecharger_recu": "📄 Download my PDF receipt",
        "apres_paiement": "⚠️ After payment, send your receipt screenshot on WhatsApp to confirm.",
        "envoyer_wa": "➡️ Also send on WhatsApp",
        "decrire_projet": "Describe your project here:",
        "placeholder_projet": "Ex: Curved road 200m, complex architectural design...",
        "entrez_numero": "Enter your WhatsApp number:",
        "aucun_devis": "No quotes found for this number.",
        "connecte": "✅ Connected",
        "deconnecter": "Log out",
        "mdp_label": "Password:",
        "se_connecter": "Log in",
        "mdp_incorrect": "❌ Incorrect password.",
        "toutes_commandes": "### 📋 All orders",
        "aucune_commande": "No orders yet.",
        "faq_titre": "❓ Frequently Asked Questions",
        "faq1_q": "⏱️ How long does delivery take?",
        "faq1_r": "Delivery in **3 to 7 business days**. Cotonou/Calavi: 3 days. Parakou: 5-7 days.",
        "faq2_q": "🌧️ Do the paving stones resist rain and heat?",
        "faq2_r": "Yes! Our paving stones include **UV treatment** and resist high temperatures.",
        "faq3_q": "🧱 Can I see a sample before ordering?",
        "faq3_r": "Yes! Contact us on WhatsApp at **+229 69 71 06 23**.",
        "faq4_q": "💰 Are the displayed prices final?",
        "faq4_r": "Prices are **estimates**. The final amount is confirmed within 24h.",
        "commande_confirmee": "✅ Order confirmed! Here is your receipt:",
        "repondrons": "📬 We will reply within **24h**. Thank you for your trust!",
        "proceder_paiement": "### 💳 Proceed to payment of",
        "localisation": "Benin (address being finalized)",
        "temoignages_titre": "⭐ Customer Testimonials",
        "admin_titre": "🔐 Admin Dashboard",
        "devis_label": "📋 Quotes",
        "ca_label": "💰 Estimated Revenue",
        "plastique_label2": "🌿 Plastic Recycled",
        "economie_label2": "💡 Customer Savings",
        "expire_label": "⏱️ Expires",
        "statut_label": "Status",
        "envoyer_demande": "✅ Request ready!",
        "desc_vide": "Please describe your project.",
        "nom_contact_requis": "Please fill in your name and contact.",
        "superficie_calculee": "Calculated area",
        "module_indispo": "Map module unavailable. Manual entry activated.",
        "config_ok": "✅ Your configuration is well balanced!",
        "sug_grande_surface": "💡 Large area: High Resistance Paving recommended.",
        "sug_parakou": "🚚 Parakou delivery: order in large quantities to optimize transport.",
        "sug_melange": "🎨 Rich mix: consider the Spiral/Rosette pattern for a premium result.",
        "sug_pluie": "🌧️ Rainy area: Eco-Draining Paving strongly recommended.",
        "pave_drainant": "Eco-Draining Paving", "pave_autobloquant": "Classic Interlocking Paving",
        "pave_haute_res": "High Resistance Paving",
        "drain_faible": "🟢 Total instant absorption.",
        "drain_moderate": "🟢 Fluid evacuation.",
        "drain_forte": "🟡 Maximum absorption activated.",
        "auto_faible": "🟢 Slight infiltration through joints.",
        "auto_moderate": "🟡 Standard runoff.",
        "auto_forte": "🔴 Risk of stagnation.",
        "haute_drain": "❌ High-density waterproof structure.",
        "faible": "Light", "moderee": "Moderate", "forte": "Heavy (Rainy Season)",
        "retrait": "On-site pickup (Free)",
        "cotonou": "Cotonou / Calavi", "porto": "Porto-Novo",
        "abomey": "Abomey / Bohicon", "parakou": "Parakou",
        "devis_sur_mesure_desc": "Your project doesn't fit our standard options? Describe it to us!",
        "decouvrir": "Discover ST-Ecoparvis", "commander": "Place an Order",
        "galerie_btn": "Our Achievements", "contact_btn": "Contact Us",
        "chiffres": "Key Figures",
        "vision": "Our Vision", "pourquoi": "Why choose us?",
        "surface_label": "Area to cover (m²)", "type_pave_label": "Paving type",
        "zone_label": "Delivery zone", "pluie_label": "Simulated rain intensity",
        "couleur_titre": "🎨 Color customization",
        "couleur_q": "Choose your color option",
        "naturel": "Natural (no extra cost)",
        "couleur_unie": "Single color (+500 FCFA/m²)",
        "melange": "Color mix (variable price)",
        "nb_couleurs": "Number of colors",
        "couleurs_dispo": "Choose your colors",
        "forme_titre": "🔷 Paving shape",
        "motif_titre": "🎭 Pattern on paving",
        "motif_std": "Standard pattern",
        "motif_perso": "Custom pattern",
        "motif_perso_info": "📸 Can't find your pattern? Send a photo of your desired pattern on WhatsApp (+229 69 71 06 23) after order confirmation. Extra: +1000 FCFA/m²",
        "superficie_titre": "📐 How to enter your area?",
        "manuelle": "Manual entry",
        "carte": "Via map (OpenStreetMap)",
        "carte_info": "Draw your land on the map to auto-calculate.",
        "montant_label": "💰 Estimated Total Amount",
        "economie_label": "💡 Savings vs classic concrete",
        "validite": "⏱️ This quote is valid for 48h",
        "commander_label": "📩 Confirm my order",
        "nom_label": "Your Name / Company",
        "contact_label": "WhatsApp Number",
        "btn_wa": "✅ Confirm and receive my receipt",
        "partager": "📤 Share this quote",
        "historique_label": "📋 My Quote History",
        "contact_page": "Contact Us",
        "plastique_label": "kg of plastic waste removed!",
        "resistance_label": "Mechanical resistance",
        "simulation_label": "Rain simulation",
        "specs_label": "⚙️ Specifications & Simulation",
        "galerie_titre": "ST-Ecoparvis Gallery",
        "galerie_sous": "Preview of our paving stones and achievements",
        "progression": ["Simulation", "Customization", "Confirmation", "Payment"],
        "devis_complexe": "📋 Complex project? Request a custom quote",
        "devis_complexe_info": "Your project doesn't fit our standard options? Describe it to us directly!",
        "devis_complexe_btn": "Send my custom quote request",
        "apercu_pave": "👁️ Preview your paving",
        "galerie_lien": "View gallery for more inspiration",
        "suggestions_ia": "🤖 Smart suggestions",
    },
    "Español": {
        "titre": "ST-ECOPARVIS", "slogan": "Cada residuo es un ladrillo para el futuro",
        "sous_titre": "Adoquines ecológicos reciclados — cero residuos, alto rendimiento",
        "nav": ["🏠 Inicio", "🧮 Calculadora & Presupuesto", "📸 Galería", "📞 Contacto", "📋 Mi Historial", "⭐ Testimonios", "🔐 Admin"],
        "decouvrir": "Descubrir ST-Ecoparvis", "commander": "Realizar pedido",
        "galerie_btn": "Nuestras Realizaciones", "contact_btn": "Contáctenos",
        "chiffres": "Cifras Clave",
        "vision": "Nuestra Visión", "pourquoi": "¿Por qué elegirnos?",
        "surface_label": "Superficie a cubrir (m²)", "type_pave_label": "Tipo de adoquín",
        "zone_label": "Zona de entrega", "pluie_label": "Intensidad de lluvia simulada",
        "couleur_titre": "🎨 Personalización de color",
        "couleur_q": "Elija su opción de color",
        "naturel": "Natural (sin recargo)",
        "couleur_unie": "Color sólido (+500 FCFA/m²)",
        "melange": "Mezcla de colores (precio variable)",
        "nb_couleurs": "Número de colores",
        "couleurs_dispo": "Elija sus colores",
        "forme_titre": "🔷 Forma del adoquín",
        "motif_titre": "🎭 Motivo en el adoquín",
        "motif_std": "Motivo estándar",
        "motif_perso": "Motivo personalizado",
        "motif_perso_info": "📸 ¿No encuentra su motivo? Envíe una foto por WhatsApp (+229 69 71 06 23) tras confirmación. Extra: +1000 FCFA/m²",
        "superficie_titre": "📐 ¿Cómo ingresar su superficie?",
        "manuelle": "Entrada manual",
        "carte": "Via mapa (OpenStreetMap)",
        "carte_info": "Dibuje su terreno en el mapa para calcular automáticamente.",
        "montant_label": "💰 Monto Total Estimado",
        "economie_label": "💡 Ahorro vs hormigón clásico",
        "validite": "⏱️ Este presupuesto es válido por 48h",
        "commander_label": "📩 Confirmar mi pedido",
        "nom_label": "Su Nombre / Empresa",
        "contact_label": "Número WhatsApp",
        "btn_wa": "✅ Confirmar y recibir mi recibo",
        "partager": "📤 Compartir este presupuesto",
        "historique_label": "📋 Mi Historial",
        "contact_page": "Contáctenos",
        "plastique_label": "kg de residuos plásticos retirados!",
        "resistance_label": "Resistencia mecánica",
        "simulation_label": "Simulación de lluvia",
        "specs_label": "⚙️ Especificaciones & Simulación",
        "galerie_titre": "Galería ST-Ecoparvis",
        "galerie_sous": "Vista previa de nuestros adoquines",
        "progression": ["Simulación", "Personalización", "Confirmación", "Pago"],
        "devis_complexe": "📋 ¿Proyecto complejo? Solicite un presupuesto personalizado",
        "devis_complexe_info": "¿Su proyecto no cabe en nuestras opciones estándar? ¡Descríbanoslo directamente!",
        "devis_complexe_btn": "Enviar mi solicitud de presupuesto",
        "apercu_pave": "👁️ Vista previa de su adoquín",
        "galerie_lien": "Ver galería para más inspiración",
        "suggestions_ia": "🤖 Sugerencias inteligentes",
    },
    "Fon": {
        "titre": "ST-ECOPARVIS", "slogan": "Bɔbɔ bǐ nyí agbǎ ɖokpo",
        "sous_titre": "Mǐ wà pavé lɛ sín fánní jɔ, bo ma ɖó fánní ɖokpo",
        "nav": ["🏠 Hwɛ", "🧮 Tɛnmɛ & Azɔ̌", "📸 Mɛtɛnmɛ", "📞 Wá mǐ kpɔ́n", "📋 Azɔ̌ Taji", "⭐ Nǔ Yɔyɔ̌", "🔐 Admin"],
        "decouvrir": "Mɔ ST-Ecoparvis", "commander": "Sɛ̀n azɔ̌",
        "galerie_btn": "Azɔ̌ mǐtɔn", "contact_btn": "Wá mǐ kpɔ́n",
        "chiffres": "Nǔ taji lɛ",
        "vision": "Mǐɖé nǔ wà", "pourquoi": "Etɛ wu è na xɔ mǐ?",
        "surface_label": "Fí e a jló na kpé (m²)", "type_pave_label": "Pavé xɔ́ntɔn",
        "zone_label": "Fí e è na zán", "pluie_label": "Jɔhɔn sixu kpé",
        "couleur_titre": "🎨 Rɔ̌ xɔ́ntɔn",
        "couleur_q": "Xɔ rɔ̌ ɖé",
        "naturel": "Sín ayǐ (ɖě sín)",
        "couleur_unie": "Rɔ̌ ɖokpo (+500 FCFA/m²)",
        "melange": "Rɔ̌ lɛ bǐ (nǔɖé)",
        "nb_couleurs": "Rɔ̌ mɛ",
        "couleurs_dispo": "Xɔ rɔ̌ lɛ",
        "forme_titre": "🔷 Pavé ta",
        "motif_titre": "🎭 Motif ɖò pavé",
        "motif_std": "Motif ɖé",
        "motif_perso": "Motif towe",
        "motif_perso_info": "📸 A mɔ motif e a jló ǎ? Sɛ̀n foto towe WhatsApp (+229 69 71 06 23). Nǔɖé: +1000 FCFA/m²",
        "superficie_titre": "📐 Alǒ tɛ nu a na zán?",
        "manuelle": "A wlan bǐ",
        "carte": "Carte jí",
        "carte_info": "Wlan fí towe ɖò carte jí.",
        "montant_label": "💰 Gbɛ̌ bǐ mlɛ́mlɛ́",
        "economie_label": "💡 A hɛn lɛ vs béton",
        "validite": "⏱️ Azɔ̌ elɔ nyí 48h",
        "commander_label": "📩 Sɛ̀n azɔ̌",
        "nom_label": "Nyǐkɔ towe",
        "contact_label": "WhatsApp",
        "btn_wa": "✅ Sɛ̀n bo hɛn reçu",
        "partager": "📤 Sɛ̀n azɔ̌ elɔ",
        "historique_label": "📋 Azɔ̌ taji towe",
        "contact_page": "Wá mǐ kpɔ́n",
        "plastique_label": "kg fánní e è sɔ́!",
        "resistance_label": "Pavé gbɔ̌n",
        "simulation_label": "Jɔhɔn tɛnmɛ",
        "specs_label": "⚙️ Nǔ & Tɛnmɛ",
        "galerie_titre": "Mɛtɛnmɛ ST-Ecoparvis",
        "galerie_sous": "Pavé lɛ kpɔ́n",
        "progression": ["Tɛnmɛ", "Xɔ́ntɔn", "Sɛ̀n", "Yí gbɛ̌"],
        "devis_complexe": "📋 Azɔ̌ gègě? Byɔ devis",
        "devis_complexe_info": "Azɔ̌ towe lɛ́ kpò ǎ? Ɖó nǔ e a jló lɛ xlɛ́ mǐ!",
        "devis_complexe_btn": "Sɛ̀n byɔ devis",
        "apercu_pave": "👁️ Kpɔ́n pavé towe",
        "galerie_lien": "Kpɔ́n mɛtɛnmɛ",
        "suggestions_ia": "🤖 Nǔ tɛnmɛ",
    },
    "Yoruba": {
        "titre": "ST-ECOPARVIS", "slogan": "Ẹ̀tàn kọọkan jẹ́ gẹ̀lẹ̀ kan fún ọjọ́ iwájú",
        "sous_titre": "Pavé tí a tún ṣe — kò sí ègbin, agbára gíga",
        "nav": ["🏠 Ilé", "🧮 Iṣirò & Iye Owó", "📸 Àwòrán", "📞 Kan Sí Wa", "📋 Ìtàn Mi", "⭐ Ẹ̀rí Àwọn", "🔐 Admin"],
        "decouvrir": "Ṣàwárí ST-Ecoparvis", "commander": "Fí àṣẹ",
        "galerie_btn": "Iṣẹ́ Wa", "contact_btn": "Kan Sí Wa",
        "chiffres": "Àwọn Nọ́mbà Wa",
        "vision": "Ìríran Wa", "pourquoi": "Kí ló dára nípa wa?",
        "surface_label": "Àgbègbè (m²)", "type_pave_label": "Irú pavé",
        "zone_label": "Àgbègbè ifijiṣẹ́", "pluie_label": "Ìpele ìjì líle",
        "couleur_titre": "🎨 Àṣàyàn àwọ̀",
        "couleur_q": "Yan àwọ̀ rẹ",
        "naturel": "Àdánidá (kò sí àfikún)",
        "couleur_unie": "Àwọ̀ kan (+500 FCFA/m²)",
        "melange": "Àpapọ̀ àwọ̀ (iye owó yàtọ̀)",
        "nb_couleurs": "Iye àwọ̀",
        "couleurs_dispo": "Yan àwọ̀ rẹ",
        "forme_titre": "🔷 Ìrísí pavé",
        "motif_titre": "🎭 Àpẹẹrẹ lórí pavé",
        "motif_std": "Àpẹẹrẹ àdánidá",
        "motif_perso": "Àpẹẹrẹ tìrẹ",
        "motif_perso_info": "📸 Kò rí àpẹẹrẹ rẹ? Firanṣẹ́ fọ́tò rẹ WhatsApp (+229 69 71 06 23). Àfikún: +1000 FCFA/m²",
        "superficie_titre": "📐 Báwo ni o ṣe fẹ́ tẹ?",
        "manuelle": "Tẹ pẹ̀lú ọwọ́",
        "carte": "Nípasẹ̀ maapu",
        "carte_info": "Ya àgbègbè rẹ lórí maapu.",
        "montant_label": "💰 Apapọ̀ Iye Owó",
        "economie_label": "💡 Àpamọ́ vs bẹ́tọ̀n àdánidá",
        "validite": "⏱️ Ìdámọ̀ owó yìí wà fún 48h",
        "commander_label": "📩 Jẹ́rìí àṣẹ mi",
        "nom_label": "Orúkọ rẹ / Ilé-iṣẹ́",
        "contact_label": "Nọ́mbà WhatsApp",
        "btn_wa": "✅ Jẹ́rìí àti gba rẹ́sìtì mi",
        "partager": "📤 Pín ìdámọ̀ owó yìí",
        "historique_label": "📋 Ìtàn Àṣẹ Mi",
        "contact_page": "Kan Sí Wa",
        "plastique_label": "kg ègbin pilasitiki tí a yọ!",
        "resistance_label": "Agbára pavé",
        "simulation_label": "Ìjì líle",
        "specs_label": "⚙️ Àlàyé & Ìfọ̀rọ̀",
        "galerie_titre": "Àwòrán ST-Ecoparvis",
        "galerie_sous": "Wo àwọn pavé àti iṣẹ́ wa",
        "progression": ["Iṣirò", "Ìṣàpẹẹrẹ", "Jẹ́rìí", "Ìsanwó"],
        "devis_complexe": "📋 Iṣẹ́ tó ṣòro? Béèrè ìdámọ̀ owó",
        "devis_complexe_info": "Iṣẹ́ rẹ kò bá àwọn aṣàyàn wa mu? Ṣàpèjúwe rẹ̀ fún wa!",
        "devis_complexe_btn": "Firanṣẹ́ ìbéèrè mi",
        "apercu_pave": "👁️ Wo pavé rẹ",
        "galerie_lien": "Wo àwòrán fún àwokòtò",
        "suggestions_ia": "🤖 Àwọn ìmọ̀ràn ọlọ́gbọ́n",
    }
}

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;900&display=swap');
* { font-family: 'Poppins', sans-serif; }
/* Mode sombre - forcer couleurs texte */
.stMarkdown p { color: inherit !important; }
h1, h2, h3, h4, h5, h6 { color: #1B5E20 !important; }
.stApp { color: #1a1a1a !important; }
[data-theme="dark"] .card, [data-theme="dark"] .contact-card,
[data-theme="dark"] .historique-card, [data-theme="dark"] .temoignage-card,
[data-theme="dark"] .apercu-pave, [data-theme="dark"] .paiement-box { 
    color: #1a1a1a !important; background-color: #f1f8e9 !important; 
}
.contact-card p, .contact-card h4 { color: #1B5E20 !important; }
.card p, .card h4 { color: #1a1a1a !important; }
.historique-card { color: #1a1a1a !important; }
.temoignage-card p { color: #333 !important; }
.eco-badge { color: #1B5E20 !important; }
.nav-title { color: #1B5E20 !important; }
.nav-desc { color: #555 !important; }
.stat-label { color: #C8E6C9 !important; }
.main-title { font-size: 42px; font-weight: 900; color: #1B5E20; text-align: center; margin-bottom: 4px; letter-spacing: 2px; }
.slogan { font-size: 16px; color: #4CAF50; text-align: center; font-style: italic; margin-bottom: 8px; }
.section-title { font-size: 24px; font-weight: 700; color: #2E7D32; margin-top: 25px; margin-bottom: 15px; border-bottom: 3px solid #4CAF50; padding-bottom: 8px; }
.card { background: linear-gradient(135deg, #F1F8E9, #E8F5E9); padding: 20px; border-radius: 14px; border-left: 5px solid #4CAF50; margin-bottom: 15px; box-shadow: 0 2px 12px rgba(76,175,80,0.1); }
.eco-badge { background: linear-gradient(135deg, #E8F5E9, #C8E6C9); color: #1B5E20; padding: 18px; border-radius: 12px; border: 2px dashed #4CAF50; text-align: center; font-size: 18px; font-weight: bold; margin-bottom: 20px; }
.nav-card { background: white; padding: 28px 20px; border-radius: 16px; text-align: center; cursor: pointer; border: 2px solid #E8F5E9; transition: all 0.3s; box-shadow: 0 4px 16px rgba(0,0,0,0.08); margin-bottom: 10px; }
.nav-card:hover { border-color: #4CAF50; box-shadow: 0 8px 24px rgba(76,175,80,0.2); transform: translateY(-2px); }
.nav-icon { font-size: 48px; margin-bottom: 10px; }
.nav-title { font-size: 16px; font-weight: 700; color: #1B5E20; margin-bottom: 6px; }
.nav-desc { font-size: 12px; color: #777; }
.stat-card { background: linear-gradient(135deg, #1B5E20, #2E7D32); color: white; padding: 20px; border-radius: 14px; text-align: center; }
.stat-number { font-size: 32px; font-weight: 900; color: #A5D6A7; }
.stat-label { font-size: 12px; color: #C8E6C9; margin-top: 4px; }
.progress-bar { display: flex; justify-content: space-between; margin-bottom: 20px; padding: 12px; background: #F1F8E9; border-radius: 10px; }
.prog-step { text-align: center; flex: 1; font-size: 11px; font-weight: 600; }
.prog-step.active { color: #1B5E20; }
.prog-step.done { color: #4CAF50; }
.prog-step.inactive { color: #BDBDBD; }
.logo-box { background: linear-gradient(135deg, #1B5E20, #2E7D32); padding: 18px 36px; border-radius: 16px; display: inline-flex; align-items: center; gap: 14px; box-shadow: 0 8px 32px rgba(27,94,32,0.35); }
.logo-brand { font-size: 28px; font-weight: 900; color: #fff; letter-spacing: 2px; }
.logo-brand span { color: #A5D6A7; }
.logo-tag { font-size: 10px; color: #C8E6C9; letter-spacing: 3px; text-transform: uppercase; }
.contact-card { background: linear-gradient(135deg, #F1F8E9, #E8F5E9); padding: 24px; border-radius: 14px; border-left: 5px solid #4CAF50; margin-bottom: 15px; }
.historique-card { background: #F9FBE7; border-left: 4px solid #8BC34A; padding: 12px 16px; border-radius: 10px; margin-bottom: 10px; }
.temoignage-card { background: white; padding: 20px; border-radius: 14px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); border-top: 4px solid #4CAF50; margin-bottom: 15px; }
.apercu-pave { background: #F5F5F5; padding: 20px; border-radius: 14px; text-align: center; border: 2px dashed #4CAF50; margin: 15px 0; }
.color-notice { background: #FFF8E1; padding: 12px; border-radius: 10px; border-left: 4px solid #FFC107; margin: 10px 0; font-size: 14px; }
.paiement-box { background: linear-gradient(135deg, #E8F5E9, #F1F8E9); padding: 20px; border-radius: 14px; border: 2px solid #4CAF50; margin: 15px 0; }
.stButton>button { background: linear-gradient(135deg, #2E7D32, #1B5E20); color: white; border-radius: 10px; width: 100%; font-weight: 700; height: 48px; border: none; box-shadow: 0 4px 12px rgba(27,94,32,0.3); }
.stButton>button:hover { background: linear-gradient(135deg, #1B5E20, #0a3d0a); transform: translateY(-1px); }
</style>
""", unsafe_allow_html=True)

# ─── Langue & Session State ───────────────────────────────────────────────────
langue = st.sidebar.selectbox("🌍 Langue / Language", list(TRADUCTIONS.keys()))
T = TRADUCTIONS[langue]

if "page" not in st.session_state:
    st.session_state.page = T["nav"][0]
if "etape" not in st.session_state:
    st.session_state.etape = 0
if "carousel_idx" not in st.session_state:
    st.session_state.carousel_idx = 0
if "admin_connecte" not in st.session_state:
    st.session_state.admin_connecte = False

# ─── Logo ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;justify-content:center;margin-bottom:8px;">
  <div class="logo-box">
    <span style="font-size:40px;">♻️</span>
    <div>
      <div class="logo-brand"><span>ST-</span>ECOPARVIS</div>
      <div class="logo-tag">Pavés Écologiques · Bénin</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
st.markdown(f'<div class="slogan">"{T["slogan"]}"</div>', unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center;color:#777;font-size:13px;'>{T['sous_titre']}</p>", unsafe_allow_html=True)

# ─── Navigation ───────────────────────────────────────────────────────────────
menu = st.sidebar.selectbox("Navigation", T["nav"])

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — ACCUEIL REDESIGNÉ
# ══════════════════════════════════════════════════════════════════════════════
if menu == T["nav"][0]:
    # Carousel
    images_carousel = [
        "/mnt/user-data/uploads/1000427947.jpg",
        "/mnt/user-data/uploads/1000427961.jpg",
        "/mnt/user-data/uploads/1000427945.jpg",
        "/mnt/user-data/uploads/1000428515.jpg",
        "/mnt/user-data/uploads/1000427951.jpg",
        "/mnt/user-data/uploads/1000427983.jpg",
    ]
    captions = ["Pavé Écologique ST-Ecoparvis", "Mélange Premium Turquoise & Or",
                "Pavés Hexagonaux", "Gamme Colorée", "Haute Performance", "Dalles Recyclées"]

    img_path = images_carousel[st.session_state.carousel_idx]
    try:
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        st.markdown(f"""
        <div style="position:relative;margin-bottom:10px;">
            <img src="data:image/jpeg;base64,{b64}"
                 style="width:100%;max-height:360px;object-fit:cover;border-radius:16px;
                        box-shadow:0 6px 24px rgba(0,0,0,0.2);" />
            <div style="position:absolute;bottom:12px;left:0;right:0;text-align:center;
                        background:rgba(0,0,0,0.4);padding:6px;border-radius:0 0 16px 16px;
                        color:white;font-size:13px;">
                {captions[st.session_state.carousel_idx]}
            </div>
        </div>""", unsafe_allow_html=True)
    except:
        pass

    col_prev, col_dots, col_next = st.columns([1, 4, 1])
    with col_prev:
        if st.button("◀"):
            st.session_state.carousel_idx = (st.session_state.carousel_idx - 1) % len(images_carousel)
            st.rerun()
    with col_dots:
        dots = " ".join(["🟢" if i == st.session_state.carousel_idx else "⚪" for i in range(len(images_carousel))])
        st.markdown(f"<div style='text-align:center;'>{dots}</div>", unsafe_allow_html=True)
    with col_next:
        if st.button("▶"):
            st.session_state.carousel_idx = (st.session_state.carousel_idx + 1) % len(images_carousel)
            st.rerun()

    st.markdown("---")

    # 4 cartes de navigation
    st.markdown(f"<h3 style='text-align:center;color:#1B5E20;'>{T.get("que_faire", "Que souhaitez-vous faire ?")}</h3>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""<div class="nav-card">
            <div class="nav-icon">🌱</div>
            <div class="nav-title">{T['decouvrir']}</div>
            <div class="nav-desc">Notre concept, nos valeurs, nos engagements</div>
        </div>""", unsafe_allow_html=True)
        if st.button("→", key="btn_decouvrir"):
            st.info(T.get("decouvrir_info", "ST-Ecoparvis transforme les déchets plastiques en pavés écologiques.\n\n✅ Zéro résidu · ✅ Haute résistance · ✅ Éco-drainant · ✅ Made in Bénin"))

    with c2:
        st.markdown(f"""<div class="nav-card">
            <div class="nav-icon">🧮</div>
            <div class="nav-title">{T['commander']}</div>
            <div class="nav-desc">Simulez, personnalisez et commandez</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Commander →", key="btn_commander"):
            st.info(T.get("aller_calc", "👈 Allez dans Calculateur & Devis dans le menu de gauche."))

    with c3:
        st.markdown(f"""<div class="nav-card">
            <div class="nav-icon">📸</div>
            <div class="nav-title">{T['galerie_btn']}</div>
            <div class="nav-desc">Inspirez-vous de nos réalisations</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Voir galerie →", key="btn_galerie"):
            st.info(T.get("aller_gal", "👈 Allez dans Galerie dans le menu de gauche."))

    with c4:
        st.markdown(f"""<div class="nav-card">
            <div class="nav-icon">📞</div>
            <div class="nav-title">{T['contact_btn']}</div>
            <div class="nav-desc">On vous répond sous 24h</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Contacter →", key="btn_contact"):
            st.info(T.get("aller_contact", "👈 Allez dans Contact dans le menu de gauche."))

    st.markdown("---")

    # Chiffres clés
    st.markdown(f"<h3 style='text-align:center;color:#1B5E20;'>{T['chiffres']}</h3>", unsafe_allow_html=True)
    s1, s2, s3, s4 = st.columns(4)
    stat1_label = T.get("plastique_recycle", "♻️ Plastique recyclé par m²")
    stat2_label = T.get("resistance_meca", "💪 Résistance mécanique")
    stat3_label = T.get("zones_livraison", "🚚 Livraison au Bénin")
    stat4_label = T.get("interface_multi", "🌍 Interface multilingue")
    with s1:
        st.markdown(f'<div class="stat-card"><div class="stat-number">12-18 kg</div><div class="stat-label">{stat1_label}</div></div>', unsafe_allow_html=True)
    with s2:
        st.markdown(f'<div class="stat-card"><div class="stat-number">30-55 MPa</div><div class="stat-label">{stat2_label}</div></div>', unsafe_allow_html=True)
    with s3:
        st.markdown(f'<div class="stat-card"><div class="stat-number">5 zones</div><div class="stat-label">{stat3_label}</div></div>', unsafe_allow_html=True)
    with s4:
        st.markdown(f'<div class="stat-card"><div class="stat-number">5 langues</div><div class="stat-label">{stat4_label}</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — CALCULATEUR & DEVIS
# ══════════════════════════════════════════════════════════════════════════════
elif menu == T["nav"][1]:

    # Barre de progression
    etapes = T["progression"]
    etape_active = st.session_state.get("etape", 0)
    prog_html = '<div class="progress-bar">'
    for i, e in enumerate(etapes):
        if i < etape_active:
            cls = "done"; ico = "✅"
        elif i == etape_active:
            cls = "active"; ico = "🔵"
        else:
            cls = "inactive"; ico = "⚪"
        prog_html += f'<div class="prog-step {cls}">{ico}<br>{e}</div>'
    prog_html += '</div>'
    st.markdown(prog_html, unsafe_allow_html=True)

    st.markdown(f'<div class="section-title">{T.get("simulateur_titre", "🧮 Simulateur de Commande")}</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(T.get("parametres", "🧱 Paramètres"))

        # Superficie
        st.markdown(f"#### {T['superficie_titre']}")
        mode_sup = st.radio("", [T["manuelle"], T["carte"]], horizontal=True)
        surface = 10.0
        if mode_sup == T["manuelle"]:
            surface = st.number_input(T["surface_label"], min_value=1.0, value=10.0, step=1.0)
            st.session_state.etape = max(st.session_state.etape, 1)
        else:
            st.info(T["carte_info"])
            try:
                import folium
                from streamlit_folium import st_folium
                from shapely.geometry import Polygon
                import math
                m = folium.Map(location=[6.3654, 2.4183], zoom_start=13)
                folium.plugins.Draw(export=True, draw_options={"polygon": True, "rectangle": True, "circle": False, "marker": False, "polyline": False, "circlemarker": False}).add_to(m)
                result = st_folium(m, height=300, width=None)
                if result and result.get("last_active_drawing"):
                    coords = result["last_active_drawing"]["geometry"]["coordinates"][0]
                    poly = Polygon([(c[0], c[1]) for c in coords])
                    lat_rad = math.radians(6.3654)
                    surface = poly.area * 111132.92 * 111132.92 * math.cos(lat_rad)
                    st.success(f"Superficie : **{surface:,.1f} m²**")
                    st.session_state.etape = max(st.session_state.etape, 1)
                else:
                    surface = st.number_input(T["surface_label"], min_value=1.0, value=10.0, step=1.0)
            except:
                surface = st.number_input(T["surface_label"], min_value=1.0, value=10.0, step=1.0)

        type_pave = st.selectbox(T["type_pave_label"], ["Pavé Drainant (Éco)", "Pavé Autobloquant Classique", "Pavé Haute Résistance"])

        # Forme
        st.markdown(f"#### {T['forme_titre']}")
        formes = {"Carré ⬛": 0, "Rectangle ▬": 0, "Hexagone ⬡ (+300 FCFA/m²)": 300, "Forme H/I/S/Z (+500 FCFA/m²)": 500, "Forme personnalisée (+1000 FCFA/m²)": 1000}
        forme_choisie = st.selectbox("", list(formes.keys()))
        supplement_forme = formes[forme_choisie]

        # Motif
        st.markdown(f"#### {T['motif_titre']}")
        motifs_std = {
            "Lisse (sans motif)": 0, "Briques classiques 🧱": 300,
            "Chevrons ↗ (+300 FCFA/m²)": 300, "Hexagones ⬡ (+300 FCFA/m²)": 300,
            "Quadrillage ⊞ (+300 FCFA/m²)": 300, "Losanges ◇ (+300 FCFA/m²)": 300,
            "Cercles ○ (+300 FCFA/m²)": 300, "Opus romain (+300 FCFA/m²)": 300,
            "Galets 〰 (+300 FCFA/m²)": 300, "Spirale/Rosace 🌸 (+800 FCFA/m²)": 800,
        }
        option_motif = st.radio(T["motif_titre"], [T["motif_std"], T["motif_perso"]])
        if option_motif == T["motif_std"]:
            motif_choisi = st.selectbox("", list(motifs_std.keys()))
            supplement_motif = motifs_std[motif_choisi]
        else:
            motif_choisi = "Motif personnalisé"
            supplement_motif = 1000
            st.markdown(f'<div class="color-notice">{T["motif_perso_info"]}</div>', unsafe_allow_html=True)
            photo_motif = st.file_uploader(
                "📸 Téléchargez votre photo de motif (optionnel)",
                type=["jpg", "jpeg", "png", "webp"],
                key="photo_motif"
            )
            if photo_motif:
                st.image(photo_motif, caption="Votre motif personnalisé", width=200)
                st.success("✅ Photo reçue ! Elle sera jointe à votre commande WhatsApp.")

        # Couleur
        st.markdown(f"#### {T['couleur_titre']}")
        couleurs_dispo = ["Rouge brique 🔴", "Vert 🟢", "Jaune 🟡", "Gris anthracite ⬛", "Violet 🟣", "Bleu 🔵", "Noir ⬛", "Blanc ⬜", "Orange 🟠"]
        option_couleur = st.radio(T["couleur_q"], [T["naturel"], T["couleur_unie"], T["melange"]])
        supplement_couleur = 0
        couleur_choisie = "Naturel"

        if option_couleur == T["couleur_unie"]:
            supplement_couleur = 500
            couleur_choisie = st.selectbox(T["couleurs_dispo"], couleurs_dispo)
            st.markdown(f'<div class="color-notice">⚠️ Supplément : <b>+500 FCFA/m²</b></div>', unsafe_allow_html=True)
        elif option_couleur == T["melange"]:
            nb_couleurs = st.slider(T["nb_couleurs"], 2, 5, 2)
            supplement_couleur = nb_couleurs * 500
            couleurs_sel = st.multiselect(T["couleurs_dispo"], couleurs_dispo, max_selections=nb_couleurs)
            couleur_choisie = " + ".join(couleurs_sel) if couleurs_sel else "Mélange"
            st.markdown(f'<div class="color-notice">🎨 {nb_couleurs} couleurs → <b>+{supplement_couleur} FCFA/m²</b></div>', unsafe_allow_html=True)

        st.markdown(f'<div style="text-align:right;"><a href="#" style="color:#4CAF50;font-size:12px;">👁️ {T["galerie_lien"]}</a></div>', unsafe_allow_html=True)

        # Zone
        zone_livraison = st.selectbox(T["zone_label"], ["Cotonou / Calavi", "Porto-Novo", "Abomey / Bohicon", "Parakou", "Retrait sur place (Gratuit)"])
        intensite_pluie = st.select_slider(T["pluie_label"], options=["Faible", "Modérée", "Forte (Saison des pluies)"])

        # Configs
        if type_pave == "Pavé Drainant (Éco)":
            prix_unitaire = 5000; plastique_par_m2 = 12.5; resistance = "~30 MPa"
            drainage_info = {"Faible": "🟢 Absorption totale instantanée.", "Modérée": "🟢 Évacuation fluide.", "Forte (Saison des pluies)": "🟡 Absorption maximale activée."}[intensite_pluie]
        elif type_pave == "Pavé Autobloquant Classique":
            prix_unitaire = 4500; plastique_par_m2 = 14.0; resistance = "~45 MPa"
            drainage_info = {"Faible": "🟢 Légère infiltration.", "Modérée": "🟡 Ruissellement standard.", "Forte (Saison des pluies)": "🔴 Risque de stagnation."}[intensite_pluie]
        else:
            prix_unitaire = 6500; plastique_par_m2 = 18.5; resistance = "~55 MPa"
            drainage_info = "❌ Structure étanche haute densité."

        nb_paves = surface * 20
        if zone_livraison == "Retrait sur place (Gratuit)":
            frais_livraison = 0
        elif zone_livraison == "Cotonou / Calavi":
            frais_livraison = round((5000 + surface * 300 + (10000 if nb_paves > 500 else 0)) / 500) * 500
        elif zone_livraison == "Porto-Novo":
            frais_livraison = round((7000 + surface * 300 + (10000 if nb_paves > 500 else 0)) / 500) * 500
        elif zone_livraison == "Abomey / Bohicon":
            frais_livraison = round((10000 + surface * 400 + (15000 if nb_paves > 400 else 0)) / 500) * 500
        else:
            frais_livraison = round((20000 + surface * 500 + (20000 if nb_paves > 300 else 0)) / 500) * 500

        st.session_state.etape = max(st.session_state.etape, 1)

    with col2:
        st.subheader(f"📊 {T['specs_label']}")
        total_plastique = surface * plastique_par_m2
        prix_beton = surface * 9000
        prix_total_m2 = prix_unitaire + supplement_couleur + supplement_forme + supplement_motif
        montant_paves = surface * prix_total_m2
        montant_total = montant_paves + frais_livraison
        economie = prix_beton - montant_total

        st.markdown(f"""
        <div class="eco-badge">
            🎉 Grâce à cette commande :<br>
            <span style="font-size:26px;color:#1B5E20;">{total_plastique:,.1f} kg</span><br>
            <span style="font-size:13px;">{T['plastique_label']}</span>
        </div>""", unsafe_allow_html=True)

        # Aperçu visuel du pavé
        couleur_css = {"Rouge brique 🔴": "#8B2500", "Vert 🟢": "#2E7D32", "Jaune 🟡": "#F9A825",
                       "Gris anthracite ⬛": "#424242", "Violet 🟣": "#6A1B9A", "Bleu 🔵": "#1565C0",
                       "Noir ⬛": "#212121", "Blanc ⬜": "#F5F5F5", "Orange 🟠": "#E65100", "Naturel": "#5D4037"}
        couleur_hex = couleur_css.get(couleur_choisie.split(" + ")[0] if " + " in couleur_choisie else couleur_choisie, "#5D4037")
        forme_shape = "50%" if "Hexagone" in forme_choisie else ("30% 70% 70% 30%" if "H/I" in forme_choisie else "8px")

        st.markdown(f"""
        <div class="apercu-pave">
            <p style="font-size:13px;color:#777;margin-bottom:10px;">{T['apercu_pave']}</p>
            <div style="width:100px;height:100px;background:{couleur_hex};border-radius:{forme_shape};
                        margin:0 auto 10px;box-shadow:0 4px 12px rgba(0,0,0,0.3);
                        display:flex;align-items:center;justify-content:center;color:white;font-size:11px;">
                {motif_choisi[:8]}
            </div>
            <p style="font-size:12px;color:#555;">{forme_choisie.split('(')[0]} · {couleur_choisie[:20]}</p>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card">
            <p><b>{T['resistance_label']} :</b> {resistance}</p>
            <p><b>Forme :</b> {forme_choisie.split('(')[0]}</p>
            <p><b>Motif :</b> {motif_choisi}</p>
            <p><b>Couleur :</b> {couleur_choisie[:30]}</p>
            <p><b>{T['simulation_label']} ({intensite_pluie}) :</b> {drainage_info}</p>
            <p><b>Pavés estimés :</b> ~{int(nb_paves)} unités</p>
        </div>""", unsafe_allow_html=True)

        # Suggestions IA
        st.markdown(f"#### {T['suggestions_ia']}")
        suggestions = []
        if surface > 50:
            suggestions.append("💡 Grande surface : le Pavé Haute Résistance est recommandé pour une durabilité maximale.")
        if zone_livraison == "Parakou":
            suggestions.append("🚚 Livraison Parakou : commandez en grande quantité pour optimiser les frais de transport.")
        if option_couleur == T["melange"] and nb_couleurs >= 4:
            suggestions.append("🎨 Mélange riche : pensez à la Spirale/Rosace comme motif pour un rendu premium.")
        if intensite_pluie == "Forte (Saison des pluies)":
            suggestions.append("🌧️ Zone pluvieuse : le Pavé Drainant (Éco) est fortement recommandé.")
        if not suggestions:
            suggestions.append("✅ Votre configuration est équilibrée et adaptée à votre projet !")
        for s in suggestions:
            st.info(s)

    # Calcul final
    st.markdown("---")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown(f'<div style="color:#ffffff;background:linear-gradient(135deg,#1B5E20,#2E7D32);padding:16px;border-radius:12px;margin-bottom:8px;"><span style="font-size:20px;font-weight:900;">{T["montant_label"]} : {montant_total:,.0f} FCFA</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color:#4CAF50;font-size:12px;">Pavés: {montant_paves:,.0f} FCFA | Transport: {frais_livraison:,.0f} FCFA</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color:#4CAF50;font-weight:bold;margin-top:6px;">⏱️ {T["validite"]}</div>', unsafe_allow_html=True)
    with col_m2:
        if economie > 0:
            st.markdown(f'<div style="color:#ffffff;background:linear-gradient(135deg,#2E7D32,#4CAF50);padding:16px;border-radius:12px;"><span style="font-size:18px;font-weight:900;">{T["economie_label"]} : {economie:,.0f} FCFA 🎉</span></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="color:#ffffff;background:linear-gradient(135deg,#2E7D32,#4CAF50);padding:16px;border-radius:12px;"><span style="font-size:16px;font-weight:700;">{T["economie_label"]} : Prix compétitif ✅</span></div>', unsafe_allow_html=True)

    st.session_state.etape = max(st.session_state.etape, 2)

    # Commande
    st.markdown(f'<div class="section-title">📩 {T["commander_label"]}</div>', unsafe_allow_html=True)
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        nom_client = st.text_input(T["nom_label"])
    with col_c2:
        contact = st.text_input(T["contact_label"])

    if st.button(T["btn_wa"]):
        if nom_client and contact:
            st.session_state.etape = 3
            numero_cmd = generer_numero_commande()
            sauvegarder_devis(numero_cmd, nom_client, contact, type_pave, surface, zone_livraison,
                              couleur_choisie, forme_choisie, motif_choisi, montant_total, total_plastique, max(economie, 0))
            envoyer_email_notification(nom_client, contact, type_pave, surface, montant_total, zone_livraison, numero_cmd)

            st.success(f"{T.get('commande_confirmee', '✅ Commande confirmée !').replace('Commande', f'Commande {numero_cmd}')}")
            st.info(T.get("repondrons", "📬 Nous vous répondrons sous 24h."))

            # Reçu PDF
            pdf_buffer = generer_recu_pdf(numero_cmd, nom_client, contact, type_pave, surface,
                                          zone_livraison, couleur_choisie, forme_choisie, motif_choisi,
                                          montant_total, total_plastique, max(economie, 0), frais_livraison, montant_paves)
            st.download_button(T.get("telecharger_recu", "📄 Télécharger mon reçu PDF"), data=pdf_buffer,
                               file_name=f"Recu_ST_Ecoparvis_{numero_cmd}.pdf", mime="application/pdf")

            # Paiement
            st.markdown(f'<div class="paiement-box">', unsafe_allow_html=True)
            st.markdown(f"### 💳 Procédez au paiement de **{montant_total:,.0f} FCFA**")
            p1, p2 = st.columns(2)
            with p1:
                st.markdown(f"""<div style="background:#FFD700;padding:16px;border-radius:12px;text-align:center;">
                    <h4 style="color:#1a1a1a;margin:0;">📱 MTN Mobile Money</h4>
                    <p style="font-size:22px;font-weight:900;color:#1a1a1a;margin:8px 0;">+229 69 71 06 23</p>
                    <p style="color:#333;font-size:12px;margin:0;">Montant exact : <b>{montant_total:,.0f} FCFA</b></p>
                </div>""", unsafe_allow_html=True)
            with p2:
                st.markdown(f"""<div style="background:#0066CC;padding:16px;border-radius:12px;text-align:center;">
                    <h4 style="color:white;margin:0;">📱 Celtiis</h4>
                    <p style="font-size:22px;font-weight:900;color:white;margin:8px 0;">+229 92 62 41 33</p>
                    <p style="color:#ddd;font-size:12px;margin:0;">Montant exact : <b>{montant_total:,.0f} FCFA</b></p>
                </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.warning(T.get("apres_paiement", "⚠️ Après paiement, envoyez votre capture de reçu sur WhatsApp."))

            # WhatsApp
            texte_wa = (
                f"♻️ *COMMANDE ST-ECOPARVIS — {numero_cmd}*\n\n"
                f"👤 *Nom :* {nom_client}\n📞 *Contact :* {contact}\n📍 *Zone :* {zone_livraison}\n\n"
                f"🧱 *Détails :*\n- Type : {type_pave}\n- Forme : {forme_choisie}\n"
                f"- Motif : {motif_choisi}\n- Couleur : {couleur_choisie}\n- Surface : {surface} m²\n"
                f"- 🌿 {total_plastique:,.1f} kg recyclés !\n\n"
                f"💵 Pavés : {montant_paves:,.0f} | Transport : {frais_livraison:,.0f}\n"
                f"💰 *TOTAL : {montant_total:,.0f} FCFA*"
            )
            lien_wa = f"https://wa.me/22969710623?text={urllib.parse.quote(texte_wa)}"
            st.markdown(f"[{T.get('envoyer_wa', '➡️ Envoyer aussi sur WhatsApp')}]({lien_wa})")

            # Partager
            texte_partage = f"J'ai reçu un devis ST-Ecoparvis pour {surface}m² — Montant : {montant_total:,.0f} FCFA. N° commande : {numero_cmd}"
            lien_partage = f"https://wa.me/?text={urllib.parse.quote(texte_partage)}"
            st.markdown(f"[📤 {T['partager']}]({lien_partage})")

        else:
            st.error(T.get("nom_contact_requis", "Veuillez remplir votre nom et votre contact."))

    # Devis sur mesure
    st.markdown("---")
    with st.expander(f"📋 {T['devis_complexe']}"):
        st.write(T["devis_complexe_info"])
        desc_projet = st.text_area(T.get("decrire_projet", "Décrivez votre projet :"), placeholder=T.get("placeholder_projet", "Ex: Route courbe 200m..."))
        if st.button(T["devis_complexe_btn"]):
            if desc_projet:
                msg_devis = f"📋 *DEMANDE DEVIS SUR MESURE — ST-ECOPARVIS*\n\n📝 *Description du projet :*\n{desc_projet}"
                lien_devis = f"https://wa.me/22969710623?text={urllib.parse.quote(msg_devis)}"
                st.success(T.get("envoyer_demande", "✅ Demande prête !"))
                st.markdown(f"[➡️ Envoyer la demande sur WhatsApp]({lien_devis})")
            else:
                st.error(T.get("desc_vide", "Veuillez décrire votre projet."))

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — GALERIE
# ══════════════════════════════════════════════════════════════════════════════
elif menu == T["nav"][2]:
    st.markdown(f'<div class="section-title">📸 {T["galerie_titre"]}</div>', unsafe_allow_html=True)
    st.write(T["galerie_sous"])
    galerie_images = [
        ("/mnt/user-data/uploads/1000427947.jpg", "Pavé Écologique"),
        ("/mnt/user-data/uploads/1000427961.jpg", "Mélange Turquoise & Or"),
        ("/mnt/user-data/uploads/1000427945.jpg", "Hexagones Bleus"),
        ("/mnt/user-data/uploads/1000428515.jpg", "Pavés Colorés"),
        ("/mnt/user-data/uploads/1000427951.jpg", "Haute Performance"),
        ("/mnt/user-data/uploads/1000427959.jpg", "Fabrication"),
        ("/mnt/user-data/uploads/1000427965.jpg", "Pose Chantier"),
        ("/mnt/user-data/uploads/1000427983.jpg", "Dalles Plastique"),
        ("/mnt/user-data/uploads/1000428526.jpg", "Stock Production"),
        ("/mnt/user-data/uploads/1000428527.jpg", "Technicien"),
        ("/mnt/user-data/uploads/1000428535.jpg", "Motifs Standards"),
        ("/mnt/user-data/uploads/1000428538.jpg", "Motifs Posés"),
    ]
    cols = st.columns(3)
    for i, (path, caption) in enumerate(galerie_images):
        try:
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            cols[i % 3].markdown(f"""
            <div style="margin-bottom:14px;">
                <img src="data:image/jpeg;base64,{b64}"
                     style="width:100%;border-radius:10px;object-fit:cover;height:180px;
                            box-shadow:0 4px 12px rgba(0,0,0,0.1);" />
                <p style="text-align:center;font-size:12px;color:#555;margin-top:4px;">{caption}</p>
            </div>""", unsafe_allow_html=True)
        except:
            pass

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — CONTACT
# ══════════════════════════════════════════════════════════════════════════════
elif menu == T["nav"][3]:
    st.markdown(f'<div class="section-title">📞 {T["contact_page"]}</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="contact-card">
        <h4>♻️ ST-Ecoparvis — Bénin</h4>
        <p><i>"Chaque déchet est une brique d'avenir"</i></p><br>
        <p>📱 <b>WhatsApp / MTN MoMo :</b> +229 69 71 06 23</p>
        <p>📱 <b>Celtiis :</b> +229 92 62 41 33</p>
        <p>📧 <b>Email :</b> eloisemable17@gmail.com</p>
        <p>📍 <b>Localisation :</b> {T.get("localisation", "Bénin (adresse en cours de finalisation)")}</p>
    </div>""", unsafe_allow_html=True)

    st.markdown(f'<div class="section-title">{T.get("faq_titre", "❓ Questions Fréquentes")}</div>', unsafe_allow_html=True)
    with st.expander(T.get("faq1_q", "⏱️ Combien de temps pour la livraison ?")):
        st.write(T.get("faq1_r", "Livraison sous 3 à 7 jours ouvrables."))
    with st.expander(T.get("faq2_q", "🌧️ Les pavés résistent-ils à la pluie et à la chaleur ?")):
        st.write(T.get("faq2_r", "Oui ! Nos pavés résistent aux fortes chaleurs."))
    with st.expander(T.get("faq3_q", "🧱 Puis-je voir un échantillon avant de commander ?")):
        st.write(T.get("faq3_r", "Oui ! Contactez-nous sur WhatsApp au +229 69 71 06 23."))
    with st.expander(T.get("faq4_q", "💰 Les prix affichés sont-ils définitifs ?")):
        st.write(T.get("faq4_r", "Les prix sont des estimations. Le montant définitif est confirmé sous 24h."))

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — HISTORIQUE
# ══════════════════════════════════════════════════════════════════════════════
elif menu == T["nav"][4]:
    st.markdown(f'<div class="section-title">📋 {T["historique_label"]}</div>', unsafe_allow_html=True)
    contact_search = st.text_input(T.get("entrez_numero", "Entrez votre numéro WhatsApp :"))
    if contact_search:
        rows = get_historique(contact_search)
        if rows:
            for row in rows:
                exp = row[3] if row[3] else "N/A"
                st.markdown(f"""
                <div class="historique-card">
                    📅 <b>{row[2]}</b> | 🔖 N° {row[1]} | ⏱️ Expire : {exp}<br>
                    🧱 {row[6]} | 📐 {row[7]} m² | 📍 {row[8]}<br>
                    🎨 {row[9]} | 🔷 {row[10]} | 🎭 {row[11]}<br>
                    🌿 {row[13]:,.1f} kg recyclés | 💰 <b>{row[12]:,.0f} FCFA</b>
                </div>""", unsafe_allow_html=True)
        else:
            st.info(T.get("aucun_devis", "Aucun devis trouvé pour ce numéro."))

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — TÉMOIGNAGES
# ══════════════════════════════════════════════════════════════════════════════
elif menu == T["nav"][5]:
    st.markdown(f'<div class="section-title">{T.get("temoignages_titre", "⭐ Témoignages Clients")}</div>', unsafe_allow_html=True)
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

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 7 — ADMIN
# ══════════════════════════════════════════════════════════════════════════════
elif menu == T["nav"][6]:
    st.markdown(f'<div class="section-title">{T.get("admin_titre", "🔐 Tableau de Bord Admin")}</div>', unsafe_allow_html=True)
    if not st.session_state.admin_connecte:
        mdp = st.text_input(T.get("mdp_label", "Mot de passe :"), type="password")
        if st.button("Se connecter"):
            if mdp == "Takane20":
                st.session_state.admin_connecte = True
                st.rerun()
            else:
                st.error(T.get("mdp_incorrect", "❌ Mot de passe incorrect."))
    else:
        st.success(T.get("connecte", "✅ Connecté"))
        if st.button(T.get("deconnecter", "Se déconnecter")):
            st.session_state.admin_connecte = False
            st.rerun()

        conn = sqlite3.connect("ecoparvis.db")
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM devis"); nb = c.fetchone()[0]
        c.execute("SELECT SUM(montant_total) FROM devis"); ca = c.fetchone()[0] or 0
        c.execute("SELECT SUM(plastique_kg) FROM devis"); plast = c.fetchone()[0] or 0
        c.execute("SELECT SUM(economie) FROM devis"); eco = c.fetchone()[0] or 0
        rows = get_all_devis()
        conn.close()

        s1, s2, s3, s4 = st.columns(4)
        s1.metric(T.get("devis_label", "📋 Devis"), nb)
        s2.metric(T.get("ca_label", "💰 CA Estimé"), f"{ca:,.0f} FCFA")
        s3.metric(T.get("plastique_label2", "🌿 Plastique Recyclé"), f"{plast:,.1f} kg")
        s4.metric(T.get("economie_label2", "💡 Économies Clients"), f"{eco:,.0f} FCFA")

        st.markdown("---")
        st.markdown(T.get("toutes_commandes", "### 📋 Toutes les commandes"))
        if rows:
            for row in rows:
                st.markdown(f"""
                <div class="historique-card">
                    🔖 <b>{row[1]}</b> | 📅 {row[2]} | 👤 {row[4]} | 📞 {row[5]}<br>
                    🧱 {row[6]} | 📐 {row[7]} m² | 📍 {row[8]}<br>
                    🎨 {row[9]} | 🔷 {row[10]} | 🎭 {row[11]}<br>
                    🌿 {row[13]:,.1f} kg | 💰 <b>{row[12]:,.0f} FCFA</b> | Statut : {row[15]}
                </div>""", unsafe_allow_html=True)
        else:
            st.info(T.get("aucune_commande", "Aucune commande encore enregistrée."))
