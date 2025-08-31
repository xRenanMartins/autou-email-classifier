import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from src.adapters.http.controllers import EmailClassificationController


class TestEmailClassificationController:
    """Test cases for EmailClassificationController"""
    
    def test_controller_creation(self):
        """Test controller creation"""
        controller = EmailClassificationController()
        assert controller is not None
        assert hasattr(controller, 'router')
    
    def test_controller_routes_setup(self):
        """Test that controller routes are properly set up"""
        controller = EmailClassificationController()
        
        # Verifica se as rotas foram configuradas
        routes = controller.router.routes
        assert len(routes) > 0
        
        # Verifica se as rotas principais existem
        route_paths = [route.path for route in routes]
        assert "/process" in route_paths
        assert "/process/file" in route_paths
        assert "/emails/{email_id}" in route_paths
        assert "/stats" in route_paths
        assert "/labels" in route_paths
        assert "/health" in route_paths
    
    def test_controller_methods_exist(self):
        """Test that controller methods exist"""
        controller = EmailClassificationController()
        
        # Verifica se os métodos principais existem
        assert hasattr(controller, 'process_email')
        assert hasattr(controller, 'process_email_file')
        assert hasattr(controller, 'get_email_classification')
        assert hasattr(controller, 'get_processing_stats')
        assert hasattr(controller, 'get_supported_labels')
        assert hasattr(controller, 'health_check')
    
    @patch('src.adapters.http.controllers.get_dependencies')
    def test_process_email_endpoint(self, mock_get_deps):
        """Test process email endpoint"""
        # Mock das dependências
        mock_deps = {
            "security_service": Mock(),
            "email_parser": Mock(),
            "classifier": Mock(),
            "responder": Mock(),
            "email_repository": Mock(),
            "notification_service": Mock(),
            "cache_service": Mock()
        }
        mock_get_deps.return_value = mock_deps
        
        controller = EmailClassificationController()
        
        # Mock do request
        mock_request = Mock()
        mock_request.text = "Test email content"
        mock_request.subject = "Test Subject"
        mock_request.metadata = {}
        
        # Mock dos métodos assíncronos
        mock_deps["security_service"].check_rate_limit = AsyncMock(return_value=True)
        mock_deps["notification_service"].log_processing_error = AsyncMock()
        
        # Mock do caso de uso
        with patch('src.adapters.http.controllers.ProcessEmailUseCase') as mock_use_case:
            mock_use_case_instance = Mock()
            mock_use_case.return_value = mock_use_case_instance
            mock_use_case_instance.execute = AsyncMock(return_value={
                "success": True,
                "email_id": "test-123",
                "classification": {"label": "PRODUCTIVE", "confidence": 0.9},
                "suggested_response": {"subject": "Re: Test", "body": "Response"},
                "processing_time_ms": 150.0,
                "metadata": {}
            })
            
            # Executa o método async usando asyncio.run
            result = asyncio.run(controller.process_email(mock_request, mock_deps))
            
            # Verifica se o resultado foi retornado
            assert result is not None
            assert result.success is True
            assert result.email_id == "test-123"
    
    @patch('src.adapters.http.controllers.get_dependencies')
    def test_health_check_endpoint(self, mock_get_deps):
        """Test health check endpoint"""
        # Mock das dependências
        mock_deps = {
            "classifier": Mock(),
            "responder": Mock(),
            "email_repository": Mock(),
            "notification_service": Mock()
        }
        mock_get_deps.return_value = mock_deps
        
        controller = EmailClassificationController()
        
        # Mock dos componentes
        mock_deps["classifier"].get_classification_metadata = AsyncMock(return_value={"version": "1.0"})
        mock_deps["responder"].get_response_templates = AsyncMock(return_value=[])
        mock_deps["email_repository"].get_processing_stats = AsyncMock(return_value={"total": 0})
        
        # Executa o método async usando asyncio.run
        result = asyncio.run(controller.health_check(mock_deps))
        
        # Verifica se o resultado foi retornado
        assert result is not None
        assert hasattr(result, 'status')
        assert hasattr(result, 'timestamp')
        assert hasattr(result, 'components')
        assert hasattr(result, 'version')
        assert hasattr(result, 'uptime_seconds')

