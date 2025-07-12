import { useState } from 'react'
import { useChat } from '../hooks/useChat'
import ContactList from './Sidebar/ContactList'
import ChatArea from './Chat/ChatArea'
import AddContactModal from './UI/AddContactModal'

const WhatsAppInterface = () => {
  const {
    contacts,
    selectedContact,
    messages,
    isTyping,
    searchTerm,
    setSearchTerm,
    selectContact,
    sendMessage,
    addContact
  } = useChat()

  const [isAddContactModalOpen, setIsAddContactModalOpen] = useState(false)

  const handleAddContact = (newContact) => {
    addContact(newContact)
  }

  return (
    <div className="h-screen bg-gray-100 flex">
      {/* Sidebar com lista de contatos */}
      <ContactList
        contacts={contacts}
        selectedContact={selectedContact}
        onSelectContact={selectContact}
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        onAddContact={() => setIsAddContactModalOpen(true)}
      />

      {/* Área principal do chat */}
      <div className="flex-1">
        {selectedContact ? (
          <ChatArea
            selectedContact={selectedContact}
            messages={messages}
            onSendMessage={sendMessage}
            isTyping={isTyping}
          />
        ) : (
          <div className="h-full flex items-center justify-center bg-gray-50">
            <div className="text-center">
              <div className="w-64 h-64 mx-auto mb-8 bg-green-100 rounded-full flex items-center justify-center">
                <svg
                  className="w-32 h-32 text-green-500"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                WhatsApp AI Assistant
              </h2>
              <p className="text-gray-600 mb-8 max-w-md">
                Selecione um contato para começar a conversar ou adicione um novo contato para testar o assistente de IA.
              </p>
              <button
                onClick={() => setIsAddContactModalOpen(true)}
                className="bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 transition-colors font-medium"
              >
                Adicionar Primeiro Contato
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modal para adicionar contato */}
      <AddContactModal
        isOpen={isAddContactModalOpen}
        onClose={() => setIsAddContactModalOpen(false)}
        onAddContact={handleAddContact}
      />
    </div>
  )
}

export default WhatsAppInterface