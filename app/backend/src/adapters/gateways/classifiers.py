"""
Implementações dos classificadores de email.

Suporta diferentes abordagens:
- Regras heurísticas (local, rápido)
- OpenAI GPT (IA avançada, pago)
- Hugging Face (modelos open source)
"""
import time
from typing import Optional, Dict, Any, List
import httpx
import openai
from transformers import pipeline

from ...core.ports import ClassifierPort
from ...core.domain.entities import EmailLabel, Classification, PreprocessedEmail
from ...core.domain.services import EmailClassificationService


class HeuristicClassifier(ClassifierPort):
    """
    Classificador baseado em regras heurísticas.
    
    Implementa as regras de domínio definidas no serviço
    de classificação, sendo rápido e não dependente de
    serviços externos.
    """
    
    def __init__(self):
        self.classification_service = EmailClassificationService()
    
    async def classify(
        self, 
        preprocessed_email: PreprocessedEmail,
        context: Optional[Dict[str, Any]] = None
    ) -> Classification:
        """
        Classifica email usando regras heurísticas.
        
        Args:
            preprocessed_email: Email pré-processado
            context: Contexto adicional (ignorado para heurístico)
            
        Returns:
            Classification com label e confidence
        """
        start_time = time.time()
        
        # Usa o serviço de domínio para classificação
        classification = self.classification_service.classify_with_rules(preprocessed_email)
        
        # Adiciona tempo de processamento
        processing_time = (time.time() - start_time) * 1000
        classification.processing_time_ms = processing_time
        
        return classification
    
    async def get_supported_labels(self) -> List[str]:
        """Retorna labels suportados."""
        return [label.value for label in EmailLabel]
    
    async def get_classification_metadata(self) -> Dict[str, Any]:
        """Retorna metadados sobre o classificador."""
        rules_summary = self.classification_service.get_rules_summary()
        
        return {
            "classifier_type": "heuristic_rules",
            "description": "Classificador baseado em regras heurísticas",
            "rules_count": rules_summary["total_rules"],
            "productive_rules": rules_summary["productive_rules"],
            "unproductive_rules": rules_summary["unproductive_rules"],
            "performance": "fast",
            "cost": "free",
            "accuracy": "medium"
        }


