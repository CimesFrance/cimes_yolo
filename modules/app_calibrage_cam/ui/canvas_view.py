"""
 Module pour la fenêtre d'affichage de l'image et
la gestion des interactions directes (déplacement, zoom, manipulation des points)"""

import tkinter as tk
from PIL import Image, ImageTk
from modules.app_calibrage_cam.utils.point_manager import bool_pt_appuye


# pylint: disable=too-many-ancestors
class FenetreImage(tk.Canvas):
    """Classe pour afficher l'image et les mesures. """
    def __init__(self, parent, app, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.app = app
        self.app.img.img_path.trace_add("write", self._maj_fenetre)
        # Déclenche un re-rendu quand modif_canvas est togglé
        self.app.modif_canvas.trace_add("write", self._maj_fenetre)
        self.deb_deplc_img = []  # Position de départ pour le drag de l'image
        self.deb_deplc_pt = []
        self.pt_appuye = False
        self.key_pt = None
        self.image_ref = None
        self.config(cursor="crosshair")  # Curseur par défaut en croix de précision
        self.bind("<ButtonPress-3>", self._deplacement_start)
        self.bind("<B3-Motion>", self._deplacement_move)
        self.bind("<ButtonRelease-3>", self._deplacement_stop)
        self.bind("<MouseWheel>", self._zoom)
        self.bind("<ButtonPress-1>", self._handl_pt_start)
        self.bind("<B1-Motion>", self._handl_pt_move)

    def _maj_fenetre(self, *_args):
        """Re-rendu complet du canvas : image zoomée + toutes les mesures visibles.
        Appelé à chaque changement d'image, zoom, déplacement ou toggle modif_canvas."""
        path = self.app.img.img_path.get()
        if not path:
            return
        try:
            self.app.img.import_img = Image.open(path)
            img_orig = self.app.img.import_img
            zoom = self.app.zoom_factor.get()
            # Redimensionnement de l'image selon le zoom actuel
            new_w, new_h = int(img_orig.width * zoom), int(img_orig.height * zoom)
            img_resized = img_orig.resize((new_w, new_h), Image.Resampling.LANCZOS)
            # Stockage de la référence pour empêcher le garbage collector de supprimer l'image
            self.image_ref = ImageTk.PhotoImage(img_resized)
            self.app.img.tk_image = self.image_ref
            # Effacement complet puis redessin (méthode "immediate mode")
            self.delete("all")
            orig = self.app.img.coord_origine.get()  # Position du coin haut-gauche
            self.create_image(orig["x"], orig["y"], anchor="nw", image=self.image_ref)
            # Dessin des mesures par-dessus l'image
            for mesure in self.app.list_mesures:
                if mesure.flag_affiche_ptligne.get():
                    self._dessiner_mesure(mesure, zoom, orig)
        # pylint: disable=broad-exception-caught
        except Exception as e:
            print(f"Erreur de rendu : {e}")

    def _dessiner_mesure(self, mesure, zoom, orig):
        """Dessine les points et la ligne d'une mesure sur le canvas.

        Conversion coord_pt_img → coord_pt_canvas :
            canvas_x = (img_x × zoom) + origine_x
            canvas_y = (img_y × zoom) + origine_y

        Cette conversion est l'inverse de celle faite dans add_pt (une_mesure.py)."""
        pts_canvas = []
        for pt in mesure.pts.values():
            if pt.created:
                # Conversion : coordonnées image source → coordonnées écran
                cx = (pt.coord_pt_img["x"] * zoom) + orig["x"]
                cy = (pt.coord_pt_img["y"] * zoom) + orig["y"]
                # Mise à jour des coordonnées canvas
                pt.coord_pt_canvas = {"x": cx, "y": cy}
                self.create_oval(
                    cx - 5, cy - 5, cx + 5, cy + 5, fill=pt.color, outline="white"
                )
                pts_canvas.append((cx, cy))
        # Si les 2 points existent, on trace le segment entre eux
        if len(pts_canvas) == 2:
            self.create_line(
                pts_canvas[0][0],
                pts_canvas[0][1],
                pts_canvas[1][0],
                pts_canvas[1][1],
                fill=mesure.color,
                width=2,
            )

    def _deplacement_start(self, _event):
        self.config(cursor="fleur")  # Change le curseur pendant le déplacement
        self.deb_deplc_img = [_event.x, _event.y]

    def _deplacement_stop(self, _event):
        self.config(cursor="crosshair")  # Rétablit le curseur de précision


    # pylint: disable=too-many-locals
    def _deplacement_move(self, event):
        """Déplace l'image avec le clic droit maintenu, avec des bornes
        pour empêcher de "perdre" l'image hors du canvas."""
        img_orig = self.app.img.import_img
        if not img_orig:
            return
        dx, dy = event.x - self.deb_deplc_img[0], event.y - self.deb_deplc_img[1]
        orig = self.app.img.coord_origine.get()
        zoom = self.app.zoom_factor.get()
        new_w = img_orig.width * zoom   # Largeur de l'image zoomée
        new_h = img_orig.height * zoom  # Hauteur de l'image zoomée
        canvas_w = self.winfo_width()
        canvas_h = self.winfo_height()
        # Marge de sécurité : au moins 100px de l'image doivent rester visibles.
        margin = 100
        min_x = -new_w + margin
        max_x = canvas_w - margin
        min_y = -new_h + margin
        max_y = canvas_h - margin
        # Borner (clamp) la nouvelle position dans les limites
        new_x = max(min_x, min(max_x, orig["x"] + dx))
        new_y = max(min_y, min(max_y, orig["y"] + dy))
        self.app.img.coord_origine.set({"x": new_x, "y": new_y})
        self.deb_deplc_img = [event.x, event.y]
        self._maj_fenetre()

    def _zoom(self, event):
        """Zoom centré sur la position du curseur.

        Le calcul repositionne l'origine de l'image pour que le pixel
        sous le curseur reste exactement sous le curseur après le zoom.
        Formule : new_origin = cursor - (cursor - old_origin) × step"""
        old_zoom = self.app.zoom_factor.get()
        step = 1.1 if event.delta > 0 else 0.9  # Zoom in (+10%) ou zoom out (-10%)
        new_zoom = old_zoom * step
        # Borner le zoom entre 10% et 250% pour éviter les problèmes de performance
        if new_zoom < 0.1:
            new_zoom = 0.1
            step = new_zoom / old_zoom  # Recalcul du step réel pour la formule ci-dessous
        elif new_zoom > 2.5:
            new_zoom = 2.5
            step = new_zoom / old_zoom
        self.app.zoom_factor.set(new_zoom)
        orig = self.app.img.coord_origine.get()
        # Transformation affine : le pixel sous le curseur ne bouge pas
        new_x = event.x - (event.x - orig["x"]) * step
        new_y = event.y - (event.y - orig["y"]) * step
        self.app.img.coord_origine.set({"x": new_x, "y": new_y})
        self._maj_fenetre()
        return "break"

    def _handl_pt_start(self, event):
        """Gestion du clic gauche sur le canvas.
        Deux comportements possibles :
        1. Clic PROCHE d'un point existant → mode déplacement du point
        2. Clic LOIN des points → création d'un nouveau point

        La mesure ciblée dépend du radio "Saisir" sélectionné (choix_mesure).
        Si la mesure n'est pas activée (created=False), le clic est ignoré."""
        if not self.app.img.import_img:
            return
        idx = self.app.choix_mesure.get()  # Index de la mesure sélectionnée via le radio
        mesure_active = self.app.list_mesures[idx]
        # created=False → mesure non activée
        if not mesure_active.created:
            return
        # Hit-test : vérifie si le clic est à ≤5px d'un point existant
        self.key_pt, self.pt_appuye = bool_pt_appuye(mesure_active, event)
        if self.pt_appuye:
            self.deb_deplc_pt = [event.x, event.y]  # Début du drag du point
        else:
            mesure_active.add_pt(event)  # Création d'un nouveau point
        self._maj_fenetre()

    def _handl_pt_move(self, event):
        if self.pt_appuye:
            idx = self.app.choix_mesure.get()
            self.app.list_mesures[idx].deplacer_pts(
                self.key_pt, event, self.deb_deplc_pt
            )
            self.deb_deplc_pt = [event.x, event.y]
            self._maj_fenetre()
