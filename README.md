# 🔐 USFQ Token Extractor Service

Microservicio para extraer tokens de sesión de la plataforma USFQ (D2L Brightspace).
Diseñado para ser llamado desde **n8n** workflows.

## 📦 Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/health` | Health check para EasyPanel |
| GET | `/api/obtener-tokens` | Extrae tokens usando variables de entorno |
| POST | `/api/obtener-tokens` | Extrae tokens con credenciales en body |

## 🚀 Despliegue en EasyPanel

### 1. Subir a GitHub

```bash
cd usfq-token-service
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/TU_USUARIO/usfq-token-service.git
git push -u origin main
```

### 2. Crear App en EasyPanel

1. Ve a EasyPanel → **+ Create** → **App**
2. Selecciona **GitHub** y conecta tu repositorio
3. EasyPanel detectará el `Dockerfile`

### 3. Configurar Variables de Entorno

En EasyPanel → Tu App → **Environment**:

```
USFQ_EMAIL=tu_email@estud.usfq.edu.ec
USFQ_PASSWORD=tu_contraseña
```

### 4. Configurar Puerto

- **Container Port**: 8000
- **Published Port**: 8000 (o el que prefieras)

### 5. Deploy

Click en **Deploy** y espera a que termine el build.

## 🔗 Uso desde n8n

### Opción 1: HTTP Request GET (simple)

```
GET https://tu-app.easypanel.host/api/obtener-tokens
```

Usa las variables de entorno configuradas.

### Opción 2: HTTP Request POST (flexible)

```
POST https://tu-app.easypanel.host/api/obtener-tokens
Content-Type: application/json

{
  "email": "tu_email@estud.usfq.edu.ec",
  "password": "tu_contraseña"
}
```

### Respuesta

```json
{
  "success": true,
  "d2lSessionVal": "xxx...",
  "d2lSecureSessionVal": "xxx...",
  "csrfToken": "xxx...",
  "error": null
}
```

## 🔄 Ejemplo Workflow n8n

```
[Schedule Trigger] → [HTTP Request: Obtener Tokens] → [Set Variables] → [HTTP Request: Usar Tokens]
```

1. **Schedule Trigger**: Configura cada cuánto refrescar tokens
2. **HTTP Request**: GET a `/api/obtener-tokens`
3. **Set Variables**: Guarda los tokens en variables del workflow
4. **HTTP Request**: Usa las cookies en headers para llamadas a D2L
