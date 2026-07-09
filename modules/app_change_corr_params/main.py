"""Main entry point for the CIMES application."""

import sys
import os
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    sys.path.insert(0, sys._MEIPASS)
else:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from modules.app_change_corr_params.src.ui.main_window import CIMESApp

import tkinter as tk

if __name__ == "__main__":
    app = CIMESApp()
    app.mainloop()
