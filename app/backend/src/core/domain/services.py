"""
Serviços de domínio para regras de negócio de classificação de emails.
"""
from typing import List, Optional
import re
from dataclasses import dataclass

from .entities import EmailLabel, Classification, PreprocessedEmail


@dataclass
class ClassificationRule:
    """Regra de classificação baseada em keywords."""
    name: str
    label: EmailLabel
    keywords: List[str]
    weight: float
    is_regex: bool = False
    case_sensitive: bool = False


class EmailClassificationService:
    """
    Serviço de domínio para classificação de emails.
    
    Implementa regras de negócio para determinar se um email
    é produtivo ou improdutivo baseado em heurísticas.
    """
    
    def __init__(self):
        self._rules = self._initialize_rules()
    
    def _initialize_rules(self) -> List[ClassificationRule]:
        """Inicializa as regras de classificação padrão."""
        return [
            # Regras para emails PRODUTIVOS
            ClassificationRule(
                name="suporte_tecnico",
                label=EmailLabel.PRODUCTIVE,
                keywords=[
                    "problema", "erro", "bug", "não funciona", "falha",
                    "ticket", "suporte", "ajuda", "urgente", "crítico",
                    "login", "senha", "acesso", "sistema", "aplicação"
                ],
                weight=0.8
            ),
            ClassificationRule(
                name="duvida_especifica",
                label=EmailLabel.PRODUCTIVE,
                keywords=[
                    "como fazer", "onde encontrar", "quando", "quanto",
                    "dúvida", "pergunta", "informação", "detalhes",
                    "preço", "prazo", "status", "andamento"
                ],
                weight=0.7
            ),
            ClassificationRule(
                name="solicitacao_acao",
                label=EmailLabel.PRODUCTIVE,
                keywords=[
                    "solicito", "peço", "gostaria", "preciso", "quero",
                    "favor", "por favor", "urgente", "importante",
                    "ação", "resposta", "retorno", "contato"
                ],
                weight=0.6
            ),
            
            # Regras para emails IMPRODUTIVOS
            ClassificationRule(
                name="agradecimento_simples",
                label=EmailLabel.UNPRODUCTIVE,
                keywords=[
                    "obrigado", "obrigada", "valeu", "agradeço", "agradece",
                    "muito obrigado", "muito obrigada", "parabéns", "sucesso"
                ],
                weight=0.9
            ),
            ClassificationRule(
                name="cumprimento_social",
                label=EmailLabel.UNPRODUCTIVE,
                keywords=[
                    "bom dia", "boa tarde", "boa noite", "olá", "oi",
                    "tudo bem", "como vai", "feliz aniversário", "feliz natal"
                ],
                weight=0.8
            ),
            ClassificationRule(
                name="spam_marketing",
                label=EmailLabel.UNPRODUCTIVE,
                keywords=[
                    "promoção", "oferta", "desconto", "cupom", "venda",
                    "marketing", "newsletter", "inscreva-se", "clique aqui"
                ],
                weight=0.7
            )
        ]
    
    def classify_with_rules(self, preprocessed_email: PreprocessedEmail) -> Classification:
        """
        Classifica o email usando regras heurísticas.
        
        Args:
            preprocessed_email: Email pré-processado
            
        Returns:
            Classification com label e confidence
        """
        productive_score = 0.0
        unproductive_score = 0.0
        matched_rules = []
        
        text = preprocessed_email.clean_text.lower()
        
        for rule in self._rules:
            if self._rule_matches(text, rule):
                score = rule.weight
                
                if rule.label == EmailLabel.PRODUCTIVE:
                    productive_score += score
                else:
                    unproductive_score += score
                
                matched_rules.append(rule.name)
        
        # Normaliza scores para 0-1
        total_score = productive_score + unproductive_score
        if total_score == 0:
            # Fallback para classificação neutra
            return Classification(
                label=EmailLabel.UNPRODUCTIVE,
                confidence=0.5,
                reasoning="Sem regras aplicáveis - classificação padrão"
            )
        
        productive_confidence = productive_score / total_score
        unproductive_confidence = unproductive_score / total_score
        
        # Determina o label com maior confiança
        if productive_confidence > unproductive_confidence:
            label = EmailLabel.PRODUCTIVE
            confidence = productive_confidence
        else:
            label = EmailLabel.UNPRODUCTIVE
            confidence = unproductive_confidence
        
        reasoning = f"Regras aplicadas: {', '.join(matched_rules)}"
        
        return Classification(
            label=label,
            confidence=confidence,
            reasoning=reasoning,
            model_used="heuristic_rules"
        )
    
    def _rule_matches(self, text: str, rule: ClassificationRule) -> bool:
        """Verifica se uma regra se aplica ao texto."""
        if rule.is_regex:
            for pattern in rule.keywords:
                if re.search(pattern, text, re.IGNORECASE if not rule.case_sensitive else 0):
                    return True
        else:
            search_text = text if not rule.case_sensitive else text.lower()
            for keyword in rule.keywords:
                search_keyword = keyword if rule.case_sensitive else keyword.lower()
                if search_keyword in search_text:
                    return True
        
        return False
    
    def add_custom_rule(self, rule: ClassificationRule) -> None:
        """Adiciona uma regra customizada."""
        self._rules.append(rule)
    
    def get_rules_summary(self) -> dict:
        """Retorna um resumo das regras ativas."""
        return {
            "total_rules": len(self._rules),
            "productive_rules": len([r for r in self._rules if r.label == EmailLabel.PRODUCTIVE]),
            "unproductive_rules": len([r for r in self._rules if r.label == EmailLabel.UNPRODUCTIVE]),
            "rules": [
                {
                    "name": rule.name,
                    "label": rule.label.value,
                    "weight": rule.weight,
                    "keywords_count": len(rule.keywords)
                }
                for rule in self._rules
            ]
        }


