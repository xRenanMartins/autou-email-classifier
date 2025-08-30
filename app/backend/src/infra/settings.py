"""
Configurações da aplicação usando Pydantic Settings.

Centraliza todas as configurações da aplicação,
permitindo fácil customização via variáveis de ambiente.
"""
import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """
    Configurações da aplicação.
    
    Suporta configuração via variáveis de ambiente
    com validação automática.
    """
    
    # Configurações básicas
    app_name: str = Field("Email Classifier API", description="Nome da aplicação")
    version: str = Field("1.0.0", description="Versão da aplicação")
    debug: bool = Field(False, description="Modo debug")
    environment: str = Field("development", description="Ambiente de execução")
    
    # Configurações do servidor
    host: str = Field("0.0.0.0", description="Host do servidor")
    port: int = Field(8000, description="Porta do servidor")
    
    # Configurações de segurança
    allowed_hosts: List[str] = Field(
        ["*"], 
        description="Hosts permitidos para TrustedHostMiddleware"
    )
    cors_origins: List[str] = Field(
        [
            "http://localhost:3000", 
            "http://localhost:8080",
            "https://*.vercel.app",
            "https://*.onrender.com"
        ],
        description="Origens permitidas para CORS"
    )
    
    # Configurações de banco de dados
    database_url: str = Field(
        "sqlite:///./emails.db",
        description="URL de conexão com banco de dados"
    )
    use_database: bool = Field(False, description="Se deve usar banco de dados")
    
    # Configurações de IA
    openai_api_key: Optional[str] = Field(
        None, 
        description="Chave da API OpenAI"
    )
    huggingface_token: Optional[str] = Field(
        None, 
        description="Token do Hugging Face"
    )
    
    # Configurações de cache
    redis_url: Optional[str] = Field(
        None, 
        description="URL de conexão com Redis"
    )
    
    # Configurações de logging
    log_level: str = Field("INFO", description="Nível de logging")
    log_format: str = Field("json", description="Formato dos logs")
    
    # Configurações de rate limiting
    rate_limit_enabled: bool = Field(True, description="Se rate limiting está habilitado")
    rate_limit_default: int = Field(100, description="Rate limit padrão por hora")
    
    # Configurações de upload
    max_file_size_mb: int = Field(10, description="Tamanho máximo de arquivo em MB")
    max_text_length_kb: int = Field(100, description="Tamanho máximo de texto em KB")
    
    # Configurações de métricas
    metrics_enabled: bool = Field(True, description="Se métricas estão habilitadas")
    prometheus_enabled: bool = Field(False, description="Se Prometheus está habilitado")
    
    # Configurações de monitoramento
    health_check_interval: int = Field(30, description="Intervalo de health check em segundos")
    
    # Configurações de segurança adicional
    enable_trusted_hosts: bool = Field(True, description="Se TrustedHostMiddleware está habilitado")
    enable_cors: bool = Field(True, description="Se CORS está habilitado")
    
    class Config:
        """Configuração do Pydantic."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("environment")
    def validate_environment(cls, v):
        """Valida ambiente."""
        allowed = ["development", "staging", "production", "test"]
        if v not in allowed:
            raise ValueError(f"Ambiente deve ser um de: {allowed}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Valida nível de logging."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"Nível de logging deve ser um de: {allowed}")
        return v.upper()
    
    @validator("port")
    def validate_port(cls, v):
        """Valida porta."""
        if not 1 <= v <= 65535:
            raise ValueError("Porta deve estar entre 1 e 65535")
        return v
    
    @validator("max_file_size_mb")
    def validate_max_file_size(cls, v):
        """Valida tamanho máximo de arquivo."""
        if v <= 0:
            raise ValueError("Tamanho máximo de arquivo deve ser positivo")
        if v > 100:
            raise ValueError("Tamanho máximo de arquivo não pode exceder 100MB")
        return v
    
    @validator("max_text_length_kb")
    def validate_max_text_length(cls, v):
        """Valida tamanho máximo de texto."""
        if v <= 0:
            raise ValueError("Tamanho máximo de texto deve ser positivo")
        if v > 1000:
            raise ValueError("Tamanho máximo de texto não pode exceder 1000KB")
        return v
    
    @property
    def is_production(self) -> bool:
        """Verifica se está em produção."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Verifica se está em desenvolvimento."""
        return self.environment == "development"
    
    @property
    def is_testing(self) -> bool:
        """Verifica se está em teste."""
        return self.environment == "test"
    
    @property
    def max_file_size_bytes(self) -> int:
        """Retorna tamanho máximo de arquivo em bytes."""
        return self.max_file_size_mb * 1024 * 1024
    
    @property
    def max_text_length_bytes(self) -> int:
        """Retorna tamanho máximo de texto em bytes."""
        return self.max_text_length_kb * 1024
    
    def get_cors_origins(self) -> List[str]:
        """Retorna origens CORS baseado no ambiente."""
        if self.is_production:
            # Em produção, usa apenas origens específicas
            return self.cors_origins
        else:
            # Em desenvolvimento, permite localhost
            return self.cors_origins + ["http://localhost:*", "http://127.0.0.1:*"]
    
    def get_allowed_hosts(self) -> List[str]:
        """Retorna hosts permitidos baseado no ambiente."""
        if self.is_production:
            # Em produção, usa apenas hosts específicos
            return self.allowed_hosts
        else:
            # Em desenvolvimento, permite todos
            return ["*"]
    
    def get_database_config(self) -> dict:
        """Retorna configuração de banco de dados."""
        if not self.use_database:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "url": self.database_url,
            "type": "sqlite" if "sqlite" in self.database_url else "postgresql"
        }
    
    def get_ai_config(self) -> dict:
        """Retorna configuração de IA."""
        return {
            "openai": {
                "enabled": bool(self.openai_api_key),
                "api_key": self.openai_api_key
            },
            "huggingface": {
                "enabled": bool(self.huggingface_token),
                "token": self.huggingface_token
            }
        }
    
    def get_cache_config(self) -> dict:
        """Retorna configuração de cache."""
        return {
            "type": "redis" if self.redis_url else "memory",
            "redis_url": self.redis_url,
            "enabled": True
        }
    
    def get_security_config(self) -> dict:
        """Retorna configuração de segurança."""
        return {
            "rate_limiting": {
                "enabled": self.rate_limit_enabled,
                "default_limit": self.rate_limit_default
            },
            "trusted_hosts": {
                "enabled": self.enable_trusted_hosts,
                "hosts": self.get_allowed_hosts()
            },
            "cors": {
                "enabled": self.enable_cors,
                "origins": self.get_cors_origins()
            }
        }
    
    def get_monitoring_config(self) -> dict:
        """Retorna configuração de monitoramento."""
        return {
            "metrics": {
                "enabled": self.metrics_enabled,
                "prometheus": self.prometheus_enabled
            },
            "health_check": {
                "interval": self.health_check_interval
            },
            "logging": {
                "level": self.log_level,
                "format": self.log_format
            }
        }


