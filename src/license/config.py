"""
Configuration du module licence.

SUPABASE_URL / SUPABASE_KEY ont une valeur par défaut intégrée au code :
la clé anon Supabase est conçue par Supabase pour être publique (la vraie
protection vient des policies RLS + fonctions RPC côté serveur), donc aucun
fichier .env n'est nécessaire pour un déploiement client standard.

Un .env optionnel reste supporté (utile en dev/tests pour pointer vers un
autre projet Supabase), mais n'est plus jamais obligatoire.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def _find_env_path() -> Path:
    """
    Résout le chemin du fichier .env optionnel selon le contexte d'exécution:
    - Exécutable PyInstaller: dossier contenant l'exe (sys.executable)
    - Développement : racine du projet (parents[2] de config.py)
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / ".env"
    return Path(__file__).resolve().parents[2] / ".env"


_env_path = _find_env_path()
load_dotenv(dotenv_path=_env_path, override=False)  # no-op silencieux si le fichier n'existe pas

# URL et clé anon Supabase — valeurs par défaut intégrées, surchargeables via .env si besoin
SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "https://ugvlqnthbdxihixgvzwk.supabase.co")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "sb_publishable_42ipxNOjIX0avaCtkush4A_VF_YSQqH")

# Grace period hors-ligne en jours
# Si Supabase est injoignable, le cache local est accepté pendant N jours
OFFLINE_GRACE_DAYS: int = int(os.environ.get("OFFLINE_GRACE_DAYS", "7"))


def _find_base_dir() -> Path:
    """Retourne le dossier de base pour le cache : dossier de l'exe ou racine projet."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


_base = Path(os.environ.get("APP_BASE_DIR", "")) or _find_base_dir()
LICENSE_CACHE_PATH: Path = _base / ".license_cache"