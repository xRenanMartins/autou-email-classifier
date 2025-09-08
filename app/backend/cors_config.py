"""
Configuração de CORS para resolver problemas com Vercel
"""

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import os


def setup_cors(app: FastAPI):
    """Configura CORS de forma robusta."""

    # Origens permitidas
    origins = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://*.vercel.app",
        "https://vercel.app",
        "https://*.onrender.com",
    ]

    # Adiciona origens específicas se configuradas
    env_origins = os.getenv("CORS_ORIGINS", "")
    if env_origins:
        origins.extend(env_origins.split(","))

    # Remove duplicatas e valores vazios
    origins = list(set([origin.strip() for origin in origins if origin.strip()]))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
