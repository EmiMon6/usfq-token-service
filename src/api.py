"""
API FastAPI unificada - USFQ y SRI Token Extractors
"""
import os
import secrets
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Literal
from dotenv import load_dotenv

# Importar extractores
from token_extractor import obtener_tokens as obtener_tokens_usfq
from sri_extractor import obtener_tokens_sri

load_dotenv()

app = FastAPI(
    title="Universal Token Extractor API",
    description="API para extraer tokens de USFQ y SRI",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# Seguridad
# ==========================================

async def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    expected_key = os.getenv("API_KEY", "")
    if not expected_key:
        raise HTTPException(status_code=500, detail="API_KEY no configurada")
    if not x_api_key or not secrets.compare_digest(x_api_key, expected_key):
        raise HTTPException(status_code=403, detail="API Key inválida")
    return True

# ==========================================
# Modelos
# ==========================================

class TokenRequest(BaseModel):
    type: Literal["usfq", "sri"]
    user: Optional[str] = None      # RUC para SRI
    email: Optional[str] = None     # Email para USFQ
    ruc: Optional[str] = None       # Alias para user (SRI)
    password: str

class USFQResponse(BaseModel):
    success: bool
    d2lSessionVal: Optional[str] = None
    d2lSecureSessionVal: Optional[str] = None
    csrfToken: Optional[str] = None
    error: Optional[str] = None

class SRIResponse(BaseModel):
    success: bool
    cookie_header: Optional[str] = None
    view_state: Optional[str] = None
    final_url: Optional[str] = None
    error: Optional[str] = None

class UnifiedResponse(BaseModel):
    success: bool
    type: str
    # USFQ fields
    d2lSessionVal: Optional[str] = None
    d2lSecureSessionVal: Optional[str] = None
    csrfToken: Optional[str] = None
    # SRI fields
    cookie_header: Optional[str] = None
    view_state: Optional[str] = None
    final_url: Optional[str] = None
    # Error
    error: Optional[str] = None

# ==========================================
# Endpoints
# ==========================================

@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "Universal Token Extractor",
        "version": "2.0.0",
        "types": ["usfq", "sri"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/obtener-tokens", response_model=UnifiedResponse)
async def api_obtener_tokens(req: TokenRequest, _: bool = Depends(verify_api_key)):
    """
    Endpoint unificado para obtener tokens.
    
    - type: "usfq" o "sri"
    - user/email/ruc: identificador del usuario
    - password: contraseña
    """
    # Normalizar usuario
    username = req.user or req.email or req.ruc
    if not username:
        raise HTTPException(status_code=400, detail="Se requiere user, email o ruc")

    try:
        if req.type == "usfq":
            result = await obtener_tokens_usfq(username, req.password)
            return UnifiedResponse(
                success=result.get("success", False),
                type="usfq",
                d2lSessionVal=result.get("d2lSessionVal"),
                d2lSecureSessionVal=result.get("d2lSecureSessionVal"),
                csrfToken=result.get("csrfToken"),
                error=result.get("error")
            )
            
        elif req.type == "sri":
            result = await obtener_tokens_sri(username, req.password)
            return UnifiedResponse(
                success=result.get("success", False),
                type="sri",
                cookie_header=result.get("cookie_header"),
                view_state=result.get("view_state"),
                final_url=result.get("final_url"),
                error=result.get("error")
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints separados (opcional, para compatibilidad)
@app.post("/api/usfq", response_model=USFQResponse)
async def api_usfq(req: TokenRequest, _: bool = Depends(verify_api_key)):
    """Endpoint específico para USFQ"""
    username = req.user or req.email or req.ruc
    if not username:
        raise HTTPException(status_code=400, detail="Se requiere email")
    result = await obtener_tokens_usfq(username, req.password)
    return USFQResponse(**result)

@app.post("/api/sri", response_model=SRIResponse)
async def api_sri(req: TokenRequest, _: bool = Depends(verify_api_key)):
    """Endpoint específico para SRI"""
    username = req.user or req.email or req.ruc
    if not username:
        raise HTTPException(status_code=400, detail="Se requiere ruc")
    result = await obtener_tokens_sri(username, req.password)
    return SRIResponse(**result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
