"""
Script de génération d'une paire de clés RSA (2048 bits) pour le système de licence CIMES.

Génère deux fichiers :
  - private_key.pem : Clé privée à conserver précieusement et secrètement.
  - public_key.pem  : Clé publique à distribuer dans le code du logiciel.
"""

import os
import sys

try:
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
except ImportError:
    print("[ERREUR] Le paquet 'cryptography' est requis.")
    print("         Installez-le avec : pip install cryptography")
    sys.exit(1)


def generate_keys():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    keys_dir = os.path.join(project_root, "keys")
    os.makedirs(keys_dir, exist_ok=True)

    private_key_path = os.path.join(keys_dir, "private_key.pem")
    public_key_path = os.path.join(keys_dir, "public_key.pem")

    # Si les clés existent déjà, on ne les écrase pas par accident
    if os.path.exists(private_key_path) or os.path.exists(public_key_path):
        print("[INFO] Une paire de clés existe déjà dans le dossier 'keys/'.")
        print("       Supprimez-les manuellement si vous souhaitez en générer de nouvelles.")
        return

    print("[INFO] Génération de la paire de clés RSA 2048 bits...")
    
    # 1. Générer la clé privée
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    # 2. Sauvegarder la clé privée au format PEM
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()  # Non chiffrée pour simplifier le script CLI interne
    )

    with open(private_key_path, "wb") as f:
        f.write(pem_private)

    # 3. Extraire et sauvegarder la clé publique au format PEM
    public_key = private_key.public_key()
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    with open(public_key_path, "wb") as f:
        f.write(pem_public)

    print()
    print("=" * 60)
    print("Paire de clés générée avec succès !")
    print(f"  Clé privée (CONFIDENTIELLE) : {private_key_path}")
    print(f"  Clé publique (À EMBARQUER)  : {public_key_path}")
    print()
    print(" ATTENTION : Ne committez JAMAIS la clé privée sur Git !")
    print("=" * 60)


if __name__ == "__main__":
    generate_keys()
