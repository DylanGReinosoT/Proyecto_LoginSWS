# SFS Login Backend - API Documentation

## 🚀 Base URL
```
http://localhost:8000
```

## 📋 Documentación Interactiva
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

---

## 🔐 Autenticación

Para acceder a endpoints protegidos, debes incluir el token JWT en el header:

```
Authorization: Bearer <tu_access_token>
```

---

# 📌 ENDPOINTS

## 1️⃣ Health Check (Sin autenticación)

### GET /health
Verifica que el servidor esté en funcionamiento

**Request:**
```bash
GET http://localhost:8000/health
```

**Response (200):**
```json
{
  "status": "healthy",
  "environment": "development",
  "version": "1.0.0"
}
```

---

### GET /
Bienvenida a la API

**Request:**
```bash
GET http://localhost:8000/
```

**Response (200):**
```json
{
  "message": "Bienvenido a SFS Login Backend API",
  "docs": "/api/docs",
  "version": "1.0.0"
}
```

---

## 2️⃣ AUTENTICACIÓN - /api/auth

### POST /api/auth/register
Registra un nuevo usuario en el sistema

**Request:**
```bash
POST http://localhost:8000/api/auth/register
Content-Type: application/json

{
  "email": "usuario@example.com",
  "username": "usuariotest",
  "password": "Password123!",
  "full_name": "Juan Pérez"
}
```

**Response (201 - Created):**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "usuario@example.com",
  "username": "usuariotest",
  "full_name": "Juan Pérez",
  "is_active": true,
  "two_factor_enabled": false,
  "facial_recognition_enabled": false,
  "created_at": "2026-02-01T10:30:00"
}
```

**Errores:**

❌ Email inválido (400):
```json
{
  "detail": "Email inválido"
}
```

❌ Email ya registrado (409):
```json
{
  "detail": "El email ya está registrado"
}
```

❌ Contraseña débil (400):
```json
{
  "detail": "La contraseña debe contener al menos un carácter especial"
}
```

---

### POST /api/auth/login
Autentica un usuario y devuelve un token JWT

**Request:**
```bash
POST http://localhost:8000/api/auth/login
Content-Type: application/json

{
  "email": "usuario@example.com",
  "password": "Password123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errores:**

❌ Credenciales inválidas (401):
```json
{
  "detail": "Credenciales inválidas"
}
```

❌ Usuario inactivo (403):
```json
{
  "detail": "Usuario inactivo"
}
```

---

### GET /api/auth/health
Verifica que el servicio de autenticación esté funcionando

**Request:**
```bash
GET http://localhost:8000/api/auth/health
```

**Response (200):**
```json
{
  "status": "healthy",
  "service": "authentication"
}
```

---

## 3️⃣ USUARIOS - /api/users

### GET /api/users/me
Obtiene el perfil del usuario autenticado

**Request:**
```bash
GET http://localhost:8000/api/users/me
Authorization: Bearer <tu_access_token>
```

**Response (200):**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "usuario@example.com",
  "username": "usuariotest",
  "full_name": "Juan Pérez",
  "is_active": true,
  "two_factor_enabled": false,
  "facial_recognition_enabled": false,
  "created_at": "2026-02-01T10:30:00"
}
```

**Errores:**

❌ Token no proporcionado (403):
```json
{
  "detail": "Token inválido"
}
```

---

### GET /api/users/{user_id}
Obtiene la información de un usuario específico

**Request:**
```bash
GET http://localhost:8000/api/users/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <tu_access_token>
```

**Response (200):**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "usuario@example.com",
  "username": "usuariotest",
  "full_name": "Juan Pérez",
  "is_active": true,
  "two_factor_enabled": false,
  "facial_recognition_enabled": false,
  "created_at": "2026-02-01T10:30:00"
}
```

**Errores:**

❌ Usuario no encontrado (404):
```json
{
  "detail": "Usuario no encontrado"
}
```

---

### PUT /api/users/me
Actualiza el perfil del usuario autenticado

**Request:**
```bash
PUT http://localhost:8000/api/users/me
Authorization: Bearer <tu_access_token>
Content-Type: application/json

{
  "full_name": "Juan Carlos Pérez",
  "password": "NewPassword456!"
}
```

