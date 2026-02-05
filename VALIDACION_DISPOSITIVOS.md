# 🔒 Validación Mejorada de Liveness Detection

## Descripción
Se ha implementado una validación **CRÍTICA** en `_check_liveness()` que detecta si el rostro está siendo presentado a través de un dispositivo (pantalla, teléfono, tablet, monitor, TV, etc.).

## ¿Qué se detecta?

### 🚫 RECHAZA AUTOMÁTICAMENTE (Security Level: CRÍTICO)
Estas detecciones provocan **rechazo inmediato**:

| Dispositivo | Clase COCO | Razón |
|------------|-----------|-------|
| **Laptop** | 62 | Pantalla donde se podría mostrar rostro fake |
| **TV/Monitor** | 63 | Pantalla grande donde se muestra un rostro |
| **Celular/Teléfono** | 74 | Pantalla pequeña mostrando rostro falso |
| **Control Remoto** | 65 | Indica presencia de pantalla cercana |
| **Libro/Papel** | 73 | Podría contener foto impresa del rostro |

**Error retornado:**
```
❌ VERIFICACIÓN FALLIDA: Se detectó un dispositivo de pantalla 
(laptop/tv/phone). El rostro debe presentarse directamente, 
no a través de una pantalla, teléfono, tablet o monitor.
```

---

### ⚠️ RECHAZA SI HAY 2+ ACCESORIOS (Security Level: ALTO)
Si se detectan múltiples accesorios:

| Accesorio | Problema |
|-----------|----------|
| Gafas oscuras | Ocultan los ojos |
| Sombrero/Gorro | Oculta características del rostro |
| Máscara | Oculta el rostro completamente |
| Corbata grande | Cubre zona inferior del rostro |

**Ejemplo:**
- Gafas + Sombrero = **RECHAZADO**
- Solo gafas = **ADVERTENCIA** (permitido con registro)

---

### 🟡 ADVERTENCIA (Security Level: MEDIO)
Se detectan objetos pero se permite con precaución:

| Objeto | Impacto |
|--------|--------|
| Botella | Puede ocluir parte del rostro |
| Taza/Vaso | Objeto frente al rostro |
| Fruta | Distracción visual |
| Utensilio | Distracción visual |

**Ejemplo de respuesta:**
```json
{
  "is_alive": true,
  "reason": "⚠️ ADVERTENCIA: Se detectaron objetos (bottle, cup). 
             Imagen aceptada pero verificada con objetos presentes.",
  "security_level": "MEDIO",
  "warnings": ["bottle", "cup"]
}
```

---

### ✅ ACEPTADO (Security Level: BAJO)
Rostro presenta directamente sin objetos sospechosos.

---

## Ejemplos de Escenarios

### ❌ RECHAZADO - Mostrar rostro en la pantalla del celular
```
[⚠️ DEVICE] CELL PHONE detectado con 95% confianza
[❌ RECHAZO] Se detectó dispositivo de video: cell phone
```
**Razón:** El usuario está mostrando su rostro a través de la pantalla del teléfono (captura de pantalla, video en directo, etc.)

---

### ❌ RECHAZADO - Rostro en monitor/pantalla
```
[⚠️ DEVICE] LAPTOP detectado con 87% confianza (ocupa 45.3% de la imagen)
[❌ RECHAZO] Se detectó dispositivo de pantalla: laptop
```
**Razón:** El rostro está siendo mostrado en la pantalla de una laptop

---

### ⚠️ ADVERTENCIA - Rostro con gafas
```
[⚠️ ACCESORIO] glasses detectado
[⚠️ ADVERTENCIA] Objetos detectados: glasses
```
**Resultado:** Se permite pero se registra en logs

---

### ✅ ACEPTADO - Rostro limpio
```
[LOG] ========== ANÁLISIS YOLO ==========
[LOG] ====================================
✅ Verificación de liveness exitosa
```

---

## Flujo de Verificación en Login

