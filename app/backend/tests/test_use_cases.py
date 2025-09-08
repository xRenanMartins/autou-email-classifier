import pytest
from unittest.mock import Mock
from src.core.application.use_cases import ClassifyEmailAndSuggestResponse


class TestClassifyEmailAndSuggestResponse:
    """Test cases for ClassifyEmailAndSuggestResponse use case"""

    def test_classify_email_with_text(self, mock_classifier, mock_responder):
        """Test email classification with text input"""
        use_case = ClassifyEmailAndSuggestResponse(
            classifier=mock_classifier, responder=mock_responder
        )

        request = {
            "text": "Preciso de suporte técnico urgente para resolver um problema no sistema."
        }

        result = use_case.execute(request)

        assert result is not None
        assert "email_id" in result
        assert "classification" in result
        assert "suggested_response" in result
        assert "processing_time_ms" in result

        # Verificar se os mocks foram chamados
        mock_classifier.classify.assert_called_once()
        mock_responder.suggest_reply.assert_called_once()

    def test_classify_email_with_file(self, mock_classifier, mock_responder):
        """Test email classification with file input"""
        use_case = ClassifyEmailAndSuggestResponse(
            classifier=mock_classifier, responder=mock_responder
        )

        # Mock file object
        mock_file = Mock()
        mock_file.filename = "test.txt"
        mock_file.read.return_value = b"Conteudo do arquivo de teste"

        request = {"file": mock_file}

        result = use_case.execute(request)

        assert result is not None
        assert "email_id" in result
        assert "classification" in result
        assert "suggested_response" in result
        assert "processing_time_ms" in result

    def test_classify_email_with_both_text_and_file(
        self, mock_classifier, mock_responder
    ):
        """Test email classification with both text and file"""
        use_case = ClassifyEmailAndSuggestResponse(
            classifier=mock_classifier, responder=mock_responder
        )

        mock_file = Mock()
        mock_file.filename = "test.txt"
        mock_file.read.return_value = b"Conteudo do arquivo"

        request = {"text": "Texto adicional", "file": mock_file}

        result = use_case.execute(request)

        assert result is not None
        assert "email_id" in result
        assert "classification" in result
        assert "suggested_response" in result
        assert "processing_time_ms" in result

    def test_classify_email_with_metadata(self, mock_classifier, mock_responder):
        """Test email classification with metadata"""
        use_case = ClassifyEmailAndSuggestResponse(
            classifier=mock_classifier, responder=mock_responder
        )

        request = {
            "text": "Email de teste",
            "metadata": {
                "sender": "test@example.com",
                "priority": "high",
                "category": "support",
            },
        }

        result = use_case.execute(request)

        assert result is not None
        assert "email_id" in result
        assert "classification" in result
        assert "suggested_response" in result
        assert "processing_time_ms" in result

    def test_classify_email_empty_request(self, mock_classifier, mock_responder):
        """Test email classification with empty request"""
        use_case = ClassifyEmailAndSuggestResponse(
            classifier=mock_classifier, responder=mock_responder
        )

        request = {}

        with pytest.raises(ValueError, match="Either text or file must be provided"):
            use_case.execute(request)

    def test_classify_email_invalid_text(self, mock_classifier, mock_responder):
        """Test email classification with invalid text"""
        use_case = ClassifyEmailAndSuggestResponse(
            classifier=mock_classifier, responder=mock_responder
        )

        request = {"text": "a"}  # Texto muito curto

        with pytest.raises(ValueError, match="Text must be at least 10 characters"):
            use_case.execute(request)

    def test_classify_email_classification_failure(self, mock_responder):
        """Test email classification when classifier fails"""
        # Mock classifier that raises an exception
        mock_classifier = Mock()
        mock_classifier.classify.side_effect = Exception("Classification failed")

        use_case = ClassifyEmailAndSuggestResponse(
            classifier=mock_classifier, responder=mock_responder
        )

        request = {"text": "Email de teste com texto suficiente para validação."}

        with pytest.raises(Exception, match="Classification failed"):
            use_case.execute(request)

    def test_classify_email_response_generation_failure(self, mock_classifier):
        """Test email classification when response generation fails"""
        # Mock responder that raises an exception
        mock_responder = Mock()
        mock_responder.suggest_reply.side_effect = Exception(
            "Response generation failed"
        )

        use_case = ClassifyEmailAndSuggestResponse(
            classifier=mock_classifier, responder=mock_responder
        )

        request = {"text": "Email de teste com texto suficiente para validação."}

        with pytest.raises(Exception, match="Response generation failed"):
            use_case.execute(request)