**Response (200):**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "usuario@example.com",
  "username": "usuariotest",
  "full_name": "Juan Carlos Pérez",
  "is_active": true,
  "two_factor_enabled": false,
  "facial_recognition_enabled": false,
  "created_at": "2026-02-01T10:30:00"
}
```

**Nota:** Puedes actualizar solo algunos campos (full_name, password o ambos)

---

### POST /api/users/facial-recognition/enable
Habilita autenticación con reconocimiento facial

**Request:**
```bash
POST http://localhost:8000/api/users/facial-recognition/enable
Authorization: Bearer <tu_access_token>
```

**Response (200):**
```json
{
  "message": "Reconocimiento facial habilitado",
  "user": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "usuario@example.com",
    "username": "usuariotest",
    "full_name": "Juan Pérez",
    "is_active": true,
    "two_factor_enabled": false,
    "facial_recognition_enabled": true,
    "created_at": "2026-02-01T10:30:00"
  }
}
```

---

### POST /api/users/facial-recognition/disable
Desactiva autenticación con reconocimiento facial

**Request:**
```bash
POST http://localhost:8000/api/users/facial-recognition/disable
Authorization: Bearer <tu_access_token>
```

**Response (200):**
```json
{
  "message": "Reconocimiento facial deshabilitado",
  "user": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "usuario@example.com",
    "username": "usuariotest",
    "full_name": "Juan Pérez",
    "is_active": true,
    "two_factor_enabled": false,
    "facial_recognition_enabled": false,
    "created_at": "2026-02-01T10:30:00"
  }
}
```

---

### GET /api/users/health
Verifica que el servicio de usuarios esté funcionando

**Request:**
```bash
GET http://localhost:8000/api/users/health
```

**Response (200):**
```json
{
  "status": "healthy",
  "service": "users"
}
```

---

## 4️⃣ RECONOCIMIENTO FACIAL - /api/facial

### POST /api/facial/capture
Captura y guarda una imagen facial para el usuario autenticado

**Request:**
```bash
POST http://localhost:8000/api/facial/capture
Authorization: Bearer <tu_access_token>
Content-Type: application/json

{
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "description": "Foto de registro"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Imagen facial capturada correctamente",
  "filepath": "app/facial_data/user-id/face_20260201_103000.jpg"
}
```

**Errores:**

❌ Imagen inválida (400):
```json
{
  "detail": "Imagen inválida"
}
```

---

### POST /api/facial/detect
Detecta si hay un rostro en la imagen (sin autenticación)

**Request:**
```bash
POST http://localhost:8000/api/facial/detect
Content-Type: application/json

{
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
}
```

**Response (200):**
```json
{
  "face_detected": true,
  "message": "Rostro detectado correctamente",
  "bbox": {
    "x": 100,
    "y": 50,
    "width": 150,
    "height": 200,
    "confidence": 0.95
  },
  "confidence": 0.95
}
```

**Errores:**

❌ No se detectó rostro (400):
```json
{
  "detail": "No se detectó rostro en la imagen"
}
```

---

### POST /api/facial/verify
Verifica si el rostro coincide con el registrado (con autenticación)

**Request:**
```bash
POST http://localhost:8000/api/facial/verify
Authorization: Bearer <tu_access_token>
Content-Type: application/json

{
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
}
```

**Response (200):**
```json
{
  "verified": true,
  "message": "Rostro verificado correctamente",
  "confidence": 0.92
}
```

**Errores:**

❌ No tiene rostro registrado (400):
```json
{
  "detail": "El usuario no tiene rostro registrado"
}
```

---

### GET /api/facial/my-images
Obtiene todas las imágenes faciales guardadas del usuario

**Request:**
```bash
GET http://localhost:8000/api/facial/my-images
Authorization: Bearer <tu_access_token>
```

**Response (200):**
```json
{
  "images": [
    "app/facial_data/user-id/face_20260201_103000.jpg",
    "app/facial_data/user-id/face_20260201_102500.jpg"
  ],
  "count": 2
}
```

---

### GET /api/facial/health
Verifica que el servicio de reconocimiento facial esté funcionando

**Request:**
```bash
GET http://localhost:8000/api/facial/health
```

**Response (200):**
```json
{
  "status": "healthy",
  "service": "facial_recognition"
}

