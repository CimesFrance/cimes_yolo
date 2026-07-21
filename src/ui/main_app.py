"""Application principale CIMES — coordinateur des vues."""

import os
import warnings
import zipfile
import threading
from datetime import datetime

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

warnings.filterwarnings("ignore")

from src.ui.widgets.ui_utils import (  # pylint: disable=wrong-import-position
    COLOR_BG_DARK,
    COLOR_ACCENT,
    COLOR_TEXT_LIGHT,
    COLOR_FRAME_BG,
    LOGO_PATH,
    configure_styles,
)
from src.ui.app_init.variables import initialize_variables  # pylint: disable=wrong-import-position
from src.ui.app_init.camera_controller import CameraController  # pylint: disable=wrong-import-position
from src.ui.views.measure_view import MeasureView  # pylint: disable=wrong-import-position
from src.ui.views.curve_view import CurveView  # pylint: disable=wrong-import-position
from src.ui.views.reload_view import ReloadView  # pylint: disable=wrong-import-position
from src.ui.views.param_view import ParamView  # pylint: disable=wrong-import-position
from src.utils.file_manager import (  # pylint: disable=wrong-import-position
    load_calibration_files,
    ensure_results_directory,
    load_correction_parameters,
    get_project_root,
)
from src.utils.config_manager import (  # pylint: disable=wrong-import-position
    load_sensor_settings,
    load_report_configuration,
    load_calibration_settings,
)
from src.utils.report_generator import generate_pdf_report  # pylint: disable=wrong-import-position
from src.utils.email_sender import envoyer_email_rapport  # pylint: disable=wrong-import-position


