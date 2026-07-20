# Architecture et Fonctionnement du Système de Licence CIMES

Ce document décrit en détail le mécanisme de protection par licence de l'application CIMES, du calcul de l'empreinte de la machine cliente jusqu'à la validation locale du fichier de licence, en assurant la sécurité via des clés cryptographiques asymétriques (RSA).

## 1. Génération de l'Empreinte Machine (Hardware Fingerprint)
L'objectif est d'identifier de manière unique et stable la machine physique (ou virtuelle) sur laquelle l'application s'exécute, afin d'empêcher le partage abusif d'une même licence entre plusieurs utilisateurs.

**Fichier concerné :** `src/license/machine_fingerprint.py`

Le système récolte trois informations matérielles/système principales :
1. **UUID du Disque Principal (C:)** : Récupéré via `wmic volume` ou `wmic logicaldisk` sous Windows. 
2. **Modèle du Processeur (CPU)** : Récupéré via `wmic cpu get Name`, le module Python `platform`, ou `/proc/cpuinfo` sous Linux.
3. **Nom d'hôte (Hostname)** : Nom réseau de la machine en minuscules.

**Calcul de l'empreinte finale :**
- Ces trois identifiants sont concaténés dans une chaîne brute ayant le format suivant : `CIMES|<disk_uuid>|<cpu_id>|<hostname>`
- Cette chaîne est hachée à l'aide de l'algorithme **SHA-256**.
- Le condensat (hash) obtenu en hexadécimal est converti en majuscules, tronqué pour ne conserver que les 16 premiers caractères, puis formaté en blocs de 4 séparés par des tirets : `XXXX-XXXX-XXXX-XXXX`.

L'utilisateur communique cet identifiant (de 19 caractères au total) à l'éditeur du logiciel pour obtenir sa licence.

## 2. Cryptographie Asymétrique (Clés RSA)
Afin de garantir qu'un fichier de licence ne puisse être créé ou altéré que par l'éditeur du logiciel, le système s'appuie sur une paire de clés RSA de 2048 bits.

**Fichier concerné :** `tools/generate_keypair.py`

- **La Clé Privée (`private_key.pem`)** : Elle est conservée secrètement par l'éditeur. Elle sert à **signer** numériquement les données de la licence lors de sa génération (côté serveur / éditeur).
- **La Clé Publique (`public_key.pem`)** : Elle est intégrée "en dur" dans le code source de l'application cliente (dans `src/license/config.py`). Son unique rôle est de **vérifier** la signature des fichiers de licence.

Cette séparation empêche quiconque de forger une licence valide, même en ayant accès au code source de l'application (qui ne contient que la clé publique).

## 3. Structure du Fichier de Licence (`.lic`)
Le fichier de licence distribué au client est un fichier texte au format JSON contenant les droits accordés ainsi que la signature numérique.

Exemple de contenu d'un fichier `.lic` :
```json
{
  "client": "Nom de l'entreprise",
  "fingerprints": ["ABCD-EFGH-IJKL-MNOP", "1234-5678-90AB-CDEF"],
  "max_postes": 2,
  "expires_at": "2026-12-31",
  "signature": "<signature_hexadecimale_rsa_sha256>"
}
```

## 4. Processus de Validation de la Licence par l'Application
Lors du démarrage de l'application, le module de licence effectue une validation 100% hors-ligne du fichier.

**Fichier concerné :** `src/license/license_checker.py`

Le processus (`check_license()`) se déroule en 5 étapes strictes :

1. **Localisation du fichier :** Le système cherche un fichier avec l'extension `.lic` dans le répertoire principal de l'application. S'il n'est pas présent, la licence est considérée invalide.
2. **Extraction et Préparation des Données :** Le fichier JSON est lu. La clé `signature` est extraite et retirée de la structure. Le reste des données est sérialisé en chaîne de caractères de façon canonique (les clés JSON sont triées alphabétiquement pour garantir que la chaîne sera strictement identique à celle signée par l'éditeur).
3. **Vérification de la Signature (RSA) :** 
   - L'application charge sa Clé Publique RSA embarquée (`config.py`).
   - Elle vérifie la signature extraite par rapport aux données canoniques, en utilisant l'algorithme de padding **PSS** et le hachage **SHA-256**.
   - *Si la vérification échoue, cela signifie que le fichier a été modifié manuellement ou corrompu. La licence est rejetée.*
4. **Vérification de l'Empreinte Machine :** 
   - L'application calcule sa propre empreinte (via `compute_fingerprint()`).
   - Elle vérifie que cette empreinte figure dans la liste `fingerprints` du fichier de licence.
   - *Si elle n'y est pas, la licence n'est pas prévue pour ce poste physique.*
5. **Vérification de l'Expiration :**
   - La date du jour est comparée à la date `expires_at` définie dans le fichier.
   - *Si la date limite est dépassée, la licence est rejetée avec un message d'expiration.*

Si toutes ces étapes sont franchies avec succès, la fonction retourne un état valide et l'application est autorisée à se lancer. Ce mécanisme garantit robustesse (RSA-2048), fiabilité (hors-ligne) et contrôle strict du déploiement physique (Fingerprinting matériel).
