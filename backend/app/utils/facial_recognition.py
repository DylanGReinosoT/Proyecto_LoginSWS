import cv2
import numpy as np
import mediapipe as mp
from typing import Tuple, Optional


class FacialRecognitionUtil:
    """
    Utilidades para reconocimiento facial usando MediaPipe
    
    Esta clase será expandida posteriormente para implementar:
    - Captura de rostros para registro
    - Verificación de rostros para autenticación
    - Análisis de características faciales
    """
    
    def __init__(self):
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils
    
    def detect_face(self, image: np.ndarray) -> Tuple[bool, Optional[dict]]:
        """
        Detecta si hay un rostro en la imagen
        
        Args:
            image: Array de imagen en formato OpenCV
            
        Returns:
            Tupla (face_detected, face_landmarks)
        """
        try:
            with self.mp_face_detection.FaceDetection(
                model_selection=0,
                min_detection_confidence=0.5
            ) as face_detection:
                
                results = face_detection.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                
                if results.detections:
                    return True, results.detections
                return False, None
        except Exception as e:
            print(f"Error detectando rostro: {str(e)}")
            return False, None
    
    def extract_face_region(self, image: np.ndarray, detection) -> Optional[np.ndarray]:
        """
        Extrae la región del rostro de la imagen
        
        Args:
            image: Array de imagen
            detection: Objeto de detección de MediaPipe
            
        Returns:
            Región de rostro extraída o None
        """
        try:
            h, w, c = image.shape
            
            bboxC = detection.location_data.relative_bounding_box
            bbox = int(bboxC.xmin * w), int(bboxC.ymin * h), \
                   int(bboxC.width * w), int(bboxC.height * h)
            
            x, y, width, height = bbox
            face_region = image[y:y+height, x:x+width]
            
            return face_region
        except Exception as e:
            print(f"Error extrayendo región del rostro: {str(e)}")
            return None

    # Placeholder para futuras funcionalidades
    def register_face(self, face_encoding: np.ndarray, user_id: str) -> bool:
        """
        Registra una codificación facial para un usuario
        IMPLEMENTACIÓN FUTURA
        """
        pass
    
    def verify_face(self, face_encoding: np.ndarray, user_id: str) -> bool:
        """
        Verifica si una codificación facial coincide con un usuario registrado
        IMPLEMENTACIÓN FUTURA
        """
        pass
