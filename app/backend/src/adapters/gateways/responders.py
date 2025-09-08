"""
Implementações dos geradores de resposta.

Suporta diferentes abordagens:
- Templates estáticos (rápido, previsível)
- OpenAI GPT (IA avançada, personalizado)
- Hugging Face (modelos open source)
"""

import time
from typing import Optional, Dict, Any, List
import openai
from transformers import pipeline

from ...core.ports import ResponderPort
from ...core.domain.entities import (
    Email,
    EmailLabel,
    Classification,
    SuggestedResponse,
    ResponseTemplate,
)


class TemplateResponder(ResponderPort):
    """
    Gerador de respostas baseado em templates.

    Usa templates pré-definidos para gerar respostas
    rápidas e consistentes, sem dependência externa.
    """

    def __init__(self) -> None:
        self.templates = self._initialize_templates()

    def _initialize_templates(self) -> List[ResponseTemplate]:
        """Inicializa templates padrão."""
        from uuid import uuid4

        return [
            # Templates para emails PRODUTIVOS
            ResponseTemplate(
                template_id=uuid4(),
                label_target=EmailLabel.PRODUCTIVE,
                template_text=(
                    "Olá! Entendo sua solicitação sobre {topic}. "
                    "Vou analisar e retornar em breve com uma solução. "
                    "Se precisar de mais informações, estarei aqui para ajudar."
                ),
                variables=["topic"],
                tone="professional",
                language="pt",
            ),
            ResponseTemplate(
                template_id=uuid4(),
                label_target=EmailLabel.PRODUCTIVE,
                template_text=(
                    "Obrigado pelo contato! Sua dúvida sobre {topic} "
                    "foi registrada e está sendo analisada pela nossa equipe. "
                    "Retornaremos em até 24 horas."
                ),
                variables=["topic"],
                tone="friendly",
                language="pt",
            ),
            ResponseTemplate(
                template_id=uuid4(),
                label_target=EmailLabel.PRODUCTIVE,
                template_text=(
                    "Recebemos sua solicitação. Para agilizar o atendimento, "
                    "preciso de algumas informações adicionais: {missing_info}. "
                    "Assim que receber, poderei ajudá-lo imediatamente."
                ),
                variables=["missing_info"],
                tone="professional",
                language="pt",
            ),
            # Templates para emails IMPRODUTIVOS
            ResponseTemplate(
                template_id=uuid4(),
                label_target=EmailLabel.UNPRODUCTIVE,
                template_text=(
                    "Obrigado pelo contato! Ficamos felizes em saber que "
                    "está satisfeito com nossos serviços. "
                    "Se precisar de algo mais, estamos aqui!"
                ),
                variables=[],
                tone="friendly",
                language="pt",
            ),
            ResponseTemplate(
                template_id=uuid4(),
                label_target=EmailLabel.UNPRODUCTIVE,
                template_text=(
                    "Agradecemos sua mensagem! É sempre um prazer "
                    "receber feedback positivo de nossos clientes. "
                    "Continue nos acompanhando!"
                ),
                variables=[],
                tone="warm",
                language="pt",
            ),
            ResponseTemplate(
                template_id=uuid4(),
                label_target=EmailLabel.UNPRODUCTIVE,
                template_text=(
                    "Obrigado pelo contato! Sua mensagem foi recebida. "
                    "Se precisar de suporte técnico ou tiver dúvidas, "
                    "nossa equipe está disponível para ajudá-lo."
                ),
                variables=[],
                tone="professional",
                language="pt",
            ),
        ]

    async def suggest_reply(
        self,
        email: Email,
        classification: Classification,
        context: Optional[Dict[str, Any]] = None,
    ) -> SuggestedResponse:
        """
        Gera resposta sugerida usando templates.

        Args:
            email: Email original
            classification: Classificação do email
            context: Contexto adicional

        Returns:
            SuggestedResponse com corpo e tom
        """
        start_time = time.time()

        # Seleciona template apropriado
        template = self._select_template(email, classification)

        # Prepara variáveis para o template
        variables = self._prepare_template_variables(email, classification, context)

        # Renderiza o template
        body = template.render(**variables)

        # Gera assunto se necessário
        subject = self._generate_subject(email, classification, template)

        # Adiciona tempo estimado de resposta
        estimated_time = self._estimate_response_time(classification)

        (time.time() - start_time) * 1000

        return SuggestedResponse(
            subject=subject,
            body=body,
            tone=template.tone,
            language=template.language,
            estimated_response_time=estimated_time,
        )

    async def get_response_templates(self, label: EmailLabel) -> List[ResponseTemplate]:
        """Retorna templates disponíveis para um label."""
        return [t for t in self.templates if t.label_target == label]

    async def customize_response(
        self, base_response: SuggestedResponse, customizations: Dict[str, Any]
    ) -> SuggestedResponse:
        """Customiza uma resposta base com ajustes específicos."""
        # Aplica customizações
        if "tone" in customizations:
            base_response.tone = customizations["tone"]

        if "language" in customizations:
            base_response.language = customizations["language"]

        if "urgency" in customizations:
            # Adiciona indicador de urgência
            if customizations["urgency"] == "high":
                base_response.body = f"URGENTE: {base_response.body}"

        return base_response

    def _select_template(
        self, email: Email, classification: Classification
    ) -> ResponseTemplate:
        """Seleciona o template mais apropriado."""
        # Filtra templates compatíveis
        compatible_templates = [
            t for t in self.templates if t.is_compatible_with(email)
        ]

        if not compatible_templates:
            # Fallback para template genérico
            return self.templates[0]  # type: ignore[return-value]

        # Para produtivos, evita templates com variáveis obrigatórias complexas
        if classification.label == EmailLabel.PRODUCTIVE:
            # Prioriza templates simples sem variáveis obrigatórias
            simple_templates = [t for t in compatible_templates if not t.variables]
            if simple_templates:
                return simple_templates[0]  # type: ignore[return-value]

            # Se não houver templates simples, usa o primeiro compatível
            return compatible_templates[0]  # type: ignore[return-value]

        # Retorna o primeiro compatível
        return compatible_templates[0]  # type: ignore[return-value]

    def _prepare_template_variables(
        self,
        email: Email,
        classification: Classification,
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Prepara variáveis para renderização do template."""
        variables = {}

        # Extrai tópico do email
        if email.subject:
            variables["topic"] = email.subject
        else:
            # Tenta extrair tópico do conteúdo
            content_words = email.raw_content.split()[:5]
            variables["topic"] = " ".join(content_words)

        # Adiciona informações de contexto
        if context:
            if "missing_info" in context:
                variables["missing_info"] = context["missing_info"]
            if "priority" in context:
                variables["priority"] = context["priority"]

        # Fallback para variáveis obrigatórias
        if "topic" not in variables:
            variables["topic"] = "sua solicitação"

        # Fallback para missing_info se necessário
        if "missing_info" not in variables:
            variables["missing_info"] = "detalhes específicos da solicitação"

        return variables

    def _generate_subject(
        self, email: Email, classification: Classification, template: ResponseTemplate
    ) -> Optional[str]:
        """Gera assunto para a resposta."""
        if classification.label == EmailLabel.PRODUCTIVE:
            if email.subject:
                return f"Re: {email.subject}"
            else:
                return "Resposta à sua solicitação"
        else:
            # Para improdutivos, geralmente não precisa de assunto
            return None

    def _estimate_response_time(self, classification: Classification) -> str:
        """Estima tempo de resposta baseado na classificação."""
        if classification.label == EmailLabel.PRODUCTIVE:
            if classification.confidence > 0.8:
                return "2-4 horas"
            else:
                return "4-8 horas"
        else:
            return "24 horas"


class OpenAIResponder(ResponderPort):
    """
    Gerador de respostas usando OpenAI GPT.

    Oferece respostas personalizadas e contextuais,
    mas depende de API externa e tem custo.
    """

    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo"

    async def suggest_reply(
        self,
        email: Email,
        classification: Classification,
        context: Optional[Dict[str, Any]] = None,
    ) -> SuggestedResponse:
        """
        Gera resposta sugerida usando OpenAI GPT.

        Args:
            email: Email original
            classification: Classificação do email
            context: Contexto adicional

        Returns:
            SuggestedResponse com corpo e tom
        """
        start_time = time.time()

        try:
            # Prepara prompt para geração de resposta
            prompt = self._create_response_prompt(email, classification, context)

            # Chama OpenAI API
            response = await self._call_openai_api(prompt)

            # Parse da resposta
            suggested_response = self._parse_openai_response(
                response, email, classification
            )

            # Adiciona tempo de processamento
            (time.time() - start_time) * 1000

            return suggested_response

        except Exception:
            # Fallback para template em caso de erro
            template_responder = TemplateResponder()
            return await template_responder.suggest_reply(
                email, classification, context
            )

    async def get_response_templates(self, label: EmailLabel) -> List[ResponseTemplate]:
        """Retorna templates disponíveis (delega para TemplateResponder)."""
        template_responder = TemplateResponder()
        return await template_responder.get_response_templates(label)

    async def customize_response(
        self, base_response: SuggestedResponse, customizations: Dict[str, Any]
    ) -> SuggestedResponse:
        """Customiza resposta usando OpenAI."""
        try:
            prompt = f"""
            Personalize a seguinte resposta de email com as seguintes customizações:
            
            Resposta original:
            {base_response.body}
            
            Customizações:
            {customizations}
            
            Retorne apenas a resposta personalizada.
            """

            response = await self._call_openai_api(prompt)

            return SuggestedResponse(
                subject=base_response.subject,
                body=response.strip(),
                tone=base_response.tone,
                language=base_response.language,
                estimated_response_time=base_response.estimated_response_time,
            )

        except Exception:
            # Fallback para customização simples
            template_responder = TemplateResponder()
            return await template_responder.customize_response(
                base_response, customizations
            )

    def _create_response_prompt(
        self,
        email: Email,
        classification: Classification,
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Cria prompt para geração de resposta."""
        prompt = f"""
        Você é um assistente especializado em gerar respostas profissionais para emails.
        
        Email original:
        Assunto: {email.subject or 'Sem assunto'}
        Conteúdo: {email.raw_content}
        
        Classificação: {classification.label.value}
        Confiança: {classification.confidence}
        Explicação: {classification.reasoning}
        
        Gere uma resposta apropriada seguindo estas diretrizes:
        - Para emails PRODUTIVOS: Ofereça ajuda, peça informações faltantes se necessário
        - Para emails IMPRODUTIVOS: Agradeça e mantenha tom cordial
        - Use o mesmo idioma do email original
        - Seja profissional mas amigável
        - Mantenha a resposta concisa (2-3 frases)
        - Inclua um assunto apropriado se necessário
        
        Responda apenas com:
        ASSUNTO: [assunto da resposta ou "Sem assunto"]
        CORPO: [corpo da resposta]
        TOM: [professional, friendly, warm]
        IDIOMA: [pt, en]
        TEMPO_ESTIMADO: [tempo estimado de resposta]
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
                    {
                        "role": "system",
                        "content": "Você é um assistente especializado em respostas de email.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=300,
                temperature=0.7,
            )

            content = response.choices[0].message.content
            return content or "Resposta não disponível"

        except Exception as e:
            raise Exception(f"Erro na API OpenAI: {str(e)}")

    def _parse_openai_response(
        self, response: str, email: Email, classification: Classification
    ) -> SuggestedResponse:
        """Parse da resposta da OpenAI."""
        try:
            lines = response.strip().split("\n")
            subject = None
            body = ""
            tone = "professional"
            language = "pt"
            estimated_time = "24 horas"

            for line in lines:
                line = line.strip()
                if line.startswith("ASSUNTO:"):
                    subject_str = line.split(":", 1)[1].strip()
                    if subject_str.lower() != "sem assunto":
                        subject = subject_str

                elif line.startswith("CORPO:"):
                    body = line.split(":", 1)[1].strip()

                elif line.startswith("TOM:"):
                    tone_str = line.split(":", 1)[1].strip()
                    if tone_str in ["professional", "friendly", "warm"]:
                        tone = tone_str

                elif line.startswith("IDIOMA:"):
                    lang_str = line.split(":", 1)[1].strip()
                    if lang_str in ["pt", "en"]:
                        language = lang_str

                elif line.startswith("TEMPO_ESTIMADO:"):
                    time_str = line.split(":", 1)[1].strip()
                    if time_str:
                        estimated_time = time_str

            # Fallbacks se não conseguir parsear
            if not body:
                body = "Obrigado pelo contato. Retornaremos em breve."

            # Detecta idioma do email original se não especificado
            if language == "pt" and email._preprocessed:
                language = email._preprocessed.language

            return SuggestedResponse(
                subject=subject,
                body=body,
                tone=tone,
                language=language,
                estimated_response_time=estimated_time,
            )

        except Exception:
            # Fallback em caso de erro no parse
            return SuggestedResponse(
                subject=f"Re: {email.subject}" if email.subject else None,
                body="Obrigado pelo contato. Retornaremos em breve.",
                tone="professional",
                language="pt",
                estimated_response_time="24 horas",
            )


class HuggingFaceResponder(ResponderPort):
    """
    Gerador de respostas usando modelos Hugging Face.

    Oferece respostas baseadas em modelos open source,
    mas pode ser mais limitado que OpenAI.
    """

    def __init__(self, token: str):
        self.token = token
        self.model_name = "microsoft/DialoGPT-medium"  # Exemplo
        self.generator = None
        self._initialize_generator()

    def _initialize_generator(self) -> None:
        """Inicializa o gerador Hugging Face."""
        try:
            self.generator = pipeline(
                "text-generation", model=self.model_name, token=self.token
            )
        except Exception as e:
            print(f"Erro ao inicializar Hugging Face: {e}")
            self.generator = None

    async def suggest_reply(
        self,
        email: Email,
        classification: Classification,
        context: Optional[Dict[str, Any]] = None,
    ) -> SuggestedResponse:
        """
        Gera resposta sugerida usando Hugging Face.

        Args:
            email: Email original
            classification: Classificação do email
            context: Contexto adicional

        Returns:
            SuggestedResponse com corpo e tom
        """
        if not self.generator:
            # Fallback para template se não conseguir inicializar
            template_responder = TemplateResponder()
            return await template_responder.suggest_reply(
                email, classification, context
            )

        try:
            # Prepara prompt para o modelo
            prompt = self._create_generation_prompt(email, classification)

            # Gera resposta
            response = self.generator(prompt, max_length=100, num_return_sequences=1)

            # Parse da resposta
            suggested_response = self._parse_hf_response(
                response, email, classification
            )

            return suggested_response

        except Exception:
            # Fallback para template em caso de erro
            template_responder = TemplateResponder()
            return await template_responder.suggest_reply(
                email, classification, context
            )

    async def get_response_templates(self, label: EmailLabel) -> List[ResponseTemplate]:
        """Retorna templates disponíveis (delega para TemplateResponder)."""
        template_responder = TemplateResponder()
        return await template_responder.get_response_templates(label)

    async def customize_response(
        self, base_response: SuggestedResponse, customizations: Dict[str, Any]
    ) -> SuggestedResponse:
        """Customiza resposta (delega para TemplateResponder)."""
        template_responder = TemplateResponder()
        return await template_responder.customize_response(
            base_response, customizations
        )

    def _create_generation_prompt(
        self, email: Email, classification: Classification
    ) -> str:
        """Cria prompt para geração de resposta."""
        if classification.label == EmailLabel.PRODUCTIVE:
            prompt = (
                f"Email sobre: {email.subject or 'solicitação'}. Resposta profissional:"
            )
        else:
            prompt = "Email de agradecimento. Resposta cordial:"

        return prompt

    def _parse_hf_response(
        self, response: List[Dict], email: Email, classification: Classification
    ) -> SuggestedResponse:
        """Parse da resposta do Hugging Face."""
        try:
            # Extrai texto gerado
            generated_text = response[0]["generated_text"]

            # Remove o prompt original
            prompt = self._create_generation_prompt(email, classification)
            body = generated_text.replace(prompt, "").strip()

            # Limita o tamanho da resposta
            if len(body) > 200:
                body = body[:200] + "..."

            # Fallback se resposta estiver vazia
            if not body:
                body = "Obrigado pelo contato. Retornaremos em breve."

            return SuggestedResponse(
                subject=f"Re: {email.subject}" if email.subject else None,
                body=body,
                tone="professional",
                language="pt",
                estimated_response_time="24 horas",
            )

        except Exception:
            # Fallback em caso de erro
            return SuggestedResponse(
                subject=f"Re: {email.subject}" if email.subject else None,
                body="Obrigado pelo contato. Retornaremos em breve.",
                tone="professional",
                language="pt",
                estimated_response_time="24 horas",
            )
