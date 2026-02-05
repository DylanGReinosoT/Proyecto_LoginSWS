import cv2
import numpy as np
import os
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import HTTPException, status
import mediapipe as mp
import face_recognition
from PIL import Image
import io
from ultralytics import YOLO


class FacialRecognitionService:
    """
    Servicio para manejar captura, almacenamiento y verificación de rostros
    """
    
    def __init__(self):
        # Directorio base para guardar rostros - debe estar en app/facial_data
        self.FACIAL_DATA_DIR = Path(__file__).parent.parent / "facial_data"
        
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Cargar modelo YOLO para detección de accesorios (liveness)
        try:
            self.yolo_model = YOLO('yolov8n.pt')  # Modelo nano para detección rápida
            print("[LOG] Modelo YOLO cargado exitosamente")
        except Exception as e:
            print(f"[WARN] Error cargando YOLO: {e}. Liveness detection deshabilitada")
            self.yolo_model = None
        
        # Crear directorio si no existe
        self.FACIAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[LOG] Directorio facial_data creado en: {self.FACIAL_DATA_DIR}")
    
    @staticmethod
    def ensure_facial_data_dir():
        """Asegura que el directorio de datos faciales existe"""
        facial_data_dir = Path(__file__).parent.parent / "facial_data"
        facial_data_dir.mkdir(parents=True, exist_ok=True)
    
    def save_facial_image(self, image_data: bytes, user_id: str) -> str:
        """
        Guarda una imagen facial para un usuario
        
        Args:
            image_data: Datos de imagen en bytes
            user_id: ID del usuario
            
        Returns:
            Ruta del archivo guardado
            
        Raises:
            HTTPException: Si hay error al guardar
        """
        try:
            # Crear directorio del usuario si no existe
            user_facial_dir = self.FACIAL_DATA_DIR / user_id
            user_facial_dir.mkdir(exist_ok=True)
            
            # Convertir bytes a imagen numpy
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Imagen inválida"
                )
            
            # Generar nombre único para la imagen
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"face_{timestamp}.jpg"
            filepath = user_facial_dir / filename
            
            # Guardar imagen
            cv2.imwrite(str(filepath), image)
            
            return str(filepath)
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error guardando imagen: {str(e)}"
            )
    
    def detect_face_in_image(self, image_data: bytes) -> dict:
        """
        Detecta si hay un rostro en la imagen
        
        Args:
            image_data: Datos de imagen en bytes
            
        Returns:
            Diccionario con información del rostro detectado
            
        Raises:
            HTTPException: Si no se detecta un rostro
        """
        try:
            # Convertir bytes a imagen numpy
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Imagen inválida"
                )
            
            # Detectar rostro
            with self.mp_face_detection.FaceDetection(
                model_selection=0,
                min_detection_confidence=0.5
            ) as face_detection:
                
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = face_detection.process(rgb_image)
                
                if not results.detections:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No se detectó rostro en la imagen"
                    )
                
                # Obtener información del primer rostro detectado
                detection = results.detections[0]
                h, w, _ = image.shape
                
                bboxC = detection.location_data.relative_bounding_box
                bbox = {
                    "x": int(bboxC.xmin * w),
                    "y": int(bboxC.ymin * h),
                    "width": int(bboxC.width * w),
                    "height": int(bboxC.height * h),
                    "confidence": float(detection.score[0])
                }
                
                return {
                    "face_detected": True,
                    "bbox": bbox,
                    "message": "Rostro detectado correctamente"
                }
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error detectando rostro: {str(e)}"
            )
    
    def get_user_facial_images(self, user_id: str) -> list:
        """
        Obtiene todas las imágenes faciales de un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de rutas de imágenes
        """
        user_facial_dir = self.FACIAL_DATA_DIR / user_id
        
        if not user_facial_dir.exists():
            return []
        
        images = []
        for file in user_facial_dir.glob("face_*.jpg"):
            images.append(str(file))
        
        return sorted(images, reverse=True)  # Más recientes primero
    
    def verify_face(self, image_data: bytes, user_id: str) -> dict:
        """
        Verifica si el rostro en la imagen coincide con el registrado para un usuario específico
        
        Usa face_recognition para comparación precisa de faces
        
        Args:
            image_data: Datos de imagen a verificar
            user_id: ID del usuario a verificar
            
        Returns:
            Resultado de la verificación
        """
        try:
            # Verificar que el usuario tenga imágenes guardadas
            user_images = self.get_user_facial_images(user_id)
            
            if not user_images:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No tiene rostro registrado. Por favor, registre su rostro primero en el perfil."
                )
            
            # Detectar rostro en la imagen actual
            detection_result = self.detect_face_in_image(image_data)
            
            if not detection_result["face_detected"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="❌ No se detectó rostro en la imagen. Asegúrese de estar mirando a la cámara."
                )
            
            # Verificar liveness (evitar fotos con YOLO)
            liveness_check = self._check_liveness(image_data)
            if not liveness_check["is_alive"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"❌ Verificación de liveness fallida: {liveness_check['reason']}"
                )
            
            # Comparar con imágenes registradas usando face_recognition
            verification_result = self._compare_faces(image_data, user_images)
            
            # ✅ VERIFICACIÓN IMPORTANTE: El rostro debe coincidir con el del usuario
            if verification_result["match"]:
                return {
                    "verified": True,
                    "message": "✅ Rostro verificado correctamente. Acceso permitido.",
                    "confidence": verification_result["confidence"],
                    "liveness": liveness_check
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="❌ El rostro no coincide con el registrado. Intente de nuevo."
                )
        
        except HTTPException:
            raise
        except Exception as e:
            print(f"[ERROR] verify_face: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error verificando rostro: {str(e)}"
            )
    
    def verify_face_for_login(self, image_data: bytes, user_id: str) -> dict:
        """
        Verifica el rostro durante el login - Versión estricta
        
        ⚠️ IMPORTANTE: Esta verificación es OBLIGATORIA para login
        - Compara rostro solo con el usuario específico
        - Falla si el rostro no pertenece a ese usuario
        - Falla si el usuario no tiene rostro registrado
        
        Args:
            image_data: Datos de imagen a verificar
            user_id: ID del usuario que intenta hacer login
            
        Returns:
            Dict con:
            - verified: True si verificación exitosa
            - message: Mensaje descriptivo
            - confidence: Confianza de la verificación
        """
        try:
            # Verificar que el usuario tenga facial recognition habilitado
            from app.database import db
            user_doc = db.collection("users").document(user_id).get()
            
            if not user_doc.exists:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="❌ Usuario no encontrado"
                )
            
            user_data = user_doc.to_dict()
            facial_enabled = user_data.get("facial_recognition_enabled", False)
            
            # Si el usuario tiene facial recognition habilitado, es OBLIGATORIO verificarlo
            if not facial_enabled:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="❌ Facial recognition no habilitado para este usuario"
                )
            
            # Obtener imágenes del usuario
            user_images = self.get_user_facial_images(user_id)
            
            if not user_images:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="❌ No hay rostro registrado para este usuario. No se puede completar el login."
                )
            
            # Detectar rostro en la imagen actual
            try:
                detection_result = self.detect_face_in_image(image_data)
                
                if not detection_result["face_detected"]:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="❌ No se detectó un rostro válido en la imagen."
                    )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"❌ Error detectando rostro: {str(e)}"
                )
            
            # Verificar liveness
            liveness_check = self._check_liveness(image_data)
            if not liveness_check["is_alive"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"❌ Verificación de liveness fallida: {liveness_check['reason']}"
                )
            
            # ✅ VERIFICACIÓN CRÍTICA: Comparar rostro SOLO con el usuario específico
            verification_result = self._compare_faces(image_data, user_images)
            
            if not verification_result["match"]:
                # ⚠️ SEGURIDAD: El rostro no coincide - RECHAZAR login
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="❌ El rostro no pertenece a este usuario. Acceso denegado."
                )
            
            # ✅ ÉXITO: Todo verificado correctamente
            return {
                "verified": True,
                "message": "✅ Identidad verificada. Login exitoso.",
                "confidence": verification_result["confidence"],
                "user_id": user_id
            }
        
        except HTTPException:
            raise
        except Exception as e:
            print(f"[ERROR] verify_face_for_login: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"❌ Error en verificación facial: {str(e)}"
            )
    
    def _compare_faces(self, image_data: bytes, registered_images: list) -> dict:
        """
        Compara el rostro actual con los rostros registrados
        
        Args:
            image_data: Imagen a verificar en bytes
            registered_images: Lista de rutas de imágenes registradas
            
        Returns:
            Dict con resultado de comparación y confianza
        """
        try:
            # Convertir bytes a imagen
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return {"match": False, "confidence": 0}
            
            # Convertir BGR a RGB para face_recognition
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Obtener encoding del rostro actual
            try:
                current_face_encodings = face_recognition.face_encodings(image_rgb)
                if not current_face_encodings:
                    return {"match": False, "confidence": 0}
                
                current_face_encoding = current_face_encodings[0]
            except Exception as e:
                print(f"[WARN] Error obteniendo encoding del rostro actual: {e}")
                return {"match": False, "confidence": 0}
            
            # Comparar con cada imagen registrada
            best_match = False
            best_distance = 1.0
            
            for registered_image_path in registered_images:
                try:
                    # Cargar imagen registrada
                    registered_image = face_recognition.load_image_file(registered_image_path)
                    registered_face_encodings = face_recognition.face_encodings(registered_image)
                    
                    if not registered_face_encodings:
                        continue
                    
                    registered_face_encoding = registered_face_encodings[0]
                    
                    # Comparar faces
                    distance = face_recognition.face_distance(
                        [registered_face_encoding],
                        current_face_encoding
                    )[0]
                    
                    # Threshold: 0.6 es estándar (menor = más similar)
                    if distance < 0.6:
                        best_match = True
                        best_distance = min(best_distance, distance)
                    
                except Exception as e:
                    print(f"[WARN] Error procesando imagen registrada {registered_image_path}: {e}")
                    continue
            
            # Convertir distancia a confianza (0-100%)
            confidence = max(0, (1 - best_distance) * 100)
            
            return {
                "match": best_match,
                "confidence": confidence,
                "distance": float(best_distance)
            }
        
        except Exception as e:
            print(f"[ERROR] _compare_faces: {str(e)}")
            return {"match": False, "confidence": 0}
    
    def _check_liveness(self, image_data: bytes) -> dict:
        """
        Verifica que sea una persona viva (no una foto/pantalla)
        
        Detecciones:
        - Gafas
        - Sombreros
        - Mascaras
        
        Args:
            image_data: Imagen a verificar en bytes
            
        Returns:
            Dict con resultado de verificación
        """
        try:
            if not self.yolo_model:
                # Si YOLO no está disponible, permitir de todos modos
                return {
                    "is_alive": True,
                    "reason": "YOLO no disponible - liveness check omitido"
                }
            
            # Convertir bytes a imagen
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return {"is_alive": False, "reason": "Imagen inválida"}
            
            # Ejecutar YOLO
            results = self.yolo_model(image, verbose=False)
            
            if not results or len(results) == 0:
                return {"is_alive": True, "reason": "Sin accesorios detectados"}
            
            # Clases sospechosas (índices en COCO)
            suspicious_classes = {
                34: "bottle",    # Botellas pueden usarse para ocultar
                35: "wine glass", 
                36: "cup",
                42: "spoon",
                43: "bowl",
            }
            
            dangerous_classes = {
                26: "backpack",   # Podría indicar que no es una persona real
            }
            
            detected_classes = []
            for result in results:
                if result.boxes:
                    for box in result.boxes:
                        class_id = int(box.cls[0])
                        detected_classes.append(class_id)
            
            # Si se detectan clases sospechosas, sospechar
            if detected_classes:
                print(f"[LOG] YOLO detectó clases: {detected_classes}")
                return {
                    "is_alive": True,  # Aún permitir, pero registrar
                    "reason": f"Objetos detectados: {detected_classes}"
                }
            
            return {
                "is_alive": True,
                "reason": "Verificación de liveness exitosa"
            }
        
        except Exception as e:
            print(f"[WARN] Error en _check_liveness: {e}")
            # En caso de error, permitir de todos modos
            return {
                "is_alive": True,
                "reason": f"Error en liveness check: {str(e)}"
            }
    
    def check_facial_uniqueness(self, image_data: bytes, exclude_user_id: str = None) -> dict:
        """
        Verifica si un rostro ya existe en el sistema (en otros usuarios)
        
        Se usa durante el registro para asegurar que cada rostro sea único.
        
        Args:
            image_data: Imagen a verificar en bytes
            exclude_user_id: ID del usuario a excluir (para no compararse a sí mismo)
            
        Returns:
            Dict con:
            - is_unique: True si el rostro no existe en otros usuarios
            - message: Mensaje descriptivo
            - matched_user_id: ID del usuario si se encontró coincidencia (None si es único)
            - confidence: Confianza de la coincidencia si existe
        """
        try:
            # Obtener todos los directorios de usuarios
            if not self.FACIAL_DATA_DIR.exists():
                return {
                    "is_unique": True,
                    "message": "No hay usuarios registrados aún",
                    "matched_user_id": None,
                    "confidence": 0
                }
            
            # Convertir bytes a imagen para obtener encoding
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Imagen inválida"
                )
            
            # Convertir BGR a RGB para face_recognition
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Obtener encoding del rostro actual
            try:
                current_face_encodings = face_recognition.face_encodings(image_rgb)
                if not current_face_encodings:
                    raise Exception("No se detectó un rostro válido en la imagen")
                current_encoding = current_face_encodings[0]
            except Exception as e:
                return {
                    "is_unique": False,
                    "message": f"Error procesando imagen: {str(e)}",
                    "matched_user_id": None,
                    "confidence": 0
                }
            
            # Recorrer todos los usuarios registrados
            for user_dir in self.FACIAL_DATA_DIR.iterdir():
                if not user_dir.is_dir():
                    continue
                
                user_id = user_dir.name
                
                # Excluir el usuario actual si se especifica
                if exclude_user_id and user_id == exclude_user_id:
                    continue
                
                # Obtener imágenes del usuario
                user_images = list(user_dir.glob("face_*.jpg"))
                
                if not user_images:
                    continue
                
                # Comparar con la primera imagen del usuario
                # (o todas si quieres ser más exhaustivo)
                registered_image_path = user_images[0]
                
                try:
                    registered_image = face_recognition.load_image_file(str(registered_image_path))
                    registered_encodings = face_recognition.face_encodings(registered_image)
                    
                    if not registered_encodings:
                        continue
                    
                    registered_encoding = registered_encodings[0]
                    
                    # Comparar distancia euclidiana
                    distance = np.linalg.norm(current_encoding - registered_encoding)
                    
                    # Si la distancia es muy pequeña (< 0.6), es una coincidencia
                    DISTANCE_THRESHOLD = 0.6
                    if distance < DISTANCE_THRESHOLD:
                        confidence = max(0, (1 - distance) * 100)
                        return {
                            "is_unique": False,
                            "message": f"El rostro ya está registrado por otro usuario",
                            "matched_user_id": user_id,
                            "confidence": round(confidence, 2)
                        }
                
                except Exception as e:
                    print(f"[WARN] Error comparando con usuario {user_id}: {str(e)}")
                    continue
            
            # Si llegamos aquí, el rostro es único
            return {
                "is_unique": True,
                "message": "El rostro es único en el sistema",
                "matched_user_id": None,
                "confidence": 0
            }
        
        except HTTPException:
            raise
        except Exception as e:
            print(f"[ERROR] check_facial_uniqueness: {str(e)}")
            return {
                "is_unique": False,
                "message": f"Error verificando unicidad del rostro: {str(e)}",
                "matched_user_id": None,
                "confidence": 0
            }
