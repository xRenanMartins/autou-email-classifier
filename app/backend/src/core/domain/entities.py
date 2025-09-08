"""
Entidades do domínio para o sistema de classificação de emails.
"""

from datetime import datetime
from typing import Optional, List, Any
from dataclasses import dataclass
from enum import Enum
from uuid import UUID, uuid4


class EmailLabel(str, Enum):
    """Labels possíveis para classificação de emails."""

    PRODUCTIVE = "PRODUCTIVE"
    UNPRODUCTIVE = "UNPRODUCTIVE"


class EmailPriority(str, Enum):
    """Prioridades de processamento."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class EmailAttachment:
    """Value Object para anexos de email."""

    filename: str
    content_type: str
    size_bytes: int
    content: bytes


@dataclass
class PreprocessedEmail:
    """Value Object para email pré-processado."""

    clean_text: str
    tokens: List[str]
    language: str
    word_count: int
    has_attachments: bool


@dataclass
class Classification:
    """Value Object para resultado da classificação."""

    label: EmailLabel
    confidence: float
    reasoning: Optional[str] = None
    model_used: Optional[str] = None
    processing_time_ms: Optional[float] = None


@dataclass
class SuggestedResponse:
    """Value Object para resposta sugerida."""

    subject: Optional[str]
    body: str
    tone: str
    language: str
    estimated_response_time: Optional[str] = None


class Email:
    """
    Aggregate Root para emails.

    Responsável por manter a consistência do domínio e
    coordenar as operações relacionadas ao email.
    """

    def __init__(
        self,
        raw_content: str,
        subject: Optional[str] = None,
        sender: Optional[str] = None,
        recipients: Optional[List[str]] = None,
        received_at: Optional[datetime] = None,
        attachments: Optional[List[EmailAttachment]] = None,
        email_id: Optional[UUID] = None,
    ):
        self.email_id = email_id or uuid4()
        self.raw_content = raw_content
        self.subject = subject
        self.sender = sender
        self.recipients = recipients or []
        self.received_at = received_at or datetime.utcnow()
        self.attachments = attachments or []

        # Estados derivados
        self._preprocessed: Optional[PreprocessedEmail] = None
        self._classification: Optional[Classification] = None
        self._suggested_response: Optional[SuggestedResponse] = None
        self._processing_status = "PENDING"

        # Timestamps
        self._created_at = datetime.utcnow()
        self._updated_at = datetime.utcnow()

    @property
    def is_processed(self) -> bool:
        """Verifica se o email foi completamente processado."""
        return (
            self._preprocessed is not None
            and self._classification is not None
            and self._suggested_response is not None
        )

    @property
    def priority(self) -> EmailPriority:
        """Calcula a prioridade baseada no conteúdo e contexto."""
        if self._classification and self._classification.label == EmailLabel.PRODUCTIVE:
            return EmailPriority.HIGH
        elif self._classification and self._classification.confidence < 0.7:
            return EmailPriority.MEDIUM
        return EmailPriority.LOW

    def set_preprocessed(self, preprocessed: PreprocessedEmail) -> None:
        """Define o email pré-processado."""
        self._preprocessed = preprocessed
        self._processing_status = "PREPROCESSED"
        self._updated_at = datetime.utcnow()

    def set_classification(self, classification: Classification) -> None:
        """Define a classificação do email."""
        self._classification = classification
        self._processing_status = "CLASSIFIED"
        self._updated_at = datetime.utcnow()

    def set_suggested_response(self, response: SuggestedResponse) -> None:
        """Define a resposta sugerida."""
        self._suggested_response = response
        self._processing_status = "COMPLETED"
        self._updated_at = datetime.utcnow()

    def get_processing_summary(self) -> dict:
        """Retorna um resumo do processamento."""
        return {
            "email_id": str(self.email_id),
            "subject": self.subject,
            "status": self._processing_status,
            "priority": self.priority.value,
            "classification": (
                self._classification.label.value if self._classification else None
            ),
            "confidence": (
                self._classification.confidence if self._classification else None
            ),
            "has_response": self._suggested_response is not None,
        }

    def validate(self) -> List[str]:
        """Valida a entidade e retorna lista de erros."""
        errors = []

        if not self.raw_content or len(self.raw_content.strip()) == 0:
            errors.append("Conteúdo do email não pode estar vazio")

        if len(self.raw_content) > 100000:  # 100KB limit
            errors.append("Conteúdo do email excede o limite de 100KB")

        if self.sender and len(self.sender) > 255:
            errors.append("Email do remetente muito longo")

        return errors


class ResponseTemplate:
    """
    Entidade para templates de resposta.

    Permite reutilização de respostas comuns e
    personalização baseada em contexto.
    """

    def __init__(
        self,
        template_id: UUID,
        label_target: EmailLabel,
        template_text: str,
        variables: List[str],
        tone: str = "professional",
        language: str = "pt",
        is_active: bool = True,
    ):
        self.template_id = template_id
        self.label_target = label_target
        self.template_text = template_text
        self.variables = variables
        self.tone = tone
        self.language = language
        self.is_active = is_active
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def render(self, **kwargs: Any) -> str:
        """Renderiza o template com as variáveis fornecidas."""
        try:
            return self.template_text.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Variável obrigatória não fornecida: {e}")

    def is_compatible_with(self, email: Email) -> bool:
        """Verifica se o template é compatível com o email."""
        if not email._classification:
            return False

        return (
            self.label_target == email._classification.label
            and self.language
            == (email._preprocessed.language if email._preprocessed else "pt")
            and self.is_active
        )