class EmailPreprocessingService:
    """
    Serviço de domínio para pré-processamento de emails.
    
    Implementa regras de limpeza e normalização do texto.
    """
    
    def __init__(self):
        self._stop_words = self._load_stop_words()
        self._signature_patterns = self._load_signature_patterns()
    
    def _load_stop_words(self) -> set:
        """Carrega lista de stop words em português."""
        return {
            "a", "o", "e", "é", "de", "do", "da", "em", "um", "para", "é", "com",
            "não", "na", "mais", "as", "dos", "como", "mas", "foi", "ele", "das",
            "tem", "à", "seu", "sua", "ou", "ser", "quando", "muito", "há", "nos",
            "já", "está", "eu", "também", "só", "pelo", "pela", "até", "isso",
            "ela", "entre", "era", "depois", "sem", "mesmo", "aos", "ter", "seus",
            "suas", "minha", "têm", "naquela", "neles", "essas", "esses", "pelos",
            "elas", "estava", "fosse", "nela", "neles", "estas", "estes", "pelas",
            "este", "dele", "dela", "nós", "lhe", "deles", "delas", "mesma",
            "fosse", "meu", "minha", "teu", "tua", "teus", "tuas", "nosso",
            "nossa", "nossos", "nossas", "dela", "deles", "estas", "estes",
            "pelas", "este", "dele", "dela", "nós", "lhe", "deles", "delas"
        }
    
    def _load_signature_patterns(self) -> List[str]:
        """Carrega padrões comuns de assinatura de email."""
        return [
            r"--\s*$",  # -- no final
            r"^\s*--\s*$",  # -- isolado
            r"^\s*[A-Z][a-z]+\s+[A-Z][a-z]+\s*$",  # Nome Sobrenome
            r"^\s*[A-Z][a-z]+\s+[A-Z][a-z]+\s*<[^>]+>\s*$",  # Nome <email>
            r"^\s*Tel[:\s]*[\d\-\+\(\)\s]+\s*$",  # Telefone
            r"^\s*[A-Z][a-z]+[:\s]*[\d\-\+\(\)\s]+\s*$",  # Outros contatos
        ]
    
    def preprocess(self, raw_content: str, subject: Optional[str] = None) -> PreprocessedEmail:
        """
        Pré-processa o conteúdo do email.
        
        Args:
            raw_content: Conteúdo bruto do email
            subject: Assunto do email (opcional)
            
        Returns:
            PreprocessedEmail com texto limpo e tokens
        """
        # Combina assunto e conteúdo
        full_text = ""
        if subject:
            full_text += f"{subject}\n\n"
        full_text += raw_content
        
        # Remove assinaturas
        clean_text = self._remove_signatures(full_text)
        
        # Normaliza espaços e quebras de linha
        clean_text = self._normalize_whitespace(clean_text)
        
        # Remove caracteres especiais desnecessários
        clean_text = self._remove_special_chars(clean_text)
        
        # Tokeniza o texto
        tokens = self._tokenize(clean_text)
        
        # Remove stop words
        filtered_tokens = [token for token in tokens if token.lower() not in self._stop_words]
        
        # Detecta idioma (simplificado - assume português por padrão)
        language = self._detect_language(clean_text)
        
        # Conta palavras
        word_count = len(filtered_tokens)
        
        return PreprocessedEmail(
            clean_text=clean_text,
            tokens=filtered_tokens,
            language=language,
            word_count=word_count,
            has_attachments=False  # Será definido pelo parser
        )
    
    def _remove_signatures(self, text: str) -> str:
        """Remove assinaturas de email."""
        lines = text.split('\n')
        clean_lines = []
        
        for line in lines:
            is_signature = False
            for pattern in self._signature_patterns:
                if re.match(pattern, line):
                    is_signature = True
                    break
            
            if not is_signature:
                clean_lines.append(line)
            else:
                break  # Para no primeiro padrão de assinatura
        
        return '\n'.join(clean_lines)
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normaliza espaços em branco."""
        # Remove múltiplos espaços
        text = re.sub(r'\s+', ' ', text)
        # Remove espaços no início e fim
        text = text.strip()
        # Normaliza quebras de linha
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text
    
    def _remove_special_chars(self, text: str) -> str:
        """Remove caracteres especiais desnecessários."""
        # Remove caracteres de controle
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        # Remove caracteres especiais excessivos
        text = re.sub(r'[^\w\s\.,!?;:()\[\]{}"\'-]', '', text)
        return text
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokeniza o texto em palavras."""
        # Remove pontuação e quebra em palavras
        words = re.findall(r'\b\w+\b', text.lower())
        # Filtra palavras muito curtas
        return [word for word in words if len(word) > 2]
    
    def _detect_language(self, text: str) -> str:
        """
        Detecta o idioma do texto (simplificado).
        
        Por simplicidade, assume português por padrão.
        Em produção, usar biblioteca como langdetect.
        """
        # Heurística simples baseada em palavras comuns
        portuguese_words = {"de", "a", "o", "e", "é", "para", "com", "não", "que", "um"}
        english_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to"}
        
        text_lower = text.lower()
        pt_count = sum(1 for word in portuguese_words if word in text_lower)
        en_count = sum(1 for word in english_words if word in text_lower)
        
        if pt_count > en_count:
            return "pt"
        elif en_count > pt_count:
            return "en"
        else:
            return "pt"  # Default

