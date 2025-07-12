#!/usr/bin/env python3
"""
WhatsApp AI Agent - Aplicação principal
Integração com MEGA API para automação de WhatsApp
Refatorado com LangChain para gerenciamento de IA e memória, AGORA COM SISTEMA RAG INTEGRADO.
"""

import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import logging
import threading
import shutil # Importar shutil para manipulação de diretórios
from flask_cors import CORS # <--- JÁ ESTÁ IMPORTADO, ÓTIMO!

# LangChain Imports
from langchain_openai import ChatOpenAI, OpenAIEmbeddings # OpenAIEmbeddings precisa ser importado aqui também
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate

from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps

# RAG Imports
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain.schema import Document # Mantido, caso precise explicitamente, mas pode ser removido se não usado

# --- INÍCIO DAS CORREÇÕES DE ORDEM ---

# 1. Configuração de Logging: DEVE SER O PRIMEIRO A SER CONFIGURADO
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler() # Saída para o console/logs do Render
        # Removido FileHandler por ser problemático em ambientes sem persistência de disco
        # logging.FileHandler('whatsapp_agent.log'), # Para desenvolvimento local
    ]
)
logger = logging.getLogger(__name__)

# 2. Carregar variáveis de ambiente: ANTES DO USO DAS VARIÁVEIS
load_dotenv() # Para desenvolvimento local (carrega do .env se existir)

# 3. Inicialização do Flask App: ANTES DO USO DE app.config
app = Flask(__name__)
CORS(app)  #HABILITA O CORS PARA O SEU APLICATIVO FLASK

# 4. Variáveis de Ambiente e SECRET_KEY: CARREGADAS ANTES DE SEREM USADAS
SECRET_KEY = os.getenv('SECRET_KEY')
MEGA_API_BASE_URL = os.getenv('MEGA_API_BASE_URL')
MEGA_API_TOKEN = os.getenv('MEGA_API_TOKEN')
MEGA_INSTANCE_ID = os.getenv('MEGA_INSTANCE_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Atribui SECRET_KEY à configuração do Flask
app.config['SECRET_KEY'] = SECRET_KEY if SECRET_KEY else 'fallback-secret-key-for-development' # fallback para dev

# Debug das variáveis de ambiente: AGORA logger ESTÁ DEFINIDO
logger.info(f" Debug - SECRET_KEY: {'***' if SECRET_KEY else 'None'}")
logger.info(f"🔍 Debug - MEGA_API_BASE_URL: {MEGA_API_BASE_URL}")
logger.info(f"🔍 Debug - MEGA_API_TOKEN: {'***' if MEGA_API_TOKEN else 'None'}")
logger.info(f"🔍 Debug - MEGA_INSTANCE_ID: {MEGA_INSTANCE_ID}")
logger.info(f"🔍 Debug - OPENAI_API_KEY: {'***' if OPENAI_API_KEY else 'None'}")

# Validação das variáveis essenciais: APÓS CARREGAMENTO
required_vars = {
    'SECRET_KEY': SECRET_KEY, # Adicionado para validação
    'MEGA_API_BASE_URL': MEGA_API_BASE_URL,
    'MEGA_API_TOKEN': MEGA_API_TOKEN,
    'MEGA_INSTANCE_ID': MEGA_INSTANCE_ID,
    'OPENAI_API_KEY': OPENAI_API_KEY
}

missing_vars = [var for var, value in required_vars.items() if not value]

if missing_vars:
    logger.error(f"❌ Variáveis de ambiente obrigatórias não encontradas: {missing_vars}")
    logger.error("Certifique-se de que todas as variáveis essenciais estão configuradas corretamente.")
    exit(1)

# --- FIM DAS CORREÇÕES DE ORDEM INICIAIS ---


# --- INÍCIO DA CONFIGURAÇÃO DO LANGCHAIN E RAG: MOVIDO PARA CIMA ---

# Configuração do LangChain LLM (ChatOpenAI)
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model="gpt-3.5-turbo", # Ou "gpt-4" se preferir e tiver acesso
    temperature=0.7 # Criatividade da resposta
)

