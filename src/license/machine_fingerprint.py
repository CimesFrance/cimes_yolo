"""
Module de génération d'empreinte machine pour le système de licence CIMES.

L'empreinte est construite à partir de 3 sources matérielles stables :
  1. UUID du volume disque principal (wmic ou PowerShell)
  2. Modèle du processeur CPU
  3. Hostname de la machine

Résultat : SHA-256 tronqué et formaté en XXXX-XXXX-XXXX-XXXX
"""

import hashlib
import platform
import socket
import subprocess
import sys


def _get_disk_uuid() -> str:
    """
    Récupère l'UUID du volume C: via wmic.
    Retourne une chaîne vide en cas d'échec.
    """
    # Tentative 1 : wmic volume
    try:
        result = subprocess.run(
            ["wmic", "volume", "get", "DeviceID,DriveLetter"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        for line in result.stdout.splitlines():
            line = line.strip()
            if "C:" in line and "{" in line:
                start = line.find("{")
                end = line.find("}")
                if start != -1 and end != -1:
                    return line[start : end + 1]
        # Fallback : premier GUID trouvé
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("\\\\?\\Volume{"):
                start = line.find("{")
                end = line.find("}")
                if start != -1 and end != -1:
                    return line[start : end + 1]
    except Exception:  # pylint: disable=broad-except
        pass

    # Tentative 2 : VolumeSerialNumber via wmic logicaldisk
    try:
        result = subprocess.run(
            [
                "wmic",
                "logicaldisk",
                "where",
                "DeviceID='C:'",
                "get",
                "VolumeSerialNumber",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        for line in result.stdout.splitlines():
            line = line.strip()
            if line and line != "VolumeSerialNumber":
                return line
    except Exception:  # pylint: disable=broad-except
        pass

    return ""


def _get_cpu_id() -> str:
    """
    Récupère le nom/modèle du processeur.
    Compatible Windows / Linux / macOS.
    """
    # Windows via wmic
    if sys.platform == "win32":
        try:
            result = subprocess.run(
                ["wmic", "cpu", "get", "Name"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            for line in result.stdout.splitlines():
                line = line.strip()
                if line and line != "Name":
                    return line
        except Exception:  # pylint: disable=broad-except
            pass

    # Fallback universel via platform
    cpu = platform.processor()
    if cpu:
        return cpu

    # Fallback Linux : /proc/cpuinfo
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":")[1].strip()
    except Exception:  # pylint: disable=broad-except
        pass

    return "unknown_cpu"


def _get_hostname() -> str:
    """Retourne le hostname de la machine normalisé en minuscules."""
    return socket.gethostname().strip().lower()


def compute_fingerprint() -> str:
    """
    Calcule l'empreinte unique de la machine.

    Returns:
        str: Empreinte au format 'XXXX-XXXX-XXXX-XXXX'; de 19 caractères.
    """
    disk_uuid = _get_disk_uuid()
    cpu_id = _get_cpu_id()
    hostname = _get_hostname()

    raw = f"CIMES|{disk_uuid}|{cpu_id}|{hostname}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()

    return f"{digest[0:4]}-{digest[4:8]}-{digest[8:12]}-{digest[12:16]}"


def get_fingerprint_details() -> dict:
    """
    Retourne les composants de l'empreinte pour affichage/débogage.

    Returns:
        dict avec les clés : fingerprint, disk_uuid, cpu_id, hostname
    """
    disk_uuid = _get_disk_uuid()
    cpu_id = _get_cpu_id()
    hostname = _get_hostname()

    raw = f"CIMES|{disk_uuid}|{cpu_id}|{hostname}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()
    fp = f"{digest[0:4]}-{digest[4:8]}-{digest[8:12]}-{digest[12:16]}"

    return {
        "fingerprint": fp,
        "disk_uuid": disk_uuid or "(non trouvé)",
        "cpu_id": cpu_id,
        "hostname": hostname,
    }


if __name__ == "__main__":
    details = get_fingerprint_details()
    print("=== Empreinte Machine CIMES ===")
    print(f"  Empreinte  : {details['fingerprint']}")
    print(f"  Disque     : {details['disk_uuid']}")
    print(f"  CPU        : {details['cpu_id']}")
    print(f"  Hostname   : {details['hostname']}")
