"""
Ce module contient les fonctions de segmentation et d'analyse des particules.
"""

import os
import sys
import numpy as np


# Vérifier disponibilité de skimage
try:
    from skimage.measure import label, regionprops

    SKIMAGE_AVAILABLE = True
except ImportError:
    SKIMAGE_AVAILABLE = False

# Vérifier disponibilité de YOLO
try:
    from ultralytics import YOLO

    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

import cv2
from src.core.calibration import undistort_img, homo_and_pixel_conversion


def _get_base_dir():
    """chemin absolu vers le modele de yolo obb"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return getattr(sys, "_MEIPASS", "")
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Chemin du modèle YOLO-OBB entraîné
YOLO_MODEL_PATH = os.path.join(_get_base_dir(), "best.pt")

# Seuil de confiance par défaut
YOLO_CONF_DEFAULT = 0.25

# Cache global pour éviter de recharger le modèle à chaque capture
_YOLO_MODEL = None


def mask_overlay(img, masks):
    """Overlay masks on image (set image to grayscale).

    Args:
        img (int or float, 2D or 3D array): Image de taille [Ly x Lx (x nchan)].
        masks (int, 2D array): Masques où 0=pas de masque ; 1,2,...=labels.

    Returns:
        RGB (uint8, 3D array): Image avec masques colorés superposés.
    """
    if img.ndim > 2:
        gray = img.astype(np.float32).mean(axis=-1)
    else:
        gray = img.astype(np.float32)

    # Normaliser en [0, 1]
    gray_norm = np.clip(gray / 255.0 if gray.max() > 1 else gray, 0, 1)

    # Créer l'image HSV
    hsv_img = np.zeros((img.shape[0], img.shape[1], 3), np.float32)
    hsv_img[:, :, 2] = np.clip(gray_norm * 1.5, 0, 1)

    n_masks = int(masks.max())
    if n_masks > 0:
        hues = np.linspace(0, 1, n_masks + 1)[np.random.permutation(n_masks)]
        for n in range(n_masks):
            ipix = (masks == n + 1).nonzero()
            hsv_img[ipix[0], ipix[1], 0] = hues[n]
            hsv_img[ipix[0], ipix[1], 1] = 1.0

    # Convertir HSV → RGB via OpenCV (float32 [0,1] → uint8)
    hsv_uint8 = (hsv_img * 255).astype(np.uint8)
    rgb_img = cv2.cvtColor(hsv_uint8, cv2.COLOR_HSV2BGR)  # pylint: disable=no-member
    return rgb_img


def segment_and_analyze(
    image,
    scale_mm_per_pixel=1.0,
    min_area_px=10,
    min_axis_px=1.0,
    use_undistortion=False,
    mtx=None,
    dist=None,
    use_homography=False,
    homo_matrix=None,
    conf_threshold=YOLO_CONF_DEFAULT,
):
    """
    Segment and analyze particles in an image using YOLO-OBB.

    Args:
        image (int or float, 2D or 3D array): Image de taille [Ly x Lx (x nchan)].
        scale_mm_per_pixel (float, optional): Échelle mm/pixel. Défaut 1.0.
        min_area_px (int, optional): Aire minimale en pixels. Défaut 10.
        min_axis_px (int, optional): Axe minimal en pixels. Défaut 1.0.
        use_undistortion (bool, optional): Appliquer la correction de distorsion. Défaut False.
        mtx (int or float, 2D array, optional): Matrice caméra. Défaut None.
        dist (int or float, 1D array, optional): Coefficients de distorsion. Défaut None.
        use_homography (bool, optional): Appliquer l'homographie. Défaut False.
        homo_matrix (int or float, 3x3 array, optional): Matrice d'homographie. Défaut None.
        conf_threshold (float, optional): Seuil de confiance YOLO [0.0–1.0]. Défaut 0.25.

    Returns:
        tuple: (masks, overlay_bgr, particles_data, flows, l_min_axis, l_max_axis)
            - masks (int, 2D array): Masques où 0=pas de masque ; 1,2,...=labels.
            - overlay_bgr (uint8, 3D array): Image segmentée colorée (BGR).
            - particles_data (list): Liste des données par particule.
            - flows (None): Non utilisé (conservé pour compatibilité).
            - l_min_axis (list): Axes mineurs en pixels.
            - l_max_axis (list): Axes majeurs en pixels.
    """
    # pylint: disable=no-member, too-many-arguments, too-many-positional-arguments
    # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    print("\n=== DÉBUT SEGMENTATION (YOLO-OBB) ===")
    if image is None:
        raise ValueError("L'image fournie pour la segmentation est nulle.")
    if len(image.shape) != 3 or image.shape[2] != 3:
        raise ValueError(
            f"Format d'image invalide pour la segmentation : {image.shape}"
        )
    if not YOLO_AVAILABLE:
        raise ImportError(
            "Le module ultralytics n'est pas installé. "
            "Veuillez l'installer avec : pip install ultralytics"
        )
    if not os.path.isfile(YOLO_MODEL_PATH):
        raise FileNotFoundError(
            f"Modèle YOLO-OBB introuvable : {YOLO_MODEL_PATH}\n"
            "Vérifiez le chemin dans src/core/segmentation.py"
        )

    # Appliquer les corrections si demandées
    processed_image = image.copy()
    if use_undistortion and mtx is not None and dist is not None:
        processed_image = undistort_img(dist, mtx, processed_image)
    if use_homography and homo_matrix is not None:
        processed_image = homo_and_pixel_conversion(processed_image, homo_matrix)

    # YOLO attend une image BGR ou RGB
    global _YOLO_MODEL  # pylint: disable=global-statement
    if _YOLO_MODEL is None:
        print(f"Chargement initial du modèle YOLO-OBB : {YOLO_MODEL_PATH}")
        try:
            _YOLO_MODEL = YOLO(YOLO_MODEL_PATH)
            print("[OK] Modèle YOLO-OBB chargé en mémoire")
        except Exception as e:
            print(f"[ERREUR] Échec du chargement du modèle YOLO : {e}")
            raise
    else:
        print("[OK] Utilisation du modèle YOLO-OBB pré-chargé")
    model = _YOLO_MODEL

    print(
        f"[DEBUG] Inférence YOLO sur image de taille {processed_image.shape}, conf={conf_threshold}"
    )
    try:
        results = model.predict(processed_image, verbose=False, conf=conf_threshold)
        print("[OK] Inférence YOLO terminée")
    except Exception as e:
        print(f"[ERREUR] Échec de model.predict : {e}")
        raise

    # Extraire les polygones OBB
    result = results[0]
    h, w = processed_image.shape[:2]
    masks = np.zeros((h, w), dtype=np.int32)

    polygons = []
    if result.obb is not None and result.obb.xyxyxyxy is not None:
        obb_data = result.obb.xyxyxyxy.cpu().numpy()  # shape [N, 4, 2]
        for idx, polygon in enumerate(obb_data, start=1):
            pts = polygon.astype(np.int32)  # [4, 2]
            cv2.fillPoly(masks, [pts], color=idx)
            polygons.append(pts)

    num_particles = len(polygons)
    print(f"[OK] Particules détectées par YOLO-OBB : {num_particles}")

    # Générer l'overlay coloré
    rgb_img = cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB)
    overlay_rgb = mask_overlay(rgb_img, masks)
    overlay_bgr = cv2.cvtColor(overlay_rgb, cv2.COLOR_RGB2BGR)

    # Analyse SKIMAGE avec filtrage
    particles_data = []
    l_min_axis = []
    l_max_axis = []

    if SKIMAGE_AVAILABLE and num_particles > 0:
        try:
            label_img = label(masks)
            regions = regionprops(label_img)
            print(f"[INFO] Régions détectées par skimage : {len(regions)}")
            for props in regions:
                minor = props.axis_minor_length
                major = props.axis_major_length
                # Filtrer les particules trop petites ou invalides
                if (
                    minor < min_axis_px
                    or major < min_axis_px
                    or props.area < min_area_px
                ):
                    continue
                # Stocker en pixels
                l_min_axis.append(minor)
                l_max_axis.append(major)
                # Convertir en mm
                minor_mm = minor * scale_mm_per_pixel
                major_mm = major * scale_mm_per_pixel
                particles_data.append(
                    {
                        "area": props.area,
                        "minor_axis_px": minor,
                        "major_axis_px": major,
                        "minor_axis_mm": minor_mm,
                        "major_axis_mm": major_mm,
                        "centroid": props.centroid,
                        "orientation": props.orientation,
                        "perimeter": props.perimeter,
                    }
                )
            print(f"[OK] Particules valides après filtrage : {len(particles_data)}")
            if l_min_axis:
                print(
                    f"[OK] Axe mineur min/max : "
                    f"{np.min(l_min_axis):.1f}/{np.max(l_min_axis):.1f} px"
                )
                print(
                    f"[OK] Axe majeur min/max : "
                    f"{np.min(l_max_axis):.1f}/{np.max(l_max_axis):.1f} px"
                )
            else:
                print("[ATTENTION] Aucune particule valide après filtrage")
        except Exception as e:
            raise RuntimeError(
                f"Erreur lors de l'analyse des particules avec skimage : {e}"
            ) from e

    print("=== FIN SEGMENTATION ===")
    # flows=None : conservé pour compatibilité avec la signature d'origine
    return masks, overlay_bgr, particles_data, None, l_min_axis, l_max_axis
