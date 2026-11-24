"""Reçu de commande en PDF."""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import config
from outils import maintenant

VERT = colors.HexColor("#1B5E20")
VERT_CLAIR = colors.HexColor("#E8F5E9")
GRIS = colors.HexColor("#BDBDBD")


def _nombre(x, decimales=0):
    return f"{x:,.{decimales}f}".replace(",", " ")


def generer_recu_pdf(numero, nom, contact, type_pave, surface, zone, couleur, forme, motif,
                     montant_total, plastique_kg, economie, frais_livraison, montant_paves):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm,
                            title=f"Reçu {numero}", author="ST-Ecoparvis")
    titre = ParagraphStyle("t", fontSize=20, leading=26, fontName="Helvetica-Bold", textColor=VERT,
                           alignment=TA_CENTER, spaceAfter=4)
    sous = ParagraphStyle("s", fontSize=11, leading=14, textColor=colors.HexColor("#2E7D32"),
                          alignment=TA_CENTER, spaceAfter=16)
    petit = ParagraphStyle("n", fontSize=9, leading=12, textColor=colors.grey, alignment=TA_CENTER, spaceAfter=4)

    story = [
        Paragraph("ST-ECOPARVIS", titre),
        Paragraph("\"Chaque déchet est une brique d'avenir\"", sous),
        Paragraph(f"REÇU DE COMMANDE N° {numero}",
                  ParagraphStyle("r", fontSize=14, leading=18, fontName="Helvetica-Bold", textColor=VERT,
                                 alignment=TA_CENTER, spaceAfter=4)),
        Paragraph(f"Date : {maintenant().strftime('%d/%m/%Y %H:%M')} | Valable {config.VALIDITE_HEURES}h",
                  ParagraphStyle("d", fontSize=9, alignment=TA_CENTER, textColor=colors.grey, spaceAfter=16)),
        Spacer(1, 0.3*cm),
    ]

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
        ["Pavés estimés", f"~{int(surface * config.PAVES_PAR_M2)} unités"],
        ["Plastique recyclé", f"{_nombre(plastique_kg, 1)} kg"],
        ["", ""],
        ["DÉTAIL FINANCIER", ""],
        ["Coût des pavés", f"{_nombre(montant_paves)} FCFA"],
        ["Frais de livraison", f"{_nombre(frais_livraison)} FCFA"],
        ["Économie vs béton classique", f"- {_nombre(economie)} FCFA"],
        ["TOTAL À PAYER", f"{_nombre(montant_total)} FCFA"],
    ]
    t = Table(data, colWidths=[7*cm, 9.5*cm])
    style = [("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"), ("TEXTCOLOR", (0, 1), (0, -1), VERT),
             ("GRID", (0, 0), (-1, -1), 0.5, GRIS), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
             ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, VERT_CLAIR])]
    for ligne in (0, 5, 14):  # titres de section
        style += [("BACKGROUND", (0, ligne), (-1, ligne), VERT), ("TEXTCOLOR", (0, ligne), (-1, ligne), colors.white),
                  ("FONTNAME", (0, ligne), (-1, ligne), "Helvetica-Bold"), ("SPAN", (0, ligne), (-1, ligne))]
    style += [("BACKGROUND", (0, 18), (-1, 18), colors.HexColor("#FFD700")),
              ("FONTNAME", (0, 18), (-1, 18), "Helvetica-Bold"), ("FONTSIZE", (0, 18), (-1, 18), 12)]
    t.setStyle(TableStyle(style))
    story += [t, Spacer(1, 0.5*cm)]

    paiement = [["MODE DE PAIEMENT", "NUMÉRO"]] + [[p["nom"], p["numero"]] for p in config.PAIEMENTS]
    tp = Table(paiement, colWidths=[8.25*cm, 8.25*cm])
    tp.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERT), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#E3F2FD"), colors.HexColor("#FFF9C4")]),
        ("GRID", (0, 0), (-1, -1), 0.5, GRIS), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story += [tp, Spacer(1, 0.3*cm),
              Paragraph(f"Ce devis est valable {config.VALIDITE_HEURES}h. Après paiement, envoyez votre reçu "
                        "sur WhatsApp. Le nom du titulaire affiché au moment du paiement peut être différent "
                        "de celui d'ST-Ecoparvis : demandez-nous confirmation sur WhatsApp avant d'envoyer.", petit),
              Paragraph(f"WhatsApp {config.WHATSAPP_AFFICHAGE} | {config.EMAIL_CONTACT}",
                        ParagraphStyle("c", fontSize=9, textColor=VERT, alignment=TA_CENTER))]
    doc.build(story)
    buffer.seek(0)
    return buffer