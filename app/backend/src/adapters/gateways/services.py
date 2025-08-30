"""
Implementações dos serviços básicos.

Inclui:
- Serviço de notificação com logs estruturados
- Serviço de segurança básico
- Serviço de cache em memória
- Serviço de métricas Prometheus
"""
import time
import json
import re
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import structlog

from ...core.ports import NotificationPort, SecurityPort, CachePort
from ...core.domain.entities import Email, Classification, SuggestedResponse


class StructuredLoggingService(NotificationPort):
    """
    Serviço de notificação usando logs estruturados.
    
    Implementa logging estruturado com structlog para
    observabilidade e debugging.
    """
    
    def __init__(self):
        # Configura structlog para logs estruturados
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        self.logger = structlog.get_logger()
        self.metrics = defaultdict(int)
    
    async def notify_classification_completed(
        self, 
        email: Email, 
        classification: Classification
    ) -> None:
        """Notifica que uma classificação foi completada."""
        self.logger.info(
            "classification_completed",
            email_id=str(email.email_id),
            label=classification.label,
            confidence=classification.confidence,
            reasoning=classification.reasoning,
            processed_at=classification.processing_time_ms
        )
        
        # Incrementa métricas
        self.metrics[f"classification_{classification.label.lower()}"] += 1
        self.metrics["total_classifications"] += 1
    
    async def notify_response_generated(
        self, 
        email: Email, 
        response: SuggestedResponse
    ) -> None:
        """Notifica que uma resposta foi gerada."""
        self.logger.info(
            "response_generated",
            email_id=str(email.email_id),
            response_subject=response.subject,
            response_body=response.body,
            generated_at=datetime.utcnow()
        )
        
        # Incrementa métricas
        self.metrics["responses_generated"] += 1
    
    async def log_processing_error(
        self, 
        error: Exception, 
        context: Dict[str, Any]
    ) -> None:
        """Registra erro de processamento."""
        self.logger.error(
            "processing_error",
            error_type=type(error).__name__,
            error_message=str(error),
            **context
        )
        
        # Incrementa métricas
        self.metrics["processing_errors"] += 1
        self.metrics[f"error_{type(error).__name__.lower()}"] += 1
    
    async def record_metrics(
        self, 
        metrics: Dict[str, Any]
    ) -> None:
        """Registra métricas de performance."""
        self.logger.info(
            "metrics_recorded",
            **metrics
        )
        
        # Atualiza métricas locais
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                self.metrics[key] = value
            else:
                self.metrics[f"metric_{key}"] = 1
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Retorna resumo das métricas coletadas."""
        return dict(self.metrics)


class BasicSecurityService(SecurityPort):
    """
    Serviço de segurança básico.
    
    Implementa validações básicas de entrada,
    sanitização e rate limiting simples.
    """
    
    def __init__(self):
        self.rate_limit_store = defaultdict(list)
        self.rate_limits = {
            "text_processing": {"max_requests": 100, "window_seconds": 3600},  # 100 por hora
            "file_processing": {"max_requests": 20, "window_seconds": 3600},   # 20 por hora
            "api_calls": {"max_requests": 1000, "window_seconds": 3600}       # 1000 por hora
        }
        
        # Padrões de segurança
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',                 # JavaScript protocol
            r'vbscript:',                   # VBScript protocol
            r'on\w+\s*=',                   # Event handlers
            r'<iframe[^>]*>',              # Iframe tags
            r'<object[^>]*>',              # Object tags
            r'<embed[^>]*>',               # Embed tags
            r'<form[^>]*>',                # Form tags
            r'<input[^>]*>',               # Input tags
            r'<textarea[^>]*>',            # Textarea tags
            r'<select[^>]*>',              # Select tags
            r'<button[^>]*>',              # Button tags
        ]
        
        self.dangerous_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.dangerous_patterns]
    
    async def validate_input(
        self, 
        content: str, 
        content_type: str
    ) -> bool:
        """
        Valida entrada do usuário.
        
        Args:
            content: Conteúdo a ser validado
            content_type: Tipo do conteúdo
            
        Returns:
            True se válido, False caso contrário
        """
        if not content or not isinstance(content, str):
            return False
        
        # Verifica tamanho
        if len(content) > 100000:  # 100KB
            return False
        
        # Verifica padrões perigosos
        for pattern in self.dangerous_patterns:
            if pattern.search(content):
                return False
        
        # Validações específicas por tipo
        if content_type == "text":
            # Verifica caracteres de controle perigosos
            if any(ord(char) < 32 and char not in '\n\r\t' for char in content):
                return False
        
        return True
    
    async def sanitize_content(self, content: str) -> str:
        """
        Sanitiza conteúdo removendo elementos perigosos.
        
        Args:
            content: Conteúdo a ser sanitizado
            
        Returns:
            Conteúdo sanitizado
        """
        if not content:
            return content
        
        # Remove HTML tags perigosas
        for pattern in self.dangerous_patterns:
            content = pattern.sub('', content)
        
        # Remove caracteres de controle perigosos
        content = ''.join(char for char in content if ord(char) >= 32 or char in '\n\r\t')
        
        # Remove múltiplos espaços
        content = re.sub(r'\s+', ' ', content)
        
        return content.strip()
    
    async def check_rate_limit(self, identifier: str) -> bool:
        """
        Verifica se o rate limit foi excedido.
        
        Args:
            identifier: Identificador do tipo de operação
            
        Returns:
            True se dentro do limite, False se excedido
        """
        if identifier not in self.rate_limits:
            return True  # Sem limite para este tipo
        
        limit_config = self.rate_limits[identifier]
        current_time = time.time()
        window_start = current_time - limit_config["window_seconds"]
        
        # Limpa registros antigos
        self.rate_limit_store[identifier] = [
            timestamp for timestamp in self.rate_limit_store[identifier]
            if timestamp > window_start
        ]
        
        # Verifica se excedeu o limite
        if len(self.rate_limit_store[identifier]) >= limit_config["max_requests"]:
            return False
        
        # Adiciona timestamp atual
        self.rate_limit_store[identifier].append(current_time)
        return True
    
    async def log_security_event(
        self, 
        event_type: str, 
        details: Dict[str, Any]
    ) -> None:
        """Registra eventos de segurança."""
        # Usa structlog para logging de segurança
        logger = structlog.get_logger("security")
        
        logger.warning(
            "security_event",
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat(),
            **details
        )
    
    def get_rate_limit_info(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Retorna informações sobre rate limit."""
        if identifier not in self.rate_limits:
            return None
        
        limit_config = self.rate_limits[identifier]
        current_usage = len(self.rate_limit_store[identifier])
        
        return {
            "identifier": identifier,
            "max_requests": limit_config["max_requests"],
            "window_seconds": limit_config["window_seconds"],
            "current_usage": current_usage,
            "remaining": max(0, limit_config["max_requests"] - current_usage),
            "reset_time": datetime.utcnow() + timedelta(seconds=limit_config["window_seconds"])
        }