# Instância global das configurações
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Retorna instância das configurações."""
    global _settings
    
    if _settings is None:
        _settings = Settings()
    
    return _settings


def reload_settings() -> Settings:
    """Recarrega as configurações."""
    global _settings
    _settings = Settings()
    return _settings


# Configurações específicas por ambiente
def get_development_settings() -> Settings:
    """Configurações para desenvolvimento."""
    return Settings(
        environment="development",
        debug=True,
        host="127.0.0.1",
        port=8000,
        cors_origins=["http://localhost:3000", "http://localhost:8080"],
        log_level="DEBUG",
        use_database=False,
        metrics_enabled=False
    )


def get_production_settings() -> Settings:
    """Configurações para produção."""
    return Settings(
        environment="production",
        debug=False,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        cors_origins=os.getenv("CORS_ORIGINS", "").split(","),
        log_level="INFO",
        use_database=True,
        metrics_enabled=True,
        prometheus_enabled=True,
        enable_trusted_hosts=True
    )


def get_test_settings() -> Settings:
    """Configurações para testes."""
    return Settings(
        environment="test",
        debug=True,
        host="127.0.0.1",
        port=0,  # Porta aleatória para testes
        cors_origins=["http://localhost:3000"],
        log_level="DEBUG",
        use_database=False,
        metrics_enabled=False,
        rate_limit_enabled=False
    )