class OpenAIClassifier(ClassifierPort):
    """
    Classificador usando OpenAI GPT.
    
    Oferece alta precisão mas depende de API externa
    e tem custo associado.
    """
    
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo"
    
    async def classify(
        self, 
        preprocessed_email: PreprocessedEmail,
        context: Optional[Dict[str, Any]] = None
    ) -> Classification:
        """
        Classifica email usando OpenAI GPT.
        
        Args:
            preprocessed_email: Email pré-processado
            context: Contexto adicional
            
        Returns:
            Classification com label e confidence
        """
        start_time = time.time()
        
        try:
            # Prepara prompt para classificação
            prompt = self._create_classification_prompt(preprocessed_email, context)
            
            # Chama OpenAI API
            response = await self._call_openai_api(prompt)
            
            # Parse da resposta
            classification = self._parse_openai_response(response, preprocessed_email)
            
            # Adiciona tempo de processamento
            processing_time = (time.time() - start_time) * 1000
            classification.processing_time_ms = processing_time
            
            return classification
            
        except Exception as e:
            # Fallback para classificador heurístico em caso de erro
            fallback_classifier = HeuristicClassifier()
            return await fallback_classifier.classify(preprocessed_email, context)
    
    async def get_supported_labels(self) -> List[str]:
        """Retorna labels suportados."""
        return [label.value for label in EmailLabel]
    
    async def get_classification_metadata(self) -> Dict[str, Any]:
        """Retorna metadados sobre o classificador."""
        return {
            "classifier_type": "openai_gpt",
            "model": self.model,
            "description": "Classificador usando OpenAI GPT",
            "performance": "high",
            "cost": "paid",
            "accuracy": "high",
            "fallback": "heuristic_rules"
        }
    
    def _create_classification_prompt(
        self, 
        preprocessed_email: PreprocessedEmail,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Cria prompt para classificação."""
        prompt = f"""
        Você é um assistente especializado em classificar emails como produtivos ou improdutivos.
        
        Classifique o seguinte email:
        
        Texto: {preprocessed_email.clean_text}
        Idioma: {preprocessed_email.language}
        Número de palavras: {preprocessed_email.word_count}
        
        Regras de classificação:
        - PRODUTIVE: Emails que requerem ação/resposta específica (suporte, dúvidas, solicitações)
        - UNPRODUCTIVE: Emails que não requerem ação imediata (agradecimentos, cumprimentos, spam)
        
        Responda apenas com:
        LABEL: [PRODUCTIVE ou UNPRODUCTIVE]
        CONFIDENCE: [0.0 a 1.0]
        REASONING: [explicação breve da classificação]
        """
        
        if context:
            prompt += f"\nContexto adicional: {context}"
        
        return prompt
    
    async def _call_openai_api(self, prompt: str) -> str:
        """Chama API da OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um classificador de emails especializado."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Erro na API OpenAI: {str(e)}")
    
    def _parse_openai_response(
        self, 
        response: str, 
        preprocessed_email: PreprocessedEmail
    ) -> Classification:
        """Parse da resposta da OpenAI."""
        try:
            lines = response.strip().split('\n')
            label = None
            confidence = 0.5
            reasoning = "Classificação via OpenAI GPT"
            
            for line in lines:
                line = line.strip()
                if line.startswith('LABEL:'):
                    label_str = line.split(':', 1)[1].strip()
                    if label_str.upper() == 'PRODUCTIVE':
                        label = EmailLabel.PRODUCTIVE
                    elif label_str.upper() == 'UNPRODUCTIVE':
                        label = EmailLabel.UNPRODUCTIVE
                
                elif line.startswith('CONFIDENCE:'):
                    try:
                        conf_str = line.split(':', 1)[1].strip()
                        confidence = float(conf_str)
                        confidence = max(0.0, min(1.0, confidence))  # Clampa entre 0-1
                    except ValueError:
                        pass
                
                elif line.startswith('REASONING:'):
                    reasoning = line.split(':', 1)[1].strip()
            
            # Fallback se não conseguir parsear
            if label is None:
                label = EmailLabel.UNPRODUCTIVE
                reasoning = "Falha no parse da resposta OpenAI - usando fallback"
            
            return Classification(
                label=label,
                confidence=confidence,
                reasoning=reasoning,
                model_used="openai_gpt"
            )
            
        except Exception as e:
            # Fallback em caso de erro no parse
            return Classification(
                label=EmailLabel.UNPRODUCTIVE,
                confidence=0.5,
                reasoning=f"Erro no parse da resposta: {str(e)}",
                model_used="openai_gpt"
            )


