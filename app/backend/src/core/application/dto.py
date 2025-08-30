"""
DTOs (Data Transfer Objects) e schemas para a camada de aplicação.

Define estruturas de dados para comunicação entre camadas
e validação de entrada/saída.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

from ..domain.entities import EmailLabel


class EmailProcessingRequest(BaseModel):
    """Request para processamento de email."""
    
    text: Optional[str] = Field(None, description="Texto do email")
    subject: Optional[str] = Field(None, description="Assunto do email")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados adicionais")
    
    @validator('text')
    def validate_text(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Texto não pode estar vazio")
        if v is not None and len(v) > 100000:
            raise ValueError("Texto excede o limite de 100KB")
        return v
    
    @validator('subject')
    def validate_subject(cls, v):
        if v is not None and len(v) > 255:
            raise ValueError("Assunto excede o limite de 255 caracteres")
        return v


class EmailProcessingResponse(BaseModel):
    """Response para processamento de email."""
    
    success: bool = Field(..., description="Indica se o processamento foi bem-sucedido")
    email_id: str = Field(..., description="ID único do email processado")
    classification: Dict[str, Any] = Field(..., description="Resultado da classificação")
    suggested_response: Dict[str, Any] = Field(..., description="Resposta sugerida")
    processing_time_ms: float = Field(..., description="Tempo de processamento em ms")
    metadata: Dict[str, Any] = Field(..., description="Metadados do processamento")
    error: Optional[str] = Field(None, description="Mensagem de erro (se houver)")


class ClassificationResult(BaseModel):
    """Resultado da classificação."""
    
    model_config = {"protected_namespaces": ()}
    
    label: str = Field(..., description="Label da classificação")
    confidence: float = Field(..., description="Confiança da classificação (0-1)")
    reasoning: Optional[str] = Field(None, description="Explicação da classificação")
    model_used: Optional[str] = Field(None, description="Modelo usado para classificação")


class SuggestedResponseResult(BaseModel):
    """Resposta sugerida."""
    
    subject: Optional[str] = Field(None, description="Assunto sugerido")
    body: str = Field(..., description="Corpo da resposta sugerida")
    tone: str = Field(..., description="Tom da resposta")
    language: str = Field(..., description="Idioma da resposta")
    estimated_response_time: Optional[str] = Field(None, description="Tempo estimado de resposta")


class EmailMetadata(BaseModel):
    """Metadados do email processado."""
    
    word_count: int = Field(..., description="Número de palavras")
    language: str = Field(..., description="Idioma detectado")
    has_attachments: bool = Field(..., description="Se possui anexos")
    processing_status: str = Field(..., description="Status do processamento")


class EmailInfo(BaseModel):
    """Informações básicas do email."""
    
    email_id: str = Field(..., description="ID único do email")
    subject: Optional[str] = Field(None, description="Assunto do email")
    sender: Optional[str] = Field(None, description="Remetente")
    received_at: datetime = Field(..., description="Data/hora de recebimento")
    processing_status: str = Field(..., description="Status do processamento")


class ProcessingStats(BaseModel):
    """Estatísticas de processamento."""
    
    total_emails: int = Field(..., description="Total de emails processados")
    productive_count: int = Field(..., description="Emails produtivos")
    unproductive_count: int = Field(..., description="Emails improdutivos")
    average_confidence: float = Field(..., description="Confiança média")
    average_processing_time_ms: float = Field(..., description="Tempo médio de processamento")
    last_processed_at: Optional[datetime] = Field(None, description="Último email processado")


class HealthCheckResponse(BaseModel):
    """Response para verificação de saúde."""
    
    status: str = Field(..., description="Status geral do sistema")
    timestamp: datetime = Field(..., description="Timestamp da verificação")
    components: Dict[str, Dict[str, Any]] = Field(..., description="Status dos componentes")
    version: str = Field(..., description="Versão da aplicação")
    uptime_seconds: float = Field(..., description="Tempo de atividade em segundos")


class ComponentHealth(BaseModel):
    """Status de saúde de um componente."""
    
    status: str = Field(..., description="Status do componente")
    last_check: datetime = Field(..., description="Última verificação")
    response_time_ms: Optional[float] = Field(None, description="Tempo de resposta")
    error: Optional[str] = Field(None, description="Erro (se houver)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados do componente")


class ErrorResponse(BaseModel):
    """Response padrão para erros."""
    
    error: str = Field(..., description="Tipo do erro")
    message: str = Field(..., description="Mensagem descritiva do erro")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalhes adicionais")
    timestamp: datetime = Field(..., description="Timestamp do erro")
    request_id: Optional[str] = Field(None, description="ID da requisição")


class RateLimitResponse(BaseModel):
    """Response para rate limit excedido."""
    
    error: str = Field("rate_limit_exceeded", description="Tipo do erro")
    message: str = Field("Rate limit excedido", description="Mensagem do erro")
    retry_after_seconds: int = Field(..., description="Segundos para tentar novamente")
    limit: int = Field(..., description="Limite de requisições")
    window_seconds: int = Field(..., description="Janela de tempo em segundos")


class FileUploadRequest(BaseModel):
    """Request para upload de arquivo."""
    
    file: bytes = Field(..., description="Conteúdo do arquivo")
    filename: str = Field(..., description="Nome do arquivo")
    content_type: str = Field(..., description="Tipo de conteúdo")
    subject: Optional[str] = Field(None, description="Assunto do email")
    
    @validator('filename')
    def validate_filename(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Nome do arquivo é obrigatório")
        if len(v) > 255:
            raise ValueError("Nome do arquivo muito longo")
        return v
    
    @validator('file')
    def validate_file_size(cls, v):
        if len(v) > 10 * 1024 * 1024:  # 10MB
            raise ValueError("Arquivo excede o limite de 10MB")
        return v


class BatchProcessingRequest(BaseModel):
    """Request para processamento em lote."""
    
    emails: List[EmailProcessingRequest] = Field(..., description="Lista de emails para processar")
    batch_size: Optional[int] = Field(10, description="Tamanho do lote")
    priority: Optional[str] = Field("normal", description="Prioridade do processamento")
    
    @validator('emails')
    def validate_emails(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Lista de emails não pode estar vazia")
        if len(v) > 100:
            raise ValueError("Máximo de 100 emails por lote")
        return v
    
    @validator('batch_size')
    def validate_batch_size(cls, v):
        if v is not None and (v < 1 or v > 50):
            raise ValueError("Tamanho do lote deve estar entre 1 e 50")
        return v


class BatchProcessingResponse(BaseModel):
    """Response para processamento em lote."""
    
    batch_id: str = Field(..., description="ID do lote processado")
    total_emails: int = Field(..., description="Total de emails no lote")
    processed_count: int = Field(..., description="Emails processados com sucesso")
    failed_count: int = Field(..., description="Emails que falharam")
    results: List[EmailProcessingResponse] = Field(..., description="Resultados individuais")
    processing_time_ms: float = Field(..., description="Tempo total de processamento")
    errors: List[Dict[str, Any]] = Field(..., description="Erros encontrados")


class SearchRequest(BaseModel):
    """Request para busca de emails."""
    
    query: Optional[str] = Field(None, description="Query de busca")
    label: Optional[str] = Field(None, description="Filtrar por label")
    date_from: Optional[datetime] = Field(None, description="Data inicial")
    date_to: Optional[datetime] = Field(None, description="Data final")
    limit: Optional[int] = Field(100, description="Limite de resultados")
    offset: Optional[int] = Field(0, description="Offset para paginação")
    
    @validator('limit')
    def validate_limit(cls, v):
        if v is not None and (v < 1 or v > 1000):
            raise ValueError("Limite deve estar entre 1 e 1000")
        return v
    
    @validator('offset')
    def validate_offset(cls, v):
        if v is not None and v < 0:
            raise ValueError("Offset deve ser maior ou igual a 0")
        return v


class SearchResponse(BaseModel):
    """Response para busca de emails."""
    
    results: List[EmailInfo] = Field(..., description="Resultados da busca")
    total_count: int = Field(..., description="Total de resultados")
    has_more: bool = Field(..., description="Se há mais resultados")
    query_time_ms: float = Field(..., description="Tempo da consulta")
    facets: Dict[str, Any] = Field(..., description="Facetas da busca")

