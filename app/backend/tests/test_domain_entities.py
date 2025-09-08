from datetime import datetime
from uuid import uuid4
from src.core.domain.entities import (
    Email,
    PreprocessedEmail,
    Classification,
    ResponseTemplate,
    SuggestedResponse,
    EmailLabel,
    EmailPriority,
)


class TestEmail:
    """Test cases for Email entity"""

    def test_email_creation(self):
        """Test email creation with valid data"""
        email = Email(
            raw_content="Test email content",
            subject="Test Subject",
            sender="test@example.com",
            recipients=["recipient@example.com"],
            received_at=datetime.utcnow(),
        )

        assert email.email_id is not None
        assert email.raw_content == "Test email content"
        assert email.sender == "test@example.com"
        assert email.subject == "Test Subject"
        assert email.received_at is not None
        assert len(email.recipients) == 1

    def test_email_without_optional_fields(self):
        """Test email creation without optional fields"""
        email = Email(raw_content="Test email content")

        assert email.email_id is not None
        assert email.raw_content == "Test email content"
        assert email.sender is None
        assert email.subject is None
        assert email.received_at is not None
        assert len(email.recipients) == 0

    def test_email_validation(self):
        """Test email validation"""
        # Valid email
        email = Email(raw_content="Valid content")
        errors = email.validate()
        assert len(errors) == 0

        # Empty content
        email = Email(raw_content="")
        errors = email.validate()
        assert len(errors) > 0
        assert "não pode estar vazio" in errors[0]

    def test_email_processing_status(self):
        """Test email processing status changes"""
        email = Email(raw_content="Test content")
        assert email._processing_status == "PENDING"
        assert not email.is_processed

        # Set preprocessed
        preprocessed = PreprocessedEmail(
            clean_text="clean text",
            tokens=["clean", "text"],
            language="pt",
            word_count=2,
            has_attachments=False,
        )
        email.set_preprocessed(preprocessed)
        assert email._processing_status == "PREPROCESSED"

        # Set classification
        classification = Classification(label=EmailLabel.PRODUCTIVE, confidence=0.9)
        email.set_classification(classification)
        assert email._processing_status == "CLASSIFIED"

        # Set response
        response = SuggestedResponse(
            subject="Re: Test", body="Response body", tone="professional", language="pt"
        )
        email.set_suggested_response(response)
        assert email._processing_status == "COMPLETED"
        assert email.is_processed


class TestPreprocessedEmail:
    """Test cases for PreprocessedEmail entity"""

    def test_preprocessed_email_creation(self):
        """Test preprocessed email creation"""
        email = PreprocessedEmail(
            clean_text="clean text with tokens",
            tokens=["clean", "text", "with", "tokens"],
            language="pt",
            word_count=4,
            has_attachments=False,
        )

        assert email.clean_text == "clean text with tokens"
        assert len(email.tokens) == 4
        assert email.language == "pt"
        assert email.word_count == 4
        assert email.has_attachments is False


class TestClassification:
    """Test cases for Classification entity"""

    def test_classification_creation(self):
        """Test classification creation"""
        classification = Classification(
            label=EmailLabel.PRODUCTIVE,
            confidence=0.85,
            reasoning="Email contém solicitação específica",
        )

        assert classification.label == EmailLabel.PRODUCTIVE
        assert classification.confidence == 0.85
        assert classification.reasoning == "Email contém solicitação específica"
        assert classification.model_used is None

    def test_classification_label_enum(self):
        """Test classification label enum values"""
        assert EmailLabel.PRODUCTIVE == "PRODUCTIVE"
        assert EmailLabel.UNPRODUCTIVE == "UNPRODUCTIVE"
        assert len(EmailLabel) == 2


class TestResponseTemplate:
    """Test cases for ResponseTemplate entity"""

    def test_response_template_creation(self):
        """Test response template creation"""
        template = ResponseTemplate(
            template_id=uuid4(),
            label_target=EmailLabel.PRODUCTIVE,
            template_text="Obrigado pelo seu email sobre {topic}.",
            variables=["topic"],
            tone="professional",
            language="pt",
        )

        assert template.template_id is not None
        assert template.label_target == EmailLabel.PRODUCTIVE
        assert template.template_text == "Obrigado pelo seu email sobre {topic}."
        assert template.variables == ["topic"]
        assert template.tone == "professional"
        assert template.language == "pt"
        assert template.is_active is True

    def test_template_rendering(self):
        """Test template rendering with variables"""
        template = ResponseTemplate(
            template_id=uuid4(),
            label_target=EmailLabel.PRODUCTIVE,
            template_text="Olá {name}, {message}",
            variables=["name", "message"],
        )

        rendered = template.render(name="João", message="como vai?")
        assert rendered == "Olá João, como vai?"

    def test_template_compatibility(self):
        """Test template compatibility with email"""
        template = ResponseTemplate(
            template_id=uuid4(),
            label_target=EmailLabel.PRODUCTIVE,
            template_text="Template",
            variables=[],
        )

        # Create email with classification
        email = Email(raw_content="Test")
        preprocessed = PreprocessedEmail(
            clean_text="test",
            tokens=["test"],
            language="pt",
            word_count=1,
            has_attachments=False,
        )
        email.set_preprocessed(preprocessed)

        classification = Classification(label=EmailLabel.PRODUCTIVE, confidence=0.9)
        email.set_classification(classification)

        assert template.is_compatible_with(email)


class TestSuggestedResponse:
    """Test cases for SuggestedResponse entity"""

    def test_suggested_response_creation(self):
        """Test suggested response creation"""
        response = SuggestedResponse(
            subject="Re: Suporte Técnico",
            body="Obrigado pelo seu email. Vou analisar sua solicitação.",
            tone="professional",
            language="pt",
        )

        assert response.subject == "Re: Suporte Técnico"
        assert response.body == "Obrigado pelo seu email. Vou analisar sua solicitação."
        assert response.tone == "professional"
        assert response.language == "pt"
        assert response.estimated_response_time is None


class TestEmailPriority:
    """Test cases for EmailPriority enum"""

    def test_priority_enum_values(self):
        """Test priority enum values"""
        assert EmailPriority.LOW == "LOW"
        assert EmailPriority.MEDIUM == "MEDIUM"
        assert EmailPriority.HIGH == "HIGH"
        assert len(EmailPriority) == 3
