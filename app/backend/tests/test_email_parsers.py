"""
Testes para os parsers de email.
"""
import pytest
from unittest.mock import Mock, patch
from io import BytesIO

from src.adapters.gateways.email_parsers import (
    TextEmailParser,
    FileEmailParser,
    CompositeEmailParser
)
from src.core.domain.entities import Email


class TestTextEmailParser:
    """Testes para TextEmailParser."""
    
    @pytest.fixture
    def parser(self):
        return TextEmailParser()
    
    @pytest.mark.asyncio
    async def test_parse_text_with_subject(self, parser):
        """Testa parse de texto com assunto fornecido."""
        text = "Conteudo do email aqui"
        subject = "Teste de assunto"
        
        result = await parser.parse_text(text, subject)
        
        assert isinstance(result, Email)
        assert result.subject == subject
        assert result.raw_content == text
        assert result.sender is None
        assert result.recipients == []
    
    @pytest.mark.asyncio
    async def test_parse_text_extract_subject(self, parser):
        """Testa extração automática de assunto do texto."""
        text = "assunto: Teste automatico\nConteudo aqui"
        
        result = await parser.parse_text(text)
        
        assert result.subject == "Teste automatico"
        assert "assunto: Teste automatico" not in result.raw_content
    
    @pytest.mark.asyncio
    async def test_parse_text_extract_from(self, parser):
        """Testa extração automática de remetente."""
        text = "de: usuario@teste.com\nConteudo aqui"
        
        result = await parser.parse_text(text)
        
        assert result.sender == "usuario@teste.com"
    
    @pytest.mark.asyncio
    async def test_parse_text_extract_to(self, parser):
        """Testa extração automática de destinatários."""
        text = "para: destino@teste.com\nConteudo aqui"
        
        result = await parser.parse_text(text)
        
        assert result.recipients == ["destino@teste.com"]
    
    @pytest.mark.asyncio
    async def test_parse_txt_file(self, parser):
        """Testa parse de arquivo .txt."""
        content = b"Conteudo do arquivo txt"
        filename = "test.txt"
        
        result = await parser.parse_file(content, filename)
        
        assert isinstance(result, Email)
        assert result.raw_content == "Conteudo do arquivo txt"
    
    def test_supports_file_type(self, parser):
        """Testa verificação de tipos de arquivo suportados."""
        assert parser.supports_file_type("test.txt") is True
        assert parser.supports_file_type("test.eml") is True
        assert parser.supports_file_type("test.pdf") is False
        assert parser.supports_file_type("") is False


class TestFileEmailParser:
    """Testes para FileEmailParser."""
    
    @pytest.fixture
    def parser(self):
        return FileEmailParser()
    
    @pytest.mark.asyncio
    async def test_parse_pdf_file(self, parser):
        """Testa parse de arquivo PDF."""
        # Cria um PDF mock simples
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test PDF Content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000111 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n292\n%%EOF"
        filename = "test.pdf"
        
        with patch('pypdf.PdfReader') as mock_pdf_reader:
            # Mock do PdfReader
            mock_reader = Mock()
            mock_page = Mock()
            mock_page.extract_text.return_value = "Test PDF Content"
            mock_reader.pages = [mock_page]
            mock_reader.metadata = {'/Subject': 'Test Subject'}
            mock_pdf_reader.return_value = mock_reader
            
            result = await parser.parse_file(pdf_content, filename)
            
            assert isinstance(result, Email)
            assert result.subject == "Test Subject"
            assert "Test PDF Content" in result.raw_content
    
    @pytest.mark.asyncio
    async def test_parse_txt_file(self, parser):
        """Testa parse de arquivo .txt."""
        content = b"Conteudo do arquivo txt"
        filename = "test.txt"
        
        result = await parser.parse_file(content, filename)
        
        assert isinstance(result, Email)
        assert result.raw_content == "Conteudo do arquivo txt"
    
    @pytest.mark.asyncio
    async def test_parse_eml_file(self, parser):
        """Testa parse de arquivo .eml."""
        content = b"From: sender@test.com\nTo: recipient@test.com\nSubject: Test Subject\n\nEmail body content"
        filename = "test.eml"
        
        result = await parser.parse_file(content, filename)
        
        assert isinstance(result, Email)
        assert result.subject == "Test Subject"
    
    @pytest.mark.asyncio
    async def test_parse_unsupported_file(self, parser):
        """Testa erro para arquivo não suportado."""
        content = b"Conteudo qualquer"
        filename = "test.doc"
        
        with pytest.raises(ValueError, match="Tipo de arquivo não suportado"):
            await parser.parse_file(content, filename)
    
    def test_supports_file_type(self, parser):
        """Testa verificação de tipos de arquivo suportados."""
        assert parser.supports_file_type("test.pdf") is True
        assert parser.supports_file_type("test.txt") is True
        assert parser.supports_file_type("test.eml") is True
        assert parser.supports_file_type("test.doc") is False
        assert parser.supports_file_type("") is False


class TestCompositeEmailParser:
    """Testes para CompositeEmailParser."""
    
    @pytest.fixture
    def parser(self):
        text_parser = TextEmailParser()
        file_parser = FileEmailParser()
        return CompositeEmailParser(text_parser, file_parser)
    
    @pytest.mark.asyncio
    async def test_parse_text_delegates_to_text_parser(self, parser):
        """Testa se parse de texto é delegado para TextEmailParser."""
        text = "Conteudo de teste"
        subject = "Assunto teste"
        
        result = await parser.parse_text(text, subject)
        
        assert isinstance(result, Email)
        assert result.subject == subject
        assert result.raw_content == text
    
    @pytest.mark.asyncio
    async def test_parse_file_delegates_to_file_parser(self, parser):
        """Testa se parse de arquivo é delegado para FileEmailParser."""
        content = b"Conteudo do arquivo"
        filename = "test.txt"
        
        result = await parser.parse_file(content, filename)
        
        assert isinstance(result, Email)
        assert result.raw_content == "Conteudo do arquivo"
    
    def test_supports_file_type_combines_both_parsers(self, parser):
        """Testa se suporte a tipos combina ambos os parsers."""
        # TextEmailParser suporta .txt e .eml
        # FileEmailParser suporta .pdf, .txt e .eml
        assert parser.supports_file_type("test.txt") is True
        assert parser.supports_file_type("test.pdf") is True
        assert parser.supports_file_type("test.eml") is True
        assert parser.supports_file_type("test.doc") is False
