"""
Implementações dos repositórios em memória.

Para desenvolvimento e testes, oferece persistência
temporária sem dependência de banco de dados.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from collections import defaultdict

from ...core.ports import EmailRepositoryPort, TemplateRepositoryPort
from ...core.domain.entities import Email, EmailLabel, ResponseTemplate


class InMemoryEmailRepository(EmailRepositoryPort):
    """
    Repositório de emails em memória.
    
    Armazena emails em dicionário Python para desenvolvimento
    e testes. Dados são perdidos ao reiniciar a aplicação.
    """
    
    def __init__(self):
        self._emails: Dict[str, Email] = {}
        self._counter = 0
    
    async def save(self, email: Email) -> Email:
        """Salva um email no repositório."""
        # Gera ID se não existir
        if not hasattr(email, 'email_id') or not email.email_id:
            email.email_id = uuid.uuid4()
        
        email_id_str = str(email.email_id)
        
        # Adiciona timestamp de criação/modificação
        if not hasattr(email, '_created_at'):
            email._created_at = datetime.utcnow()
        email._updated_at = datetime.utcnow()
        
        # Armazena no dicionário
        self._emails[email_id_str] = email
        self._counter += 1
        
        return email
    
    async def get_by_id(self, email_id: str) -> Optional[Email]:
        """Busca email por ID."""
        return self._emails.get(email_id)
    
    async def get_by_classification(
        self, 
        label: EmailLabel, 
        limit: int = 100
    ) -> List[Email]:
        """Busca emails por classificação."""
        filtered_emails = []
        
        for email in self._emails.values():
            if (hasattr(email, '_classification') and 
                email._classification and 
                email._classification.label == label):
                filtered_emails.append(email)
                
                if len(filtered_emails) >= limit:
                    break
        
        # Ordena por data de criação (mais recente primeiro)
        filtered_emails.sort(key=lambda x: x._created_at, reverse=True)
        
        return filtered_emails
    
    async def get_processing_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de processamento."""
        total_emails = len(self._emails)
        productive_count = 0
        unproductive_count = 0
        total_confidence = 0.0
        total_processing_time = 0.0
        last_processed = None
        
        for email in self._emails.values():
            if hasattr(email, '_classification') and email._classification:
                if email._classification.label == EmailLabel.PRODUCTIVE:
                    productive_count += 1
                else:
                    unproductive_count += 1
                
                total_confidence += email._classification.confidence
                
                if hasattr(email._classification, 'processing_time_ms'):
                    total_processing_time += email._classification.processing_time_ms
                
                if hasattr(email, '_updated_at'):
                    if last_processed is None or email._updated_at > last_processed:
                        last_processed = email._updated_at
        
        # Calcula médias
        avg_confidence = total_confidence / total_emails if total_emails > 0 else 0.0
        avg_processing_time = total_processing_time / total_emails if total_emails > 0 else 0.0
        
        return {
            "total_emails": total_emails,
            "productive_count": productive_count,
            "unproductive_count": unproductive_count,
            "average_confidence": round(avg_confidence, 3),
            "average_processing_time_ms": round(avg_processing_time, 2),
            "last_processed_at": last_processed.isoformat() if last_processed else None,
            "repository_type": "in_memory"
        }
    
    async def delete(self, email_id: str) -> bool:
        """Remove um email do repositório."""
        if email_id in self._emails:
            del self._emails[email_id]
            return True
        return False
    
    async def search(
        self, 
        query: Optional[str] = None,
        label: Optional[EmailLabel] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Email]:
        """Busca emails com filtros."""
        filtered_emails = []
        
        for email in self._emails.values():
            # Filtra por label
            if label and (not hasattr(email, '_classification') or 
                         not email._classification or 
                         email._classification.label != label):
                continue
            
            # Filtra por data
            if date_from and hasattr(email, '_created_at') and email._created_at < date_from:
                continue
            if date_to and hasattr(email, '_created_at') and email._created_at > date_to:
                continue
            
            # Filtra por query de texto
            if query:
                query_lower = query.lower()
                content_match = query_lower in email.raw_content.lower()
                subject_match = email.subject and query_lower in email.subject.lower()
                
                if not content_match and not subject_match:
                    continue
            
            filtered_emails.append(email)
        
        # Ordena por data de criação (mais recente primeiro)
        filtered_emails.sort(key=lambda x: x._created_at, reverse=True)
        
        # Aplica paginação
        start = offset
        end = start + limit
        return filtered_emails[start:end]
    
    async def get_recent_emails(self, limit: int = 10) -> List[Email]:
        """Retorna emails mais recentes."""
        all_emails = list(self._emails.values())
        all_emails.sort(key=lambda x: x._created_at, reverse=True)
        return all_emails[:limit]
    
    async def clear(self) -> int:
        """Limpa todos os emails e retorna quantidade removida."""
        count = len(self._emails)
        self._emails.clear()
        self._counter = 0
        return count


