"""Calcul du devis : prix, livraison, plastique recyclé, économie."""
import config


def frais_livraison(zone, surface):
    regle = config.LIVRAISON.get(zone)
    if not regle:
        return 0
    nb_paves = surface * config.PAVES_PAR_M2
    brut = regle["base"] + surface * regle["par_m2"]
    if nb_paves > regle["seuil_paves"]:
        brut += regle["majoration"]
    return round(brut / 500) * 500


def calculer(type_pave, surface, suppl_couleur, suppl_forme, suppl_motif, zone):
    t = config.TYPES_PAVE[type_pave]
    prix_total_m2 = t["prix_m2"] + suppl_couleur + suppl_forme + suppl_motif
    montant_paves = surface * prix_total_m2
    frais = frais_livraison(zone, surface)
    montant_total = montant_paves + frais
    return {
        "resistance": t["resistance"],
        "nb_paves": surface * config.PAVES_PAR_M2,
        "total_plastique": surface * t["plastique_kg_m2"],
        "montant_paves": montant_paves,
        "frais_livraison": frais,
        "montant_total": montant_total,
        "economie": surface * config.PRIX_BETON_M2 - montant_total,
    }