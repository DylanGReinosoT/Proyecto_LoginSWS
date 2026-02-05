# 🔒 Implementación: Verificación de Rostro Único

## ¿Qué se hizo?

Se agregó una **verificación de unicidad de rostro** al sistema de registro. Ahora:
- ✅ Cada usuario solo puede tener UN rostro único en el sistema
- ✅ No se permite registrar dos usuarios con el mismo rostro
- ✅ Se verifica en dos puntos: durante registro y durante captura posterior

## 📍 Cambios por Archivo

### 1️⃣ `app/services/facial_recognition_service.py`
**Agregado:**
```
✅ check_facial_uniqueness(image_data, exclude_user_id=None)
   └─ Compara rostro contra todos los usuarios registrados
   └─ Retorna: {is_unique, message, matched_user_id, confidence}
```

### 2️⃣ `app/routes/facial.py`
**Modificado:**
```
📝 POST /api/facial/capture-registration
   └─ Ahora verifica unicidad ANTES de guardar
   └─ Si rostro existe: Error 409 Conflict
   
✅ POST /api/facial/check-uniqueness (NUEVA RUTA)
   └─ Permite validar rostro sin guardarlo
   └─ Útil para validación previa en frontend
```

### 3️⃣ `app/services/auth_service.py`
**Modificado:**
```
📝 register_user()
   └─ Si facial_image_base64 viene incluida
   └─ Verifica unicidad
   └─ Si hay duplicado: Elimina usuario creado + Error 409
```

### 4️⃣ `app/schemas/facial_schema.py`
**Agregado:**
```
✅ FacialUniquenessResponseSchema
   └─ is_unique: bool
   └─ message: str
   └─ matched_user_id: str | null
   └─ confidence: float
```

## 🔀 Flujo de Verificación

```
REGISTRO CON FOTO
─────────────────────────────────────────────
Usuario envía formulario + foto
         ↓
    ¿Foto ya existe?
     /           \
    SÍ (409)      NO ✅
     ↓            ↓
  Error      Crear usuario
  "Rostro"   + Guardar foto
  duplicado  + Habilitar facial

CAPTURA POSTERIOR
─────────────────────────────────────────────
Usuario ya registrado captura foto
         ↓
    ¿Foto ya existe?
     /           \
    SÍ (409)      NO ✅
     ↓            ↓
  Error      Guardar foto
  "Rostro"   + Habilitar facial
  duplicado
```

## 🎯 Respuestas API

### ✅ Rostro Único (OK)
```json
POST /api/facial/check-uniqueness
{
    "is_unique": true,
    "message": "El rostro es único en el sistema",
    "matched_user_id": null,
    "confidence": 0
}
```

### ❌ Rostro Duplicado (ERROR 409)
```json
POST /api/facial/capture-registration
Status: 409 Conflict
{
    "detail": "⛔ El rostro ya está registrado en el sistema. No se pueden registrar dos usuarios con el mismo rostro. Usuario coincidente: abc-def-123 (Confianza: 92.5%)"
}
```

## 🔧 Detalles Técnicos

**Método de Comparación:**
- Algoritmo: `face_recognition` library (dlib)
- Distancia: Euclidiana (0.0 = idéntico, 1.0 = diferente)
- Umbral: 0.6 (ajustable)

**Proceso:**
1. Extrae encoding facial de imagen proporcionada
2. Recorre todos los directorios de usuarios en `facial_data/`
3. Extrae encoding del primer rostro guardado de cada usuario
4. Calcula distancia euclidiana
5. Si distancia < 0.6 → Coincidencia encontrada

## 🧪 Cómo Probar

### Prueba 1: Validar Rostro Único
```bash
curl -X POST http://localhost:8000/api/facial/check-uniqueness \
  -H "Content-Type: application/json" \
  -d '{"image_base64":"...tu_foto_en_base64..."}'
```

### Prueba 2: Registrar con Foto (Nuevo Usuario)
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nuevo@example.com",
    "username": "nuevouser",
    "password": "SecurePass123!",
    "full_name": "Nuevo Usuario",
    "facial_image_base64": "...foto..."
  }'
```

### Prueba 3: Intentar Registrar con Foto Duplicada
```bash
# Usar la MISMA foto del usuario anterior
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "otro@example.com",
    "username": "otrouser",
    "password": "SecurePass123!",
    "full_name": "Otro Usuario",
    "facial_image_base64": "...MISMA_FOTO..."
  }'

# Resultado esperado: Error 409
```

## ⚙️ Configuración

Si necesitas ajustar la sensibilidad, modifica `DISTANCE_THRESHOLD`:

En `facial_recognition_service.py`, método `check_facial_uniqueness()`:
```python
DISTANCE_THRESHOLD = 0.6  # Cambia este valor
```

- **Aumentar a 0.7+**: Menos restricción (menos falsos positivos)
- **Disminuir a 0.5-**: Más restricción (puede rechazar rostros ligeramente diferentes)

## 📌 Notas Importantes

1. **Privacidad**: Solo se comparan los encodings (datos matemáticos), no las fotos
2. **BD**: El usuario NO se crea si el rostro es duplicado
3. **Error 409**: Indica "Conflict" - estándar REST para duplicados
4. **Performance**: Para 1000+ usuarios, considera indexación de embeddings

---
✅ **Estado**: Listo para usar  
🚀 **Próximos pasos**: Actualizar frontend para manejar error 409 en registro
