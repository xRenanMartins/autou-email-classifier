"""
Aplicação principal FastAPI para o sistema de classificação de emails.

Configura a aplicação com:
- Middleware de segurança
- CORS
- Logging estruturado
- Métricas Prometheus
- Rotas da API
"""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog

from .adapters.http.controllers import api_router
from .adapters.dependencies import initialize_dependencies
from .infra.settings import get_settings
from .infra.logging import setup_logging


# Configurações
settings = get_settings()

# Setup de logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.

    - Inicializa dependências na startup
    - Limpa recursos no shutdown
    """
    # Startup
    print("🚀 Iniciando Email Classifier API...")

    try:
        # Inicializa dependências
        initialize_dependencies()
        print("✅ Dependências inicializadas com sucesso")

        # Log de startup
        logger = structlog.get_logger()
        logger.info(
            "application_started",
            version="1.0.0",
            environment=settings.environment,
            debug=settings.debug,
        )

    except Exception as e:
        print(f"❌ Erro ao inicializar dependências: {e}")
        logger = structlog.get_logger()
        logger.error("startup_error", error=str(e))

    yield

    # Shutdown
    print("🛑 Encerrando Email Classifier API...")

    try:
        logger = structlog.get_logger()
        logger.info("application_shutdown")

    except Exception as e:
        print(f"❌ Erro no shutdown: {e}")


# Criação da aplicação FastAPI
app = FastAPI(
    title="Email Classifier API",
    description="API para classificação automática de emails e geração de respostas sugeridas",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)

# Middleware de segurança
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

# Middleware CORS - SOLUÇÃO TEMPORÁRIA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens temporariamente
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Middleware de logging e métricas
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging de requests e métricas."""
    start_time = time.time()

    # Log do request
    logger = structlog.get_logger()
    logger.info(
        "request_started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    # Processa o request
    try:
        response = await call_next(request)

        # Calcula duração
        duration = time.time() - start_time

        # Log do response
        logger.info(
            "request_completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
        )

        # Adiciona header de duração
        response.headers["X-Processing-Time"] = str(round(duration * 1000, 2))

        return response

    except Exception as e:
        # Log de erro
        duration = time.time() - start_time
        logger.error(
            "request_error",
            method=request.method,
            url=str(request.url),
            error=str(e),
            duration_ms=round(duration * 1000, 2),
        )
        raise


# Middleware de tratamento de erros
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global para exceções não tratadas."""
    logger = structlog.get_logger()

    # Log do erro
    logger.error(
        "unhandled_exception",
        method=request.method,
        url=str(request.url),
        error_type=type(exc).__name__,
        error_message=str(exc),
    )

    # Retorna resposta de erro
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "Erro interno do servidor",
            "timestamp": time.time(),
            "request_id": request.headers.get("X-Request-ID", "unknown"),
        },
    )


# Rotas da API
app.include_router(api_router)


# Rota raiz
@app.get("/", tags=["root"])
async def root():
    """Rota raiz da API."""
    return {
        "message": "Email Classifier API",
        "version": "1.0.0",
        "status": "running",
        "docs": (
            "/docs" if settings.debug else "Documentação não disponível em produção"
        ),
    }


# Rota de métricas Prometheus
@app.get("/metrics", tags=["monitoring"])
async def metrics():
    """Endpoint para métricas Prometheus."""
    try:
        from .adapters.gateways.services import PrometheusMetricsService

        # Cria serviço de métricas
        metrics_service = PrometheusMetricsService()

        # Retorna métricas no formato Prometheus
        return Response(content=metrics_service.get_metrics(), media_type="text/plain")

    except Exception as e:
        logger = structlog.get_logger()
        logger.error("metrics_error", error=str(e))

        return JSONResponse(
            status_code=500, content={"error": "Erro ao gerar métricas"}
        )


# Rota de status detalhado
@app.get("/status", tags=["monitoring"])
async def detailed_status():
    """Status detalhado da aplicação."""
    try:
        from .adapters.dependencies import get_dependency_container

        container = get_dependency_container()

        # Obtém status dos componentes
        classifier = container.get_classifier()
        responder = container.get_responder()
        email_repo = container.get_email_repository()

        # Verifica saúde dos componentes
        components_status = {}

        try:
            classifier_meta = await classifier.get_classification_metadata()
            components_status["classifier"] = {
                "status": "healthy",
                "metadata": classifier_meta,
            }
        except Exception as e:
            components_status["classifier"] = {"status": "unhealthy", "error": str(e)}

        try:
            templates = await responder.get_response_templates(
                container.get_classifier().get_supported_labels()[0]
            )
            components_status["responder"] = {
                "status": "healthy",
                "templates_count": len(templates),
            }
        except Exception as e:
            components_status["responder"] = {"status": "unhealthy", "error": str(e)}

        try:
            stats = await email_repo.get_processing_stats()
            components_status["repository"] = {"status": "healthy", "stats": stats}
        except Exception as e:
            components_status["repository"] = {"status": "unhealthy", "error": str(e)}

        # Determina status geral
        overall_status = "healthy"
        if any(comp["status"] == "unhealthy" for comp in components_status.values()):
            overall_status = "degraded"

        return {
            "status": overall_status,
            "timestamp": time.time(),
            "version": "1.0.0",
            "environment": settings.environment,
            "components": components_status,
        }

    except Exception as e:
        logger = structlog.get_logger()
        logger.error("status_check_error", error=str(e))

        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e), "timestamp": time.time()},
        )


# Rota de health check simples
@app.get("/health", tags=["monitoring"])
async def health_check():
    """Health check simples da aplicação."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "email-classifier-api",
    }


# Configuração de logging para uvicorn
if __name__ == "__main__":
    import uvicorn

    print(f"🌍 Servidor rodando em: http://{settings.host}:{settings.port}")
    print(f"🔧 Ambiente: {settings.environment}")
    print(f"🐛 Debug: {settings.debug}")

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_config=None,  # Usa configuração do structlog
    )
