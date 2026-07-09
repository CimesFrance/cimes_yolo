"""Module de gestion des points de l'application.
"""

import numpy as np


def bool_pt_appuye(mesure, event):
    """Hit-test : vérifie si le clic est assez proche d'un point existant.

    Compare la distance entre le clic (event.x, event.y) et chaque point
    en utilisant les coordonnées CANVAS (écran). Si la distance est ≤ taille
    du point (5px par défaut), on considère que l'utilisateur a cliqué dessus.

    ATTENTION : coord_pt_canvas est mis à jour uniquement lors du re-rendu
    (dans canvas_view._dessiner_mesure). Si le canvas n'a pas été redessiné
    récemment, les coordonnées peuvent être désynchronisées.

    Args:
        mesure: Objet mesure contenant les points.
        event: Objet event contenant les coordonnées du clic.

    Returns:
        key_pt: Clé du point cliqué ("pt1" ou "pt2"), ou -1 si aucun.
        pt_appuye: True si un point a été cliqué, False sinon.
    """
    key_pt, pt_appuye = -1, False
    for key, pt in mesure.pts.items():
        # Vecteur distance entre le clic et le centre du point
        vect_dist = np.array(
            [pt.coord_pt_canvas["x"] - event.x, pt.coord_pt_canvas["y"] - event.y]
        )
        dist = np.linalg.norm(vect_dist)  # Distance euclidienne
        if dist <= pt.taille:  # pt.taille = rayon de détection (5px)
            key_pt, pt_appuye = key, True
            break
    return key_pt, pt_appuye
