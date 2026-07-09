# CIMES - Analyse Granulométrique par Vision Artificielle

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.13-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-5.0-green)
![Framework](https://img.shields.io/badge/Framework-Tkinter-orange)
![Gestionnaire](https://img.shields.io/badge/package_manager-uv-purple)

## Présentation

**CIMES** (Captation et Imagerie pour la Mesure et l'Évaluation des Solides) est une application professionnelle de **granulométrie par vision artificielle**. Elle permet d'analyser en temps réel ou de manière différée la distribution de taille des particules à partir d'un flux vidéo (caméra IP/RTSP) ou d'images enregistrées.

Le logiciel utilise des algorithmes de Deep Learning via **YOLO-OBB** pour segmenter les particules avec précision, même dans des conditions de superposition ou de textures complexes.

---

## Fonctionnalités Clés

*   **Flux Vidéo Temps Réel :** Connexion stable aux flux RTSP avec gestion des tampons pour une latence minimale.
*   **Segmentation Avancée :** Intégration de modèles YOLO-OBB (compatible GPU) pour une détection précise des contours.
*   **Analyse Morphologique :** Calcul automatique des axes majeurs/mineurs, aires et périmètres via scikit-image.
*   **Correction Empirique :** Système de correction ADN (empirique) pour ajuster les mesures aux standards physiques.
*   **Visualisation Dynamique :** Courbes granulométriques interactives (passant et distribution) mises à jour en direct.
*   **Gestion de l'Historique :** Rechargement et comparaison de sessions de mesure passées.
*   **Rapports PDF Professionnels :** Génération automatique de rapports complets incluant statistiques, images segmentées et courbes.
*   **Calibration Caméra :** Outils intégrés pour la correction de distorsion et la transformation d'homographie (conversion mm/pixel).
*   **Système de Licence :** Vérification en ligne via Supabase avec cache local pour un fonctionnement hors connexion (grace period configurable).

---

## Architecture du Projet

Le projet suit une structure modulaire pour faciliter la maintenance et l'évolution :

```text
Cimes/
├── main.py              # Point d'entrée de l'application
├── pyproject.toml       # Configuration du projet et dépendances (uv)
├── uv.lock              # Verrouillage des versions (généré par uv)
├── .python-version      # Version Python imposée (3.13)
├── .env                 # Variables d'environnement (SUPABASE_URL, SUPABASE_KEY…)
├── best.pt              # Modèle YOLO-OBB entraîné
├── assets/              # Logos, icônes et fichiers de calibration (.npz)
├── src/
│   ├── core/            # Moteurs de calcul (segmentation, stats, granulométrie)
│   ├── license/         # Vérification et gestion de la licence (Supabase)
│   ├── ui/              # Interface graphique (Tkinter)
│   │   ├── views/       # Vues principales (Mesure, Courbe, Paramètres, etc.)
│   │   ├── widgets/     # Composants UI réutilisables et utilitaires
│   │   └── app_init/    # Logique d'initialisation et variables d'état
│   └── utils/           # Gestion des fichiers, config et logs
└── modules/             # Sous-applications et outils externes
```

---

## Installation

### Prérequis

- **[uv](https://docs.astral.sh/uv/)** — gestionnaire de projet Python
- Python **3.13**
- Une carte graphique NVIDIA
- Pilotes CUDA installés

#### Installer uv

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

```bash
# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

### Procédure

1. **Cloner le dépôt :**
   ```bash
   git clone https://github.com/CimesFrance/Cimes_app.git
   cd Cimes_app
   ```

2. **Synchroniser l'environnement:**
   ```bash
   uv sync
   ```
   > `uv sync` crée automatiquement le virtualenv `.venv`, installe la bonne version de Python (3.13) et toutes les dépendances déclarées dans `pyproject.toml` à partir du fichier de verrou `uv.lock`.

3. **Configurer les variables d'environnement :**

   Créez un fichier `.env` à la racine du projet et renseignez vos clés Supabase :
   ```env
   SUPABASE_URL=https://xxxx.supabase.co
   SUPABASE_KEY=your-anon-or-service-key
   ```

---

## Utilisation

### Lancer l'application

```bash
uv run main.py
```

> `uv run` active automatiquement l'environnement virtuel avant d'exécuter la commande — inutile d'activer manuellement le `.venv`.

### Modules secondaires

```bash
# Outil de calibration caméra
uv run main.py --module-calibration

# Outil de correction des paramètres
uv run main.py --module-correction
```

### Workflow habituel

1. **Configuration :** Allez dans l'onglet **Paramètres** pour configurer l'URL RTSP de votre caméra et les chemins de sauvegarde.
2. **Calibration :** Assurez-vous d'importer vos fichiers de calibration (`.npz`) pour obtenir des mesures précises en millimètres.
3. **Mesure :** Dans l'onglet **Mesure**, lancez le flux et utilisez le mode automatique ou manuel pour capturer et analyser les images.
4. **Rapports :** Une fois les mesures effectuées, générez un rapport PDF depuis la vue des courbes.

---

## Gestion des dépendances avec uv

| Action | Commande |
|---|---|
| Installer / mettre à jour l'env | `uv sync` |
| Ajouter une dépendance | `uv add nom-du-paquet` |
| Supprimer une dépendance | `uv remove nom-du-paquet` |
| Mettre à jour toutes les dépendances | `uv lock --upgrade` puis `uv sync` |
| Lister les paquets installés | `uv pip list` |
| Exécuter un script dans l'env | `uv run script.py` |

Les dépendances sont déclarées dans `pyproject.toml` et verrouillées dans `uv.lock` pour garantir la reproductibilité des builds.

---

## Technologies Utilisées

*   **Interface :** Tkinter (Python Standard Library)
*   **Traitement d'Image :** OpenCV 5, Pillow, Scikit-Image
*   **IA / Segmentation :** YOLO-OBB via Ultralytics (Deep Learning)
*   **Analyse de Données :** Pandas, NumPy, SciPy
*   **Visualisation :** Matplotlib
*   **Reporting :** ReportLab
*   **Base de données / Licences :** Supabase (PostgreSQL)
*   **Gestion du projet :** [uv](https://docs.astral.sh/uv/)

---

## Auteurs & Licence

Développé par l'équipe **Cimes France**.  
Tous droits réservés.
