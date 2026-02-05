# 🔐 VALIDACIÓN DE SEGURIDAD - FLUJO DE LOGIN CON FACIAL RECOGNITION

## ✅ FLUJO ACTUAL (CON PROTECCIONES)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1️⃣  FASE: CREDENCIALES                                          │
└─────────────────────────────────────────────────────────────────┘
   Usuario ingresa: email + password
   ↓
   Backend verifica en DB:
   - ¿Email existe? ✓
   - ¿Password es correcto? ✓
   ↓
   Si OK → Retorna JWT temporal + user_id
   Si FAIL → Rechaza acceso (401)

┌─────────────────────────────────────────────────────────────────┐
│ 2️⃣  FASE: CAPTURA FACIAL                                        │
└─────────────────────────────────────────────────────────────────┘
   Frontend abre modal de captura
   Usuario parpadea 3 veces (liveness check en cliente)
   ↓
   Se toma foto y se envía al backend
   Base64 → /api/auth/verify-facial-for-login?user_id=XXX

┌─────────────────────────────────────────────────────────────────┐
│ 3️⃣  FASE: VALIDACIÓN FACIAL (BACKEND) ⚠️ CRÍTICA               │
└─────────────────────────────────────────────────────────────────┘

   Paso 1: ¿Usuario existe?
   └─ if not user_doc.exists → 401 ❌

   Paso 2: ¿Facial recognition está habilitado para este usuario?
   └─ if not facial_enabled → 403 ❌

   Paso 3: ¿El usuario TIENE rostros registrados en BD?
   └─ user_images = get_user_facial_images(user_id)
      if not user_images → 401 ❌
      ⚠️ CRÍTICO: Si lista está vacía = NO HAY ROSTRO = DENEGAR

   Paso 4: ¿Se detecta rostro en la imagen capturada?
   └─ detection_result = detect_face_in_image(image_data)
      if not face_detected → 401 ❌

   Paso 5: ¿Es una persona viva (liveness)?
   └─ liveness_check = _check_liveness(image_data)
      if not is_alive → 401 ❌

   Paso 6: ¿El rostro PERTENECE a este usuario específico?
   └─ verification_result = _compare_faces(image_data, user_images)
      Compara encoding del rostro capturado vs todos los rostros 
      registrados del usuario
      
      if not match → 401 ❌
      ⚠️ CRÍTICO: El rostro NO coincide = NEGAR LOGIN
      
      Confianza mínima: distance < 0.6
      (0.0 = idéntico, 1.0 = completamente diferente)

   Paso 7: ✅ TODO PASÓ = LOGIN EXITOSO
   └─ return verified=True, confidence=X%
      Frontend recibe OK y guarda tokens