class InMemoryCacheService(CachePort):
    """
    Serviço de cache em memória.
    
    Implementa cache simples usando dicionário Python.
    Útil para desenvolvimento e testes.
    """
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._expiry_times: Dict[str, float] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """Recupera valor do cache."""
        if key not in self._cache:
            return None
        
        # Verifica se expirou
        if key in self._expiry_times:
            if time.time() > self._expiry_times[key]:
                # Remove item expirado
                await self.delete(key)
                return None
        
        return self._cache[key]["value"]
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl_seconds: Optional[int] = None
    ) -> None:
        """
        Armazena valor no cache.
        
        Args:
            key: Chave do cache
            value: Valor a ser armazenado
            ttl_seconds: Tempo de vida em segundos (opcional)
        """
        self._cache[key] = {
            "value": value,
            "created_at": time.time(),
            "access_count": 0
        }
        
        if ttl_seconds:
            self._expiry_times[key] = time.time() + ttl_seconds
    
    async def delete(self, key: str) -> bool:
        """Remove valor do cache."""
        if key in self._cache:
            del self._cache[key]
            if key in self._expiry_times:
                del self._expiry_times[key]
            return True
        return False
    
    async def clear(self) -> None:
        """Limpa todo o cache."""
        self._cache.clear()
        self._expiry_times.clear()
    
    async def get_cache_info(self, key: str) -> Optional[Dict[str, Any]]:
        """Retorna informações sobre item do cache."""
        if key not in self._cache:
            return None
        
        item = self._cache[key]
        expiry_time = self._expiry_times.get(key)
        
        return {
            "key": key,
            "created_at": datetime.fromtimestamp(item["created_at"]).isoformat(),
            "access_count": item["access_count"],
            "expires_at": datetime.fromtimestamp(expiry_time).isoformat() if expiry_time else None,
            "is_expired": expiry_time and time.time() > expiry_time if expiry_time else False
        }
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        total_items = len(self._cache)
        expired_items = sum(
            1 for key in self._cache.keys()
            if key in self._expiry_times and time.time() > self._expiry_times[key]
        )
        
        total_size = sum(
            len(str(item["value"])) for item in self._cache.values()
        )
        
        return {
            "total_items": total_items,
            "expired_items": expired_items,
            "active_items": total_items - expired_items,
            "total_size_bytes": total_size,
            "cache_type": "in_memory"
        }
    
    async def cleanup_expired(self) -> int:
        """Remove itens expirados e retorna quantidade removida."""
        expired_keys = [
            key for key in self._cache.keys()
            if key in self._expiry_times and time.time() > self._expiry_times[key]
        ]
        
        for key in expired_keys:
            await self.delete(key)
        
        return len(expired_keys)


