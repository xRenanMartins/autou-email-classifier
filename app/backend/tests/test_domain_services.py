from src.core.domain.services import (
    EmailPreprocessingService,
    EmailClassificationService,
)
from src.core.domain.entities import (
    PreprocessedEmail,
    EmailLabel,
    Classification,
)


class TestEmailPreprocessingService:
    """Test cases for EmailPreprocessingService"""

    def test_preprocess_email_text(self):
        """Test email text preprocessing"""
        service = EmailPreprocessingService()
        text = "Olá! Preciso de SUPORTE TÉCNICO urgente para resolver um problema."

        result = service.preprocess(text)

        assert isinstance(result, PreprocessedEmail)
        assert result.clean_text is not None
        assert "suporte técnico" in result.clean_text.lower()
        assert len(result.tokens) > 0
        assert result.word_count > 0
        assert result.language is not None

    def test_preprocess_email_with_special_characters(self):
        """Test email preprocessing with special characters"""
        service = EmailPreprocessingService()
        text = "Email com caracteres especiais: @#$%^&*()_+{}|:<>?[]\\;'\""

        result = service.preprocess(text)

        assert result.clean_text is not None
        assert len(result.tokens) > 0

    def test_preprocess_empty_email(self):
        """Test preprocessing empty email"""
        service = EmailPreprocessingService()
        text = ""

        result = service.preprocess(text)

        assert result.clean_text == ""
        assert len(result.tokens) == 0
        assert result.word_count == 0


class TestEmailClassificationService:
    """Test cases for EmailClassificationService"""

    def test_classify_productive_email(self):
        """Test classification of productive email"""
        service = EmailClassificationService()

        # Cria um email pré-processado
        preprocessed = PreprocessedEmail(
            clean_text="Preciso de suporte técnico para resolver um problema urgente no sistema.",
            tokens=["preciso", "suporte", "técnico", "problema", "urgente", "sistema"],
            language="pt",
            word_count=7,
            has_attachments=False,
        )

        result = service.classify_with_rules(preprocessed)

        assert isinstance(result, Classification)
        assert hasattr(result, "label")
        assert hasattr(result, "confidence")
        assert hasattr(result, "reasoning")
        assert result.label in [EmailLabel.PRODUCTIVE, EmailLabel.UNPRODUCTIVE]
        assert 0 <= result.confidence <= 1

    def test_classify_unproductive_email(self):
        """Test classification of unproductive email"""
        service = EmailClassificationService()

        preprocessed = PreprocessedEmail(
            clean_text="Olá! Como você está? Apenas passando para dar um oi.",
            tokens=["olá", "como", "está", "passando", "dar", "oi"],
            language="pt",
            word_count=6,
            has_attachments=False,
        )

        result = service.classify_with_rules(preprocessed)

        assert isinstance(result, Classification)
        assert hasattr(result, "label")
        assert hasattr(result, "confidence")
        assert hasattr(result, "reasoning")

    def test_classify_email_with_keywords(self):
        """Test classification with specific keywords"""
        service = EmailClassificationService()

        # Email com palavras-chave produtivas
        preprocessed = PreprocessedEmail(
            clean_text="Solicito análise de relatório, revisão de contrato e aprovação de orçamento.",
            tokens=[
                "solicito",
                "análise",
                "relatório",
                "revisão",
                "contrato",
                "aprovação",
                "orçamento",
            ],
            language="pt",
            word_count=7,
            has_attachments=False,
        )

        result = service.classify_with_rules(preprocessed)

        assert result.label == EmailLabel.PRODUCTIVE
        assert result.confidence > 0.5

    def test_classify_email_with_greetings_only(self):
        """Test classification of email with only greetings"""
        service = EmailClassificationService()

        preprocessed = PreprocessedEmail(
            clean_text="Bom dia! Tudo bem? Abraços!",
            tokens=["bom", "dia", "tudo", "bem", "abraços"],
            language="pt",
            word_count=5,
            has_attachments=False,
        )

        result = service.classify_with_rules(preprocessed)

        assert result.label == EmailLabel.UNPRODUCTIVE
        assert result.confidence > 0.5
