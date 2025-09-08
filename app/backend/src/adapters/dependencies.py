"""
Sistema de injeção de dependências.

Conecta as portas (interfaces) com suas implementações (adapters),
permitindo fácil troca de implementações e testes.
"""

from typing import Dict, Any
from functools import lru_cache

from ..core.ports import (
    EmailParserPort,
    ClassifierPort,
    ResponderPort,
    EmailRepositoryPort,
    NotificationPort,
    SecurityPort,
    CachePort,
)
from .gateways import (
    TextEmailParser,
    FileEmailParser,
    HeuristicClassifier,
    TemplateResponder,
    InMemoryEmailRepository,
    InMemoryTemplateRepository,
    StructuredLoggingService,
    BasicSecurityService,
    InMemoryCacheService,
)

# from .persistence import SQLAlchemyEmailRepository, SQLAlchemyTemplateRepository
from ..infra.settings import get_settings


class DependencyContainer:
    """
    Container de dependências para injeção.

    Gerencia a criação e configuração de todas as dependências
    da aplicação, permitindo fácil troca de implementações.
    """

    def __init__(self) -> None:
        self._instances: Dict[str, Any] = {}
        self._settings = get_settings()

    def get_email_parser(self) -> EmailParserPort:
        """Retorna implementação do parser de emails."""
        if "email_parser" not in self._instances:
            # Combina parser de texto e arquivo
            text_parser = TextEmailParser()
            file_parser = FileEmailParser()

            # Parser composto que delega para o apropriado
            from .gateways import CompositeEmailParser

            self._instances["email_parser"] = CompositeEmailParser(
                text_parser, file_parser
            )

        return self._instances["email_parser"]  # type: ignore

    def get_classifier(self) -> ClassifierPort:
        """Retorna implementação do classificador."""
        if "classifier" not in self._instances:
            # Por padrão usa classificador heurístico
            # Pode ser trocado por OpenAI, Hugging Face, etc.
            self._instances["classifier"] = HeuristicClassifier()

        return self._instances["classifier"]  # type: ignore

    def get_responder(self) -> ResponderPort:
        """Retorna implementação do gerador de respostas."""
        if "responder" not in self._instances:
            # Por padrão usa templates estáticos
            # Pode ser trocado por OpenAI, Hugging Face, etc.
            self._instances["responder"] = TemplateResponder()

        return self._instances["responder"]  # type: ignore

    def get_email_repository(self) -> EmailRepositoryPort:
        """Retorna implementação do repositório de emails."""
        if "email_repository" not in self._instances:
            if self._settings.use_database:
                # Usa SQLAlchemy se configurado
                # self._instances["email_repository"] = SQLAlchemyEmailRepository(
                #     self._settings.database_url
                # )
                self._instances["email_repository"] = InMemoryEmailRepository()
            else:
                # Usa memória para desenvolvimento
                self._instances["email_repository"] = InMemoryEmailRepository()

        return self._instances["email_repository"]  # type: ignore

    def get_template_repository(self) -> Any:
        """Retorna implementação do repositório de templates."""
        if "template_repository" not in self._instances:
            if self._settings.use_database:
                # self._instances["template_repository"] = SQLAlchemyTemplateRepository(
                #     self._settings.database_url
                # )
                self._instances["template_repository"] = InMemoryTemplateRepository()
            else:
                self._instances["template_repository"] = InMemoryTemplateRepository()

        return self._instances["template_repository"]

    def get_notification_service(self) -> NotificationPort:
        """Retorna implementação do serviço de notificações."""
        if "notification_service" not in self._instances:
            self._instances["notification_service"] = StructuredLoggingService()

        return self._instances["notification_service"]  # type: ignore

    def get_security_service(self) -> SecurityPort:
        """Retorna implementação do serviço de segurança."""
        if "security_service" not in self._instances:
            self._instances["security_service"] = BasicSecurityService()

        return self._instances["security_service"]  # type: ignore

    def get_cache_service(self) -> CachePort:
        """Retorna implementação do serviço de cache."""
        if "cache_service" not in self._instances:
            self._instances["cache_service"] = InMemoryCacheService()

        return self._instances["cache_service"]  # type: ignore

    def get_all_dependencies(self) -> Dict[str, Any]:
        """Retorna todas as dependências como dicionário."""
        return {
            "email_parser": self.get_email_parser(),
            "classifier": self.get_classifier(),
            "responder": self.get_responder(),
            "email_repository": self.get_email_repository(),
            "template_repository": self.get_template_repository(),
            "notification_service": self.get_notification_service(),
            "security_service": self.get_security_service(),
            "cache_service": self.get_cache_service(),
        }

    def reset(self) -> None:
        """Reseta todas as instâncias (útil para testes)."""
        self._instances.clear()


