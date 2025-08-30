from typing import List
from pydantic import Field

    # Configurações de segurança
    allowed_hosts: List[str] = Field(
        ["*"], 
        description="Hosts permitidos para TrustedHostMiddleware"
    )
    cors_origins: List[str] = Field(
        [
            "http://localhost:3000", 
            "http://localhost:8080",
            "https://*.vercel.app",
            "https://*.onrender.com"
        ],
        description="Origens permitidas para CORS"
    )
