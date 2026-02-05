import firebase_admin
from firebase_admin import credentials, firestore
from app.config import FIREBASE_PROJECT_ID, FIREBASE_PRIVATE_KEY, FIREBASE_CLIENT_EMAIL
import json
import os

# Initialize Firebase
def init_firebase():
    """
    Inicializa la conexión con Firebase usando las variables de entorno
    """
    if not firebase_admin._apps:
        try:
            # Intenta cargar desde un archivo de credenciales
            cred = credentials.Certificate("serviceAccountKey.json")
        except FileNotFoundError:
            # Si no existe el archivo, intenta usar las variables de entorno
            cred_dict = {
                "type": "service_account",
                "project_id": FIREBASE_PROJECT_ID,
                "private_key": FIREBASE_PRIVATE_KEY.replace("\\n", "\n") if FIREBASE_PRIVATE_KEY else "",
                "client_email": FIREBASE_CLIENT_EMAIL,
            }
            cred = credentials.Certificate(cred_dict)
        
        firebase_admin.initialize_app(cred)
    
    return firestore.client()

# Get Firestore client
db = init_firebase()
