// frontend/src/services/api/authService.jsx
import apiClient from './apiClient';

const authService = {
  login: async (email, password) => {
    try {
      const response = await apiClient.post('/api/auth/login', { email, password });
      return response.data; // Espera-se que o backend retorne o token e/ou dados do usuário
    } catch (error) {
      throw error.response ? error.response.data : new Error('Erro de conexão');
    }
  },

  register: async (name, email, password) => {
    try {
      const response = await apiClient.post('/api/auth/register', { name, email, password });
      return response.data; // Espera-se que o backend retorne o token e/ou dados do usuário
    } catch (error) {
      throw error.response ? error.response.data : new Error('Erro de conexão');
    }
  },

  // Você pode adicionar uma função para verificar o token (se necessário)
  // Por exemplo, para validar o token no carregamento da aplicação
  verifyToken: async () => {
    try {
      const response = await apiClient.get('/api/auth/verify'); // Ou outro endpoint de verificação
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : new Error('Erro de conexão');
    }
  }
};

export default authService;