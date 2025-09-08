"""Gateways de integração."""

"""
Gateways - Implementações das portas (interfaces).

Contém todas as implementações concretas das portas definidas
na camada de domínio, incluindo:
- Parsers de email
- Classificadores de IA
- Geradores de resposta
- Repositórios em memória
- Serviços de notificação
- Serviços de segurança
- Serviços de cache
"""

from .email_parsers import TextEmailParser, FileEmailParser, CompositeEmailParser
from .classifiers import HeuristicClassifier, OpenAIClassifier, HuggingFaceClassifier
from .responders import TemplateResponder, OpenAIResponder, HuggingFaceResponder
from .repositories import InMemoryEmailRepository, InMemoryTemplateRepository
from .services import (
    StructuredLoggingService,
    BasicSecurityService,
    InMemoryCacheService,
    PrometheusMetricsService,
    RedisCacheService,
)

__all__ = [
    # Email Parsers
    "TextEmailParser",
    "FileEmailParser",
    "CompositeEmailParser",
    # Classifiers
    "HeuristicClassifier",
    "OpenAIClassifier",
    "HuggingFaceClassifier",
    # Responders
    "TemplateResponder",
    "OpenAIResponder",
    "HuggingFaceResponder",
    # Repositories
    "InMemoryEmailRepository",
    "InMemoryTemplateRepository",
    # Services
    "StructuredLoggingService",
    "BasicSecurityService",
    "InMemoryCacheService",
    "PrometheusMetricsService",
    "RedisCacheService",
]
