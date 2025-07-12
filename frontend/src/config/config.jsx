// Configurações da aplicação
export const config = {
  // Configurações da API (quando implementar backend real)
  api: {
    baseUrl: process.env.REACT_APP_API_URL || 'http://localhost:3001',
    timeout: 10000,
  },
  
  // Configurações do WhatsApp Business API (para futuro)
  whatsapp: {
    businessAccountId: process.env.REACT_APP_WA_BUSINESS_ID,
    accessToken: process.env.REACT_APP_WA_ACCESS_TOKEN,
    webhookVerifyToken: process.env.REACT_APP_WA_WEBHOOK_TOKEN,
  },
  
  // Configurações da IA
  ai: {
    provider: 'openai', // ou 'anthropic', 'google', etc.
    model: 'gpt-3.5-turbo',
    temperature: 0.7,
    maxTokens: 1000,
  },
  
  // Configurações gerais
  app: {
    name: 'WhatsApp AI Agent',
    version: '1.0.0',
    environment: process.env.NODE_ENV || 'development',
  },
  
  // Configurações de storage
  storage: {
    prefix: 'whatsapp_ai_',
    keys: {
      user: 'user',
      token: 'token',
      contacts: 'contacts',
      conversations: 'conversations',
    },
  },
}

export default config