"""
Module de vérification de licence pour l'application Cimes.

Appel Supabase direct.

Utilisation :
    from src.license import check_license, LicenseStatus

    status = check_license()
    if not status.valid:
        # Bloquer l'accès à l'application
        print(status.message)
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from getmac import get_mac_address as gma
from supabase import create_client, Client

from .config import (
    API_SECRET_KEY,
    LICENSE_CACHE_PATH,
    SUPABASE_URL,
    SUPABASE_KEY,
    OFFLINE_GRACE_DAYS,
)

logger = logging.getLogger(__name__)

# Client Supabase
_supabase: Optional[Client] = None

def _get_client() -> Client:
    """Retourne le client Supabase avec un timeout de 8 s pour éviter le freeze au démarrage."""
    global _supabase
    if _supabase is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError(
                "Variables d'environnement SUPABASE_URL et SUPABASE_KEY manquantes."
            )
        try:
            from supabase.lib.client_options import ClientOptions  # pylint: disable=import-outside-toplevel
            _supabase = create_client(
                SUPABASE_URL,
                SUPABASE_KEY,
                options=ClientOptions(postgrest_client_timeout=8),
            )
        except (ImportError, TypeError, AttributeError):
            # Fallback si la version de supabase-py ne supporte pas ClientOptions
            _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase


# Structures de données
@dataclass
class LicenseStatus:
    """Résultat de la vérification de licence."""
    valid: bool
    license_key: Optional[str] = None
    expires: Optional[str] = None       # "YYYY-MM-DD"
    days_remaining: Optional[int] = None
    message: str = ""
    from_cache: bool = False            # True si le résultat vient du cache local



# Helpers — Adresse MAC
def get_mac_address() -> str:
    """Retourne l'adresse MAC de la machine en minuscules avec ':' comme séparateur."""
    mac = gma() or ""
    return mac.strip().lower().replace("-", ":").replace(".", ":")


def _mask_mac(mac: str) -> str:
    """Masque les 3 derniers octets de la MAC pour les logs (ex: aa:bb:cc:**:**:**)."""
    parts = mac.split(":")
    if len(parts) == 6:
        return ":".join(parts[:3] + ["**", "**", "**"])
    return "**:**:**:**:**:**"


# Helpers — Cache local
def _cache_signature(data: dict) -> str:
    """Signature HMAC-lite pour détecter toute falsification du cache.

    La MAC de la machine est incluse dans le secret : un cache forgé sur une
    autre machine ne sera jamais accepté ici.
    """
    mac = get_mac_address()
    payload = json.dumps(data, sort_keys=True)
    secret = f"{API_SECRET_KEY}:{mac}"
    return hashlib.sha256(secret.encode() + payload.encode()).hexdigest()


def _save_cache(status: LicenseStatus) -> None:
    """Sauvegarde le résultat de vérification dans le cache local."""
    try:
        data = {
            "valid": status.valid,
            "license_key": status.license_key,
            "expires": status.expires,
            "days_remaining": status.days_remaining,
            "message": status.message,
            "cached_at": datetime.now().isoformat(),
        }
        data["signature"] = _cache_signature(data)
        LICENSE_CACHE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Impossible d'écrire le cache licence : %s", exc)


def _load_cache() -> Optional[LicenseStatus]:
    """
    Charge le cache local si :
    - Le fichier existe
    - La signature est valide
    - Le cache date de moins de OFFLINE_GRACE_DAYS jours
    """
    if not LICENSE_CACHE_PATH.exists():
        return None
    try:
        data = json.loads(LICENSE_CACHE_PATH.read_text(encoding="utf-8"))
        signature = data.pop("signature", "")
        if _cache_signature(data) != signature:
            logger.warning("Signature du cache licence invalide — cache ignoré.")
            return None

        cached_at = datetime.fromisoformat(data["cached_at"])
        if datetime.now() - cached_at > timedelta(days=OFFLINE_GRACE_DAYS):
            logger.warning("Cache licence expiré (plus de %d jours).", OFFLINE_GRACE_DAYS)
            return None

        # Fix #4 — Vérifier que la licence n'a pas expiré même en mode hors-ligne
        expires_str = data.get("expires")
        cache_valid = bool(data.get("valid"))
        if cache_valid and expires_str:
            try:
                cache_valid = date.fromisoformat(expires_str) >= date.today()
                if not cache_valid:
                    logger.warning("Licence expirée détectée dans le cache hors-ligne.")
            except ValueError:
                logger.warning("Format de date invalide dans le cache : %s", expires_str)
                cache_valid = False

        return LicenseStatus(
            valid=cache_valid,
            license_key=data.get("license_key"),
            expires=expires_str,
            days_remaining=data.get("days_remaining"),
            message=f"[Hors-ligne] {data.get('message', '')}",
            from_cache=True,
        )
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Impossible de lire le cache licence : %s", exc)
        return None


