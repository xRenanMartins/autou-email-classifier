"""
Ports (interfaces) para Clean Architecture e Hexagonal Architecture.

Define contratos que devem ser implementados pelos adapters,
permitindo desacoplamento entre camadas.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from .domain.entities import (
    Email,
    EmailLabel,
    Classification,
    PreprocessedEmail,
    SuggestedResponse,
    ResponseTemplate,
)


class EmailParserPort(ABC):
    """
    Porta para parsing de emails de diferentes fontes.

    Permite implementar parsers para diferentes formatos:
    - Texto simples
    - Arquivos PDF
    - Arquivos .eml
    - HTML
    """

    @abstractmethod
    async def parse_text(self, text: str, subject: Optional[str] = None) -> Email:
        """Parse de texto simples."""
        pass

    @abstractmethod
    async def parse_file(self, file_content: bytes, filename: str) -> Email:
        """Parse de arquivo (PDF, .txt, etc.)."""
        pass

    @abstractmethod
    async def parse_email_file(self, eml_content: str) -> Email:
        """Parse de arquivo .eml."""
        pass

    @abstractmethod
    def supports_file_type(self, filename: str) -> bool:
        """Verifica se o tipo de arquivo é suportado."""
        pass


class ClassifierPort(ABC):
    """
    Porta para classificação de emails.

    Permite diferentes implementações:
    - Regras heurísticas (local)
    - Hugging Face Zero-shot
    - OpenAI GPT
    - Modelos customizados
    """

    @abstractmethod
    async def classify(
        self,
        preprocessed_email: PreprocessedEmail,
        context: Optional[Dict[str, Any]] = None,
    ) -> Classification:
        """
        Classifica um email pré-processado.

        Args:
            preprocessed_email: Email limpo e tokenizado
            context: Contexto adicional (opcional)

        Returns:
            Classification com label e confidence
        """
        pass

    @abstractmethod
    async def get_supported_labels(self) -> List[str]:
        """Retorna lista de labels suportados."""
        pass

    @abstractmethod
    async def get_classification_metadata(self) -> Dict[str, Any]:
        """Retorna metadados sobre o classificador."""
        pass


class ResponderPort(ABC):
    """
    Porta para geração de respostas sugeridas.

    Permite diferentes implementações:
    - Templates estáticos
    - OpenAI GPT
    - Hugging Face LLMs
    - Modelos customizados
    """

    @abstractmethod
    async def suggest_reply(
        self,
        email: Email,
        classification: Classification,
        context: Optional[Dict[str, Any]] = None,
    ) -> SuggestedResponse:
        """
        Gera uma resposta sugerida para o email.

        Args:
            email: Email original
            classification: Classificação do email
            context: Contexto adicional (opcional)

        Returns:
            SuggestedResponse com corpo e tom
        """
        pass

    @abstractmethod
    async def get_response_templates(self, label: EmailLabel) -> List[ResponseTemplate]:
        """Retorna templates disponíveis para um label."""
        pass

    @abstractmethod
    async def customize_response(
        self, base_response: SuggestedResponse, customizations: Dict[str, Any]
    ) -> SuggestedResponse:
        """Customiza uma resposta base com ajustes específicos."""
        pass


class EmailRepositoryPort(ABC):
    """
    Porta para persistência de emails.

    Permite diferentes implementações:
    - SQLite (desenvolvimento)
    - PostgreSQL (produção)
    - MongoDB (documentos)
    - Redis (cache)
    """

    @abstractmethod
    async def save(self, email: Email) -> Email:
        """Salva um email no repositório."""
        pass

    @abstractmethod
    async def get_by_id(self, email_id: str) -> Optional[Email]:
        """Busca email por ID."""
        pass

    @abstractmethod
    async def get_by_classification(
        self, label: EmailLabel, limit: int = 100
    ) -> List[Email]:
        """Busca emails por classificação."""
        pass

    @abstractmethod
    async def get_processing_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de processamento."""
        pass

    @abstractmethod
    async def delete(self, email_id: str) -> bool:
        """Remove um email do repositório."""
        pass


class TemplateRepositoryPort(ABC):
    """
    Porta para persistência de templates de resposta.
    """

    @abstractmethod
    async def save(self, template: ResponseTemplate) -> ResponseTemplate:
        """Salva um template."""
        pass

    @abstractmethod
    async def get_by_id(self, template_id: str) -> Optional[ResponseTemplate]:
        """Busca template por ID."""
        pass

    @abstractmethod
    async def get_by_label(self, label: EmailLabel) -> List[ResponseTemplate]:
        """Busca templates por label."""
        pass

    @abstractmethod
    async def get_active_templates(self) -> List[ResponseTemplate]:
        """Retorna todos os templates ativos."""
        pass


class NotificationPort(ABC):
    """
    Porta para notificações e eventos.

    Permite diferentes implementações:
    - Logs estruturados
    - Métricas Prometheus
    - Eventos assíncronos
    - Webhooks
    """

    @abstractmethod
    async def notify_classification_completed(
        self, email: Email, classification: Classification
    ) -> None:
        """Notifica que uma classificação foi completada."""
        pass

    @abstractmethod
    async def notify_response_generated(
        self, email: Email, response: SuggestedResponse
    ) -> None:
        """Notifica que uma resposta foi gerada."""
        pass

    @abstractmethod
    async def log_processing_error(
        self, error: Exception, context: Dict[str, Any]
    ) -> None:
        """Registra erro de processamento."""
        pass

    @abstractmethod
    async def record_metrics(self, metrics: Dict[str, Any]) -> None:
        """Registra métricas de performance."""
        pass


class SecurityPort(ABC):
    """
    Porta para funcionalidades de segurança.

    Permite diferentes implementações:
    - Validação de entrada
    - Rate limiting
    - Sanitização
    - Autenticação (futuro)
    """

    @abstractmethod
    async def validate_input(self, content: str, content_type: str) -> bool:
        """Valida entrada do usuário."""
        pass

    @abstractmethod
    async def sanitize_content(self, content: str) -> str:
        """Sanitiza conteúdo removendo elementos perigosos."""
        pass

    @abstractmethod
    async def check_rate_limit(self, identifier: str) -> bool:
        """Verifica se o rate limit foi excedido."""
        pass

    @abstractmethod
    async def log_security_event(
        self, event_type: str, details: Dict[str, Any]
    ) -> None:
        """Registra eventos de segurança."""
        pass


class CachePort(ABC):
    """
    Porta para cache de resultados.

    Permite diferentes implementações:
    - Redis
    - Memória local
    - Arquivo
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Recupera valor do cache."""
        pass

    @abstractmethod
    async def set(
        self, key: str, value: Any, ttl_seconds: Optional[int] = None
    ) -> None:
        """Armazena valor no cache."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Remove valor do cache."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Limpa todo o cache."""
        pass
