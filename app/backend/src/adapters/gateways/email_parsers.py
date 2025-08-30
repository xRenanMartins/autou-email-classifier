"""
Implementações dos parsers de email.

Suporta diferentes formatos:
- Texto simples
- Arquivos PDF
- Arquivos .txt
- Arquivos .eml
"""
import re
from typing import Optional, List
from datetime import datetime
import pypdf
from email import message_from_string
from email.parser import Parser as EmailParser

from ...core.ports import EmailParserPort
from ...core.domain.entities import Email, EmailAttachment


class TextEmailParser(EmailParserPort):
    """
    Parser para emails em formato texto simples.
    
    Extrai informações básicas como assunto e conteúdo,
    assumindo formato simples de email.
    """
    
    def __init__(self):
        self.subject_pattern = re.compile(r'^assunto:\s*(.+)$', re.IGNORECASE | re.MULTILINE)
        self.from_pattern = re.compile(r'^de:\s*(.+)$', re.IGNORECASE | re.MULTILINE)
        self.to_pattern = re.compile(r'^para:\s*(.+)$', re.IGNORECASE | re.MULTILINE)
    
    async def parse_text(self, text: str, subject: Optional[str] = None) -> Email:
        """
        Parse de texto simples para Email.
        
        Args:
            text: Conteúdo do email
            subject: Assunto opcional
            
        Returns:
            Entidade Email populada
        """
        # Extrai metadados do texto se não fornecidos
        extracted_subject = subject or self._extract_subject(text)
        extracted_from = self._extract_from(text)
        extracted_to = self._extract_to(text)
        
        # Remove cabeçalhos do conteúdo
        clean_content = self._clean_content(text)
        
        return Email(
            raw_content=clean_content,
            subject=extracted_subject,
            sender=extracted_from,
            recipients=extracted_to.split(',') if extracted_to else [],
            received_at=datetime.utcnow()
        )
    
    async def parse_file(self, file_content: bytes, filename: str) -> Email:
        """Parse de arquivo de texto."""
        if not filename.lower().endswith('.txt'):
            raise ValueError(f"Tipo de arquivo não suportado: {filename}")
        
        text_content = file_content.decode('utf-8', errors='ignore')
        return await self.parse_text(text_content)
    
    async def parse_email_file(self, eml_content: str) -> Email:
        """Parse de arquivo .eml."""
        # Usa parser de email padrão do Python
        email_message = message_from_string(eml_content)
        
        # Extrai informações básicas
        subject = email_message.get('Subject')
        sender = email_message.get('From')
        recipients = email_message.get('To', '').split(',')
        
        # Extrai corpo do email
        body = self._extract_email_body(email_message)
        
        return Email(
            raw_content=body,
            subject=subject,
            sender=sender,
            recipients=recipients,
            received_at=datetime.utcnow()
        )
    
    def supports_file_type(self, filename: str) -> bool:
        """Verifica se o tipo de arquivo é suportado."""
        if not filename:
            return False
        
        supported_extensions = ['.txt', '.eml']
        return any(filename.lower().endswith(ext) for ext in supported_extensions)
    
    def _extract_subject(self, text: str) -> Optional[str]:
        """Extrai assunto do texto."""
        match = self.subject_pattern.search(text)
        return match.group(1).strip() if match else None
    
    def _extract_from(self, text: str) -> Optional[str]:
        """Extrai remetente do texto."""
        match = self.from_pattern.search(text)
        return match.group(1).strip() if match else None
    
    def _extract_to(self, text: str) -> Optional[str]:
        """Extrai destinatários do texto."""
        match = self.to_pattern.search(text)
        return match.group(1).strip() if match else None
    
    def _clean_content(self, text: str) -> str:
        """Remove cabeçalhos e limpa o conteúdo."""
        lines = text.split('\n')
        clean_lines = []
        
        for line in lines:
            # Para no primeiro conteúdo que não seja cabeçalho
            if not any([
                self.subject_pattern.match(line),
                self.from_pattern.match(line),
                self.to_pattern.match(line),
                line.strip() == ''
            ]):
                clean_lines.append(line)
        
        return '\n'.join(clean_lines).strip()
    
    def _extract_email_body(self, email_message) -> str:
        """Extrai corpo do email MIME."""
        body = ""
        
        if email_message.is_multipart():
            # Email multipart
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
        else:
            # Email simples
            body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        return body


