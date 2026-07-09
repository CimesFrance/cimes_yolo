"""
Configuration du module licence.

Les valeurs sont lues depuis les variables d'environnement ou un fichier .env
situé à la racine du projet.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cherche le .env à la racine du projet
_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=_env_path, override=False)

# URL et clé anon Supabase
SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "")

# Clé secrète locale pour signer le cache
API_SECRET_KEY: str = os.environ.get("API_SECRET_KEY", "")
if not API_SECRET_KEY:
    raise RuntimeError(
        "API_SECRET_KEY manquante dans le fichier .env.\n"
        "Générez une valeur avec :\n"
        "  python -c \"import secrets; print(secrets.token_hex(32))\"\n"
        "puis ajoutez-la dans votre .env : API_SECRET_KEY=<valeur>"
    )

# Grace period hors-ligne en jours
# Si Supabase est injoignable, le cache local est accepté pendant N jours
OFFLINE_GRACE_DAYS: int = int(os.environ.get("OFFLINE_GRACE_DAYS", "7"))

# Chemin du fichier de cache local
_base = Path(os.environ.get("APP_BASE_DIR", Path(__file__).resolve().parents[2]))
LICENSE_CACHE_PATH: Path = _base / ".license_cache"
