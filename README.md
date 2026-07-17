# CIMES - Analyse Granulométrique par Vision Artificielle

![Version](https://img.shields.io/badge/version-1.1.0-blue)
![Python](https://img.shields.io/badge/python-3.13-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-5.0-green)
![Framework](https://img.shields.io/badge/Framework-Tkinter-orange)
![Gestionnaire](https://img.shields.io/badge/package_manager-uv-purple)

## Présentation

**CIMES** est une application professionnelle de **granulométrie par vision artificielle**. Elle permet d'analyser en temps réel ou de manière différée la distribution de taille des solides (comme le ballast) à partir d'un flux vidéo (caméra IP/RTSP) ou d'images enregistrées.

Le logiciel utilise des algorithmes de Deep Learning via **YOLO-OBB** pour segmenter les particules avec précision, même dans des conditions de superposition ou de textures complexes.

---

## Fonctionnalités Clés

*   **Flux Vidéo Temps Réel :** Connexion stable aux flux RTSP avec gestion des tampons et threads asynchrones pour une latence minimale.
*   **Segmentation Avancée :** Intégration de modèles YOLO-OBB (compatible GPU) pour une détection précise des contours.
*   **Analyse Morphologique :** Calcul automatique des axes majeurs/mineurs, aires et périmètres via scikit-image.
*   **Correction Empirique :** Système de correction empirique (courbe ADN) pour adapter les mesures aux standards physiques.
*   **Visualisation Dynamique :** Courbes granulométriques interactives (passant et distribution) mises à jour en direct.
*   **Gestion de l'Historique :** Rechargement et comparaison de sessions de mesure passées.
*   **Rapports PDF Professionnels :** Génération automatique de rapports complets incluant statistiques, images segmentées et courbes de répartition.
*   **Calibration Caméra :** Correction dynamique de la distorsion de lentille et transformation d'homographie (conversion mm/pixel).
*   **Système de Licence Hors-ligne :** Vérification cryptographique RSA locale à l'aide d'empreintes matérielles stables, parfaitement adaptée aux environnements industriels sans connexion Internet.

---

## Architecture du Projet

Le projet suit une structure modulaire claire :

```text
Cimes/
├── main.py              # Point d'entrée de l'application principale
├── pyproject.toml       # Configuration du projet et dépendances (uv)
├── uv.lock              # Verrouillage des versions (généré par uv)
├── .python-version      # Version Python imposée (3.13)
├── best.pt              # Modèle YOLO-OBB entraîné (chargement unique en cache)
├── assets/              # Logos, icônes et fichiers de calibration (.npz)
├── keys/                # Clés de sécurité (public_key.pem pour vérification)
├── src/
│   ├── core/            # Moteurs de calcul (segmentation, stats, calibration)
│   ├── license/         # Gestion de la licence (RSA, empreintes, dialogue Tkinter)
│   ├── ui/              # Interface graphique (Tkinter)
│   │   ├── views/       # Vues principales (Mesure, Courbe, Paramètres, etc.)
│   │   ├── widgets/     # Composants UI réutilisables et utilitaires
│   │   └── app_init/    # Logique d'initialisation et variables d'état
│   └── utils/           # Gestion des fichiers, config, mail SMTP et logs
├── tools/               # Scripts internes (génération de clé, signature, machine_id)
└── modules/             # Sous-applications et outils externes
```

---

## Installation

### Prérequis

- **[uv](https://docs.astral.sh/uv/)** — gestionnaire de projet Python ultra-rapide
- Python **3.13**
- Une carte graphique NVIDIA avec pilotes CUDA installés (recommandé pour YOLO)

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

### Procédure de déploiement

1. **Cloner le dépôt :**
   ```bash
   git clone https://github.com/CimesFrance/cimes_yolo.git
   cd cimes_yolo
   ```

2. **Synchroniser l'environnement et installer les dépendances :**
   ```bash
   uv sync
   ```
   > `uv sync` crée automatiquement le virtualenv `.venv`, installe la bonne version de Python (3.13) et toutes les dépendances verrouillées dans `uv.lock`.

---

## Système de Licence

Le logiciel utilise un système de licence **100% hors-ligne** fondé sur de la cryptographie asymétrique (RSA).

### 1. Obtenir l'empreinte machine (Côté Client)
Pour activer CIMES, le client doit générer et envoyer son empreinte matérielle unique.
* Lancez l'outil d'identification :
  ```bash
  uv run python tools/machine_id.py
  ```
  *(Ou utilisez l'exécutable compilé `dist/machine_id.exe` fourni avec le programme d'installation).*
* Copiez l'identifiant (format `XXXX-XXXX-XXXX-XXXX`) et envoyez-le à `activation@cimes.fr`.

### 2. Générer une licence (Côté CimesFrance)
* Générer en amont la paire de clés RSA (à faire une seule fois) :
  ```bash
  uv run python tools/generate_keypair.py
  ```
  *(Génère `keys/private_key.pem` à conserver secrètement, et `keys/public_key.pem` à embarquer dans le projet).*
* Créer le fichier de licence `.lic` signé pour le client :
  ```bash
  uv run python tools/issue_license.py --client "Nom Entreprise" --fingerprints "EMPREINTE-CLIENT-1,EMPREINTE-CLIENT-2" --max-postes 2 --expires 2027-12-31 --output client.lic
  ```
* Transmettez le fichier `client.lic` au client.

### 3. Activer le logiciel
Au premier démarrage, CIMES affichera un écran d'activation. Le client clique sur **"Importer un fichier de licence (.lic)"** et sélectionne son fichier. La licence est enregistrée localement et validée immédiatement.

---

## Utilisation

### Lancer l'application

```bash
uv run main.py
```

### Outils et Modules secondaires

```bash
# Outil de calibration caméra
uv run main.py --module-calibration

# Outil d'édition des paramètres de correction
uv run main.py --module-correction

# Compiler l'exécutable machine_id autonome
python tools/build_machine_id.py
```

---

## Technologies Utilisées

*   **Interface :** Tkinter (Python Standard Library)
*   **Traitement d'Image :** OpenCV 5, Pillow, Scikit-Image
*   **IA / Segmentation :** YOLO-OBB via Ultralytics (Deep Learning)
*   **Analyse de Données :** Pandas, NumPy, SciPy
*   **Visualisation :** Matplotlib
*   **Reporting :** ReportLab
*   **Cryptographie :** PyCa/Cryptography (RSA)
*   **Gestion du projet :** [uv](https://docs.astral.sh/uv/)

---

## Auteurs & Licence

Développé par l'équipe **Cimes France**.  
Tous droits réservés.
