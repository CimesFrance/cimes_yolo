"""
Script de compilation de machine_id.py en machine_id.exe via PyInstaller.

Usage :
    python tools/build_machine_id.py

Prérequis :
    pip install pyinstaller

Le fichier machine_id.exe sera généré dans : dist/machine_id.exe
"""

import os
import subprocess
import sys


def build() -> None:
    # Répertoire racine du projet (parent du dossier tools/)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tools_dir = os.path.join(project_root, "tools")
    src_dir = os.path.join(project_root, "src")
    assets_dir = os.path.join(project_root, "assets")
    script = os.path.join(tools_dir, "machine_id.py")

    # Vérifie que PyInstaller est disponible
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("[ERREUR] PyInstaller n'est pas installé.")
        print("         Installez-le avec : pip install pyinstaller")
        sys.exit(1)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",  # Un seul .exe autonome
        "--windowed",  # Pas de console en arrière-plan
        "--name",
        "machine_id",  # Nom du fichier de sortie
        "--distpath",
        os.path.join(project_root, "dist"),
        "--workpath",
        os.path.join(project_root, "build"),
        "--specpath",
        os.path.join(project_root, "build"),
        # Inclure uniquement le dossier src/license/
        "--paths",
        os.path.join(src_dir, "license"),
        # Exclusions massives pour éviter de packager l'environnement lourd de l'application
        "--exclude-module",
        "cv2",
        "--exclude-module",
        "numpy",
        "--exclude-module",
        "pandas",
        "--exclude-module",
        "matplotlib",
        "--exclude-module",
        "numba",
        "--exclude-module",
        "PySide6",
        "--exclude-module",
        "PIL",
        "--exclude-module",
        "scipy",
        "--exclude-module",
        "sympy",
        "--exclude-module",
        "h5py",
        "--exclude-module",
        "sqlalchemy",
        "--exclude-module",
        "sqlite3",
        "--exclude-module",
        "openpyxl",
        "--exclude-module",
        "weasyprint",
        "--exclude-module",
        "reportlab",
    ]

    # Ajout de l'icône officielle
    icon_path = os.path.join(
        project_root,
        "modules",
        "app_change_corr_params",
        "assets",
        "icons",
        "cimes-logo.ico",
    )
    if os.path.exists(icon_path):
        cmd += ["--icon", icon_path]
        # Embarquer aussi l'icône comme donnée pour qu'elle soit accessible au runtime (barre des tâches)
        cmd += ["--add-data", f"{icon_path};."]
        print(f"[INFO] Icône officielle trouvée et embarquée : {icon_path}")
    else:
        print(
            f"[AVERTISSEMENT] Icône introuvable à {icon_path} — compilation sans icône."
        )

    cmd.append(script)

    print(f"[INFO] Compilation de : {script}")
    print(f"[INFO] Commande : {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd, cwd=project_root)

    if result.returncode == 0:
        exe_path = os.path.join(project_root, "dist", "machine_id.exe")
        print()
        print("=" * 55)
        print(f"Compilation réussie !")
        print(f"   Fichier généré : {exe_path}")
        print()
        print("   → Distribuez ce fichier avec votre installeur CIMES.")
        print("   → Le client le lance AVANT de recevoir sa licence.")
        print("=" * 55)
    else:
        print()
        print("[ERREUR] La compilation a échoué. Consultez la sortie ci-dessus.")
        sys.exit(1)


if __name__ == "__main__":
    build()
