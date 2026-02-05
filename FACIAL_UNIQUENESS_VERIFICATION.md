# Verificación de Unicidad Facial - Documentación

## 📋 Resumen
Se ha implementado un sistema de **verificación de rostro único** que garantiza que cada rostro registrado en el sistema sea único. Esto previene que múltiples usuarios se registren con el mismo rostro.

## ✅ Características Implementadas

### 1. **Nuevo método en `FacialRecognitionService`**
**Archivo**: `app/services/facial_recognition_service.py`

```python
def check_facial_uniqueness(self, image_data: bytes, exclude_user_id: str = None) -> dict:
    """
    Verifica si un rostro ya existe en el sistema (en otros usuarios)
    
    Returns:
    - is_unique: True si el rostro no existe en otros usuarios
    - message: Mensaje descriptivo
    - matched_user_id: ID del usuario si se encontró coincidencia
    - confidence: Confianza de la coincidencia (0-100%)
    """
```

**Lógica:**
- Obtiene el encoding del rostro proporcionado
- Compara con todas las imágenes faciales registradas de otros usuarios
- Usa distancia euclidiana (umbral: 0.6) para determinar coincidencia
- Retorna `is_unique=False` si encuentra una coincidencia

### 2. **Protección en Ruta de Captura Durante Registro**
**Archivo**: `app/routes/facial.py`

Endpoint: `POST /api/facial/capture-registration`

```python
# ✅ NUEVA VERIFICACIÓN: Comprobar que el rostro sea único
facial_uniqueness = facial_service.check_facial_uniqueness(
    image_bytes, 
    exclude_user_id=user_id
)

if not facial_uniqueness["is_unique"]:
    raise HTTPException(
        status_code=409,  # Conflict
        detail=f"⛔ El rostro ya está registrado en el sistema. "
               f"Usuario coincidente: {matched_user_id} "
               f"(Confianza: {confidence}%)"
    )
```

**Respuesta de Error (409 Conflict):**
```json
{
    "detail": "⛔ El rostro ya está registrado en el sistema. No se pueden registrar dos usuarios con el mismo rostro. Usuario coincidente: abc123 (Confianza: 92.5%)"
}
```

### 3. **Protección en Servicio de Autenticación**
**Archivo**: `app/services/auth_service.py`

Al registrar un usuario con imagen facial (`UserRegisterSchema.facial_image_base64`):

```python
# ✅ NUEVA VERIFICACIÓN: Comprobar que el rostro sea único
facial_uniqueness = facial_service.check_facial_uniqueness(
    image_data, 
    exclude_user_id=user_id
)

if not facial_uniqueness["is_unique"]:
    # Eliminar el usuario si el rostro ya existe
    db.collection("users").document(user_id).delete()
    
    raise HTTPException(
        status_code=409,
        detail="⛔ El rostro ya está registrado..."
    )
```

**Acción importante:** Si se detecta un rostro duplicado, el usuario **NO es creado** en la base de datos.

### 4. **Nuevo Endpoint para Verificar Unicidad**
**Archivo**: `app/routes/facial.py`

Endpoint: `POST /api/facial/check-uniqueness`

```python
@router.post("/check-uniqueness")
async def check_facial_uniqueness(facial_data: FacialCaptureSchema):
    """
    Verifica si un rostro es único sin guardarlo
    
    Útil para validación previa en el frontend
    """
```

**Solicitud:**
```json
{
    "image_base64": "iVBORw0KGgo..."
}
```

**Respuesta (rostro único):**
```json
{
    "is_unique": true,
    "message": "El rostro es único en el sistema",
    "matched_user_id": null,
    "confidence": 0
}
```

**Respuesta (rostro duplicado):**
```json
{
    "is_unique": false,
    "message": "El rostro ya está registrado por otro usuario",
    "matched_user_id": "user-id-aqui",
    "confidence": 92.5
}
```

### 5. **Esquema Actualizado**
**Archivo**: `app/schemas/facial_schema.py`

Se agregó:
```python
class FacialUniquenessResponseSchema(BaseModel):
    """Respuesta de verificación de unicidad facial"""
    is_unique: bool
    message: str
    matched_user_id: Optional[str] = None
    confidence: float
```

## 🔒 Flujo de Seguridad

### Registro con Captura Facial (Frontend → Backend)

```
1. Usuario completa formulario de registro
   ↓
2. Se abre modal de captura facial
   ↓
3. Se captura imagen y se envía a /api/auth/register
   (incluye facial_image_base64)
   ↓
4. Backend crea el usuario temporalmente
   ↓
5. ✅ VERIFICACIÓN: check_facial_uniqueness()
   ├─ Si es único → Guardar imagen, habilitar facial recognition
   └─ Si es duplicado → Eliminar usuario, retornar error 409
   ↓
6. Frontend maneja error 409 y muestra mensaje de rostro duplicado
```

### Captura Separada (Frontend → Backend)

```
1. Usuario se registra, luego captura rostro después
   ↓
2. POST /api/facial/capture-registration?user_id=xyz
   ↓
3. ✅ VERIFICACIÓN: check_facial_uniqueness()
   ├─ Si es único → Guardar imagen
   └─ Si es duplicado → Retornar error 409
   ↓
4. Frontend maneja respuesta
```

## 📊 Parámetros de Configuración

**DISTANCE_THRESHOLD** (en `check_facial_uniqueness`):
- Valor actual: `0.6`
- Rango: 0 (idéntico) a 1 (completamente diferente)
- Ajusta si necesitas más o menos sensibilidad:
  - Aumentar (ej: 0.7): Menos sensitivo, menos falsos positivos
  - Disminuir (ej: 0.5): Más sensitivo, más falsos positivos

## 🧪 Pruebas Sugeridas

### 1. Verificar Rostro Único
```bash
curl -X POST "http://localhost:8000/api/facial/check-uniqueness" \
  -H "Content-Type: application/json" \
  -d '{"image_base64": "..."}'
```

### 2. Registrar Usuario (con rostro)
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "SecurePass123!",
    "full_name": "Test User",
    "facial_image_base64": "..."
  }'
```

### 3. Intentar Registrar con Rostro Duplicado
Debería retornar:
```json
{
    "detail": "⛔ El rostro ya está registrado en el sistema..."
}
```

## ⚠️ Consideraciones Importantes

1. **Rendimiento**: La verificación compara el rostro con todos los usuarios registrados. Para sistemas con muchos usuarios, considera:
   - Usar una base de datos de embeddings (Faiss, Milvus)
   - Indexación de rostros
   - Caché de encodings

2. **Privacidad**: Los encodings faciales se comparan pero no se almacenan en la BD, solo las imágenes.

3. **Exactitud**: El umbral de 0.6 es estándar para `face_recognition`. Ajusta según pruebas.

4. **Errores**: Si hay error en `check_facial_uniqueness`, por defecto retorna `is_unique=False` para ser más seguro.

## 📝 Cambios Resumidos

| Archivo | Cambio | Impacto |
|---------|--------|--------|
| `facial_recognition_service.py` | `+check_facial_uniqueness()` | Nueva función de verificación |
| `facial.py` | `+ /check-uniqueness` endpoint | Validación previa opcional |
| `facial.py` | Modificar `/capture-registration` | Añadir verificación |
| `auth_service.py` | Modificar `register_user()` | Verificar y rechazar duplicados |
| `facial_schema.py` | `+FacialUniquenessResponseSchema` | Nuevo esquema |

---

**Estado**: ✅ Completado  
**Fecha**: 2026-02-03  
**Versión**: 1.0
