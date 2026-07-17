"""
Module de vérification de licence locale pour l'application CIMES.

Valide un fichier de licence '.lic' signé avec la clé publique RSA locale.
Fonctionne 100% hors-ligne.
"""

from dataclasses import dataclass
from datetime import date, datetime
import json
import logging
import os
import shutil
from typing import Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key

from .config import PUBLIC_KEY_PEM, get_license_file_path, _find_base_dir
from .machine_fingerprint import compute_fingerprint

logger = logging.getLogger(__name__)


@dataclass
class LicenseStatus:
    """Résultat de la vérification de licence."""
    valid: bool
    client: Optional[str] = None
    expires: Optional[str] = None       # "YYYY-MM-DD"
    days_remaining: Optional[int] = None
    message: str = ""
    license_key: Optional[str] = None  # Conservé pour compatibilité ascendante


def _days_remaining(expires_at: str) -> int:
    """Retourne le nombre de jours restants avant expiration (peut être négatif)."""
    try:
        exp = date.fromisoformat(expires_at)
        return (exp - date.today()).days
    except ValueError:
        return -9999


def check_license() -> LicenseStatus:
    """
    Vérifie la licence de la machine courante localement.

    1. Recherche le fichier .lic.
    2. Valide sa signature RSA à l'aide de la clé publique.
    3. Vérifie que l'empreinte machine courante fait partie de la liste autorisée.
    4. Vérifie la date d'expiration.

    Returns:
        LicenseStatus avec l'état de la licence.
    """
    lic_path = get_license_file_path()
    
    # 1. Recherche du fichier .lic
    if not lic_path or not lic_path.exists():
        return LicenseStatus(
            valid=False,
            message="Aucun fichier de licence (.lic) trouvé.\n"
                    "Veuillez copier votre fichier de licence dans le dossier de l'application."
        )

    try:
        # 2. Charger le JSON de la licence
        with open(lic_path, "r", encoding="utf-8") as f:
            lic_data = json.load(f)
    except Exception as exc:
        return LicenseStatus(
            valid=False,
            message=f"Le fichier de licence est corrompu ou illisible :\n{exc}"
        )

    # Extraction de la signature
    signature_hex = lic_data.pop("signature", None)
    if not signature_hex:
        return LicenseStatus(
            valid=False,
            message="Format de licence invalide : signature manquante."
        )

    # 3. Vérifier la signature RSA
    try:
        # Sérialisation canonique (tri des clés pour correspondre à la signature d'origine)
        canonical_data = json.dumps(lic_data, sort_keys=True)
        signature = bytes.fromhex(signature_hex)
        
        # Charger la clé publique
        public_key = load_pem_public_key(PUBLIC_KEY_PEM)
        
        # Vérification
        public_key.verify(
            signature,
            canonical_data.encode("utf-8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
    except Exception:
        return LicenseStatus(
            valid=False,
            message="Signature de licence invalide. Le fichier a été falsifié."
        )

    # Récupération des informations de licence validées
    client = lic_data.get("client", "Client Inconnu")
    fingerprints = lic_data.get("fingerprints", [])
    max_postes = lic_data.get("max_postes", 1)
    expires_at = lic_data.get("expires_at", "")

    # 4. Vérifier l'empreinte machine
    local_fp = compute_fingerprint()
    if local_fp not in [fp.upper() for fp in fingerprints]:
        return LicenseStatus(
            valid=False,
            client=client,
            message=f"Cette licence n'est pas autorisée pour ce poste.\n"
                    f"Identifiant de cette machine : {local_fp}\n"
                    f"Contactez le support à activation@cimes.fr."
        )

    # 5. Vérifier la date d'expiration
    days = _days_remaining(expires_at)
    if days < 0:
        return LicenseStatus(
            valid=False,
            client=client,
            expires=expires_at,
            days_remaining=days,
            message=f"La licence pour '{client}' a expiré le {expires_at}.\n"
                    f"Contactez le support pour la renouveler."
        )

    # Licence valide !
    return LicenseStatus(
        valid=True,
        client=client,
        expires=expires_at,
        days_remaining=days,
        message=f"Licence active pour '{client}' (expire dans {days} jour(s)).",
        license_key="LICENCE-LOCALE"
    )


def register_license(filepath_or_key: str) -> LicenseStatus:
    """
    Installe un nouveau fichier de licence en le copiant dans le répertoire de base.

    Args:
        filepath_or_key: Soit un chemin d'accès vers un fichier '.lic' existant,
                         soit une clé texte brute (non supportée dans le nouveau système).
    """
    filepath = filepath_or_key.strip()
    
    if not filepath.lower().endswith(".lic"):
        return LicenseStatus(
            valid=False,
            message="Le format de clé texte n'est plus utilisé.\n"
                    "Veuillez sélectionner ou fournir un fichier de licence (.lic)."
        )

    if not os.path.exists(filepath):
        return LicenseStatus(
            valid=False,
            message=f"Fichier de licence introuvable au chemin spécifié : {filepath}"
        )

    try:
        dest_dir = _find_base_dir()
        dest_path = dest_dir / "license.lic"
        
        # Copie du fichier
        shutil.copy2(filepath, dest_path)
        
        # Re-vérifier après installation
        return check_license()
        
    except Exception as exc:
        return LicenseStatus(
            valid=False,
            message=f"Erreur lors de l'installation du fichier de licence :\n{exc}"
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    status = check_license()
    print("--- Vérification Licence Locale ---")
    print(f"Valide : {status.valid}")
    print(f"Client : {status.client}")
    print(f"Expire : {status.expires} ({status.days_remaining} jours restants)")
    print(f"Msg    : {status.message}")