```
1. Usuario envía foto/video para login
   ↓
2. Detección de rostro (MediaPipe) ✓
   ↓
3. ⚠️ LIVENESS CHECK (NEW - MEJORADO)
   ├─ ¿Se detecta dispositivo (pantalla, TV, phone)?
   │  ├─ SÍ → 🚫 RECHAZAR INMEDIATAMENTE
   │  └─ NO → Continuar
   │
   ├─ ¿Hay 2+ accesorios sospechosos?
   │  ├─ SÍ → 🚫 RECHAZAR INMEDIATAMENTE
   │  └─ NO → Continuar
   │
   └─ ¿Hay objetos sospechosos (1 accesorio, botellas, etc.)?
      ├─ SÍ → ⚠️ ADVERTENCIA (pero permitir)
      └─ NO → ✅ ACEPTAR
   ↓
4. Comparación de rostro (face_recognition) ✓
   ↓
5. ✅ LOGIN EXITOSO O ❌ RECHAZADO
```

---

## Clases COCO Utilizadas

### Dispositivos (CRITICAL - Clase 62, 63, 65, 73, 74)
```python
device_classes = {
    62: "laptop",        # RECHAZA
    63: "tv",            # RECHAZA
    65: "remote",        # RECHAZA (indica pantalla)
    73: "book",          # RECHAZA (foto impresa)
    74: "cell phone",    # RECHAZA
}
```

### Accesorios (HIGH - 2+ detecciones)
```python
accessory_classes = {
    0: "person",         # Persona (oclusor)
    27: "tie",           # Corbata
    28: "cake",          # Objeto frente
    29: "couch",         # Objeto grande
    30: "potted plant",  # Objeto oclusivo
}
```

### Objetos Sospechosos (MEDIUM - 1+ detecciones)
```python
suspicious_classes = {
    34: "bottle",        # Botella
    35: "wine glass",    # Cristal
    36: "cup",           # Taza
    42: "spoon",         # Utensilio
    43: "bowl",          # Recipiente
    44-52: "alimentos",  # Frutas, pizza, etc.
}
```

---

## Mejoras Implementadas

✅ **Detección de dispositivos de pantalla**
- Rechaza automáticamente si hay laptop, TV, monitor
- Rechaza si hay teléfono/tablet detectado
- Rechaza si hay control remoto (indica pantalla)

✅ **Detección de accesorios múltiples**
- Rechaza si hay 2 o más accesorios
- Permite 0 o 1 accesorio con advertencia

✅ **Logging mejorado**
- Registra qué dispositivos se detectaron
- Porcentaje de ocupación en la imagen
- Nivel de confianza de YOLO
- Posición del dispositivo (bbox)

✅ **Manejo de errores seguro**
- En caso de error en YOLO, rechaza por seguridad (antes permitía)
- Mensajes claros para el usuario
- Niveles de seguridad identificados

---

## Testing Recomendado

### Pruebas que deberían FALLAR (✅ seguridad OK)
1. Mostrar rostro en pantalla del celular
2. Mostrar rostro en pantalla de laptop
3. Mostrar rostro en TV/monitor
4. Mostrar foto impresa en papel
5. Rostro con gafas + sombrero
6. Rostro con máscara

### Pruebas que deberían PASAR (✅ seguridad OK)
1. Rostro directo a la cámara, sin accesorios
2. Rostro con solo gafas (con advertencia)
3. Rostro con solo sombrero (con advertencia)
4. Buena iluminación, sin objetos en el fondo

---

## Configuración (Thresholds)

```python
DISTANCE_THRESHOLD = 0.55          # Para face_recognition
CONFIDENCE_MIN = 35                # % mínimo de confianza
LIVENESS_DEVICE_THRESHOLD = 0.5    # Confianza mínima YOLO
```

Estos valores pueden ajustarse en `_check_liveness()` según necesidad.

---

## Impacto en Seguridad

| Vulnerabilidad | Antes | Después |
|----------------|-------|---------|
| Rostro en pantalla | ⚠️ Permitido | 🚫 RECHAZADO |
| Rostro con máscara | ⚠️ Permitido | 🚫 RECHAZADO |
| Foto impresa mostrada | ⚠️ Permitido | 🚫 RECHAZADO |
| Foto en papel | ⚠️ Permitido | 🚫 RECHAZADO |
| Múltiples accesorios | ⚠️ Permitido | 🚫 RECHAZADO |

---

## Próximos Pasos Opcionales

1. **Detección de emojis/filtros**: Agregar clases para detectar filtros virtuales
2. **Análisis de reflejo**: Detectar reflejos de pantalla en los ojos
3. **Análisis de profundidad**: Usar profundidad para confirmar que es persona real
4. **Detección de movimiento**: Verificar que hay movimiento natural
5. **Detección de fondo**: Analizar si el fondo es sospechoso (pantalla verde, etc.)