class PrometheusMetricsService(NotificationPort):
    """
    Serviço de métricas Prometheus.
    
    Implementa coleta de métricas para monitoramento
    e observabilidade em produção.
    """
    
    def __init__(self):
        try:
            from prometheus_client import Counter, Histogram, Gauge, generate_latest
            self.prometheus_available = True
            
            # Métricas Prometheus
            self.classification_counter = Counter(
                'email_classifications_total',
                'Total de classificações de email',
                ['label', 'model_used']
            )
            
            self.processing_duration = Histogram(
                'email_processing_duration_seconds',
                'Duração do processamento de email',
                ['operation']
            )
            
            self.response_generation_counter = Counter(
                'email_responses_generated_total',
                'Total de respostas geradas',
                ['tone', 'language']
            )
            
            self.error_counter = Counter(
                'email_processing_errors_total',
                'Total de erros de processamento',
                ['error_type']
            )
            
            self.active_emails_gauge = Gauge(
                'active_emails_total',
                'Total de emails ativos no sistema'
            )
            
        except ImportError:
            self.prometheus_available = False
            print("Prometheus client não disponível. Métricas serão ignoradas.")
    
    async def notify_classification_completed(
        self, 
        email: Email, 
        classification: Classification
    ) -> None:
        """Notifica classificação completada."""
        if not self.prometheus_available:
            return
        
        # Incrementa contador de classificações
        self.classification_counter.labels(
            label=classification.label,
            model_used="heuristic"
        ).inc()
    
    async def notify_response_generated(
        self, 
        email: Email, 
        response: SuggestedResponse
    ) -> None:
        """Notifica resposta gerada."""
        if not self.prometheus_available:
            return
        
        # Incrementa contador de respostas
        self.response_generation_counter.labels(
            tone="professional",
            language="pt"
        ).inc()
    
    async def log_processing_error(
        self, 
        error: Exception, 
        context: Dict[str, Any]
    ) -> None:
        """Registra erro de processamento."""
        if not self.prometheus_available:
            return
        
        # Incrementa contador de erros
        error_type = type(error).__name__
        self.error_counter.labels(error_type=error_type).inc()
    
    async def record_metrics(
        self, 
        metrics: Dict[str, Any]
    ) -> None:
        """Registra métricas customizadas."""
        if not self.prometheus_available:
            return
        
        # Atualiza métricas específicas
        if "active_emails" in metrics:
            self.active_emails_gauge.set(metrics["active_emails"])
    
    def get_metrics(self) -> str:
        """Retorna métricas no formato Prometheus."""
        if not self.prometheus_available:
            return "# Prometheus client não disponível"
        
        try:
            from prometheus_client import generate_latest
            return generate_latest().decode('utf-8')
        except Exception as e:
            return f"# Erro ao gerar métricas: {e}"


class RedisCacheService(CachePort):
    """
    Serviço de cache Redis.
    
    Implementa cache distribuído usando Redis.
    Para produção com alta performance.
    """
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Inicializa cliente Redis."""
        try:
            import redis
            self.redis_client = redis.from_url(self.redis_url)
            # Testa conexão
            self.redis_client.ping()
        except Exception as e:
            print(f"Erro ao conectar Redis: {e}")
            self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Recupera valor do cache Redis."""
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Armazena valor no cache Redis."""
        if not self.redis_client:
            return
        
        try:
            serialized_value = json.dumps(value)
            if ttl_seconds:
                self.redis_client.setex(key, ttl_seconds, serialized_value)
            else:
                self.redis_client.set(key, serialized_value)
        except Exception:
            pass  # Ignora erros de cache
    
    async def delete(self, key: str) -> bool:
        """Remove valor do cache Redis."""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception:
            return False
    
    async def clear(self) -> None:
        """Limpa todo o cache Redis."""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.flushdb()
        except Exception:
            pass
    
    def is_available(self) -> bool:
        """Verifica se Redis está disponível."""
        return self.redis_client is not None
