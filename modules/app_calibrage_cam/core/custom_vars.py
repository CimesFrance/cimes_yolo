"""Module de gestion des variables personnalisées de l'application.
"""

import tkinter as tk
import json

class JSONVar(tk.StringVar):
    """A Tk variable that can hold dicts and lists"""

    def __init__(self, *args, **kwargs):
        kwargs["value"] = json.dumps(kwargs.get("value"))
        super().__init__(*args, **kwargs)

    def set(self, value, *args, **kwargs):
        string = json.dumps(value)
        super().set(string, *args, **kwargs)

    def get(self, *args, **kwargs):
        string = super().get(*args, **kwargs)
        return json.loads(string)
