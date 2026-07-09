"""
Page d'entrée de l'application de calibrage de caméra. 
"""

import sys
import os
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    sys.path.insert(0, sys._MEIPASS)
else:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from modules.app_calibrage_cam.ui.main_window import ApplicationCalibrage

import tkinter as tk

if __name__ == "__main__":
    app = ApplicationCalibrage()
    app.mainloop()
