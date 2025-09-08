"""
Sistema de logging estruturado.

Configura logging usando structlog para:
- Logs estruturados em JSON
- Correlação de requests
- Diferentes níveis por ambiente
- Formatação consistente
"""

import sys
import logging
from typing import Optional
import structlog
from .settings import get_settings


def setup_logging(
    log_level: Optional[str] = None, log_format: Optional[str] = None
) -> None:
    """
    Configura o sistema de logging.

    Args:
        log_level: Nível de logging (opcional)
        log_format: Formato dos logs (opcional)
    """
    settings = get_settings()

    # Usa configurações fornecidas ou das settings
    level = log_level or settings.log_level
    format_type = log_format or settings.log_format

    # Configura logging padrão do Python
    logging.basicConfig(
        level=getattr(logging, level.upper()), format="%(message)s", stream=sys.stdout
    )

    # Configura structlog
    if format_type.lower() == "json":
        _setup_json_logging(level)
    else:
        _setup_console_logging(level)

    # Configura loggers específicos
    _setup_specific_loggers(level)


def _setup_json_logging(level: str) -> None:
    """Configura logging em formato JSON."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def _setup_console_logging(level: str) -> None:
    """Configura logging em formato console legível."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def _setup_specific_loggers(level: str) -> None:
    """Configura loggers específicos da aplicação."""
    # Logger para segurança
    security_logger = structlog.get_logger("security")
    security_logger.setLevel(getattr(logging, level.upper()))

    # Logger para métricas
    metrics_logger = structlog.get_logger("metrics")
    metrics_logger.setLevel(getattr(logging, level.upper()))

    # Logger para processamento de emails
    email_logger = structlog.get_logger("email_processing")
    email_logger.setLevel(getattr(logging, level.upper()))

    # Logger para IA
    ai_logger = structlog.get_logger("ai_services")
    ai_logger.setLevel(getattr(logging, level.upper()))


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Retorna logger configurado.

    Args:
        name: Nome do logger

    Returns:
        Logger configurado
    """
    return structlog.get_logger(name)


def log_request_start(
    method: str,
    url: str,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None,
) -> None:
    """
    Log do início de um request.

    Args:
        method: Método HTTP
        url: URL do request
        client_ip: IP do cliente
        user_agent: User agent do cliente
        request_id: ID único do request
    """
    logger = get_logger("http")

    logger.info(
        "request_started",
        method=method,
        url=url,
        client_ip=client_ip,
        user_agent=user_agent,
        request_id=request_id,
    )


def log_request_complete(
    method: str,
    url: str,
    status_code: int,
    duration_ms: float,
    request_id: Optional[str] = None,
) -> None:
    """
    Log do fim de um request.

    Args:
        method: Método HTTP
        url: URL do request
        status_code: Código de status da resposta
        duration_ms: Duração em milissegundos
        request_id: ID único do request
    """
    logger = get_logger("http")

    logger.info(
        "request_completed",
        method=method,
        url=url,
        status_code=status_code,
        duration_ms=duration_ms,
        request_id=request_id,
    )


def log_email_processing_start(
    email_id: str, content_length: int, has_attachments: bool = False
) -> None:
    """
    Log do início do processamento de email.

    Args:
        email_id: ID do email
        content_length: Tamanho do conteúdo
        has_attachments: Se possui anexos
    """
    logger = get_logger("email_processing")

    logger.info(
        "email_processing_started",
        email_id=email_id,
        content_length=content_length,
        has_attachments=has_attachments,
    )


def log_email_processing_complete(
    email_id: str,
    classification_label: str,
    confidence: float,
    processing_time_ms: float,
    model_used: Optional[str] = None,
) -> None:
    """
    Log do fim do processamento de email.

    Args:
        email_id: ID do email
        classification_label: Label da classificação
        confidence: Confiança da classificação
        processing_time_ms: Tempo de processamento
        model_used: Modelo usado
    """
    logger = get_logger("email_processing")

    logger.info(
        "email_processing_completed",
        email_id=email_id,
        classification_label=classification_label,
        confidence=confidence,
        processing_time_ms=processing_time_ms,
        model_used=model_used,
    )


def log_ai_service_call(
    service_name: str, operation: str, input_size: int, request_id: Optional[str] = None
) -> None:
    """
    Log de chamada para serviço de IA.

    Args:
        service_name: Nome do serviço (OpenAI, HuggingFace, etc.)
        operation: Operação realizada
        input_size: Tamanho da entrada
        request_id: ID único do request
    """
    logger = get_logger("ai_services")

    logger.info(
        "ai_service_called",
        service_name=service_name,
        operation=operation,
        input_size=input_size,
        request_id=request_id,
    )


def log_security_event(event_type: str, details: dict, severity: str = "info") -> None:
    """
    Log de evento de segurança.

    Args:
        event_type: Tipo do evento
        details: Detalhes do evento
        severity: Severidade (info, warning, error)
    """
    logger = get_logger("security")

    if severity.lower() == "warning":
        logger.warning("security_event", event_type=event_type, **details)
    elif severity.lower() == "error":
        logger.error("security_event", event_type=event_type, **details)
    else:
        logger.info("security_event", event_type=event_type, **details)


def log_metrics(metric_name: str, value: float, labels: Optional[dict] = None) -> None:
    """
    Log de métricas.

    Args:
        metric_name: Nome da métrica
        value: Valor da métrica
        labels: Labels adicionais
    """
    logger = get_logger("metrics")

    log_data = {"metric_name": metric_name, "value": value}

    if labels:
        log_data.update(labels)

    logger.info("metric_recorded", **log_data)


def log_error(
    error: Exception, context: Optional[dict] = None, logger_name: str = "application"
) -> None:
    """
    Log de erro.

    Args:
        error: Exceção ocorrida
        context: Contexto adicional
        logger_name: Nome do logger
    """
    logger = get_logger(logger_name)

    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "error_traceback": getattr(error, "__traceback__", None),
    }

    if context:
        error_data.update(context)

    logger.error("error_occurred", **error_data)


def log_performance(
    operation: str, duration_ms: float, additional_data: Optional[dict] = None
) -> None:
    """
    Log de performance.

    Args:
        operation: Nome da operação
        duration_ms: Duração em milissegundos
        additional_data: Dados adicionais
    """
    logger = get_logger("performance")

    log_data = {"operation": operation, "duration_ms": duration_ms}

    if additional_data:
        log_data.update(additional_data)

    logger.info("performance_measured", **log_data)


# Configuração automática ao importar o módulo
if __name__ != "__main__":
    setup_logging()
