"""
Configuration du module de licence CIMES.

Définit la clé publique RSA pour la vérification des fichiers de licence (.lic)
et résout les chemins d'accès aux fichiers.
"""

import os
from pathlib import Path
import sys

# Clé publique RSA pour vérifier la signature des licences
PUBLIC_KEY_PEM: bytes = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvuXSnEwilS2KnfzcqVLc
lOseCSJ9Oz1pir/TWNdb0UvETNR4YcfNRt4/v3m2R/8M1KEL/979RDqcLdwWgF1x
dvlqh+QQSrxFWjJJMDtvS0In/w9FWv9JTG78CfjEFzSSyOccuQhjDebrKsUE2K/Y
RIX5CZT+Cm07TboSA0KnxI1trgAy0+vFUeRTvfHRMSPov+W+ItusRPRJDuzEXswP
kQSosM3d+bw9fN+szhpJjUrJp2nQnQ0Inw9Hf5bqPnpYMf/LIanAA8gW2x5HlhAr
QbBySL6nZ9WFKPga/OytBjprspQN3AjImI6X99WOunTo7Ro3ssIO7WjKkHdOyrIx
0QIDAQAB
-----END PUBLIC KEY-----"""


def _find_base_dir() -> Path:
    """
    Retourne le dossier de base de l'application :
    - Dossier de l'exécutable si frozen.
    - Racine du projet en mode développement.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


_base = _find_base_dir()

# Cache de la licence
LICENSE_CACHE_PATH: Path = _base / ".license_cache"


def get_license_file_path() -> Path | None:
    """
    Cherche un fichier de licence (.lic) dans le dossier de base de l'application.
    Retourne le chemin complet du premier fichier trouvé, ou None.
    """
    try:
        lic_files = list(_base.glob("*.lic"))
        if lic_files:
            return lic_files[0]
    except Exception:
        pass
    return None