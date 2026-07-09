"""Module de vérification de licence pour l'application Cimes."""
from .license_checker import check_license, register_license, LicenseStatus, get_mac_address

__all__ = ["check_license", "register_license", "LicenseStatus", "get_mac_address"]
