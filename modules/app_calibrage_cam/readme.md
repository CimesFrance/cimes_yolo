# CIMES Calibration Suite 

Une application Python spécialisée dans l'inspection visuelle et la prise de mesures géométriques précises à partir d'images numériques.

## Fonctionnalités Principales

- **Importation d'image** : Chargement des formats standards (JPG, PNG) et redimensionnement optimisé via filtre de Lanczos.
- **Navigation Interactive** : Zoom à la molette et déplacement fluides par glisser-déposer pour une précision visuelle maximale.
- **Étalonnage sur Référentiel** : Outil permettant de définir la correspondance mathématique entre une ligne tracée sur l'image et sa vraie longueur (en millimètres).
- **Contrôles Multiples** : Création, gestion et masquage à la volée de multiples segments de mesures de couleurs distinctes. Les calculs de distance euclidienne se rafraîchissent en temps réel.

## Architecture du Projet

L'application repose sur un design Model-View clair :
- `core/` : Stockage de la logique métier (`AppState`, `ImageModel`, `PointModel`) fluidifiant la gestion de l'état indépendamment de l'interface.
- `ui/` : Englobe tous les widgets visuels (Canvas d'interaction, gestionnaire de Styles, disposition de la fenêtre principale).
- `utils/` : Utilitaires mathématiques vectoriels (détection de clics sur points) et scripts d'I/O.

## Installation et Lancement

1.  **Prérequis** : Assurez-vous d'avoir Python 3.x installé.
2.  **Installation des dépendances** :
    ```bash
    git clone https://github.com/CimesFrance/App-Calibrage.git
    ```
    ```bash
    pip install -r requirements.txt
    ```
3.  **Lancement** :
    ```bash
    python main.py
    ```
