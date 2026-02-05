# 🔐 FLUJO COMPLETO DE VALIDACIÓN SEGURA - LOGIN CON FACIAL RECOGNITION

## 📍 FASE 1: AUTENTICACIÓN CON CREDENCIALES

```
┌─────────────────────────────────┐
│ Usuario ingresa email + password│
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────┐
│ POST /api/auth/login                                │
│ Body: {email, password}                             │
└──────────────┬──────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────┐
│ [Backend] AuthService.login_user()                 │
│ Busca usuario en BD por email                      │
└──────────────┬──────────────────────────────────────┘
               │
         ┌─────┴─────────────────────────────────────┐
         │                                            │
         ▼                                            ▼
    ❌ FAIL                                      ✅ SUCCESS
    No existe                          Genera JWT temporal
    ├─ 401: Usuario no                 ├─ access_token
    │  encontrado                      ├─ token_type: bearer
    │                                  ├─ expires_in: 1800s
    └─ Fin                             ├─ user_id: uuid
                                       ├─ facial_recognition_enabled: bool
                                       ├─ next_step: "facial_verification"
                                       └─ Retorna al frontend
                                            │
                                            ▼
                                       [Frontend] Abre modal
                                       de captura facial
```

---

## 📍 FASE 2: CAPTURA FACIAL CON LIVENESS

```
┌─────────────────────────────────────────────────┐
│ FacialCaptureModal abierto                       │
│ ├─ Solicita permiso de cámara                  │
│ ├─ Inicia MediaPipe FaceLandmarker              │
│ └─ Detecta puntos faciales en tiempo real       │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│ Usuario parpadea 3 veces (liveness local)       │
│ ├─ Detección de apertura/cierre de ojos        │
│ ├─ Requiere movimiento natural                  │
│ └─ Previene fotos estáticas/deepfakes          │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│ Sistema detecta 3 parpadeos ✓                    │
│ └─ Captura frame actual → canvas                │
│    Convierte a JPEG base64                      │
│    Envía al backend                             │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│ POST /api/auth/verify-facial-for-login?user_id=XXX        │
│ Body: {image_base64: "base64_encoded_image"}              │
│ Headers: {"Content-Type": "application/json"}             │
└──────────────┬────────────────────────────────────────────┘
               │
               ▼ [Backend] FacialRecognitionService
               │           .verify_face_for_login()
```

---

## 📍 FASE 3: VALIDACIÓN EN BACKEND (7 CAPAS)