---

# 📝 GUÍA DE TESTING EN POSTMAN

## 1. Crear una Colección en Postman

1. Abre Postman
2. Click en "Collections" → "Create Collection"
3. Nombre: "SFS Login Backend"
4. Crea estas carpetas dentro:
   - Health Check
   - Authentication
   - Users

## 2. Variables de Entorno en Postman

En Postman, crea un Environment con estas variables:

```
base_url: http://localhost:8000
access_token: (se llena después de hacer login)
user_id: (se llena después del login o registro)
```

Luego usa `{{base_url}}` en lugar de escribir la URL completa.

## 3. Flujo de Testing Recomendado

### Paso 1: Health Check
```
GET {{base_url}}/health
```
✅ Verifica que el servidor esté corriendo

### Paso 2: Registrar un Usuario
```
POST {{base_url}}/api/auth/register
Body (JSON):
{
  "email": "test@example.com",
  "username": "testuser",
  "password": "TestPassword123!",
  "full_name": "Test User"
}
```
✅ Copia el `user_id` a la variable de Postman

### Paso 3: Login
```
POST {{base_url}}/api/auth/login
Body (JSON):
{
  "email": "test@example.com",
  "password": "TestPassword123!"
}
```
✅ Copia el `access_token` a la variable de Postman

### Paso 4: Obtener Perfil
```
GET {{base_url}}/api/users/me
Headers:
- Authorization: Bearer {{access_token}}
```
✅ Verifica que recibes tus datos

### Paso 5: Actualizar Perfil
```
PUT {{base_url}}/api/users/me
Headers:
- Authorization: Bearer {{access_token}}
Body (JSON):
{
  "full_name": "Test User Actualizado"
}
```
✅ Verifica que se actualizó

### Paso 6: Habilitar Reconocimiento Facial
```
POST {{base_url}}/api/users/facial-recognition/enable
Headers:
- Authorization: Bearer {{access_token}}
```
✅ Verifica que `facial_recognition_enabled` es true

---

# ⚠️ NOTAS IMPORTANTES

## Requisitos de Contraseña
```
✓ Mínimo 8 caracteres
✓ Al menos una mayúscula
✓ Al menos una minúscula
✓ Al menos un número
✓ Al menos un carácter especial (!@#$%^&*(),.?":{}|<>)
```

Ejemplo válido: `Password123!`

## Token JWT
- **Tipo**: Bearer token
- **Expiración**: 30 minutos
- **Ubicación**: Header `Authorization: Bearer <token>`

## Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| 401 Unauthorized | Token no válido o expirado | Haz login de nuevo |
| 403 Forbidden | Token no incluido | Añade el header Authorization |
| 400 Bad Request | Datos inválidos | Verifica el formato del JSON |
| 409 Conflict | Email ya registrado | Usa otro email |
| 422 Unprocessable Entity | Email no válido | Usa un email con formato correcto |

---

# 🔗 IMPORTAR EN POSTMAN

Puedes importar esta documentación como una colección en Postman usando la opción "Import" con el contenido JSON.

**¡Listo para testing! 🚀**

---

# 🔄 FLUJOS DE NEGOCIO

## Flujo 1: Registro con Captura Facial

```
1. POST /api/auth/register
   └─ Registra usuario en Firebase
      
2. POST /api/facial/capture
   └─ Captura y guarda imagen facial
      └─ Se almacena en: app/facial_data/{user_id}/
      
3. Resultado: Usuario registrado + Rostro guardado localmente
```

### Ejemplo completo:

```bash
# 1. Registrar usuario
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@example.com",
    "username": "usuario",
    "password": "Password123!",
    "full_name": "Juan Pérez"
  }'

# Respuesta:
# {
#   "user_id": "550e8400-e29b-41d4-a716-446655440000",
#   "email": "usuario@example.com",
#   ...
# }

# 2. Capturar foto del usuario
curl -X POST "http://localhost:8000/api/facial/capture" \
  -H "Authorization: Bearer <token_del_paso_1>" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "<imagen_en_base64>",
    "description": "Foto de registro"
  }'

# Respuesta:
# {
#   "success": true,
#   "message": "Imagen facial capturada correctamente",
#   "filepath": "app/facial_data/550e8400.../face_20260201_103000.jpg"
# }
```