# Template de prompt personalizado para a IA (original, para fallback e conversação geral)
prompt_template = PromptTemplate(
    input_variables=["history", "input"],
    template="""Você é um assistente de IA amigável e prestativo, especializado em marketing e tecnologia,
focado em ajudar Álefe Lins a desenvolver um aplicativo e iniciar um negócio de agentes de IA.
Responda de forma elaborada e forneça exemplos quando apropriado.
Seu conhecimento base é até Março de 2025.

Histórico da Conversa:
{history}
Usuário: {input}
Assistente:"""
)

# Dicionário para armazenar memórias por usuário
user_memories = {}

def get_user_memory(user_id):
    """Obtém ou cria uma memória para o usuário específico"""
    if user_id not in user_memories:
        user_memories[user_id] = ConversationBufferMemory(
            memory_key="history",
            return_messages=False # Mantenha como False para compatibilidade com o prompt_template
        )
        logger.info(f"Nova memória criada para o usuário: {user_id}")
    return user_memories[user_id]

# Variáveis globais para o sistema RAG
PERSIST_DIRECTORY = "./chroma_db"
RAG_ENABLED = False
rag_chain = None
vectorstore = None

def initialize_vectorstore():
    """Inicializa o vectorstore com verificação de compatibilidade de embeddings."""
    global RAG_ENABLED, rag_chain, vectorstore # Declarar como globais para modificar
    
    try:
        # Usar o mesmo modelo de embedding do seu código principal
        # 'text-embedding-ada-002' tem 1536 dimensões. Se seu ChromaDB foi criado com 384,
        # ele precisa ser recriado ou o modelo precisa ser ajustado (ex: text-embedding-3-small com dimensions=384).
        embeddings_model = OpenAIEmbeddings(
            model="text-embedding-ada-002", # Mantendo o modelo original que você usava
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
        
        vectorstore_recreated = False
        if os.path.exists(PERSIST_DIRECTORY) and os.listdir(PERSIST_DIRECTORY):
            try:
                logger.info("Tentando carregar ChromaDB existente...")
                temp_vectorstore = Chroma(
                    persist_directory=PERSIST_DIRECTORY,
                    embedding_function=embeddings_model
                )
                # Forçar uma busca para verificar compatibilidade
                # Isso pode falhar se a dimensão for incompatível
                temp_vectorstore.similarity_search("teste", k=1) 
                logger.info("✅ ChromaDB carregado com sucesso!")
                vectorstore = temp_vectorstore
            except Exception as e:
                logger.warning(f"⚠️ ChromaDB existente é incompatível ou corrupto: {e}. Removendo e recriando.")
                if os.path.exists(PERSIST_DIRECTORY):
                    shutil.rmtree(PERSIST_DIRECTORY) # Remove o diretório problemático
                vectorstore_recreated = True
                vectorstore = Chroma(
                    persist_directory=PERSIST_DIRECTORY,
                    embedding_function=embeddings_model
                )
        else:
            logger.warning("⚠️ Nenhuma base de conhecimento (chroma_db) encontrada. Criando nova.")
            vectorstore_recreated = True
            vectorstore = Chroma(
                persist_directory=PERSIST_DIRECTORY,
                embedding_function=embeddings_model
            )

        # Verifica e carrega documentos se a base de dados estiver vazia ou foi recriada
        if vectorstore_recreated or (vectorstore and vectorstore._collection.count() == 0):
            logger.info("📚 NOTA: A base de conhecimento foi recriada ou está vazia. Por favor, use a interface Streamlit para fazer o upload de documentos.")
            # Se você tiver um método programático para carregar documentos aqui, adicione-o.
            # Ex:
            # from langchain_community.document_loaders import TextLoader
            # from langchain.text_splitter import RecursiveCharacterTextSplitter
            # loader = TextLoader("path/to/your/initial_document.txt")
            # documents = loader.load()
            # text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            # chunks = text_splitter.split_documents(documents)
            # vectorstore.add_documents(chunks)

        if vectorstore and vectorstore._collection.count() > 0:
            doc_count = vectorstore._collection.count()
            logger.info(f"📚 Base de conhecimento: {doc_count} documentos carregados.")
            retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}
            )
            rag_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True
            )
            RAG_ENABLED = True
            logger.info("🧠 Sistema RAG ativado e pronto!")
        else:
            RAG_ENABLED = False
            rag_chain = None
            logger.warning("⚠️ ChromaDB vazio ou sem documentos. RAG desativado.")

    except Exception as e:
        logger.error(f"❌ Erro ao inicializar ChromaDB: {e}", exc_info=True)
        RAG_ENABLED = False
        rag_chain = None
    finally:
        logger.info(f"Status final do RAG: {'Ativado' if RAG_ENABLED else 'Desativado'}")


