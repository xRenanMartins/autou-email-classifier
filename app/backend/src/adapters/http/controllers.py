"""
Controllers HTTP (Adapters) para FastAPI.

Implementa as rotas da API REST, conectando com os casos de uso
através de injeção de dependência.
"""

from typing import Optional, List
from datetime import datetime
import time
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status

from ...core.application.use_cases import (
    ProcessEmailUseCase,
    GetEmailClassificationUseCase,
    GetProcessingStatsUseCase,
    GetSupportedLabelsUseCase,
    HealthCheckUseCase,
)
from ...core.application.dto import (
    EmailProcessingRequest,
    EmailProcessingResponse,
    HealthCheckResponse,
)
from ..dependencies import get_dependencies


# Router principal da API
api_router = APIRouter(prefix="/api/v1", tags=["email-classification"])


class EmailClassificationController:
    """
    Controller para endpoints de classificação de emails.

    Implementa as rotas REST seguindo Clean Architecture:
    - Recebe requests HTTP
    - Valida entrada
    - Chama casos de uso apropriados
    - Retorna responses padronizados
    """

    def __init__(self) -> None:
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Configura as rotas do controller."""
        self.router.add_api_route(
            "/process",
            self.process_email,
            methods=["POST"],
            response_model=EmailProcessingResponse,
            summary="Processa email para classificação",
            description="Classifica email e gera resposta sugerida",
        )

        self.router.add_api_route(
            "/process/file",
            self.process_email_file,
            methods=["POST"],
            response_model=EmailProcessingResponse,
            summary="Processa arquivo de email",
            description="Upload e processamento de arquivo (.txt, .pdf, .eml)",
        )

        self.router.add_api_route(
            "/emails/{email_id}",
            self.get_email_classification,
            methods=["GET"],
            summary="Obtém classificação de email",
            description="Recupera resultado de processamento por ID",
        )

        self.router.add_api_route(
            "/stats",
            self.get_processing_stats,
            methods=["GET"],
            summary="Estatísticas de processamento",
            description="Métricas e estatísticas do sistema",
        )

        self.router.add_api_route(
            "/labels",
            self.get_supported_labels,
            methods=["GET"],
            summary="Labels suportados",
            description="Lista de labels de classificação disponíveis",
        )

        self.router.add_api_route(
            "/health",
            self.health_check,
            methods=["GET"],
            response_model=HealthCheckResponse,
            summary="Verificação de saúde",
            description="Status dos componentes do sistema",
        )

    async def process_email(
        self, request: EmailProcessingRequest, deps: dict = Depends(get_dependencies)
    ) -> EmailProcessingResponse:
        """
        Processa email em formato texto.

        Args:
            request: Dados do email para processar
            deps: Dependências injetadas

        Returns:
            Resultado do processamento com classificação e resposta
        """
        start_time = time.time()

        try:
            # Verifica rate limit
            if not await deps["security_service"].check_rate_limit("text_processing"):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit excedido",
                )

            # Executa caso de uso
            use_case = ProcessEmailUseCase(
                email_parser=deps["email_parser"],
                classifier=deps["classifier"],
                responder=deps["responder"],
                email_repository=deps["email_repository"],
                notification_service=deps["notification_service"],
                security_service=deps["security_service"],
                cache_service=deps["cache_service"],
            )

            result = await use_case.execute(
                text=request.text, subject=request.subject, context=request.metadata
            )

            return EmailProcessingResponse(**result)

        except HTTPException:
            raise
        except Exception as e:
            processing_time = time.time() - start_time

            # Log do erro
            await deps["notification_service"].log_processing_error(
                e,
                {
                    "endpoint": "/api/v1/process",
                    "request_type": "text",
                    "processing_time_ms": round(processing_time * 1000, 2),
                },
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro interno: {str(e)}",
            )

    async def process_email_file(
        self,
        file: UploadFile = File(...),
        subject: Optional[str] = Form(None),
        deps: dict = Depends(get_dependencies),
    ) -> EmailProcessingResponse:
        """
        Processa arquivo de email (PDF, TXT, EML).

        Args:
            file: Arquivo enviado
            subject: Assunto opcional
            deps: Dependências injetadas

        Returns:
            Resultado do processamento
        """
        start_time = time.time()

        try:
            # Verifica rate limit
            if not await deps["security_service"].check_rate_limit("file_processing"):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit excedido",
                )

            # Valida tipo de arquivo
            if not deps["email_parser"].supports_file_type(file.filename):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Tipo de arquivo não suportado: {file.filename}",
                )

            # Lê conteúdo do arquivo
            file_content = await file.read()

            # Executa caso de uso
            use_case = ProcessEmailUseCase(
                email_parser=deps["email_parser"],
                classifier=deps["classifier"],
                responder=deps["responder"],
                email_repository=deps["email_repository"],
                notification_service=deps["notification_service"],
                security_service=deps["security_service"],
                cache_service=deps["cache_service"],
            )

            result = await use_case.execute(
                file_content=file_content, filename=file.filename, subject=subject
            )

            return EmailProcessingResponse(**result)

        except HTTPException:
            raise
        except Exception as e:
            processing_time = time.time() - start_time

            # Log do erro
            await deps["notification_service"].log_processing_error(
                e,
                {
                    "endpoint": "/api/v1/process/file",
                    "request_type": "file",
                    "filename": file.filename if file else None,
                    "processing_time_ms": round(processing_time * 1000, 2),
                },
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro interno: {str(e)}",
            )

    async def get_email_classification(
        self, email_id: str, deps: dict = Depends(get_dependencies)
    ) -> dict:
        """
        Obtém classificação de email por ID.

        Args:
            email_id: ID único do email
            deps: Dependências injetadas

        Returns:
            Dados da classificação
        """
        try:
            # Verifica cache primeiro
            cache_key = f"email_result:{email_id}"
            cached_result = await deps["cache_service"].get(cache_key)

            if cached_result:
                return {
                    "cached": True,
                    "data": cached_result,
                    "cached_at": cached_result.get("cached_at"),
                }

            # Executa caso de uso
            use_case = GetEmailClassificationUseCase(
                email_repository=deps["email_repository"]
            )

            result = await use_case.execute(email_id)

            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Email não encontrado: {email_id}",
                )

            return result

        except HTTPException:
            raise
        except Exception as e:
            # Log do erro
            await deps["notification_service"].log_processing_error(
                e, {"endpoint": f"/api/v1/emails/{email_id}", "email_id": email_id}
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro interno: {str(e)}",
            )

    async def get_processing_stats(
        self, deps: dict = Depends(get_dependencies)
    ) -> dict:
        """
        Obtém estatísticas de processamento.

        Args:
            deps: Dependências injetadas

        Returns:
            Estatísticas do sistema
        """
        try:
            use_case = GetProcessingStatsUseCase(
                email_repository=deps["email_repository"]
            )

            return await use_case.execute()

        except Exception as e:
            # Log do erro
            await deps["notification_service"].log_processing_error(
                e, {"endpoint": "/api/v1/stats"}
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro interno: {str(e)}",
            )

    async def get_supported_labels(
        self, deps: dict = Depends(get_dependencies)
    ) -> List[str]:
        """
        Obtém labels suportados pelo classificador.

        Args:
            deps: Dependências injetadas

        Returns:
            Lista de labels disponíveis
        """
        try:
            use_case = GetSupportedLabelsUseCase(classifier=deps["classifier"])

            return await use_case.execute()

        except Exception as e:
            # Log do erro
            await deps["notification_service"].log_processing_error(
                e, {"endpoint": "/api/v1/labels"}
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro interno: {str(e)}",
            )

    async def health_check(
        self, deps: dict = Depends(get_dependencies)
    ) -> HealthCheckResponse:
        """
        Verificação de saúde do sistema.

        Args:
            deps: Dependências injetadas

        Returns:
            Status dos componentes
        """
        try:
            use_case = HealthCheckUseCase(
                classifier=deps["classifier"],
                responder=deps["responder"],
                email_repository=deps["email_repository"],
            )

            result = await use_case.execute()

            return HealthCheckResponse(
                status=result["status"],
                timestamp=datetime.fromisoformat(result["timestamp"]),
                components=result["components"],
                version="1.0.0",
                uptime_seconds=time.time() - 0,  # TODO: Implementar uptime real
            )

        except Exception as e:
            # Log do erro
            await deps["notification_service"].log_processing_error(
                e, {"endpoint": "/api/v1/health"}
            )

            # Retorna status degradado em caso de erro
            return HealthCheckResponse(
                status="degraded",
                timestamp=datetime.utcnow(),
                components={"health_check": {"status": "unhealthy", "error": str(e)}},
                version="1.0.0",
                uptime_seconds=0,
            )


# Instância do controller
email_controller = EmailClassificationController()

# Adiciona rotas ao router principal
api_router.include_router(email_controller.router)