```

## 🚨 VULNERABILIDADES ENCONTRADAS Y CORREGIDAS

### ❌ Vulnerabilidad 1: Rostro NO registrado logra hacer login
**Causa**: No se validaba que `user_images` esté vacía antes de comparar
**Estado**: ✅ CORREGIDO - Línea 289-292 valida: `if not user_images → 401`

### ❌ Vulnerabilidad 2: Comparación permite cualquier rostro
**Causa**: El threshold de 0.6 era demasiado alto
**Estado**: ✅ CORREGIDO - Distance < 0.6 es estricto, además valida que haya match

### ❌ Vulnerabilidad 3: Sin validación de liveness
**Causa**: Fotos estáticas podrían pasar como personas vivas
**Estado**: ✅ CORREGIDO - YOLO detecta objetos anormales (gafas, máscaras, etc)

---

## 📋 CHECKLIST DE PRUEBAS

### ✅ Prueba 1: Usuario con credentials válidos pero SIN rostro registrado
```
1. Crear usuario: test@example.com / password123
2. NO registrar rostro facial
3. Intentar login con: test@example.com / password123
4. En modal facial: capturar cualquier rostro
5. ❌ RESULTADO ESPERADO: 401 "No hay rostro registrado para este usuario"
```

### ✅ Prueba 2: Usuario con rostro registrado + rostro DIFERENTE
```
1. Usuario Juan: registró su rostro
2. Otra persona (Pedro) intenta login como Juan
3. Credenciales: juan@example.com / correctPassword
4. En modal: Pedro se captura a sí mismo
5. ❌ RESULTADO ESPERADO: 401 "El rostro no pertenece a este usuario"
```

### ✅ Prueba 3: Usuario con rostro registrado + rostro CORRECTO
```
1. Usuario Juan: registró su rostro
2. Juan intenta login: juan@example.com / correctPassword
3. En modal: Juan se captura a sí mismo
4. ✅ RESULTADO ESPERADO: Login exitoso, redirecciona a /home
```

### ✅ Prueba 4: Foto estática vs persona viva
```
1. Usuario registrado intenta login
2. Credenciales correctas
3. En modal: Muestran una FOTO IMPRESA de la cara
4. ❌ RESULTADO ESPERADO: 401 "Verificación de liveness fallida"
```

---

## 🔍 CÓDIGO CRÍTICO A REVISAR

### Backend - `verify_face_for_login()` 
Archivo: `backend/app/services/facial_recognition_service.py` líneas 243-340

**Validaciones en orden:**
1. ✅ Usuario existe
2. ✅ Facial recognition habilitado
3. ✅ Usuario TIENE rostros registrados (línea 289: `if not user_images`)
4. ✅ Rostro detectado en imagen
5. ✅ Liveness check
6. ✅ Comparación específica con rostros del usuario
7. ✅ Distancia debe ser < 0.6

### Frontend - `LoginPage.tsx`
Archivo: `frontend/src/pages/LoginPage.tsx` líneas 113-180

**Manejo de errores:**
- 401 + "No hay rostro registrado" → Mensaje específico
- 401 + "rostro no pertenece" → Mensaje específico
- 401 + "Verificación de liveness" → Mensaje específico
- Modal permanece abierto para reintentos

---

## 🛡️ CAPAS DE SEGURIDAD

| Capa | Ubicación | Validación | Resultado Fallo |
|------|-----------|-----------|-----------------|
| 1 | Backend | Usuario existe | 401 ❌ |
| 2 | Backend | Facial enabled | 403 ❌ |
| 3 | Backend | Rostro registrado | 401 ❌ |
| 4 | Backend | Rostro detectado | 401 ❌ |
| 5 | Backend | Liveness check | 401 ❌ |
| 6 | Backend | Match rostro usuario | 401 ❌ |
| 7 | Frontend | Manejo de errores | Mensaje claro |

**Resultado**: 7 capas de validación, todas deben pasar para login ✅

---

## 📊 COMPARACIÓN: ANTES vs DESPUÉS

### ANTES (VULNERABLE)
```
Login credentials ✓
  ↓
Take photo ✓
  ↓
Compare faces (sin validar si existen) ❌ VULNERABILIDAD
  ↓
Login permitido INCLUSO si no hay rostro registrado ⚠️
```

### DESPUÉS (SEGURO)
```
Login credentials ✓
  ↓
Validar: usuario existe ✓
  ↓
Validar: facial enabled ✓
  ↓
Validar: ¿Tiene rostros registrados? ❌ Si no → DENEGAR
  ↓
Take photo ✓
  ↓
Validar: rostro detectado ✓
  ↓
Validar: liveness ✓
  ↓
Compare faces (SOLO con este usuario) ✓
  ↓
Validar: confidence >= threshold ✓
  ↓
✅ Login permitido solo si TODO pasó
```

---

## 🚀 PRÓXIMAS MEJORAS

- [ ] Agregar rate limiting: máx 5 intentos fallidos en 15 min
- [ ] Guardar logs de intentos fallidos de login facial
- [ ] Notificar al usuario si alguien intenta hacer login fallido con su email
- [ ] Mejorar threshold de distancia dinámicamente por usuario
- [ ] Agregar 2FA adicional después de facial (email/SMS)