# NOVO: Chamada para inicializar o vectorstore globalmente
initialize_vectorstore()

# --- FIM DA CONFIGURAÇÃO DO LANGCHAIN E RAG ---


# --- FUNÇÕES AUXILIARES ---

def generate_ai_response(message_text: str, user_id: str) -> str:
    """
    Gera uma resposta da IA usando o LangChain.
    Prioriza o sistema RAG se ativado e houver contexto relevante.
    Caso contrário, usa a cadeia de conversação padrão.
    """
    try:
        logger.info(f"Gerando resposta IA para a mensagem de '{user_id}': '{message_text[:100]}...'")

        memory = get_user_memory(user_id) # Obter memória específica do usuário
        final_response = ""
        used_rag = False # Flag para saber se o RAG foi a fonte da resposta

        # --- 1. Tentar responder com RAG ---
        # Garante que RAG_ENABLED e rag_chain estejam definidos globalmente pela initialize_vectorstore()
        if RAG_ENABLED and rag_chain:
            try:
                logger.info(f"📖 Tentando recuperar informações da base de conhecimento para '{user_id}'...")
                rag_result = rag_chain.invoke({"query": message_text})

                rag_answer = rag_result.get("result", "")
                sources = rag_result.get("source_documents", [])

                # Critério para decidir se a resposta RAG é "útil"
                # Uma resposta é considerada útil se houver fontes e a resposta não for genérica de "não encontrei"
                if sources and len(rag_answer) > 50 and "não encontrei informações" not in rag_answer.lower() and "não consigo responder" not in rag_answer.lower():
                    final_response = rag_answer
                    used_rag = True
                    logger.info(f"📖 RAG encontrou {len(sources)} documentos relevantes e gerou uma resposta útil: '{final_response[:100]}...'")
                else:
                    logger.info("⚠️ RAG ativado, mas nenhum documento relevante ou resposta útil encontrada para esta consulta.")
            except Exception as e:
                logger.error(f"Erro na consulta RAG para '{user_id}': {e}", exc_info=True)
                logger.info("⚠️ Falha na consulta RAG. Prosseguindo para conversação padrão.")
        else:
            logger.info("❌ Sistema RAG desativado ou não inicializado. Prosseguindo para conversação padrão.")

        # --- 2. Se RAG não gerou uma resposta útil, usar a ConversationChain padrão ---
        if not final_response:
            logger.info("💬 Usando ConversationChain padrão para gerar resposta.")
            # A ConversationChain já gerencia a memória automaticamente com o prompt_template padrão.
            conversation_chain_instance = ConversationChain( # Renomeado para evitar conflito com 'conversation' global se definido
                llm=llm,
                memory=memory,
                prompt=prompt_template, # Usa o prompt_template original (apenas history e input)
                verbose=True
            )
            final_response = conversation_chain_instance.predict(input=message_text)

        # --- 3. Atualizar memória manualmente se a resposta veio do RAG ---
        # Se a resposta final veio do RAG (e não da ConversationChain), precisamos adicionar
        # a interação (input do usuário e output do RAG) à memória para manter o histórico.
        # A ConversationChain.predict() já faz isso automaticamente.
        if used_rag:
            memory.save_context({"input": message_text}, {"output": final_response})
            logger.info("Memória atualizada manualmente com entrada e saída RAG para manter histórico.")

        logger.info(f"Resposta da IA gerada para '{user_id}': '{final_response[:100]}...'")
        return final_response

    except Exception as e:
        logger.error(f"Erro ao gerar resposta da IA para '{user_id}': {e}", exc_info=True)
        return "Desculpe, não consegui gerar uma resposta no momento. Por favor, tente novamente mais tarde."

