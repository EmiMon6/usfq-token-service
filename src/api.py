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

def get_api_key():
    """Obtiene la API Key desde variables de entorno"""
    return os.getenv("API_KEY", "")


async def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    """Verifica que la API Key sea válida"""
    expected_key = get_api_key()
    
    if not expected_key:
        raise HTTPException(
            status_code=500,
            detail="API_KEY no configurada en el servidor"
        )
    
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Header X-API-Key requerido"
        )
    
    if not secrets.compare_digest(x_api_key, expected_key):
        raise HTTPException(
            status_code=403,
            detail="API Key inválida"
        )
    
    return True


# ==========================================
# Modelos Pydantic
# ==========================================

class TokenResponse(BaseModel):
    """Respuesta con los tokens extraídos"""
    success: bool
    d2lSessionVal: str
    d2lSecureSessionVal: str
    csrfToken: str
    error: Optional[str] = None


# ==========================================
# Endpoints PÚBLICOS (sin autenticación)
# ==========================================

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "running",
        "service": "USFQ Token Extractor",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Endpoint de salud para EasyPanel"""
    return {"status": "healthy"}


# ==========================================
# Endpoint PROTEGIDO (requiere API Key)
# ==========================================

@app.get("/api/obtener-tokens", response_model=TokenResponse)
async def api_obtener_tokens(_: bool = Depends(verify_api_key)):
    """
    Obtiene los tokens de sesión de USFQ.
    
    Requiere:
    - Header: X-API-Key (tu API key secreta)
    
    Las credenciales se toman de las variables de entorno del servidor:
    - USFQ_EMAIL
    - USFQ_PASSWORD
    
    Retorna:
    - d2lSessionVal: Cookie de sesión
    - d2lSecureSessionVal: Cookie de sesión segura
    - csrfToken: Token CSRF para requests
    """
    email = os.getenv("USFQ_EMAIL")
    password = os.getenv("USFQ_PASSWORD")
    
    if not email or not password:
        raise HTTPException(
            status_code=500,
            detail="USFQ_EMAIL y USFQ_PASSWORD no configurados en el servidor"
        )
    
    try:
        result = await obtener_tokens(email, password)
        return TokenResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al extraer tokens: {str(e)}"
        )


# ==========================================
# Iniciar servidor
# ==========================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
