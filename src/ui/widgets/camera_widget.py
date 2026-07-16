"""Gère la connexion et la lecture du flux vidéo RTSP."""


# pylint: disable=no-member  # cv2 dynamic C bindings not resolvable statically
import threading
import time
import cv2

class VideoStream:
    """
    Classe pour gérer la connexion et la lecture du flux vidéo RTSP.
    """
    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url
        self.cap = None
        self.current_frame = None
        self.running = False
        self.thread = None
        self.last_error = None

    def start(self):
        """Démarre le flux vidéo de manière robuste avec un timeout de connexion de 3 secondes."""
        if self.running:
            return True
        self.last_error = None
        
        connection_result = {"cap": None, "error": None}
        
        def attempt_connection():
            try:
                cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                if not cap.isOpened():
                    connection_result["error"] = f"Impossible d'ouvrir le flux RTSP : {self.rtsp_url}"
                else:
                    connection_result["cap"] = cap
            except Exception as e:
                connection_result["error"] = f"Erreur lors de la connexion au flux : {e}"
        
        # Lancement de la tentative dans un thread temporaire
        conn_thread = threading.Thread(target=attempt_connection)
        conn_thread.daemon = True
        conn_thread.start()
        
        # Attente maximale de 3 secondes
        conn_thread.join(timeout=3.0)
        
        if conn_thread.is_alive():
            self.last_error = f"Délai d'attente dépassé (timeout 3s) lors de la connexion à : {self.rtsp_url}"
            print(f"[ERREUR] {self.last_error}")
            return False
            
        if connection_result["error"]:
            self.last_error = connection_result["error"]
            print(f"[ERREUR] {self.last_error}")
            return False
            
        self.cap = connection_result["cap"]
        self.running = True
        self.thread = threading.Thread(target=self._update, args=())
        self.thread.daemon = True
        self.thread.start()
        print(f"Connexion RTSP réussie : {self.rtsp_url}")
        return True

    def _update(self):
        """Thread de lecture du flux vidéo."""
        while self.running:
            try:
                ret, frame = self.cap.read()
                if ret:
                    self.current_frame = frame
                else:
                    self.last_error = "Erreur de lecture du flux (frame vide)."
                    print(f"[ERREUR] {self.last_error}")
                    self.running = False
                    break
            except Exception as e:  # pylint: disable=broad-exception-caught
                self.last_error = f"Erreur critique dans le thread de lecture : {e}"
                print(f"[ERREUR] {self.last_error}")
                self.running = False
                break
            time.sleep(0.01)

    def stop(self):
        """Arrête le flux vidéo."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap:
            self.cap.release()
            self.cap = None
        self.current_frame = None
        print("Flux vidéo arrêté.")

    def get_frame(self):
        """Récupère la dernière frame du flux vidéo."""
        if self.current_frame is not None:
            return self.current_frame.copy()
        return None