```
verify_face_for_login(image_bytes, user_id)
│
├─────────────────────────────────────────────────────────────────┐
│ CAPA 1: ¿Usuario existe?                                        │
├─────────────────────────────────────────────────────────────────┤
│ Código: user_doc = db.collection("users").document(user_id)   │
│ Si: not user_doc.exists                                        │
│ ├─ Lanza: HTTPException(401, "Usuario no encontrado")         │
│ └─ Retorna al frontend: error 401                             │
│                                                                 │
│ ✅ PASÓ: Continúa a CAPA 2                                     │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
├─────────────────────────────────────────────────────────────────┐
│ CAPA 2: ¿Facial recognition está habilitado?                  │
├─────────────────────────────────────────────────────────────────┤
│ Código: facial_enabled = user_data.get("facial_recognition_enabled")
│ Si: not facial_enabled                                          │
│ ├─ Lanza: HTTPException(403, "Facial recognition no habilitado")
│ └─ Retorna al frontend: error 403                              │
│                                                                 │
│ ✅ PASÓ: Continúa a CAPA 3                                     │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
├─────────────────────────────────────────────────────────────────┐
│ CAPA 3: ⚠️ ¿USUARIO TIENE ROSTRO REGISTRADO EN BD? (CRÍTICA) │
├─────────────────────────────────────────────────────────────────┤
│ Código:                                                         │
│   user_images = self.get_user_facial_images(user_id)           │
│   if not user_images:  ← VALIDACIÓN CRÍTICA                    │
│       Lanza: HTTPException(401, "No hay rostro registrado")    │
│                                                                 │
│ ❌ SI FALLA:                                                     │
│    └─ Retorna al frontend: error 401                           │
│       "No tienes un rostro registrado en BD"                   │
│       Modal abierto para reintentar                            │
│                                                                 │
│ ✅ SI PASÓ: user_images contiene ≥1 ruta de imagen facial     │
│    Continúa a CAPA 4                                           │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
├─────────────────────────────────────────────────────────────────┐
│ CAPA 4: ¿Se detecta un rostro en la imagen capturada?          │
├─────────────────────────────────────────────────────────────────┤
│ Código:                                                         │
│   detection_result = self.detect_face_in_image(image_data)     │
│   if not detection_result["face_detected"]:                    │
│       Lanza: HTTPException(401, "No se detectó rostro")        │
│                                                                 │
│ ❌ SI FALLA:                                                     │
│    └─ Retorna al frontend: error 401                           │
│       Modal abierto para nuevo intento                         │
│                                                                 │
│ ✅ SI PASÓ: Continúa a CAPA 5                                  │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
├─────────────────────────────────────────────────────────────────┐
│ CAPA 5: ¿Es una persona viva (liveness check)?                │
├─────────────────────────────────────────────────────────────────┤
│ Código:                                                         │
│   liveness_check = self._check_liveness(image_data)            │
│   if not liveness_check["is_alive"]:                           │
│       Lanza: HTTPException(401, "Liveness check fallida")      │
│                                                                 │
│ Validaciones:                                                   │
│ ├─ Detección de YOLO: objetos sospechosos                     │
│ ├─ Busca gafas, máscaras, etc.                                │
│ └─ Detecta si es foto vs persona viva                         │
│                                                                 │
│ ❌ SI FALLA (foto estática detectada):                          │
│    └─ Retorna al frontend: error 401                           │
│       "Se detectó una foto. Captura en vivo"                   │
│                                                                 │
│ ✅ SI PASÓ: Continúa a CAPA 6                                  │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
├─────────────────────────────────────────────────────────────────┐
│ CAPA 6: ⚠️ ¿EL ROSTRO PERTENECE A ESTE USUARIO? (CRÍTICA)     │
├─────────────────────────────────────────────────────────────────┤
│ Código:                                                         │
│   verification_result = self._compare_faces(                   │
│       image_data,          # Imagen capturada                  │
│       user_images          # Rostros registrados del usuario   │
│   )                                                             │
│                                                                 │
│ Validaciones en _compare_faces():                              │
│                                                                 │
│ a) ¿user_images está vacío?                                   │
│    ├─ if not user_images → return {match: False}              │
│    └─ Fail-safe contra lista vacía                            │
│                                                                 │
│ b) ¿Se puede extraer encoding del rostro capturado?            │
│    ├─ Utiliza face_recognition library                        │
│    ├─ Si no hay encoding → return {match: False}              │
│    └─ Rostro inválido/distorsionado                           │
│                                                                 │
│ c) COMPARACIÓN ESTRICTA: Para cada imagen registrada:          │
│    ├─ Carga imagen registrada                                 │
│    ├─ Extrae encoding (características faciales)               │
│    ├─ Calcula distancia euclidiana:                           │
│    │  └─ 0.0 = Idéntico, 1.0 = Diferente                    │
│    │                                                            │
│    └─ Evalúa match:                                           │
│       ├─ Threshold: distance < 0.55 (ESTRICTO)                │
│       ├─ Confianza mínima: 35%                                │
│       └─ Requiere AL MENOS 1 coincidencia                     │
│                                                                 │
│    Ejemplo de salida:                                          │
│    Imagen 1: distance=0.32 → ✓ MATCH (confianza: 68%)        │
│    Imagen 2: distance=0.58 → ✗ NO MATCH                       │
│    Imagen 3: distance=0.45 → ✓ MATCH (confianza: 55%)        │
│                                                                 │
│ ❌ SI FALLA (ninguna coincidencia):                             │
│    └─ Lanza: HTTPException(401,                               │
│       "El rostro no pertenece a este usuario")                 │
│       Retorna al frontend: error 401                           │
│       Modal abierto para reintentar                            │
│                                                                 │
│ ✅ SI PASÓ (al menos 1 coincidencia):                          │
│    └─ Continúa a CAPA 7 (LOGIN EXITOSO)                       │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
├─────────────────────────────────────────────────────────────────┐
│ CAPA 7: ✅ TODAS LAS VALIDACIONES PASARON - LOGIN EXITOSO      │
├─────────────────────────────────────────────────────────────────┤
│ Retorna al frontend:                                            │
│ {                                                               │
│   "verified": true,                                            │
│   "message": "✅ Identidad verificada. Login exitoso.",       │
│   "confidence": 67.5,  # Porcentaje de similitud               │
│   "user_id": "uuid"                                            │
│ }                                                               │
│                                                                 │
│ [Frontend]:                                                     │
│ ├─ Guarda access_token en localStorage                         │
│ ├─ Guarda user_id en localStorage                              │
│ ├─ Cierra modal facial                                         │
│ ├─ Animación de salida                                         │
│ └─ Redirige a /home (dashboard)                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 COMPARACIÓN CON VULNERABILIDAD ORIGINAL

### ❌ ANTES (VULNERABLE)

```python
def verify_face_for_login(self, image_data, user_id):
    user_images = self.get_user_facial_images(user_id)
    
    # ❌ NO VALIDABA SI user_images ESTABA VACÍO
    # ❌ Podría continuar con list = []
    
    # Rostos podrían ser comparados con lista vacía
    verification_result = self._compare_faces(image_data, user_images)
    
    # ⚠️ RESULTADO: Un rostro cualquiera podría lograr login
    # porque la comparación con lista vacía retornaba True
