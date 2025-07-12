// frontend/src/contexts/AuthContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';
// IMPORTANTE: Importe o authService para usar suas funções de login/registro reais
import authService from '../services/api/authService'; 
// Opcional: Importe apiClient se precisar de acesso direto para configuração (menos comum aqui)
// import apiClient from '../services/api/apiClient';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    const checkAuthStatus = async () => {
      const savedToken = localStorage.getItem('token');
      if (savedToken) {
        setToken(savedToken);
        // Tente verificar o token com o backend para confirmar se é válido
        // ou decodifique-o para obter os dados do usuário (se for um JWT)
        try {
          // Se authService.verifyToken() estiver implementado e retornar dados do usuário
          // const userData = await authService.verifyToken(); 
          // setUser(userData.user); 

          // Para um JWT simples que você não quer validar no backend a cada load,
          // mas apenas assumir que se existe, o usuário está logado (menos seguro)
          // Você pode decodificar o token aqui se quiser extrair info:
          // const decodedToken = JSON.parse(atob(savedToken.split('.')[1]));
          // setUser({ id: decodedToken.sub, name: decodedToken.username, email: decodedToken.email });
          
          // Por enquanto, vamos manter uma simulação mais segura com base no token
          // e assumir que o token existe e é válido para evitar um request a cada load.
          // O token será verificado no login e em requests protegidos.
          setUser({ id: 'persisted', name: 'Usuário Logado', email: 'persisted@example.com' }); // Simula usuário se token existe
        } catch (error) {
          console.error("Erro ao verificar token na inicialização:", error);
          localStorage.removeItem('token'); // Remover token inválido
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    };
    checkAuthStatus();
  }, []); // Executa apenas uma vez no carregamento do componente

  const login = async (email, password) => {
    setLoading(true);
    try {
      // ✅ CHAME A FUNÇÃO REAL DO SERVIÇO DE AUTENTICAÇÃO
      const response = await authService.login(email, password); 
      // Ajuste 'token' e 'user' de acordo com a estrutura da resposta do seu backend Flask
      const { access_token, user: userData } = response; 
      
      localStorage.setItem('token', access_token); // Guarde o token retornado
      setToken(access_token);
      setUser(userData); // Atualize o estado com os dados do usuário

      return { success: true };
    } catch (error) {
      console.error("Login falhou:", error.message);
      return { success: false, error: error.message || 'Erro ao fazer login. Verifique suas credenciais.' };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    // Opcional: você pode redirecionar o usuário para a página de login aqui
    // window.location.href = '/login'; 
  };

  const register = async (name, email, password) => {
    setLoading(true);
    try {
      // ✅ CHAME A FUNÇÃO REAL DO SERVIÇO DE AUTENTICAÇÃO
      const response = await authService.register(name, email, password);
      // Ajuste 'token' e 'user' de acordo com a estrutura da resposta do seu backend Flask
      const { access_token, user: userData } = response; 
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);

      return { success: true };
    } catch (error) {
      console.error("Registro falhou:", error.message);
      return { success: false, error: error.message || 'Erro ao registrar. Tente novamente.' };
    } finally {
      setLoading(false);
    }
  };

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    register,
    isAuthenticated: !!user // True se houver um objeto user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};