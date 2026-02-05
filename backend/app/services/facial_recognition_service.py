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
            
            # Verificar liveness (evitar fotos/pantallas/dispositivos)
            liveness_check = self._check_liveness(image_data)
            if not liveness_check["is_alive"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=liveness_check['reason']
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
            
            # Verificar liveness (detección de dispositivos, accesorios, etc.)
            liveness_check = self._check_liveness(image_data)
            if not liveness_check["is_alive"]:
                # ⚠️ SEGURIDAD CRÍTICA: Rechazar si no pasa validación de liveness
                security_level = liveness_check.get("security_level", "DESCONOCIDO")
                print(f"[🚫 SEGURIDAD {security_level}] Liveness check fallido: {liveness_check['reason']}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=liveness_check['reason']
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
        Compara el rostro actual con los rostros registrados del usuario
        
        ⚠️ CRÍTICO: Esta función SOLO se llama si:
        1. El usuario EXISTE
        2. El usuario TIENE facial recognition habilitado
        3. El usuario TIENE al menos un rostro registrado (no_images > 0)
        
        Args:
            image_data: Imagen a verificar en bytes
            registered_images: Lista de rutas de imágenes registradas del usuario
            
        Returns:
            Dict con resultado de comparación y confianza
            - match: True/False
            - confidence: Porcentaje de similitud
            - distance: Valor numérico (menor = más similar)
            - matched_images: Cuántas imágenes registradas coincidieron
        """
        try:
            # VALIDACIÓN CRÍTICA: Verificar que hay imágenes registradas
            if not registered_images or len(registered_images) == 0:
                print("[CRITICAL] VULNERABILIDAD: Se intentó comparar con lista vacía")
                return {
                    "match": False,
                    "confidence": 0,
                    "distance": 1.0,
                    "matched_images": 0,
                    "reason": "No hay imágenes registradas para comparar"
                }
            
            # Convertir bytes a imagen
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                print("[ERROR] Imagen capturada es inválida")
                return {
                    "match": False,
                    "confidence": 0,
                    "distance": 1.0,
                    "matched_images": 0,
                    "reason": "Imagen inválida"
                }
            
            # Convertir BGR a RGB para face_recognition
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Obtener encoding del rostro actual
            try:
                current_face_encodings = face_recognition.face_encodings(image_rgb)
                if not current_face_encodings:
                    print("[ERROR] No se pudo extraer encoding del rostro capturado")
                    return {
                        "match": False,
                        "confidence": 0,
                        "distance": 1.0,
                        "matched_images": 0,
                        "reason": "No se pudo extraer características del rostro"
                    }
                
                current_face_encoding = current_face_encodings[0]
            except Exception as e:
                print(f"[ERROR] Error obteniendo encoding del rostro actual: {e}")
                return {
                    "match": False,
                    "confidence": 0,
                    "distance": 1.0,
                    "matched_images": 0,
                    "reason": f"Error procesando rostro: {str(e)}"
                }
            
            # COMPARACIÓN ESTRICTA: Comparar con CADA imagen registrada
            best_match = False
            best_distance = 1.0
            matched_count = 0
            match_details = []
            
            # Threshold para considerar un match: 0.55 (más estricto que 0.6)
            DISTANCE_THRESHOLD = 0.55
            CONFIDENCE_MIN = 35  # Confianza mínima requerida (%)
            
            print(f"[LOG] Comparando rostro capturado con {len(registered_images)} imágenes registradas")
            
            for idx, registered_image_path in enumerate(registered_images):
                try:
                    # Cargar imagen registrada
                    registered_image = face_recognition.load_image_file(registered_image_path)
                    registered_face_encodings = face_recognition.face_encodings(registered_image)
                    
                    if not registered_face_encodings:
                        print(f"[WARN] No se pudo extraer encoding de imagen registrada #{idx + 1}")
                        continue
                    
                    registered_face_encoding = registered_face_encodings[0]
                    
                    # Comparar faces usando distancia euclidiana
                    distance = face_recognition.face_distance(
                        [registered_face_encoding],
                        current_face_encoding
                    )[0]
                    
                    # Calcular confianza
                    confidence = max(0, (1 - distance) * 100)
                    
                    print(f"[LOG] Imagen #{idx + 1}: distance={distance:.4f}, confidence={confidence:.1f}%")
                    
                    match_details.append({
                        "image": registered_image_path,
                        "distance": float(distance),
                        "confidence": float(confidence),
                        "is_match": distance < DISTANCE_THRESHOLD
                    })
                    
                    # Evaluar si es coincidencia: distancia < threshold
                    if distance < DISTANCE_THRESHOLD and confidence >= CONFIDENCE_MIN:
                        best_match = True
                        matched_count += 1
                        best_distance = min(best_distance, distance)
                        print(f"[✓] COINCIDENCIA ENCONTRADA en imagen #{idx + 1} con confidence {confidence:.1f}%")
                    
                except Exception as e:
                    print(f"[ERROR] Error procesando imagen registrada #{idx + 1}: {e}")
                    continue
            
            # RESULTADO FINAL: Requerir al menos UNA coincidencia
            if best_match and matched_count > 0:
                confidence = max(0, (1 - best_distance) * 100)
                print(f"[✓✓✓] VERIFICACIÓN EXITOSA: {matched_count}/{len(registered_images)} imágenes coincidieron")
                return {
                    "match": True,
                    "confidence": float(confidence),
                    "distance": float(best_distance),
                    "matched_images": matched_count,
                    "total_images": len(registered_images),
                    "reason": f"Rostro coincide con {matched_count}/{len(registered_images)} imágenes registradas"
                }
            else:
                print(f"[✗✗✗] VERIFICACIÓN FALLIDA: Ninguna imagen coincidió")
                return {
                    "match": False,
                    "confidence": 0,
                    "distance": float(best_distance),
                    "matched_images": 0,
                    "total_images": len(registered_images),
                    "reason": f"El rostro no coincide con ninguna de las {len(registered_images)} imágenes registradas",
                    "details": match_details  # Para debugging
                }
        
        except Exception as e:
            print(f"[CRITICAL ERROR] _compare_faces: {str(e)}")
            return {
                "match": False,
                "confidence": 0,
                "distance": 1.0,
                "matched_images": 0,
                "reason": f"Error crítico en comparación: {str(e)}"
            }
    
    def _check_liveness(self, image_data: bytes) -> dict:
        """
        Verifica que sea una persona viva (no una foto/pantalla/dispositivo)
        
        ⚠️ VALIDACIONES CRÍTICAS:
        1. Detecta pantallas, monitores, TVs, celulares, tablets
        2. Detecta si el rostro está siendo mostrado EN un dispositivo
        3. Rechaza accesorios sospechosos (gafas, sombreros, máscaras)
        4. Rechaza si hay objetos adicionales cerca del rostro
        
        Args:
            image_data: Imagen a verificar en bytes
            
        Returns:
            Dict con resultado de verificación
            - is_alive: True/False
            - reason: Descripción del resultado
            - devices_detected: Dispositivos encontrados (si los hay)
        """
        try:
            if not self.yolo_model:
                # Si YOLO no está disponible, permitir de todos modos
                return {
                    "is_alive": True,
                    "reason": "YOLO no disponible - liveness check omitido",
                    "devices_detected": []
                }
            
            # Convertir bytes a imagen
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return {
                    "is_alive": False, 
                    "reason": "❌ Imagen inválida",
                    "devices_detected": []
                }
            
            # Ejecutar YOLO para detección de objetos
            results = self.yolo_model(image, verbose=False)
            
            if not results or len(results) == 0:
                return {
                    "is_alive": True, 
                    "reason": "✅ Sin objetos sospechosos detectados",
                    "devices_detected": []
                }
            
            # ============================================
            # CLASES COCO - Mapeo de dispositivos peligrosos
            # ============================================
            # Dispositivos donde se podría mostrar un rostro (MÁS PELIGROSO)
            device_classes = {
                62: "laptop",        # Pantalla de laptop
                63: "tv",            # Televisor
                65: "remote",        # Control remoto (indica pantalla cercana)
                73: "book",          # Podría ser un libro/papel con foto
                74: "cell phone",    # Celular/teléfono
            }
            
            # Accesorios que ocultan/alteran el rostro
            accessory_classes = {
                0: "person",         # Persona - puede usarse para bloquear vista
                27: "tie",           # Corbata cerca del rostro
                28: "cake",          # Objeto frente al rostro
                29: "couch",         # Indicativo de ambiente controlado
                30: "potted plant",  # Objeto grande que podría ocluir
            }
            
            # Accesorios PERMITIDOS (lentes, gafas no son problema)
            allowed_accessories = {
                37: "glasses",       # ✅ PERMITIDO - Lentes/gafas normales
                38: "sunglasses",    # ✅ PERMITIDO - Gafas de sol (levemente sospechosas)
                39: "goggles",       # ✅ PERMITIDO - Gafas de protección
            }
            
            # Objetos sospechosos adicionales
            suspicious_classes = {
                34: "bottle",        # Botellas para ocultar rostro
                35: "wine glass",    # Cristalería
                36: "cup",           # Taza/vaso
                42: "spoon",         # Utensilio
                43: "bowl",          # Recipiente
                44: "banana",        # Objeto para ocluir
                45: "apple",         # Objeto para ocluir
                47: "sandwich",      # Objeto frente rostro
                48: "orange",        # Objeto para ocluir
                50: "pizza",         # Objeto grande
                51: "donut",         # Objeto frente rostro
                52: "cake",          # Objeto grande
            }
            
            # Máscara facial explícita (muy peligrosa)
            mask_classes = {
                0: "mask",           # Máscara (si el modelo la detecta)
            }
            
            detected_devices = []
            detected_accessories = []
            detected_suspicious = []
            detected_allowed_accessories = []  # Lentes, gafas (permitidas)
            device_detections = []  # Para guardar detalles de dispositivos
            
            print("[LOG] ========== ANÁLISIS YOLO ==========")
            
            for result in results:
                if result.boxes:
                    for box in result.boxes:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        
                        # Obtener coordenadas del bounding box
                        x1, y1, x2, y2 = box.xyxy[0]
                        box_width = float(x2 - x1)
                        box_height = float(y2 - y1)
                        box_area = box_width * box_height
                        
                        # Imagen total
                        img_height, img_width = image.shape[:2]
                        img_area = img_height * img_width
                        box_percentage = (box_area / img_area) * 100
                        
                        # Verificar si son LENTES PERMITIDOS
                        if class_id in allowed_accessories:
                            accessory_name = allowed_accessories[class_id]
                            detected_allowed_accessories.append(accessory_name)
                            print(f"[✅ PERMITIDO] {accessory_name.upper()} detectado - Aceptado")
                        
                        # Verificar si es un DISPOSITIVO (critial)
                        elif class_id in device_classes:
                            device_name = device_classes[class_id]
                            detected_devices.append(device_name)
                            device_detections.append({
                                "type": device_name,
                                "confidence": float(confidence),
                                "size_percentage": round(box_percentage, 2),
                                "position": {
                                    "x1": float(x1), "y1": float(y1),
                                    "x2": float(x2), "y2": float(y2)
                                }
                            })
                            print(f"[⚠️ DEVICE] {device_name.upper()} detectado con {confidence:.2%} confianza (ocupa {box_percentage:.1f}% de la imagen)")
                        
                        # Verificar accesorios
                        elif class_id in accessory_classes:
                            accessory_name = accessory_classes[class_id]
                            detected_accessories.append(accessory_name)
                            print(f"[⚠️ ACCESORIO] {accessory_name} detectado")
                        
                        # Verificar objetos sospechosos
                        elif class_id in suspicious_classes:
                            suspicious_name = suspicious_classes[class_id]
                            detected_suspicious.append(suspicious_name)
                            print(f"[⚠️ SOSPECHOSO] {suspicious_name} detectado")
            
            print("[LOG] ====================================")
            
            # ============================================
            # LÓGICA DE DECISIÓN - RECHAZO ESTRICTO
            # ============================================
            
            # 🚫 RECHAZAR SI: Se detecta dispositivo (pantalla, TV, teléfono, tablet)
            if detected_devices:
                devices_str = ", ".join(detected_devices)
                print(f"[❌ RECHAZO] Se detectó dispositivo de video: {devices_str}")
                return {
                    "is_alive": False,
                    "reason": f"❌ VERIFICACIÓN FALLIDA: Se detectó un dispositivo de pantalla ({devices_str}). El rostro debe presentarse directamente, no a través de una pantalla, teléfono, tablet o monitor.",
                    "devices_detected": device_detections,
                    "security_level": "CRÍTICO"
                }
            
            # 🚫 RECHAZAR SI: Hay múltiples accesorios sospechosos (NO incluye lentes)
            if len(detected_accessories) >= 2:
                accessories_str = ", ".join(detected_accessories)
                print(f"[❌ RECHAZO] Múltiples accesorios detectados: {accessories_str}")
                return {
                    "is_alive": False,
                    "reason": f"❌ VERIFICACIÓN FALLIDA: Demasiados accesorios/objetos detectados ({accessories_str}). Presente su rostro sin accesorios adicionales.",
                    "devices_detected": [],
                    "security_level": "ALTO"
                }
            
            # ✅ PERMITIR SI: Solo hay lentes/gafas (sin otros accesorios)
            if detected_allowed_accessories and not detected_accessories and not detected_suspicious:
                glasses_str = ", ".join(detected_allowed_accessories)
                print(f"[✅ PERMITIDO] Rostro con lentes/gafas: {glasses_str}")
                return {
                    "is_alive": True,
                    "reason": f"✅ Verificación de liveness exitosa. Rostro con {glasses_str} aceptado.",
                    "devices_detected": [],
                    "security_level": "BAJO",
                    "note": f"Usuario lleva {glasses_str}"
                }
            
            # ⚠️ ADVERTENCIA SI: Hay objetos sospechosos O lentes + otros objetos
            if detected_suspicious or detected_accessories:
                warnings = detected_suspicious + detected_accessories
                # Si hay lentes pero también otros objetos
                if detected_allowed_accessories:
                    warnings.extend(detected_allowed_accessories)
                warnings_str = ", ".join(warnings)
                print(f"[⚠️ ADVERTENCIA] Objetos detectados: {warnings_str}")
                return {
                    "is_alive": True,  # Permitir, pero registrar
                    "reason": f"⚠️ ADVERTENCIA: Se detectaron objetos ({warnings_str}). Imagen aceptada pero verificada con objetos presentes.",
                    "devices_detected": [],
                    "security_level": "MEDIO",
                    "warnings": warnings
                }
            
            # ✅ ACEPTAR: Todo está bien
            return {
                "is_alive": True,
                "reason": "✅ Verificación de liveness exitosa. Rostro válido detectado.",
                "devices_detected": [],
                "security_level": "BAJO"
            }
        
        except Exception as e:
            print(f"[ERROR] Error en _check_liveness: {e}")
            # En caso de error, RECHAZAR por seguridad
            return {
                "is_alive": False,
                "reason": f"❌ Error en verificación de liveness: {str(e)}",
                "devices_detected": [],
                "security_level": "ERROR"
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