```

**Problema**: Sin validar si `user_images` está vacío, se podía comparar contra nada y pasar la validación.

### ✅ DESPUÉS (SEGURO)

```python
def verify_face_for_login(self, image_data, user_id):
    # ... validaciones previas ...
    
    # ✅ VALIDACIÓN CRÍTICA AÑADIDA
    user_images = self.get_user_facial_images(user_id)
    
    if not user_images:  # ← LÍNEA CRÍTICA 289-292
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No hay rostro registrado para este usuario"
        )
    
    # ✅ Garantizado: user_images contiene ≥1 ruta
    verification_result = self._compare_faces(image_data, user_images)
    
    if not verification_result["match"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El rostro no pertenece a este usuario"
        )
    
    # ✅ RESULTADO: Todos los controles pasaron
    return {"verified": True, ...}
```

**Solución**: Ahora se valida explícitamente que haya al menos un rostro antes de comparar.

---

## 📊 MATRIZ DE SEGURIDAD

| Capa | Validación | Línea | Código | Resultado Fallo |
|------|-----------|-------|--------|-----------------|
| 1 | Usuario existe | 272-276 | `user_doc.exists` | 401 ❌ |
| 2 | Facial habilitado | 281-285 | `facial_enabled` | 403 ❌ |
| **3** | **Rostro registrado** | **289-292** | **`if not user_images`** | **401 ❌** |
| 4 | Rostro detectado | 294-304 | `detect_face_in_image` | 401 ❌ |
| 5 | Liveness check | 306-310 | `_check_liveness` | 401 ❌ |
| 6 | Match verificado | 312-319 | `_compare_faces` | 401 ❌ |
| 7 | Frontend OK | - | Mostrar éxito | Redirecciona |

**Capa 3 es la más crítica** (previene la vulnerabilidad identificada)

---

## 🔍 CÓMO PROBAR LA SEGURIDAD

### Prueba 1: Sin Rostro Registrado ✅
```
1. Crear usuario: test@example.com
2. NO registrar rostro
3. Intentar login
4. ❌ ESPERADO: "No hay rostro registrado"
```

### Prueba 2: Rostro Diferente ✅
```
1. Usuario A tiene su rostro registrado
2. Usuario B intenta login como A
3. Captura su propio rostro (no el de A)
4. ❌ ESPERADO: "Rostro no pertenece a este usuario"
```

### Prueba 3: Foto Estática ✅
```
1. Usuario válido con rostro
2. Intenta login con FOTO IMPRESA
3. ❌ ESPERADO: "Liveness check fallida"
```

### Prueba 4: Exitosa ✅
```
1. Usuario válido con rostro
2. Intenta login con su propio rostro
3. ✅ ESPERADO: Redirige a /home
```

---

## 🛡️ CONCLUSIÓN

El sistema ahora tiene **7 capas de seguridad** que garantizan:

✅ No se puede hacer login sin rostro registrado  
✅ No se puede usar rostro de otra persona  
✅ No se puede burlarse con fotos estáticas  
✅ Se requiere coincidencia real con rostro del usuario  
✅ Validaciones en backend + frontend  
✅ Mensajes de error específicos para debugging  
✅ Logs detallados para auditoría  

**La vulnerabilidad identificada ha sido CORREGIDA** ✅