# Instância global do container
_dependency_container = DependencyContainer()


@lru_cache()
def get_dependency_container() -> DependencyContainer:
    """Retorna instância singleton do container de dependências."""
    return _dependency_container


def get_dependencies() -> Dict[str, Any]:
    """Retorna todas as dependências para injeção no FastAPI."""
    return get_dependency_container().get_all_dependencies()


def override_dependency(dependency_name: str, implementation: Any) -> None:
    """
    Sobrescreve uma dependência (útil para testes).

    Args:
        dependency_name: Nome da dependência
        implementation: Nova implementação
    """
    container = get_dependency_container()
    container._instances[dependency_name] = implementation


def reset_dependencies() -> None:
    """Reseta todas as dependências (útil para testes)."""
    get_dependency_container().reset()


# Factory functions para criação de dependências específicas
def create_openai_classifier(api_key: str) -> ClassifierPort:
    """Cria classificador OpenAI."""
    from .gateways import OpenAIClassifier

    return OpenAIClassifier(api_key)


def create_huggingface_classifier(token: str) -> ClassifierPort:
    """Cria classificador Hugging Face."""
    from .gateways import HuggingFaceClassifier

    return HuggingFaceClassifier(token)


def create_openai_responder(api_key: str) -> ResponderPort:
    """Cria gerador de respostas OpenAI."""
    from .gateways import OpenAIResponder

    return OpenAIResponder(api_key)


def create_redis_cache(redis_url: str) -> CachePort:
    """Cria serviço de cache Redis."""
    from .gateways import RedisCacheService

    return RedisCacheService(redis_url)


def create_prometheus_metrics() -> NotificationPort:
    """Cria serviço de métricas Prometheus."""
    from .gateways import PrometheusMetricsService

    return PrometheusMetricsService()


# Configuração de dependências baseada em ambiente
def configure_dependencies_for_environment(environment: str) -> None:
    """
    Configura dependências para um ambiente específico.

    Args:
        environment: Ambiente (development, staging, production)
    """
    container = get_dependency_container()

    if environment == "production":
        # Produção: usa implementações robustas
        settings = get_settings()

        if settings.openai_api_key:
            container._instances["classifier"] = create_openai_classifier(
                settings.openai_api_key
            )
            container._instances["responder"] = create_openai_responder(
                settings.openai_api_key
            )

        if settings.redis_url:
            container._instances["cache_service"] = create_redis_cache(
                settings.redis_url
            )

        # Adiciona métricas Prometheus
        container._instances["metrics_service"] = create_prometheus_metrics()

    elif environment == "staging":
        # Staging: usa implementações intermediárias
        pass

    else:
        # Development: usa implementações simples
        pass


# Inicialização automática baseada em configuração
def initialize_dependencies() -> None:
    """Inicializa dependências baseado na configuração atual."""
    settings = get_settings()
    environment = settings.environment

    configure_dependencies_for_environment(environment)

    # Log da configuração
    container = get_dependency_container()
    notification_service = container.get_notification_service()

    # Log assíncrono (em produção seria melhor usar eventos)
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Se já está rodando, agenda para depois
            loop.create_task(
                notification_service.record_metrics(
                    {
                        "dependencies_initialized": True,
                        "environment": environment,
                        "classifier_type": type(container.get_classifier()).__name__,
                        "responder_type": type(container.get_responder()).__name__,
                        "cache_type": type(container.get_cache_service()).__name__,
                    }
                )
            )
        else:
            # Executa diretamente
            asyncio.run(
                notification_service.record_metrics(
                    {
                        "dependencies_initialized": True,
                        "environment": environment,
                        "classifier_type": type(container.get_classifier()).__name__,
                        "responder_type": type(container.get_responder()).__name__,
                        "cache_type": type(container.get_cache_service()).__name__,
                    }
                )
            )
    except Exception:
        # Fallback silencioso se não conseguir logar
        pass