class CimesApp(CameraController, tk.Tk):  # pylint: disable=too-many-instance-attributes
    """Application principale CIMES héritant de CameraController et tk.Tk."""

    def __init__(self):
        CameraController.__init__(self)
        tk.Tk.__init__(self)
        self.title("Cimes")
        icon_path = os.path.join(
            get_project_root(),
            "modules",
            "app_change_corr_params",
            "assets",
            "icons",
            "cimes-logo.ico",
        )
        try:
            self.iconbitmap(icon_path, default=icon_path)
        except tk.TclError:
            pass
        self.geometry("1600x1000")
        self.minsize(1400, 800)
        self.configure(bg=COLOR_FRAME_BG)
        configure_styles(self)
        initialize_variables(self)
        self._last_correction_mtime = 0
        # Attributs initialisés dans les méthodes de construction
        self.logo_header = None
        self.nav_container = None
        self.nav_buttons = {}
        self.change_corr_btn = None
        self.current_view_key = None
        self.mtx = None
        self.dist = None
        self.calib_path = None
        self._initialize_views()
        self._setup_initial_configuration()
        self._start_auto_updates()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    # ── Fermeture
    def _on_closing(self):
        """Gère la fermeture de l'application."""
        if (
            self.correction_process is not None
            and self.correction_process.poll() is None
        ):
            try:
                self.correction_process.terminate()
            except OSError as e:
                print(f"[LOG] Échec terminaison correction_process : {e}")
        if hasattr(self, "param_view") and hasattr(
            self.param_view, "calibration_process"
        ):
            if self.param_view.calibration_process.poll() is None:
                try:
                    self.param_view.calibration_process.terminate()
                except OSError as e:
                    print(f"[LOG] Échec terminaison calibration_process : {e}")
        self.destroy()

    # ── Construction des vues
    def _initialize_views(self):
        """Initialise les vues de l'application."""
        self._create_header()
        self.content_frame = tk.Frame(self, bg=COLOR_FRAME_BG)
        self.content_frame.pack(side="top", fill="both", expand=True)
        self.measure_view = MeasureView(self.content_frame, self)
        self.curve_view = CurveView(self.content_frame, self)
        self.reload_view = ReloadView(self.content_frame, self)
        self.param_view = ParamView(self.content_frame, self)
        self.show_measure_view()
        self._set_active_nav("measure")

    def _create_header(self):
        """Crée l'en-tête de l'application."""
        header_height = 90
        header = tk.Frame(self, bg=COLOR_BG_DARK, height=header_height)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)
        logo_container = tk.Frame(header, bg=COLOR_BG_DARK)
        logo_container.pack(side="left", padx=30, fill="y")
        try:
            img = Image.open(LOGO_PATH)
            display_height = 70
            ratio = img.width / img.height if img.height > 0 else 1
            logo_img = img.resize(
                (int(display_height * ratio), display_height), Image.Resampling.LANCZOS
            )
            self.logo_header = ImageTk.PhotoImage(logo_img)
            tk.Label(logo_container, image=self.logo_header, bg=COLOR_BG_DARK).pack(
                expand=True
            )
        except (OSError, tk.TclError):
            tk.Label(
                logo_container,
                text="CIMES",
                bg=COLOR_BG_DARK,
                fg=COLOR_TEXT_LIGHT,
                font=("Segoe UI", 18, "bold"),
            ).pack(expand=True)
        self.nav_container = tk.Frame(header, bg=COLOR_BG_DARK)
        self.nav_container.pack(side="right", padx=30, fill="y")
        nav_buttons_frame = tk.Frame(self.nav_container, bg=COLOR_BG_DARK)
        nav_buttons_frame.pack(side="top", fill="x")
        nav_items = [
            ("measure", "Mesure"),
            ("curve", "Courbe"),
            ("reload", "Recharger"),
            ("param", "Paramètres"),
        ]
        self.nav_buttons = {}
        for key, label in nav_items:
            btn_box = tk.Frame(nav_buttons_frame, bg=COLOR_BG_DARK)
            btn_box.pack(side="left", padx=5)
            btn = ttk.Button(
                btn_box,
                text=label,
                style="Nav.TButton",
                command=lambda k=key: self._on_nav_clicked(k),
            )
            btn.pack(side="top", pady=(22, 0))
            self.nav_buttons[key] = btn
            line = tk.Frame(btn_box, bg=COLOR_ACCENT, height=3)
            line.pack(side="top", fill="x", pady=(2, 0))
            line.pack_forget()
            btn.indicator = line
            btn.bind("<Enter>", lambda e, b=btn, k=key: self._on_nav_hover(b, k, True))
            btn.bind("<Leave>", lambda e, b=btn, k=key: self._on_nav_hover(b, k, False))
        self.change_corr_btn = ttk.Button(
            nav_buttons_frame,
            text="Modifier correction",
            style="Nav.TButton",
            command=self._change_correction,
        )
        self.change_corr_btn.pack(side="left", padx=(15, 0), pady=(22, 0))

    def _on_nav_hover(self, btn, key, is_entering):  # pylint: disable=unused-argument
        """Gère l'effet de survol des boutons de navigation."""

    # ── Navigation
    def _set_active_nav(self, key):
        """Met à jour l'affichage de la navigation."""
        self.current_view_key = key
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(style="NavActive.TButton")
                btn.indicator.pack(side="top", fill="x", pady=(2, 0))
            else:
                btn.configure(style="Nav.TButton")
                btn.indicator.pack_forget()

    def _on_nav_clicked(self, key):
        """Gère le clic sur un bouton de navigation."""
        if key == "measure":
            self.show_measure_view()
        elif key == "curve":
            self.show_curve_view()
            if hasattr(self, "curve_view"):
                self.curve_view._update_curve_view()  # pylint: disable=protected-access
        elif key == "reload":
            self.show_reload_view()
        elif key == "param":
            self.show_param_view()
        self._set_active_nav(key)

    def _raise_view(self, view):
        """Change l'affichage en fonction de la vue sélectionnée."""
        for v in [
            self.measure_view,
            self.curve_view,
            self.reload_view,
            self.param_view,
        ]:
            if v and hasattr(v, "frame"):
                v.frame.pack_forget()
        if view and hasattr(view, "frame"):
            view.frame.pack(fill="both", expand=True)

    def show_measure_view(self):
        """Affiche la vue de mesure."""
        self._raise_view(self.measure_view)

    def show_curve_view(self):
        """Affiche la vue de courbe."""
        self._raise_view(self.curve_view)

    def show_reload_view(self):
        """Affiche la vue de rechargement."""
        self._raise_view(self.reload_view)

    def show_param_view(self):
        """Affiche la vue des paramètres."""
        self._raise_view(self.param_view)

    # ── Configuration initiale
    def _setup_initial_configuration(self):
        """Met en place la configuration initiale de l'application."""
        self._update_clock()
        self._load_initial_settings()
        self._load_calibration_files_automatically()
        ensure_results_directory(self.results_path_var.get())
        self._update_active_params_display()
        self._update_save_delay_display()

    def _load_initial_settings(self):
        """Charge les paramètres initiaux de l'application."""
        load_sensor_settings(self)
        load_report_configuration(self)
        load_calibration_settings(self)

    def _load_calibration_files_automatically(self):
        """Charge les fichiers de calibration automatiquement."""
        self.mtx, self.dist, self.calib_path = load_calibration_files()
        if self.mtx is not None:
            self.use_undistortion_var.set(True)
        if self.homo_matrix is not None:
            self.use_homography_var.set(True)

    # ── Mises à jour automatiques
    def _start_auto_updates(self):
        """Démarre les mises à jour automatiques."""
        self.after(1000, self._update_clock)
        self.url_var.trace_add("write", lambda *a: self._update_active_params_display())
        self.capture_time_val_var.trace_add(
            "write", lambda *a: self._update_save_delay_display()
        )
        self.capture_time_unit_var.trace_add(
            "write", lambda *a: self._update_save_delay_display()
        )
        self.results_path_var.trace_add(
            "write", lambda *a: self._update_active_params_display()
        )
        self.start_time_var.trace_add(
            "write", lambda *a: self._update_active_params_display()
        )
        self.end_time_var.trace_add(
            "write", lambda *a: self._update_active_params_display()
        )
        self.capture_mode_var.trace_add(
            "write", lambda *a: self._on_capture_mode_changed()
        )
        self.facteur_conversion.trace_add("write", lambda *a: self._on_scale_changed())
        self._monitor_correction_parameters()

    def _update_clock(self):
        """Met à jour l'horloge et vérifie la transmission quotidienne."""
        current_time = datetime.now()
        self.datetime_var.set(current_time.strftime("%Y/%m/%d %H:%M:%S"))
        if (
            hasattr(self, "transmission_enabled_var")
            and self.transmission_enabled_var.get()
        ):
            if self.transmission_mode_var.get() == "daily":
                target_time = self.transmission_time_var.get()
                current_hm = current_time.strftime("%H:%M")
                if current_hm == target_time and current_time.second == 0:
                    self.after(100, self._trigger_daily_transmission)
        self.after(1000, self._update_clock)

    def _trigger_daily_transmission(self):
        """Déclenche la transmission quotidienne dans un thread séparé."""
        threading.Thread(
            target=self._run_daily_transmission_in_background, daemon=True
        ).start()

    def _run_daily_transmission_in_background(self):  # pylint: disable=too-many-locals
        """Génère et envoie le rapport quotidien (toutes les captures du jour en ZIP)."""
        print("[TRANSMISSION] Déclenchement de la transmission quotidienne...")
        try:
            today_str = datetime.now().strftime("%Y-%m-%d")
            today_dir = os.path.join(self.results_path_var.get(), today_str)
            if not os.path.exists(today_dir):
                print("[TRANSMISSION] Aucune donnée pour aujourd'hui.")
                return
            pdfs_to_send = self._collect_daily_pdfs(today_dir)
            if not pdfs_to_send:
                print("[TRANSMISSION] Aucun rapport à envoyer.")
                return
            zip_path = os.path.join(today_dir, f"Rapports_CIMES_{today_str}.zip")
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for i, pdf in enumerate(pdfs_to_send):
                    zipf.write(pdf, arcname=f"Rapport_Capture_{i + 1}.pdf")
            destinataire = self.transmission_email_var.get()
            if destinataire:
                envoyer_email_rapport(
                    destinataire,
                    zip_path,
                    subject=f"Rapports CIMES de la journée - {today_str}",
                    body=(
                        f"Bonjour,\n\nVeuillez trouver ci-joint les "
                        f"{len(pdfs_to_send)} rapports générés aujourd'hui."
                        f"\n\nCordialement,\nL'application CIMES"
                    ),
                )
        except (OSError, RuntimeError) as e:
            print(f"[TRANSMISSION] Erreur lors de la transmission quotidienne : {e}")

    def _collect_daily_pdfs(self, today_dir: str) -> list:
        """Parcourt les dossiers d'exécution et génère un PDF par capture.

        Returns:
            Liste des chemins PDF générés.
        """
        pdfs = []
        for exec_dir in os.listdir(today_dir):
            exec_path = os.path.join(today_dir, exec_dir)
            if not (os.path.isdir(exec_path) and exec_dir.startswith("execution_")):
                continue
            for cap_dir in os.listdir(exec_path):
                cap_path = os.path.join(exec_path, cap_dir)
                if os.path.isdir(cap_path) and cap_dir.startswith("capture_"):
                    pdf_path = generate_pdf_report(cap_path, self)
                    if pdf_path and os.path.exists(pdf_path):
                        pdfs.append(pdf_path)
        return pdfs

    def _update_active_params_display(self):
        """Met à jour l'affichage des paramètres actifs."""
        if hasattr(self, "measure_view"):
            self.measure_view.update_active_params_display()

    def _update_save_delay_display(self):
        """Met à jour l'affichage du délai de capture."""
        mode = self.capture_mode_var.get()
        if mode == "automatique":
            self.save_delay_display_var.set(
                f"{self.capture_time_val_var.get()} {self.capture_time_unit_var.get()}"
            )
        else:
            self.save_delay_display_var.set("Manuel")
        self._update_active_params_display()

    def _on_capture_mode_changed(self):
        """Met à jour l'affichage des paramètres actifs et les contrôles de capture."""
        self._update_save_delay_display()
        self._update_active_params_display()
        if hasattr(self, "param_view"):
            self.param_view._toggle_capture_controls()  # pylint: disable=protected-access

    def _on_scale_changed(self):
        """Met à jour l'échelle de conversion et la courbe si nécessaire."""
        try:
            scale_value = float(self.facteur_conversion.get().replace(",", "."))
            if scale_value <= 0:
                return
            self._update_active_params_display()
            if hasattr(self, "curve_view") and self.curve_view.frame.winfo_ismapped():
                self.curve_view._update_curve_view()  # pylint: disable=protected-access
        except ValueError:
            pass

    def _monitor_correction_parameters(self):
        """Surveille le fichier de paramètres de correction et met à jour l'app si besoin."""
        try:
            param_file = os.path.join(
                get_project_root(), "mesure", "params_correction.txt"
            )
            if os.path.exists(param_file):
                mtime = os.path.getmtime(param_file)
                if mtime > self._last_correction_mtime:
                    self._last_correction_mtime = mtime
                    params = load_correction_parameters()
                    self.correction_granulo["scale"].set(params["scale"])
                    self.correction_granulo["offset"].set(params["offset"])
                    if (
                        hasattr(self, "curve_view")
                        and hasattr(self.curve_view, "frame")
                        and self.curve_view.frame.winfo_ismapped()
                    ):
                        self.curve_view._update_curve_view()  # pylint: disable=protected-access
        except OSError as e:
            print(f"[LOG] Surveillance paramètres correction : {e}")
        self.after(2000, self._monitor_correction_parameters)