def send_whatsapp_message(phone_number: str, message: str) -> bool:
    """
    Envia uma mensagem de texto para um número de WhatsApp via MEGA API.
    """
    try:
        # CONSTRUÇÃO DA URL CORRETA COM BASE NA DOCUMENTAÇÃO (SUA ORIGINAL)
        url = f"{MEGA_API_BASE_URL}/rest/sendMessage/{MEGA_INSTANCE_ID}/text"

        headers = {
            'Authorization': f'Bearer {MEGA_API_TOKEN}',
            'Content-Type': 'application/json'
        }

        formatted_phone_number = phone_number
        if not ("@s.whatsapp.net" in phone_number or "@g.us" in phone_number):
             formatted_phone_number = f"{phone_number}@s.whatsapp.net"

        payload = {
            "messageData": {
                "to": formatted_phone_number,
                "text": message
            }
        }

        logger.info(f"Tentando enviar mensagem para {formatted_phone_number} via MEGA API (URL: {url})")
        logger.debug(f"Payload: {payload}")
        response = requests.post(url, json=payload, headers=headers, timeout=15)

        response.raise_for_status()

        response_json = response.json()
        if response_json.get('error'):
            logger.error(f"MEGA API reportou erro no corpo da resposta para {formatted_phone_number}: {response_json.get('message', 'Erro desconhecido da API')}. Resposta completa: {response_json}")
            return False

        logger.info(f"Mensagem enviada com sucesso para {formatted_phone_number}. Status HTTP: {response.status_code}, Resposta da API: {response_json}")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de requisição ao enviar mensagem para {phone_number} via MEGA API: {e}", exc_info=True)
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Resposta de erro da API: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"Erro inesperado ao enviar mensagem via MEGA API: {e}", exc_info=True)
        return False

def process_message_async(phone_full_jid: str, message_text: str, sender_name: str):
    """
    Função assíncrona para processar a mensagem do usuário, gerar a resposta da IA e enviá-la.
    Executada em uma thread separada para não bloquear o webhook principal.
    """
    try:
        logger.info(f"Iniciando processamento assíncrono da mensagem de {sender_name} ({phone_full_jid}).")

        user_id_for_memory = phone_full_jid.replace('@s.whatsapp.net', '').replace('@g.us', '')

        # 1. Gerar resposta com IA (que agora lida com RAG internamente)
        ai_response = generate_ai_response(message_text, user_id_for_memory)

        # 2. Enviar resposta de volta ao usuário via MEGA API
        success = send_whatsapp_message(phone_full_jid, ai_response)

        if success:
            logger.info(f"✅ Resposta da IA enviada com sucesso para {phone_full_jid}.")
        else:
            logger.error(f"❌ Falha ao enviar a resposta da IA para {phone_full_jid}.")

    except Exception as e:
        logger.error(f"Erro no processamento assíncrono da mensagem: {e}", exc_info=True)

def process_webhook_async_corrected_for_logs(data):
    """
    Processa webhook de forma assíncrona. Esta versão é mais robusta
    na forma como extrai os dados do payload da MEGA API.
    Utilizada para fins de depuração e compatibilidade com logs anteriores.
    """
    try:
        message_type = data.get('messageType')
        message_content = None

        if message_type == 'conversation':
            message_content = data.get('message', {}).get('conversation')
        elif message_type == 'textMessage':
            message_content = data.get('message', {}).get('text')

        is_from_me = data.get('key', {}).get('fromMe', False)

        if not message_content or is_from_me:
            logger.info(f"Webhook (process_webhook_async_corrected_for_logs) ignorado (messageType: {message_type}, fromMe: {is_from_me}, hasContent: {bool(message_content)})")
            return

        sender_full_jid = data.get('key', {}).get('remoteJid', '')
        sender_name = data.get('pushName', 'Usuário')

        if not sender_full_jid:
            logger.warning("JID do remetente não encontrado no webhook.")
            return

        user_id_for_memory = sender_full_jid.replace('@s.whatsapp.net', '').replace('@g.us', '')

        logger.info(f"Processando mensagem (process_webhook_async_corrected_for_logs) de {sender_name} ({user_id_for_memory}): '{message_content}'")

        ai_response = generate_ai_response(message_content, user_id_for_memory)

        success = send_whatsapp_message(sender_full_jid, ai_response)

        if success:
            logger.info(f"✅ Resposta da IA enviada com sucesso para {sender_full_jid}.")
        else:
            logger.error(f"❌ Falha ao enviar a resposta da IA para {sender_full_jid}.")

    except Exception as e:
        logger.error(f"Erro no processamento assíncrono do webhook (process_webhook_async_corrected_for_logs): {e}", exc_info=True)