# Helpers — Calcul expiration
def _days_remaining(expires_at: str) -> int:
    """Retourne le nombre de jours restants avant expiration (peut être négatif)."""
    exp = date.fromisoformat(expires_at)
    return (exp - date.today()).days

# Vérification principale
def check_license() -> LicenseStatus:
    """
    Vérifie la licence de la machine courante directement via Supabase.

    1. Récupère l'adresse MAC locale.
    2. Interroge la table 'licenses' sur Supabase (SELECT direct).
    3. Si Supabase répond → sauvegarde le résultat en cache et le retourne.
    4. Si Supabase est injoignable → tente d'utiliser le cache local
       (grace period de OFFLINE_GRACE_DAYS jours).

    Returns:
        LicenseStatus avec les informations de la licence.
    """
    mac = get_mac_address()
    logger.info("Vérification de licence pour MAC : %s", _mask_mac(mac))

    if not mac:
        return LicenseStatus(
            valid=False,
            message="Impossible de récupérer l'adresse MAC de cette machine."
        )

    # Tentative d'appel direct à Supabase
    try:
        client = _get_client()
        response = client.rpc("check_license_rpc", {"p_mac": mac}).execute()

        if not response.data:
            status = LicenseStatus(
                valid=False,
                license_key=None,
                expires=None,
                days_remaining=None,
                message="Adresse MAC non reconnue dans la base de données.",
            )
            return status

        row = response.data[0]
        expires_at: str = row["expires_at"]
        days = _days_remaining(expires_at)

        if days < 0:
            status = LicenseStatus(
                valid=False,
                license_key=row["license_key"],
                expires=expires_at,
                days_remaining=days,
                message=f"Licence expirée depuis {abs(days)} jour(s).",
            )
            return status

        status = LicenseStatus(
            valid=True,
            license_key=row["license_key"],
            expires=expires_at,
            days_remaining=days,
            message=f"Licence valide — expire dans {days} jour(s).",
        )

        # Sauvegarde du dernier résultat valide en cache
        _save_cache(status)
        return status

    except RuntimeError as exc:
        # Variables d'environnement manquantes
        logger.error("Configuration Supabase invalide : %s", exc)
        return LicenseStatus(valid=False, message=str(exc))
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Supabase injoignable — tentative sur cache local. Erreur : %s", exc)

    # Fallback : cache local
    cached = _load_cache()
    if cached:
        logger.info("Cache local utilisé (grace period %d jours).", OFFLINE_GRACE_DAYS)
        return cached

    return LicenseStatus(
        valid=False,
        message=(
            "Connexion impossible. "
            "Vérifiez votre connexion réseau."
        )
    )


def register_license(license_key: str) -> LicenseStatus:
    """
    Associe l'adresse MAC courante à une clé de licence existante dans Supabase.

    1. Récupère l'adresse MAC locale.
    2. Interroge Supabase pour vérifier si la clé de licence existe.
    3. Si la clé existe :
       - Si elle est déjà associée à une autre adresse MAC -> Erreur.
       - Si elle a expiré -> Erreur.
       - Sinon -> Associe l'adresse MAC (update 'mac_address') et met à jour le cache local.
    """
    mac = get_mac_address()
    if not mac:
        return LicenseStatus(
            valid=False,
            message="Impossible de récupérer l'adresse MAC de cette machine."
        )

    try:
        client = _get_client()
        response = client.rpc(
            "register_license_rpc",
            {"p_mac": mac, "p_key": license_key.strip()},
        ).execute()

        if not response.data:
            return LicenseStatus(
                valid=False,
                message="Erreur lors de l'association de la clé de licence."
            )

        row = response.data[0]

        if not row.get("success"):
            return LicenseStatus(
                valid=False,
                license_key=row.get("license_key"),
                expires=row.get("expires_at"),
                message=row.get("error_message") or "Clé de licence invalide ou inexistante.",
            )

        expires_at = row["expires_at"]
        days = _days_remaining(expires_at)

        status = LicenseStatus(
            valid=True,
            license_key=row["license_key"],
            expires=expires_at,
            days_remaining=days,
            message=f"Licence activée avec succès ! Expire dans {days} jour(s).",
        )

        # Sauvegarder dans le cache local
        _save_cache(status)
        return status

    except Exception as exc:
        logger.error("Erreur lors de l'enregistrement de la licence : %s", exc)
        return LicenseStatus(
            valid=False,
            message=f"Erreur de connexion à la base de données : {exc}"
        )

# Test rapide en ligne de commande
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    result = check_license()
    print("\n=== Résultat de la vérification de licence ===")
    print(f"  Valide         : {result.valid}")
    print(f"  Clé            : {result.license_key or 'N/A'}")
    print(f"  Expiration     : {result.expires or 'N/A'}")
    print(f"  Jours restants : {result.days_remaining if result.days_remaining is not None else 'N/A'}")
    print(f"  Message        : {result.message}")
    print(f"  Depuis cache   : {result.from_cache}")
