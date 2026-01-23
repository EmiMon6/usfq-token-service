"""
API FastAPI para el servicio de extracción de tokens USFQ
Endpoints para n8n
"""
import os
import asyncio
from fastapi import FastAPI, HTTPException
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
# Modelos Pydantic
# ==========================================

class CredentialsRequest(BaseModel):
    """Credenciales opcionales (si no se usan variables de entorno)"""
    email: Optional[str] = None
    password: Optional[str] = None


class TokenResponse(BaseModel):
    """Respuesta con los tokens extraídos"""
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


@app.post("/api/obtener-tokens", response_model=TokenResponse)
async def api_obtener_tokens(credentials: Optional[CredentialsRequest] = None):
    """
    Obtiene los tokens de sesión de USFQ.
    
    Puede recibir credenciales en el body o usar las variables de entorno:
    - USFQ_EMAIL
    - USFQ_PASSWORD
    
    Retorna:
    - d2lSessionVal: Cookie de sesión
    - d2lSecureSessionVal: Cookie de sesión segura
    - csrfToken: Token CSRF para requests
    """
    # Determinar credenciales a usar
    email = None
    password = None
    
    if credentials:
        email = credentials.email
        password = credentials.password
    
    # Si no se pasaron, usar variables de entorno
    if not email:
        email = os.getenv("USFQ_EMAIL")
    if not password:
        password = os.getenv("USFQ_PASSWORD")
    
    # Validar que tenemos credenciales
    if not email or not password:
        raise HTTPException(
            status_code=400,
            detail="Credenciales requeridas. Envía email/password en el body o configura USFQ_EMAIL/USFQ_PASSWORD"
        )
    
    try:
        # Ejecutar extracción
        result = await obtener_tokens(email, password)
        return TokenResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al extraer tokens: {str(e)}"
        )


@app.get("/api/obtener-tokens", response_model=TokenResponse)
async def api_obtener_tokens_get():
    """
    GET endpoint para obtener tokens usando variables de entorno.
    Útil para n8n HTTP Request node simple.
    """
    email = os.getenv("USFQ_EMAIL")
    password = os.getenv("USFQ_PASSWORD")
    
    if not email or not password:
        raise HTTPException(
            status_code=400,
            detail="Variables de entorno USFQ_EMAIL y USFQ_PASSWORD requeridas"
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