---

## Flujo 2: Login con Verificación Facial

```
1. POST /api/auth/login
   └─ Verifica credenciales
      └─ Si son correctas, retorna token
      
2. POST /api/facial/verify
   └─ Verifica rostro del usuario
      └─ Compara con imagen guardada
      
3. Resultado: Acceso concedido si ambas verificaciones son correctas
```

### Ejemplo completo:

```bash
# 1. Login (credenciales)
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@example.com",
    "password": "Password123!"
  }'

# Respuesta:
# {
#   "access_token": "eyJhbGci...",
#   "token_type": "bearer",
#   "expires_in": 1800
# }

# 2. Verificar rostro (con token del paso 1)
curl -X POST "http://localhost:8000/api/facial/verify" \
  -H "Authorization: Bearer <token_del_paso_1>" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "<imagen_en_base64>"
  }'

# Respuesta:
# {
#   "verified": true,
#   "message": "Rostro verificado correctamente",
#   "confidence": 0.92
# }
```

---

## Flujo 3: Solo Detección de Rostro (Sin Autenticación)

```
POST /api/facial/detect
└─ Detecta si hay rostro
   └─ NO requiere token
   └─ Retorna información de la detección
```

### Ejemplo:

```bash
curl -X POST "http://localhost:8000/api/facial/detect" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "<imagen_en_base64>"
  }'

# Respuesta:
# {
#   "face_detected": true,
#   "message": "Rostro detectado correctamente",
#   "bbox": {...},
#   "confidence": 0.95
# }
```

---

# 📁 ESTRUCTURA DE ALMACENAMIENTO LOCAL

Las imágenes faciales se guardan en:

```
backend/
├── app/
│   ├── facial_data/
│   │   ├── {user_id_1}/
│   │   │   ├── face_20260201_103000.jpg
│   │   │   ├── face_20260201_102500.jpg
│   │   │   └── face_20260201_102000.jpg
│   │   ├── {user_id_2}/
│   │   │   ├── face_20260201_101500.jpg
│   │   │   └── ...
│   │   └── ...
│   └── ...
└── ...
```

**Ventajas:**
- Las imágenes se guardan localmente (privacidad)
- Firebase almacena solo datos de usuario
- Mejor rendimiento para verificación
- Fácil escalabilidad

---

# 🔐 IMPLEMENTACIÓN EN FRONTEND (VITE)

## Paso 1: Capturar imagen en base64

```javascript
// Usando canvas desde video
function captureImageAsBase64() {
  const video = document.getElementById('video');
  const canvas = document.getElementById('canvas');
  const ctx = canvas.getContext('2d');
  
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL('image/jpeg').split(',')[1]; // Base64 sin prefijo
}
```

## Paso 2: Enviar a endpoint de captura

```javascript
async function capturarRostro() {
  const imageBase64 = captureImageAsBase64();
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://localhost:8000/api/facial/capture', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      image_base64: imageBase64,
      description: 'Foto de registro'
    })
  });
  
  return await response.json();
}
```

## Paso 3: Verificar rostro en login

```javascript
async function verificarRostro() {
  const imageBase64 = captureImageAsBase64();
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://localhost:8000/api/facial/verify', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      image_base64: imageBase64
    })
  });
  
  return await response.json();
}
```

---

# ⚠️ NOTAS IMPORTANTES

1. **Base64**: Las imágenes deben enviarse en formato base64 sin el prefijo `data:image/jpeg;base64,`
2. **Tamaño de imagen**: Usar imágenes de tamaño razonable (< 5MB)
3. **Calidad**: Asegurar buena iluminación para mejor detección
4. **Token**: Incluir en header `Authorization: Bearer <token>`
5. **CORS**: Ya está configurado para localhost:3000

---

**¡Listo para testing! 🚀**