class InMemoryTemplateRepository(TemplateRepositoryPort):
    """
    Repositório de templates em memória.
    
    Armazena templates de resposta para desenvolvimento
    e testes. Dados são perdidos ao reiniciar a aplicação.
    """
    
    def __init__(self):
        self._templates: Dict[str, ResponseTemplate] = {}
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        """Inicializa templates padrão."""
        from ...core.domain.entities import EmailLabel
        
        default_templates = [
            # Templates para emails PRODUTIVOS
            ResponseTemplate(
                template_id=uuid.uuid4(),
                label_target=EmailLabel.PRODUCTIVE,
                template_text=(
                    "Olá! Entendo sua solicitação sobre {topic}. "
                    "Vou analisar e retornar em breve com uma solução."
                ),
                variables=["topic"],
                tone="professional",
                language="pt"
            ),
            ResponseTemplate(
                template_id=uuid.uuid4(),
                label_target=EmailLabel.PRODUCTIVE,
                template_text=(
                    "Obrigado pelo contato! Sua dúvida sobre {topic} "
                    "foi registrada e está sendo analisada."
                ),
                variables=["topic"],
                tone="friendly",
                language="pt"
            ),
            
            # Templates para emails IMPRODUTIVOS
            ResponseTemplate(
                template_id=uuid.uuid4(),
                label_target=EmailLabel.UNPRODUCTIVE,
                template_text=(
                    "Obrigado pelo contato! Ficamos felizes em saber que "
                    "está satisfeito com nossos serviços."
                ),
                variables=[],
                tone="friendly",
                language="pt"
            ),
            ResponseTemplate(
                template_id=uuid.uuid4(),
                label_target=EmailLabel.UNPRODUCTIVE,
                template_text=(
                    "Agradecemos sua mensagem! É sempre um prazer "
                    "receber feedback positivo de nossos clientes."
                ),
                variables=[],
                tone="warm",
                language="pt"
            )
        ]
        
        # Adiciona templates padrão
        for template in default_templates:
            self._templates[str(template.template_id)] = template
    
    async def save(self, template: ResponseTemplate) -> ResponseTemplate:
        """Salva um template."""
        template_id_str = str(template.template_id)
        
        # Atualiza timestamp
        template.updated_at = datetime.utcnow()
        
        # Armazena no dicionário
        self._templates[template_id_str] = template
        
        return template
    
    async def get_by_id(self, template_id: str) -> Optional[ResponseTemplate]:
        """Busca template por ID."""
        return self._templates.get(template_id)
    
    async def get_by_label(self, label: EmailLabel) -> List[ResponseTemplate]:
        """Busca templates por label."""
        return [
            template for template in self._templates.values()
            if template.label_target == label and template.is_active
        ]
    
    async def get_active_templates(self) -> List[ResponseTemplate]:
        """Retorna todos os templates ativos."""
        return [
            template for template in self._templates.values()
            if template.is_active
        ]
    
    async def get_templates_by_language(self, language: str) -> List[ResponseTemplate]:
        """Busca templates por idioma."""
        return [
            template for template in self._templates.values()
            if template.language == language and template.is_active
        ]
    
    async def get_templates_by_tone(self, tone: str) -> List[ResponseTemplate]:
        """Busca templates por tom."""
        return [
            template for template in self._templates.values()
            if template.tone == tone and template.is_active
        ]
    
    async def delete(self, template_id: str) -> bool:
        """Remove um template."""
        if template_id in self._templates:
            del self._templates[template_id]
            return True
        return False
    
    async def deactivate(self, template_id: str) -> bool:
        """Desativa um template."""
        template = self._templates.get(template_id)
        if template:
            template.is_active = False
            template.updated_at = datetime.utcnow()
            return True
        return False
    
    async def activate(self, template_id: str) -> bool:
        """Ativa um template."""
        template = self._templates.get(template_id)
        if template:
            template.is_active = True
            template.updated_at = datetime.utcnow()
            return True
        return False
    
    async def get_template_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas dos templates."""
        total_templates = len(self._templates)
        active_templates = len([t for t in self._templates.values() if t.is_active])
        
        # Conta por label
        label_counts = defaultdict(int)
        for template in self._templates.values():
            label_counts[template.label_target.value] += 1
        
        # Conta por idioma
        language_counts = defaultdict(int)
        for template in self._templates.values():
            language_counts[template.language] += 1
        
        # Conta por tom
        tone_counts = defaultdict(int)
        for template in self._templates.values():
            tone_counts[template.tone] += 1
        
        return {
            "total_templates": total_templates,
            "active_templates": active_templates,
            "inactive_templates": total_templates - active_templates,
            "by_label": dict(label_counts),
            "by_language": dict(language_counts),
            "by_tone": dict(tone_counts),
            "repository_type": "in_memory"
        }
    
    async def clear(self) -> int:
        """Limpa todos os templates e retorna quantidade removida."""
        count = len(self._templates)
        self._templates.clear()
        self._initialize_default_templates()  # Restaura templates padrão
        return count

