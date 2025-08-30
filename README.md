# Email Classifier - Sistema de Classificação e Resposta Automática

Sistema inteligente para classificar emails em produtivos/improdutivos e sugerir respostas automáticas usando IA.

## 🏗️ Arquitetura

- **Backend**: Python FastAPI com DDD + Clean Architecture + Hexagonal
- **Frontend**: React + TypeScript com interface moderna
- **IA**: OpenAI/Hugging Face para classificação e geração de respostas
- **Deploy**: Docker + Render/Railway + Vercel

## 🚀 Quick Start

### Pré-requisitos
- Python 3.11+
- Node.js 18+
- Docker e Docker Compose

### Execução Local

```bash
# Clone e entre no projeto
git clone <repo>
cd autou

# Backend
cd app/backend
pip install -r requirements.txt
uvicorn src.main:app --reload

# Frontend (novo terminal)
cd app/frontend
npm install
npm run dev

# Ou use Docker
docker-compose up -d
```

### Variáveis de Ambiente

```bash
# Backend (.env)
OPENAI_API_KEY=sua_chave_aqui
HUGGINGFACE_TOKEN=seu_token_aqui
DATABASE_URL=sqlite:///./emails.db
CORS_ORIGINS=http://localhost:3000

# Frontend (.env)
VITE_API_URL=http://localhost:8000
```

## 📁 Estrutura do Projeto

```
/app
  /backend          # FastAPI + DDD + Clean Architecture
    /src
      /core         # Domain + Application
      /adapters     # HTTP + Gateways + Persistence
      /infra        # Config + Database
    /tests          # Unit + E2E
  /frontend         # React + TypeScript
    /src
      /components   # UI Components
      /api          # API Client
      /pages        # Routes
```

## 🔧 API Endpoints

- `POST /api/v1/process` - Processa email e retorna classificação + resposta
- `GET /api/v1/health` - Status da aplicação
- `GET /api/v1/labels` - Labels suportados

## 🧪 Testes

```bash
# Backend
cd app/backend
pytest

# Frontend
cd app/frontend
npm test
npm run test:coverage
npm run test:ui
```

## 🎨 Frontend

O frontend é uma aplicação React moderna com:

- **UI/UX**: Interface limpa e responsiva com Tailwind CSS
- **Componentes**: Upload de arquivos, classificação visual, respostas sugeridas
- **Validação**: Formulários com React Hook Form + Zod
- **Animações**: Framer Motion para transições suaves
- **Testes**: Vitest + Testing Library para testes unitários
- **Build**: Vite para desenvolvimento rápido

## 🐳 Docker

```bash
# Build e execução
docker-compose up -d

# Logs
docker-compose logs -f
```

## 📊 Exemplos de Uso

### Email Produtivo
```
Assunto: Problema com login
Conteúdo: Olá, não consigo fazer login no sistema. 
Erro: "Invalid credentials". Ticket #12345
```

**Classificação**: PRODUCTIVE (99%)
**Resposta Sugerida**: 
```
Assunto: Acompanhamento da nossa conversa sobre o projeto X
Corpo: Olá,
Foi um prazer conversar consigo na nossa reunião de hoje. Conforme discutimos, anexo este email com os detalhes da proposta que apresentámos. 
Acredito que a nossa solução pode ser muito benéfica para a sua empresa, que abordámos na nossa conversa. 
Tem interesse em discutir o próximo passo? Por favor, responda-me com a sua disponibilidade para uma breve chamada na próxima semana.

Atenciosamente,
```

### Email Improdutivo
```
Assunto: Obrigado pelo suporte
Conteúdo: Muito obrigado pela ajuda! 
Vocês são demais! 😊
```

**Classificação**: UNPRODUCTIVE (95%)
**Resposta Sugerida**: 
```
Ficamos felizes em ter ajudado! 
Se precisar de mais alguma coisa, estamos aqui! 😊
```

## 🔒 Segurança

- Validação de entrada
- Rate limiting
- Sanitização de dados
- Headers de segurança
- CORS configurável

## 📈 Observabilidade

- Logs estruturados (JSON)
- Métricas Prometheus
- Tracing de requests
- Monitoramento de performance

## 🚀 Deploy

### Backend (Render/Railway)
1. Conecte o repositório
2. Configure variáveis de ambiente
3. Deploy automático

### Frontend (Vercel/Netlify)
1. Importe o projeto
2. Configure build settings
3. Deploy automático

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit (`git commit -m 'Add nova feature'`)
4. Push (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📝 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.