# --- FIM DAS FUNÇÕES AUXILIARES ---


# --- ROTAS DA API: ORDEM MANTIDA COMO NO SEU CÓDIGO ---

@app.route('/')
def home():
    """Endpoint de teste para verificar se o Flask está rodando."""
    doc_count = 0
    # A variável vectorstore agora é global e deveria estar acessível aqui
    if RAG_ENABLED and vectorstore: # Verifica se vectorstore foi inicializado com sucesso
        try:
            collection = vectorstore._collection
            doc_count = collection.count()
        except Exception as e:
            logger.warning(f"Não foi possível obter a contagem de documentos para o endpoint home: {e}")
            doc_count = "unknown"

    # A data e hora devem ser geradas dinamicamente
    # datetime já está importado do topo, não precisa de 'import datetime' aqui
    now_utc = datetime.now(datetime.timezone.utc) # Usar datetime.now() direto
    now_brt = now_utc - datetime.timedelta(hours=3) # Brasília Time is UTC-3

    return jsonify({
        "status": "success",
        "message": "WhatsApp AI Agent está rodando!",
        "version": "1.0",
        "rag_enabled": RAG_ENABLED,
        "documents_in_chromadb": doc_count,
        "current_time_utc": now_utc.strftime("%d/%m/%Y %H:%M:%S (UTC)"),
        "current_time_brasília": now_brt.strftime("%d/%m/%Y %H:%M:%S (UTC-3)")
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Endpoint principal para receber notificações (webhooks) da MEGA API.
    """
    try:
        data = request.get_json()
        if data is None:
            logger.warning("Webhook recebido sem dados JSON.")
            return jsonify({"status": "error", "message": "No JSON data"}), 400

        logger.info(f"Webhook recebido: {data}")

        if (data and
            data.get('messageType') == 'conversation' and
            data.get('message', {}).get('conversation') and
            data.get('key', {}).get('remoteJid') and
            not data.get('key', {}).get('fromMe', False)):

            phone_full_jid = data['key']['remoteJid']
            message_text = data['message']['conversation']
            sender_name = data.get('pushName', 'Usuário')

            logger.info(f"Mensagem de texto válida recebida de {sender_name} ({phone_full_jid}): '{message_text}'")

            thread = threading.Thread(
                target=process_message_async,
                args=(phone_full_jid, message_text, sender_name)
            )
            thread.start()

            return jsonify({"status": "received", "message": "Mensagem recebida e em processamento"}), 200

        else:
            logger.info(f"Webhook ignorado (não é uma mensagem de texto para processamento de IA ou é uma mensagem própria): {data.get('messageType', 'Tipo Desconhecido')}")
            return jsonify({"status": "ignored", "message": "Payload não é uma mensagem de texto para processamento de IA ou é uma mensagem própria."}), 200

    except Exception as e:
        logger.error(f"Erro inesperado no webhook: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Erro interno no servidor de webhook."}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint para verificação de saúde da aplicação e conectividade com a MEGA API.
    """
    mega_api_status = "disconnected"
    mega_api_response_detail = "N/A"
    try:
        test_url = f"{MEGA_API_BASE_URL}/rest/instance/{MEGA_INSTANCE_ID}/status"
        headers = {
            'Authorization': f'Bearer {MEGA_API_TOKEN}'
        }
        response = requests.get(test_url, headers=headers, timeout=5)
        if response.status_code == 200:
            mega_api_status = "connected"
            mega_api_response_detail = response.json()
        else:
            mega_api_status = f"connected (HTTP {response.status_code})"
            mega_api_response_detail = response.text
            logger.warning(f"MEGA API acessível, mas retornou status: {response.status_code} no health check. Resposta: {response.text}")
    except requests.exceptions.RequestException as e:
        mega_api_status = "error"
        mega_api_response_detail = str(e)
        logger.error(f"Falha ao conectar com MEGA API durante o health check: {e}", exc_info=True)

    doc_count = 0
    if RAG_ENABLED and vectorstore: # Usando vectorstore que é global
        try:
            collection = vectorstore._collection
            doc_count = collection.count()
        except Exception as e:
            logger.warning(f"Não foi possível obter a contagem de documentos para o health check: {e}")
            doc_count = "unknown"

    return jsonify({
        "status": "healthy",
        "flask_app": "running",
        "mega_api_connectivity": mega_api_status,
        "mega_api_response_detail": mega_api_response_detail,
        "rag_enabled": RAG_ENABLED,
        "documents_in_chromadb": doc_count
    })

@app.route('/test_mega_api_send', methods=['POST'])
def test_mega_api_send():
    """
    Endpoint de teste para enviar uma mensagem via MEGA API manualmente.
    Útil para depurar o envio.
    """
    data = request.get_json()
    test_phone = data.get('phone')
    test_message = data.get('message')

    if not test_phone or not test_message:
        return jsonify({"status": "error", "message": "Parâmetros 'phone' e 'message' são obrigatórios"}), 400

    logger.info(f"Recebida requisição de teste de envio para {test_phone} com mensagem: {test_message}")

    if not ("@s.whatsapp.net" in test_phone or "@g.us" in test_phone):
        test_phone_formatted = f"{test_phone}@s.whatsapp.net"
    else:
        test_phone_formatted = test_phone

    success = send_whatsapp_message(test_phone_formatted, test_message)

    if success:
        return jsonify({"status": "success", "message": f"Mensagem de teste enviada para {test_phone}"}), 200
    else:
        return jsonify({"status": "error", "message": f"Falha ao enviar mensagem de teste para {test_phone}"}), 500

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """
    Endpoint para chat direto com o AI agent (para testes).
    """
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"status": "error", "message": "Campo 'message' é obrigatório"}), 400
        
        user_message = data['message']
        logger.info(f"📩 Mensagem recebida via API: {user_message}")
        
        # Processa a mensagem usando a mesma lógica do webhook
        # generate_ai_response já inclui a lógica RAG e de conversação padrão
        response_text = generate_ai_response(user_message, "api_user")
        
        return jsonify({
            "status": "success",
            "user_message": user_message,
            "ai_response": response_text,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro no endpoint /api/chat: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Erro interno do servidor"}), 500
users_db = {}

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
        except:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(current_user_id, *args, **kwargs)
    return decorated

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password') or not data.get('name'):
            return jsonify({'error': 'Nome, email e senha são obrigatórios'}), 400
        
        email = data['email']
        password = data['password']
        name = data['name']
        
        # Verificar se usuário já existe
        if email in users_db:
            return jsonify({'error': 'Usuário já existe'}), 400
        
        # Criar novo usuário
        user_id = len(users_db) + 1
        users_db[email] = {
            'id': user_id,
            'name': name,
            'email': email,
            'password': generate_password_hash(password)
        }
        
        # Gerar token
        token = jwt.encode({
            'user_id': user_id,
            'email': email,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user_id,
                'name': name,
                'email': email
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Erro no registro: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email e senha são obrigatórios'}), 400
        
        email = data['email']
        password = data['password']
        
        # Verificar se usuário existe
        if email not in users_db:
            return jsonify({'error': 'Credenciais inválidas'}), 401
        
        user = users_db[email]
        
        # Verificar senha
        if not check_password_hash(user['password'], password):
            return jsonify({'error': 'Credenciais inválidas'}), 401
        
        # Gerar token
        token = jwt.encode({
            'user_id': user['id'],
            'email': email,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro no login: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/auth/verify', methods=['GET'])
@token_required
def verify_token(current_user_id):
    try:
        # Encontrar usuário pelo ID
        user = None
        for email, user_data in users_db.items():
            if user_data['id'] == current_user_id:
                user = user_data
                break
        
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na verificação do token: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
# --- FIM DAS ROTAS DA API ---

# --- MAIN EXECUTION BLOCK ---
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    logger.info(f"Iniciando WhatsApp AI Agent na porta {port} (Debug: {debug})")
    logger.info(f"🧠 Sistema RAG: {'✅ Ativado' if RAG_ENABLED else '❌ Desativado'}")
    app.run(host='0.0.0.0', port=port, debug=debug)