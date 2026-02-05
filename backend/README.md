# SFS Login Backend

Backend de autenticación con FastAPI, JWT y Firebase con soporte para doble factor y reconocimiento facial.
Kechavez07.
## Estructura del Proyecto

```
backend/
├── app/
│   ├── core/              # Lógica de seguridad y constantes
│   ├── models/            # Modelos de datos Pydantic
│   ├── schemas/           # Esquemas de entrada/salida
│   ├── routes/            # Endpoints de la API
│   ├── services/          # Lógica de negocio
│   ├── utils/             # Utilidades (validadores, reconocimiento facial)
│   ├── config.py          # Configuración de la aplicación
│   ├── database.py        # Conexión con Firebase
│   └── main.py            # Punto de entrada de la aplicación
├── requirements.txt       # Dependencias del proyecto
├── .env.example          # Ejemplo de variables de entorno
└── README.md             # Este archivo
```

## Requisitos

- Python 3.8+
- Entorno virtual (venv)
- Firebase Project

## Instalación

### 1. Crear y activar el entorno virtual

```bash
python -m venv venv
# En Windows:
.\venv\Scripts\Activate
# En Linux/Mac:
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env con tus credenciales de Firebase
```

#### Opción 1: Usar archivo de credenciales de Firebase

1. Ve a [Firebase Console](https://console.firebase.google.com/)
2. Selecciona tu proyecto
3. Ve a Project Settings → Service Accounts
4. Descarga el JSON de credenciales
5. Renómbralo a `serviceAccountKey.json`
6. Colócalo en la raíz del directorio backend

#### Opción 2: Usar variables de entorno

Obtén las credenciales del archivo JSON descargado y cópialas a `.env`:

```env
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxx@xxx.iam.gserviceaccount.com
```

## Ejecutar la Aplicación

```bash
# Desarrollo
uvicorn app.main:app --reload

# O usando el módulo main
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en: http://localhost:8000

- Documentación interactiva: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Endpoints Disponibles

### Autenticación

- `POST /api/auth/register` - Registrar nuevo usuario
- `POST /api/auth/login` - Iniciar sesión
- `GET /api/auth/health` - Verificar estado

### Usuarios

- `GET /api/users/me` - Obtener perfil del usuario autenticado
- `GET /api/users/{user_id}` - Obtener datos de un usuario
- `PUT /api/users/me` - Actualizar perfil
- `POST /api/users/facial-recognition/enable` - Habilitar reconocimiento facial
- `POST /api/users/facial-recognition/disable` - Desactivar reconocimiento facial

## Ejemplos de Uso

### Registrar usuario

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "usuario",
    "password": "Password123!",
    "full_name": "Nombre Completo"
  }'
```

### Iniciar sesión

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "Password123!"
  }'
```

### Obtener perfil (requiere token)

```bash
curl -X GET "http://localhost:8000/api/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Características Implementadas

✅ Autenticación con JWT
✅ Hash de contraseñas con bcrypt
✅ Validación de datos con Pydantic
✅ Integración con Firebase Firestore
✅ Manejo de errores y excepciones
✅ Documentación automática con Swagger
✅ CORS configurado
✅ Estructura de carpetas escalable

## Características en Desarrollo

🚧 Autenticación de doble factor
🚧 Reconocimiento facial
🚧 Tokens de refresco

## Requisitos de Contraseña

Las contraseñas deben cumplir con:
- Mínimo 8 caracteres
- Al menos una mayúscula
- Al menos una minúscula
- Al menos un número
- Al menos un carácter especial (!@#$%^&*(),.?":{}|<>)

## Configuración de Desarrollo

Para desarrollo, se recomienda:

```env
DEBUG=True
ENVIRONMENT=development
SECRET_KEY=your-development-secret-key
```

Para producción:

```env
DEBUG=False
ENVIRONMENT=production
SECRET_KEY=use-a-secure-random-key
```

## Troubleshooting

### Error: "Token inválido o expirado"

Asegúrate de:
- Incluir el token en el header `Authorization: Bearer <token>`
- El token no ha expirado (30 minutos por defecto)
- El SECRET_KEY es el mismo en todas las instancias

### Error: "Conexión con Firebase fallida"

Verifica:
- El archivo `serviceAccountKey.json` existe en la raíz
- O las variables de entorno están correctamente configuradas
- Tienes las credenciales correctas de Firebase

### Error: "Database not initialized"

Asegúrate de que Firebase está correctamente inicializado en `app/database.py`

## Próximos Pasos

1. Implementar autenticación de doble factor
2. Implementar reconocimiento facial
3. Agregar endpoints para gestión de sesiones
4. Implementar rate limiting
5. Agregar logging
6. Escribir tests unitarios

## Licencia

MIT
