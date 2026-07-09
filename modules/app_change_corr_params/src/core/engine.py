"""Module de fonctions de calcul de réglage des paramètres granulométriques.
Ce module contient les fonctions de correction granulométrique, d'inversion de correction,
et de calcul d'erreur entre les courbes corrigées et les courbes pratiques."""

import numpy as np
from scipy.interpolate import interp1d


def inv_correct(tamis_act, scale_act, offset_act):
    """Inverse de la correction granulométrique."""
    return list((np.array(tamis_act) - offset_act) / scale_act)


def correct(tamis_act, scale_nv, offset_nv):
    """Applique la correction granulométrique."""
    return list(np.array(tamis_act) * scale_nv + offset_nv)


def calc_erreur(tamis_corrigee, cumulatif_corrigee, tamis_pratique, cumulatif_pratique):
    """Calcule l'erreur entre les courbes corrigées et les courbes pratiques.
     Les deux courbes n'ont pas forcément les mêmes points X.
     On crée donc 300 points réguliers sur la plage commune pour pouvoir
     les comparer point à point. 300 est un compromis précision/vitesse."""
    xfine = np.linspace(min(tamis_pratique), max(tamis_pratique), 300)
    # Interpolation linéaire : on estime les valeurs de chaque courbe
    exp_interp = interp1d(tamis_pratique, cumulatif_pratique, kind="linear")
    y_exp_interp = exp_interp(xfine)
    # fill_value="extrapolate" : si la courbe corrigée dépasse la plage
    # de la courbe pratique, on extrapole au lieu de planter.
    corr_interp = interp1d(
        tamis_corrigee, cumulatif_corrigee, kind="linear", fill_value="extrapolate"
    )
    y_corr_interp = corr_interp(xfine)
    dy = y_corr_interp - y_exp_interp
    # Erreur de type MSE:
    # plus la valeur est proche de 0, plus les courbes se superposent.
    return round(np.sum(dy**2) / 300, 3)


def erreur_minim(
    params_correct,
    tamis_originale,
    cumulatif_originale,
    tamis_pratique,
    cumulatif_pratique,
):
    """Fonction coût utilisée par scipy.optimize.minimize pour l'auto-ajustement.

    scipy.minimize appelle cette fonction en boucle en faisant varier
    params_correct = [scale, offset] jusqu'à trouver la combinaison qui
    minimise la valeur retournée (= l'erreur entre les deux courbes).
    """
    # scipy passe les paramètres dans un seul tableau [scale, offset]
    scale, offset = params_correct
    # On applique la correction pour obtenir les tamis décalés
    tamis_corr = tamis_originale * scale + offset
    # Même logique que calc_erreur : on compare sur 300 points communs
    xfine = np.linspace(min(tamis_pratique), max(tamis_pratique), 300)
    corr_interp = interp1d(
        tamis_corr, cumulatif_originale, kind="linear", fill_value="extrapolate"
    )
    cumul_corr_interp = corr_interp(xfine)
    prat_interp = interp1d(tamis_pratique, cumulatif_pratique, kind="linear")
    cumul_prat_interp = prat_interp(xfine)
    # Somme des carrés des écarts (sans diviser) : scipy cherche à minimiser ce nombre.
    return np.sum((cumul_corr_interp - cumul_prat_interp) ** 2)
