"""
API FastAPI para el servicio de extracción de tokens USFQ
Endpoints para n8n - CON AUTENTICACIÓN API KEY
"""
import os
import secrets
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

from token_extractor import obtener_tokens

# Cargar variables de entorno
load_dotenv()

app = FastAPI(
    title="USFQ Token Extractor API",
    description="API para extraer cookies y tokens de la plataforma USFQ",
    version="1.0.0"
)

# CORS para permitir llamadas desde n8n
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# Seguridad - API Key
# ==========================================

async def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    """Verifica que la API Key sea válida"""
    expected_key = os.getenv("API_KEY", "")
    
    if not expected_key:
        raise HTTPException(status_code=500, detail="API_KEY no configurada")
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Header X-API-Key requerido")
    
    if not secrets.compare_digest(x_api_key, expected_key):
        raise HTTPException(status_code=403, detail="API Key inválida")
    
    return True


# ==========================================
# Modelos
# ==========================================

class CredentialsRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    success: bool
    d2lSessionVal: str
    d2lSecureSessionVal: str
    csrfToken: str
    error: Optional[str] = None


# ==========================================
# Endpoints
# ==========================================

@app.get("/")
async def root():
    return {"status": "running", "service": "USFQ Token Extractor", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/obtener-tokens", response_model=TokenResponse)
async def api_obtener_tokens(
    credentials: CredentialsRequest,
    _: bool = Depends(verify_api_key)
):
    """
    Obtiene los tokens de sesión de USFQ.
    
    Headers:
    - X-API-Key: Tu API key secreta
    
    Body:
    - email: Correo USFQ
    - password: Contraseña USFQ
    """
    try:
        result = await obtener_tokens(credentials.email, credentials.password)
        return TokenResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
