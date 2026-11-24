"""
RÉGLAGES D'ECOPARVIS — c'est le seul fichier à modifier pour changer
les prix, les contacts et les zones de livraison. Ne touche pas au reste.
"""

# ─── Contacts (affichés dans l'application et sur le reçu PDF) ───────────────
EMAIL_CONTACT = "matech.contacts@gmail.com"
WHATSAPP_AFFICHAGE = "+228 91 20 99 98"
WHATSAPP_LIEN = "22891209998"  # même numéro, chiffres seulement, pour les liens wa.me

# Moyens de paiement (le premier est affiché en premier)
PAIEMENTS = [
    {"nom": "Celtiis Cash", "numero": "+229 01 92 62 41 33",
     "fond": "#0066CC", "texte": "white"},
    {"nom": "MTN Mobile Money", "numero": "+229 01 69 71 06 23",
     "fond": "#FFD700", "texte": "#1a1a1a"},
]

# ─── Règles générales ────────────────────────────────────────────────────────
VALIDITE_HEURES = 48        # durée de validité d'un devis
PAVES_PAR_M2 = 20           # nombre de pavés estimés par m²
PRIX_BETON_M2 = 9000        # prix de référence du béton, pour calculer l'économie

# ─── Types de pavés : prix par m², plastique recyclé par m², résistance ──────
TYPES_PAVE = {
    "drainant":     {"prix_m2": 5000, "plastique_kg_m2": 12.5, "resistance": "~30 MPa"},
    "autobloquant": {"prix_m2": 4500, "plastique_kg_m2": 14.0, "resistance": "~45 MPa"},
    "haute_res":    {"prix_m2": 6500, "plastique_kg_m2": 18.5, "resistance": "~55 MPa"},
}

# ─── Suppléments en FCFA par m² ──────────────────────────────────────────────
SUPPL_FORMES = {"carre": 0, "rectangle": 0, "hexagone": 300, "hisz": 500, "perso": 1000}

# clé du motif : (clé de traduction, supplément)
MOTIFS = {
    "lisse": ("lisse", 0),
    "briques": ("briques", 300),
    "chevrons": ("motif_chevrons", 300),
    "hexagones_motif": ("motif_hexagones", 300),
    "quadrillage": ("motif_quadrillage", 300),
    "losanges": ("motif_losanges", 300),
    "cercles": ("motif_cercles", 300),
    "opus": ("motif_opus", 300),
    "galets": ("motif_galets", 300),
    "spirale": ("motif_spirale", 800),
}
SUPPL_MOTIF_PERSO = 1000
SUPPL_COULEUR_UNIE = 500
SUPPL_PAR_COULEUR_MELANGE = 500   # multiplié par le nombre de couleurs du mélange

# ─── Livraison : base + (par_m2 × surface) + majoration si beaucoup de pavés ──
# Le total est arrondi aux 500 FCFA. "retrait" = pas de frais.
LIVRAISON = {
    "retrait": None,
    "cotonou": {"base": 5000,  "par_m2": 300, "seuil_paves": 500, "majoration": 10000},
    "porto":   {"base": 7000,  "par_m2": 300, "seuil_paves": 500, "majoration": 10000},
    "abomey":  {"base": 10000, "par_m2": 400, "seuil_paves": 400, "majoration": 15000},
    "parakou": {"base": 20000, "par_m2": 500, "seuil_paves": 300, "majoration": 20000},
}

# ─── Suivi des commandes (page Admin) ────────────────────────────────────────
STATUTS = ["En attente", "Payé", "Livré", "Annulé"]