class HuggingFaceClassifier(ClassifierPort):
    """
    Classificador usando modelos Hugging Face.
    
    Oferece boa precisão com modelos open source,
    mas pode ser mais lento que OpenAI.
    """
    
    def __init__(self, token: str):
        self.token = token
        self.model_name = "facebook/bart-large-mnli"  # Zero-shot classification
        self.classifier = None
        self._initialize_classifier()
    
    def _initialize_classifier(self):
        """Inicializa o classificador Hugging Face."""
        try:
            self.classifier = pipeline(
                "zero-shot-classification",
                model=self.model_name,
                token=self.token
            )
        except Exception as e:
            # Fallback para classificador heurístico se não conseguir inicializar
            print(f"Erro ao inicializar Hugging Face: {e}")
            self.classifier = None
    
    async def classify(
        self, 
        preprocessed_email: PreprocessedEmail,
        context: Optional[Dict[str, Any]] = None
    ) -> Classification:
        """
        Classifica email usando Hugging Face.
        
        Args:
            preprocessed_email: Email pré-processado
            context: Contexto adicional
            
        Returns:
            Classification com label e confidence
        """
        start_time = time.time()
        
        if not self.classifier:
            # Fallback para classificador heurístico
            fallback_classifier = HeuristicClassifier()
            return await fallback_classifier.classify(preprocessed_email, context)
        
        try:
            # Define as classes para classificação zero-shot
            candidate_labels = ["productive", "unproductive"]
            
            # Classifica o texto
            result = self.classifier(
                preprocessed_email.clean_text,
                candidate_labels,
                hypothesis_template="Este email é sobre {}."
            )
            
            # Parse do resultado
            label_str = result['labels'][0]
            confidence = result['scores'][0]
            
            # Mapeia para EmailLabel
            if label_str == "productive":
                label = EmailLabel.PRODUCTIVE
            else:
                label = EmailLabel.UNPRODUCTIVE
            
            # Adiciona tempo de processamento
            processing_time = (time.time() - start_time) * 1000
            
            return Classification(
                label=label,
                confidence=confidence,
                reasoning=f"Classificação via Hugging Face ({self.model_name})",
                model_used="huggingface_zero_shot",
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            # Fallback para classificador heurístico em caso de erro
            fallback_classifier = HeuristicClassifier()
            return await fallback_classifier.classify(preprocessed_email, context)
    
    async def get_supported_labels(self) -> List[str]:
        """Retorna labels suportados."""
        return [label.value for label in EmailLabel]
    
    async def get_classification_metadata(self) -> Dict[str, Any]:
        """Retorna metadados sobre o classificador."""
        return {
            "classifier_type": "huggingface_zero_shot",
            "model": self.model_name,
            "description": "Classificador usando Hugging Face Zero-Shot",
            "performance": "medium",
            "cost": "free",
            "accuracy": "good",
            "fallback": "heuristic_rules",
            "initialized": self.classifier is not None
        }


class HybridClassifier(ClassifierPort):
    """
    Classificador híbrido que combina múltiplas abordagens.
    
    Usa heurísticas primeiro (rápido), depois IA se necessário,
    oferecendo melhor performance e precisão.
    """
    
    def __init__(self, heuristic_classifier: HeuristicClassifier, ai_classifier: ClassifierPort):
        self.heuristic_classifier = heuristic_classifier
        self.ai_classifier = ai_classifier
        self.confidence_threshold = 0.8
    
    async def classify(
        self, 
        preprocessed_email: PreprocessedEmail,
        context: Optional[Dict[str, Any]] = None
    ) -> Classification:
        """
        Classifica usando abordagem híbrida.
        
        Args:
            preprocessed_email: Email pré-processado
            context: Contexto adicional
            
        Returns:
            Classification com label e confidence
        """
        # Primeiro tenta heurísticas (rápido)
        heuristic_result = await self.heuristic_classifier.classify(preprocessed_email, context)
        
        # Se a confiança for alta, usa o resultado heurístico
        if heuristic_result.confidence >= self.confidence_threshold:
            heuristic_result.reasoning += " (heurístico - alta confiança)"
            return heuristic_result
        
        # Caso contrário, usa IA para melhor precisão
        try:
            ai_result = await self.ai_classifier.classify(preprocessed_email, context)
            ai_result.reasoning += " (IA - baixa confiança heurística)"
            return ai_result
        except Exception as e:
            # Se IA falhar, usa heurístico
            heuristic_result.reasoning += " (heurístico - falha na IA)"
            return heuristic_result
    
    async def get_supported_labels(self) -> List[str]:
        """Retorna labels suportados."""
        return [label.value for label in EmailLabel]
    
    async def get_classification_metadata(self) -> Dict[str, Any]:
        """Retorna metadados sobre o classificador."""
        return {
            "classifier_type": "hybrid",
            "description": "Classificador híbrido (heurístico + IA)",
            "performance": "high",
            "cost": "variable",
            "accuracy": "high",
            "confidence_threshold": self.confidence_threshold,
            "components": [
                "heuristic_rules",
                type(self.ai_classifier).__name__.lower()
            ]
        }

