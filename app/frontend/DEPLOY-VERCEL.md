# Deploy na Vercel - Frontend Email Classifier

## ✅ Build Testado e Funcionando

O projeto foi testado e está funcionando corretamente. O build foi executado com sucesso:
- ✅ TypeScript compilado sem erros
- ✅ Vite build concluído
- ✅ Arquivos de produção gerados em `dist/`

## 🚀 Como Fazer Deploy na Vercel

### 1. **Preparar o Repositório**
- Certifique-se de que o código está no GitHub
- O repositório deve ser público ou a Vercel deve ter acesso

### 2. **Conectar na Vercel**
- Acesse [vercel.com](https://vercel.com)
- Faça login com sua conta GitHub
- Clique em "New Project"

### 3. **Importar o Projeto**
- Selecione o repositório `autou-email-classifier`
- Configure as seguintes opções:

**Configurações Básicas:**
- **Framework Preset**: `Vite` (detectado automaticamente)
- **Root Directory**: `app/frontend`
- **Build Command**: `npm run build` (padrão)
- **Output Directory**: `dist` (padrão)
- **Install Command**: `npm install` (padrão)

### 4. **Variáveis de Ambiente**
Adicione estas variáveis na Vercel:

```bash
VITE_API_URL=https://seu-backend.onrender.com
NODE_ENV=production
```

**⚠️ IMPORTANTE**: Substitua `https://seu-backend.onrender.com` pela URL real do seu backend no Render.

### 5. **Deploy**
- Clique em "Deploy"
- Aguarde a conclusão do processo
- A Vercel fornecerá uma URL (ex: `https://seu-app.vercel.app`)

## 🔧 Configurações Técnicas

### Arquivos de Configuração
- `vercel.json` - Configuração específica da Vercel
- `vite.config.ts` - Configuração do Vite
- `tsconfig.json` - Configuração do TypeScript
- `src/vite-env.d.ts` - Tipos para variáveis de ambiente

### Estrutura de Build
```
dist/
├── index.html
├── assets/
│   ├── index-*.css
│   ├── index-*.js
│   ├── vendor-*.js
│   └── ui-*.js
```

## 🌐 URLs Finais

Após o deploy:
- **Frontend**: `https://seu-app.vercel.app`
- **Backend**: `https://seu-backend.onrender.com`

## 🔍 Verificação Pós-Deploy

1. **Teste a aplicação**: Acesse a URL fornecida pela Vercel
2. **Verifique a comunicação**: Teste se o frontend está se comunicando com o backend
3. **Logs**: Verifique os logs na Vercel se houver problemas
4. **CORS**: Certifique-se de que o backend aceita requisições da Vercel

## 🚨 Solução de Problemas

### Erro de CORS
Se houver erro de CORS, verifique se o backend tem as origens corretas:
```python
cors_origins: List[str] = Field(
    [
        "http://localhost:3000", 
        "http://localhost:8080",
        "https://*.vercel.app",
        "https://*.onrender.com"
    ]
)
```

### Erro de Build
Se houver erro de build:
1. Execute `npm run build` localmente
2. Verifique se todas as dependências estão instaladas
3. Verifique se não há erros de TypeScript

## 📝 Notas Importantes

- **Deploy Automático**: A Vercel fará rebuild automático sempre que você fizer push para a branch principal
- **Preview Deployments**: Configure preview deployments para outras branches
- **Domínio Customizado**: Você pode configurar um domínio personalizado nas configurações da Vercel
- **Analytics**: A Vercel oferece analytics gratuitos para monitorar performance

## 🎉 Sucesso!

Após seguir estes passos, seu frontend estará rodando na Vercel e se comunicando com o backend no Render!
