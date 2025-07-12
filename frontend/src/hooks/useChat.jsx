import { useState, useEffect, useRef } from 'react'

// Dados simulados de contatos
const MOCK_CONTACTS = [
  {
    id: 1,
    name: 'João Silva',
    phone: '+55 11 99999-1234',
    avatar: 'https://ui-avatars.com/api/?name=João+Silva&background=10b981&color=fff',
    lastMessage: 'Olá! Como posso ajudar?',
    lastMessageTime: '14:30',
    unreadCount: 2,
    isOnline: true
  },
  {
    id: 2,
    name: 'Maria Santos',
    phone: '+55 11 99999-5678',
    avatar: 'https://ui-avatars.com/api/?name=Maria+Santos&background=3b82f6&color=fff',
    lastMessage: 'Obrigada pelo atendimento!',
    lastMessageTime: '13:45',
    unreadCount: 0,
    isOnline: false
  },
  {
    id: 3,
    name: 'Pedro Costa',
    phone: '+55 11 99999-9012',
    avatar: 'https://ui-avatars.com/api/?name=Pedro+Costa&background=f59e0b&color=fff',
    lastMessage: 'Quando vocês abrem?',
    lastMessageTime: '12:20',
    unreadCount: 1,
    isOnline: true
  },
  {
    id: 4,
    name: 'Ana Oliveira',
    phone: '+55 11 99999-3456',
    avatar: 'https://ui-avatars.com/api/?name=Ana+Oliveira&background=ef4444&color=fff',
    lastMessage: 'Perfeito! Muito obrigada',
    lastMessageTime: '11:15',
    unreadCount: 0,
    isOnline: false
  }
]

// Mensagens simuladas
const MOCK_MESSAGES = {
  1: [
    {
      id: 1,
      text: 'Olá! Gostaria de saber mais sobre seus produtos.',
      sender: 'contact',
      timestamp: '14:25',
      status: 'read'
    },
    {
      id: 2,
      text: 'Olá João! Claro, ficarei feliz em ajudar. Que tipo de produto você está procurando?',
      sender: 'me',
      timestamp: '14:26',
      status: 'read'
    },
    {
      id: 3,
      text: 'Estou interessado em soluções de IA para meu negócio.',
      sender: 'contact',
      timestamp: '14:30',
      status: 'delivered'
    }
  ],
  2: [
    {
      id: 1,
      text: 'Oi! Recebi o orçamento, muito obrigada!',
      sender: 'contact',
      timestamp: '13:40',
      status: 'read'
    },
    {
      id: 2,
      text: 'Que bom que gostou, Maria! Qualquer dúvida, estou aqui.',
      sender: 'me',
      timestamp: '13:42',
      status: 'read'
    },
    {
      id: 3,
      text: 'Obrigada pelo atendimento!',
      sender: 'contact',
      timestamp: '13:45',
      status: 'read'
    }
  ],
  3: [
    {
      id: 1,
      text: 'Quando vocês abrem?',
      sender: 'contact',
      timestamp: '12:20',
      status: 'delivered'
    }
  ],
  4: [
    {
      id: 1,
      text: 'O produto chegou hoje, está perfeito!',
      sender: 'contact',
      timestamp: '11:10',
      status: 'read'
    },
    {
      id: 2,
      text: 'Que ótima notícia, Ana! Fico muito feliz que tenha gostado.',
      sender: 'me',
      timestamp: '11:12',
      status: 'read'
    },
    {
      id: 3,
      text: 'Perfeito! Muito obrigada',
      sender: 'contact',
      timestamp: '11:15',
      status: 'read'
    }
  ]
}

