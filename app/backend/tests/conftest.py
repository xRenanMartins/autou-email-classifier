import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock

from src.main import app
from src.core.ports import ClassifierPort, ResponderPort, EmailParserPort


@pytest.fixture
def client():
    """Test client for FastAPI application"""
    return TestClient(app)


@pytest.fixture
def mock_classifier():
    """Mock classifier for testing"""
    classifier = Mock(spec=ClassifierPort)
    # Configura o mock para retornar valores síncronos
    classifier.classify = Mock(
        return_value={
            "label": "PRODUCTIVE",
            "confidence": 0.85,
            "reasoning": "Email contém solicitação específica",
        }
    )
    return classifier


@pytest.fixture
def mock_responder():
    """Mock responder for testing"""
    responder = Mock(spec=ResponderPort)
    # Configura o mock para retornar valores síncronos
    responder.suggest_reply = Mock(
        return_value={
            "subject": "Re: Suporte Técnico",
            "body": "Obrigado pelo seu email. Vou analisar sua solicitação.",
            "tone": "professional",
            "language": "pt",
        }
    )
    return responder


@pytest.fixture
def mock_email_parser():
    """Mock email parser for testing"""
    parser = Mock(spec=EmailParserPort)
    parser.parse.return_value = {
        "text": "Email de teste para classificação",
        "metadata": {"sender": "test@example.com"},
    }
    return parser


@pytest.fixture
def sample_email_data():
    """Sample email data for testing"""
    return {
        "text": "Preciso de suporte técnico para resolver um problema urgente.",
        "metadata": {"sender": "user@company.com", "priority": "high"},
    }


@pytest.fixture
def sample_classification_result():
    """Sample classification result for testing"""
    return {
        "id": "test-123",
        "label": "PRODUCTIVE",
        "confidence": 0.85,
        "reasoning": "Email contém solicitação específica de suporte",
        "suggested": {
            "subject": "Re: Suporte Técnico",
            "body": "Obrigado pelo seu email. Vou analisar sua solicitação.",
        },
        "processed_at": "2024-01-15T10:30:00Z",
    }