class FileEmailParser(EmailParserPort):
    """
    Parser para arquivos de email (PDF, etc.).
    
    Suporta diferentes tipos de arquivo e extrai
    o conteúdo textual para processamento.
    """
    
    def __init__(self):
        self.supported_extensions = ['.pdf', '.txt', '.eml']
    
    async def parse_text(self, text: str, subject: Optional[str] = None) -> Email:
        """Parse de texto simples (delega para TextEmailParser)."""
        text_parser = TextEmailParser()
        return await text_parser.parse_text(text, subject)
    
    async def parse_file(self, file_content: bytes, filename: str) -> Email:
        """
        Parse de arquivo baseado na extensão.
        
        Args:
            file_content: Conteúdo do arquivo em bytes
            filename: Nome do arquivo
            
        Returns:
            Entidade Email populada
        """
        if not self.supports_file_type(filename):
            raise ValueError(f"Tipo de arquivo não suportado: {filename}")
        
        extension = filename.lower()
        
        if extension.endswith('.pdf'):
            return await self._parse_pdf(file_content, filename)
        elif extension.endswith('.txt'):
            return await self._parse_text_file(file_content, filename)
        elif extension.endswith('.eml'):
            return await self._parse_eml_file(file_content, filename)
        else:
            raise ValueError(f"Extensão não implementada: {extension}")
    
    async def parse_email_file(self, eml_content: str) -> Email:
        """Parse de arquivo .eml."""
        text_parser = TextEmailParser()
        return await text_parser.parse_email_file(eml_content)
    
    def supports_file_type(self, filename: str) -> bool:
        """Verifica se o tipo de arquivo é suportado."""
        if not filename:
            return False
        
        return any(filename.lower().endswith(ext) for ext in self.supported_extensions)
    
    async def _parse_pdf(self, file_content: bytes, filename: str) -> Email:
        """Parse de arquivo PDF."""
        try:
            # Para pypdf 3.x, precisamos usar BytesIO para criar um stream
            from io import BytesIO
            
            # Cria um stream de bytes para o PdfReader
            pdf_stream = BytesIO(file_content)
            pdf_reader = pypdf.PdfReader(pdf_stream)
            text_content = ""
            
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
            
            # Tenta extrair metadados
            metadata = pdf_reader.metadata
            subject = metadata.get('/Subject') if metadata else None
            
            return Email(
                raw_content=text_content.strip(),
                subject=subject or f"PDF: {filename}",
                received_at=datetime.utcnow()
            )
            
        except Exception as e:
            raise ValueError(f"Erro ao processar PDF: {str(e)}")
    
    async def _parse_text_file(self, file_content: bytes, filename: str) -> Email:
        """Parse de arquivo de texto."""
        try:
            text_content = file_content.decode('utf-8', errors='ignore')
            text_parser = TextEmailParser()
            return await text_parser.parse_text(text_content, f"Arquivo: {filename}")
            
        except Exception as e:
            raise ValueError(f"Erro ao processar arquivo de texto: {str(e)}")
    
    async def _parse_eml_file(self, file_content: bytes, filename: str) -> Email:
        """Parse de arquivo .eml."""
        try:
            eml_content = file_content.decode('utf-8', errors='ignore')
            text_parser = TextEmailParser()
            return await text_parser.parse_email_file(eml_content)
            
        except Exception as e:
            raise ValueError(f"Erro ao processar arquivo .eml: {str(e)}")


class CompositeEmailParser(EmailParserPort):
    """
    Parser composto que delega para o parser apropriado.
    
    Combina diferentes parsers e escolhe o mais adequado
    baseado no tipo de entrada.
    """
    
    def __init__(self, text_parser: TextEmailParser, file_parser: FileEmailParser):
        self.text_parser = text_parser
        self.file_parser = file_parser
    
    async def parse_text(self, text: str, subject: Optional[str] = None) -> Email:
        """Parse de texto usando TextEmailParser."""
        return await self.text_parser.parse_text(text, subject)
    
    async def parse_file(self, file_content: bytes, filename: str) -> Email:
        """Parse de arquivo usando FileEmailParser."""
        return await self.file_parser.parse_file(file_content, filename)
    
    async def parse_email_file(self, eml_content: str) -> Email:
        """Parse de arquivo .eml usando TextEmailParser."""
        return await self.text_parser.parse_email_file(eml_content)
    
    def supports_file_type(self, filename: str) -> bool:
        """Verifica suporte combinando ambos os parsers."""
        return (
            self.text_parser.supports_file_type(filename) or
            self.file_parser.supports_file_type(filename)
        )