export const useChat = () => {
  const [contacts, setContacts] = useState(MOCK_CONTACTS)
  const [selectedContact, setSelectedContact] = useState(null)
  const [messages, setMessages] = useState({})
  const [newMessage, setNewMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const messagesEndRef = useRef(null)

  // Carregar mensagens iniciais
  useEffect(() => {
    setMessages(MOCK_MESSAGES)
  }, [])

  // Auto-scroll para a última mensagem
  useEffect(() => {
    scrollToBottom()
  }, [messages, selectedContact])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // Filtrar contatos por busca
  const filteredContacts = contacts.filter(contact =>
    contact.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contact.phone.includes(searchTerm)
  )

  // Selecionar contato
  const selectContact = (contact) => {
    setSelectedContact(contact)
    // Marcar mensagens como lidas
    setContacts(prev => 
      prev.map(c => 
        c.id === contact.id 
          ? { ...c, unreadCount: 0 }
          : c
      )
    )
  }

  // Enviar mensagem
  const sendMessage = async (messageText = newMessage) => {
    if (!messageText.trim() || !selectedContact) return

    setIsLoading(true)
    
    const userMessage = {
      id: Date.now(),
      text: messageText.trim(),
      sender: 'me',
      timestamp: new Date().toLocaleTimeString('pt-BR', { 
        hour: '2-digit', 
        minute: '2-digit' 
      }),
      status: 'sending'
    }

    // Adicionar mensagem do usuário
    setMessages(prev => ({
      ...prev,
      [selectedContact.id]: [
        ...(prev[selectedContact.id] || []),
        userMessage
      ]
    }))

    // Atualizar última mensagem do contato
    setContacts(prev =>
      prev.map(contact =>
        contact.id === selectedContact.id
          ? {
              ...contact,
              lastMessage: messageText.trim(),
              lastMessageTime: userMessage.timestamp
            }
          : contact
      )
    )

    setNewMessage('')

    try {
      // Simular processamento da IA
      await new Promise(resolve => setTimeout(resolve, 2000))

      // Marcar mensagem como enviada
      setMessages(prev => ({
        ...prev,
        [selectedContact.id]: prev[selectedContact.id].map(msg =>
          msg.id === userMessage.id
            ? { ...msg, status: 'sent' }
            : msg
        )
      }))

      // Simular resposta da IA (opcional)
      const aiResponse = {
        id: Date.now() + 1,
        text: generateAIResponse(messageText),
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString('pt-BR', { 
          hour: '2-digit', 
          minute: '2-digit' 
        }),
        status: 'delivered'
      }

      // Adicionar resposta da IA após um delay
      setTimeout(() => {
        setMessages(prev => ({
          ...prev,
          [selectedContact.id]: [
            ...(prev[selectedContact.id] || []),
            aiResponse
          ]
        }))

        setContacts(prev =>
          prev.map(contact =>
            contact.id === selectedContact.id
              ? {
                  ...contact,
                  lastMessage: aiResponse.text,
                  lastMessageTime: aiResponse.timestamp
                }
              : contact
          )
        )
      }, 1000)

    } catch (error) {
      console.error('Erro ao enviar mensagem:', error)
      // Marcar mensagem como erro
      setMessages(prev => ({
        ...prev,
        [selectedContact.id]: prev[selectedContact.id].map(msg =>
          msg.id === userMessage.id
            ? { ...msg, status: 'error' }
            : msg
        )
      }))
    } finally {
      setIsLoading(false)
    }
  }

  // Gerar resposta da IA (simulada)
  const generateAIResponse = (userMessage) => {
    const responses = [
      'Obrigado pela sua mensagem! Como posso ajudá-lo hoje?',
      'Entendi sua solicitação. Vou verificar isso para você.',
      'Ótima pergunta! Deixe-me buscar essas informações.',
      'Claro! Ficarei feliz em ajudar com isso.',
      'Vou encaminhar sua solicitação para o setor responsável.',
      'Obrigado pelo contato! Em breve retornaremos com uma resposta.'
    ]
    
    return responses[Math.floor(Math.random() * responses.length)]
  }

  // Adicionar novo contato
  const addContact = (contactData) => {
    const newContact = {
      id: Date.now(),
      ...contactData,
      avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(contactData.name)}&background=10b981&color=fff`,
      lastMessage: '',
      lastMessageTime: '',
      unreadCount: 0,
      isOnline: false
    }

    setContacts(prev => [newContact, ...prev])
    return newContact
  }

  // Obter mensagens do contato selecionado
  const currentMessages = selectedContact ? messages[selectedContact.id] || [] : []

  return {
    contacts: filteredContacts,
    selectedContact,
    messages: currentMessages,
    newMessage,
    isLoading,
    searchTerm,
    messagesEndRef,
    setNewMessage,
    setSearchTerm,
    selectContact,
    sendMessage,
    addContact,
    scrollToBottom
  }
}