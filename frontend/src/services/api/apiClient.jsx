// frontend/src/services/api/apiClient.jsx
import axios from 'axios';

// URL base do seu backend Flask
// Certifique-se de que esta URL corresponde ao endereço onde seu backend está rodando
const API_BASE_URL = 'http://localhost:5000'; 

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para adicionar o token de autenticação a cada requisição
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default apiClient;