import { useState, useEffect } from 'react'

// Configuração da API - sem process.env
const API_URL = 'https://mega-api-whatsapp-ai-backend.onrender.com';

export const useChat = () => {
  const [contacts, setContacts] = useState([
    {
      id: 1,
      name: 'Assistente IA',
      avatar: '🤖',
      lastMessage: 'Olá! Como posso ajudar você hoje?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      unread: 0,
      online: true
    }
  ])
  
  const [selectedContact, setSelectedContact] = useState(contacts[0])
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: 'Olá! Sou seu assistente de IA. Como posso ajudar você hoje?',
      sender: 'ai',
      timestamp: new Date(),
      status: 'read'
    }
  ])
  
  const [isTyping, setIsTyping] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')

  // Função para selecionar contato
  const selectContact = (contact) => {
    setSelectedContact(contact)
  }

  // Função para enviar mensagem
  const sendMessage = async (messageText) => {
    if (!messageText.trim()) return

    try {
      // Adiciona mensagem do usuário imediatamente
      const userMessage = {
        id: Date.now(),
        text: messageText,
        sender: 'user',
        timestamp: new Date(),
        status: 'sent'
      }
      
      setMessages(prev => [...prev, userMessage])
      setIsTyping(true)

      // Envia para o backend
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageText,
          user_id: selectedContact?.id || 'default',
          conversation_id: selectedContact?.id || 1
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      
      // Simula delay de digitação
      setTimeout(() => {
        // Adiciona resposta da IA
        const aiMessage = {
          id: Date.now() + 1,
          text: data.response || data.message || 'Desculpe, não consegui processar sua mensagem.',
          sender: 'ai',
          timestamp: new Date(),
          status: 'read'
        }
        
        setMessages(prev => [...prev, aiMessage])
        setIsTyping(false)
        
        // Atualiza última mensagem do contato
        setContacts(prev => prev.map(contact => 
          contact.id === selectedContact?.id 
            ? { 
                ...contact, 
                lastMessage: aiMessage.text.substring(0, 50) + (aiMessage.text.length > 50 ? '...' : ''),
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
              }
            : contact
        ))
      }, 1000 + Math.random() * 2000)

    } catch (error) {
      console.error('Erro ao enviar mensagem:', error)
      setIsTyping(false)
      
      // Adiciona mensagem de erro
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Desculpe, ocorreu um erro ao enviar sua mensagem. Verifique sua conexão e tente novamente.',
        sender: 'ai',
        timestamp: new Date(),
        status: 'error'
      }
      
      setMessages(prev => [...prev, errorMessage])
    }
  }

  // Função para adicionar novo contato
  const addContact = (contactData) => {
    const newContact = {
      id: Date.now(),
      name: contactData.name,
      avatar: contactData.avatar || '👤',
      lastMessage: 'Novo contato adicionado',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      unread: 0,
      online: Math.random() > 0.5
    }
    
    setContacts(prev => [...prev, newContact])
  }

  // Filtrar contatos baseado na busca
  const filteredContacts = contacts.filter(contact =>
    contact.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return {
    contacts: filteredContacts,
    selectedContact,
    messages,
    isTyping,
    searchTerm,
    setSearchTerm,
    selectContact,
    sendMessage,
    addContact
  }
}
