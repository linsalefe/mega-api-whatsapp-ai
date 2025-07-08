#!/usr/bin/env python3
"""
WhatsApp AI Agent - Aplicação principal
Integração com MEGA API para automação de WhatsApp
Refatorado com LangChain para gerenciamento de IA e memória.
"""

import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import logging
import threading

# LangChain Imports
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate

# Carrega variáveis do .env
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', # Adicionado %(name)s para melhor debug
    handlers=[
        logging.FileHandler('whatsapp_agent.log'), # Para salvar logs em arquivo
        logging.StreamHandler() # Para exibir logs no terminal
    ]
)
logger = logging.getLogger(__name__)

# Configurações da aplicação Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Configurações das APIs (carregadas do .env)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MEGA_API_BASE_URL = os.getenv('MEGA_API_BASE_URL')
MEGA_API_TOKEN = os.getenv('MEGA_API_TOKEN')
MEGA_INSTANCE_ID = os.getenv('MEGA_INSTANCE_ID') # Carrega o ID da instância

# Validação de variáveis de ambiente obrigatórias
required_vars = ['SECRET_KEY', 'OPENAI_API_KEY', 'MEGA_API_BASE_URL', 'MEGA_API_TOKEN', 'MEGA_INSTANCE_ID']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    logger.error(f"Variáveis de ambiente obrigatórias não encontradas: {missing_vars}")
    logger.error("Certifique-se de que seu arquivo .env está configurado corretamente com a URL correta da MEGA API e o ID da instância.")
    exit(1) # Sai do programa se as variáveis essenciais não estiverem configuradas

# Configuração do LangChain LLM (ChatOpenAI)
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model="gpt-3.5-turbo", # Ou "gpt-4" se preferir e tiver acesso
    temperature=0.7 # Criatividade da resposta
)

# Template de prompt personalizado para a IA
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
            return_messages=False
        )
        logger.info(f"Nova memória criada para o usuário: {user_id}")
    return user_memories[user_id]

def get_conversation_chain(user_id):
    """Cria uma cadeia de conversa para o usuário específico"""
    memory = get_user_memory(user_id)
    return ConversationChain(
        llm=llm,
        memory=memory,
        prompt=prompt_template,
        verbose=True
    )

def generate_ai_response(message_text: str, user_id: str) -> str:
    """
    Gera uma resposta da IA usando o LangChain com base na mensagem do usuário.
    """
    try:
        logger.info(f"Gerando resposta IA para a mensagem de '{user_id}': '{message_text[:100]}...'")
        
        # O prompt já foi definido globalmente na conversation chain.
        # A mensagem do usuário será passada como 'input'.
        conversation = get_conversation_chain(user_id) # Usa a memória específica do usuário
        response = conversation.predict(input=message_text)
        
        logger.info(f"Resposta da IA gerada para '{user_id}': '{response[:100]}...'")
        return response
        
    except Exception as e:
        logger.error(f"Erro ao gerar resposta da IA para '{user_id}': {e}", exc_info=True)
        return "Desculpe, não consegui gerar uma resposta no momento. Por favor, tente novamente mais tarde."

def send_whatsapp_message(phone_number: str, message: str) -> bool:
    """
    Envia uma mensagem de texto para um número de WhatsApp via MEGA API.
    """
    try:
        # CONSTRUÇÃO DA URL CORRETA COM BASE NA DOCUMENTAÇÃO
        url = f"{MEGA_API_BASE_URL}/rest/sendMessage/{MEGA_INSTANCE_ID}/text"
        
        headers = {
            'Authorization': f'Bearer {MEGA_API_TOKEN}', # ✅ CORREÇÃO APLICADA AQUI! (Token -> Bearer)
            'Content-Type': 'application/json'
        }
        
        # ESTRUTURA DO PAYLOAD CORRETA COM BASE NA DOCUMENTAÇÃO
        # A MEGA API espera o JID (e.g., '551199999999@s.whatsapp.net') no campo 'to'
        # Seu código webhook já extrai o 'remoteJid' completo.
        # Vamos garantir que ele esteja no formato correto, adicionando o sufixo se necessário.
        formatted_phone_number = phone_number
        if not ("@s.whatsapp.net" in phone_number or "@g.us" in phone_number):
             formatted_phone_number = f"{phone_number}@s.whatsapp.net" # Assume que é um número individual
        
        payload = {
            "messageData": {
                "to": formatted_phone_number, 
                "text": message
            }
        }
        
        logger.info(f"Tentando enviar mensagem para {formatted_phone_number} via MEGA API (URL: {url})")
        logger.debug(f"Payload: {payload}")
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        # A MEGA API pode retornar 200 OK mesmo com erros lógicos.
        # Por isso, verificamos o status HTTP e também o campo 'error' no JSON de resposta.
        response.raise_for_status() # Isso levantará um erro para status 4xx/5xx

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
    
    Args:
        phone_full_jid (str): O JID completo do remetente (e.g., '551199999999@s.whatsapp.net').
        message_text (str): O conteúdo da mensagem de texto.
        sender_name (str): O nome de exibição do remetente.
    """
    try:
        logger.info(f"Iniciando processamento assíncrono da mensagem de {sender_name} ({phone_full_jid}).")
        
        # O user_id para a memória deve ser consistente. Usamos o JID completo ou o número limpo.
        # Usar o número limpo para consistência com o LangChain memory
        user_id_for_memory = phone_full_jid.replace('@s.whatsapp.net', '').replace('@g.us', '')
        
        # 1. Gerar resposta com IA
        ai_response = generate_ai_response(message_text, user_id_for_memory)
        
        # 2. Enviar resposta de volta ao usuário via MEGA API
        success = send_whatsapp_message(phone_full_jid, ai_response) # Envia para o JID completo
        
        if success:
            logger.info(f"Resposta da IA enviada com sucesso para {phone_full_jid}.")
        else:
            logger.error(f"Falha ao enviar a resposta da IA para {phone_full_jid}.")
            
    except Exception as e:
        logger.error(f"Erro no processamento assíncrono da mensagem: {e}", exc_info=True)

# Esta função `process_webhook_async` foi corrigida e está incluída para robustez,
# caso seja chamada por algum outro fluxo ou em versões anteriores do código.
# A rota principal `/webhook` continua chamando `process_message_async`.
def process_webhook_async_corrected_for_logs(data):
    """
    Processa webhook de forma assíncrona. Esta versão é mais robusta
    na forma como extrai os dados do payload da MEGA API.
    Utilizada para fins de depuração e compatibilidade com logs anteriores.
    
    Args:
        data (dict): Dados do webhook recebidos.
    """
    try:
        # Extrair informações da mensagem diretamente do payload
        message_type = data.get('messageType')
        message_content = None

        # Tentar extrair o conteúdo da mensagem de texto
        if message_type == 'conversation':
            message_content = data.get('message', {}).get('conversation')
        elif message_type == 'textMessage': # Algumas APIs podem usar 'textMessage'
            message_content = data.get('message', {}).get('text')
        # Adicione outros tipos de mensagem se precisar processá-los (e.g., image, video)

        is_from_me = data.get('key', {}).get('fromMe', False) # Ignora mensagens enviadas pelo próprio bot

        # Se não for uma mensagem de texto válida, ou não tiver conteúdo, ou for do próprio bot, ignorar
        if not message_content or is_from_me:
            logger.info(f"Webhook (process_webhook_async_corrected_for_logs) ignorado (messageType: {message_type}, fromMe: {is_from_me}, hasContent: {bool(message_content)})")
            return

        sender_full_jid = data.get('key', {}).get('remoteJid', '') # Ex: '558388046720@s.whatsapp.net'
        sender_name = data.get('pushName', 'Usuário') # Nome de exibição do remetente
        
        if not sender_full_jid:
            logger.warning("JID do remetente não encontrado no webhook.")
            return

        # Para a memória do LangChain, usamos o ID do usuário (o número, sem o sufixo)
        user_id_for_memory = sender_full_jid.replace('@s.whatsapp.net', '').replace('@g.us', '')
        
        logger.info(f"Processando mensagem (process_webhook_async_corrected_for_logs) de {sender_name} ({user_id_for_memory}): '{message_content}'")
        
        # Gerar resposta com IA
        ai_response = generate_ai_response(message_content, user_id_for_memory)
        
        # Enviar resposta de volta ao usuário via MEGA API
        success = send_whatsapp_message(sender_full_jid, ai_response)
        
        if success:
            logger.info(f"✅ Resposta da IA enviada com sucesso para {sender_full_jid}.")
        else:
            logger.error(f"❌ Falha ao enviar a resposta da IA para {sender_full_jid}.")
            
    except Exception as e:
        logger.error(f"Erro no processamento assíncrono do webhook (process_webhook_async_corrected_for_logs): {e}", exc_info=True)


@app.route('/')
def home():
    """Endpoint de teste para verificar se o Flask está rodando."""
    return jsonify({
        "status": "success",
        "message": "WhatsApp AI Agent está rodando!",
        "version": "1.0",
        "current_time_utc": "08/07/2025 14:15:08 (UTC)",
        "current_time_brasília": "08/07/2025 11:15:08 (UTC-3)"
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
        
        # Verifica se o payload é um evento de mensagem de texto válido para processamento de IA
        # A estrutura pode variar um pouco, ajuste conforme a doc da MEGA API
        if (data and 
            data.get('messageType') == 'conversation' and # Tipo de mensagem de texto simples
            data.get('message', {}).get('conversation') and # Conteúdo da mensagem
            data.get('key', {}).get('remoteJid') and # Número do remetente
            not data.get('key', {}).get('fromMe', False)): # Ignora mensagens enviadas pelo próprio bot (evita loop)
            
            # Extrai informações da mensagem
            phone_full_jid = data['key']['remoteJid'] # JID completo para enviar a resposta
            message_text = data['message']['conversation']
            sender_name = data.get('pushName', 'Usuário') # Nome de exibição do remetente
            
            logger.info(f"Mensagem de texto válida recebida de {sender_name} ({phone_full_jid}): '{message_text}'")
            
            # Inicia o processamento da mensagem em uma nova thread.
            # Isso é crucial para que o webhook responda rapidamente (200 OK) e não expire,
            # enquanto o processamento da IA e o envio da resposta acontecem em segundo plano.
            thread = threading.Thread(
                target=process_message_async, # Chama a função principal de processamento de IA
                args=(phone_full_jid, message_text, sender_name)
            )
            thread.start()
            
            return jsonify({"status": "received", "message": "Mensagem recebida e em processamento"}), 200
        
        # Se não for uma mensagem de texto válida ou for um 'message.ack' ou outro tipo de evento
        else:
            logger.info(f"Webhook ignorado (não é uma mensagem de texto para processamento de IA ou é uma mensagem própria): {data.get('messageType', 'Tipo Desconhecido')}")
            # Para outros tipos de webhooks (como 'message.ack' ou outros eventos), podemos processá-los aqui
            # se houver necessidade, ou simplesmente retornar 200 OK para a API.
            # Ex: thread = threading.Thread(target=process_webhook_async_corrected_for_logs, args=(data,))
            # thread.start()
            return jsonify({"status": "ignored", "message": "Payload não é uma mensagem de texto para processamento de IA ou é uma mensagem própria."}), 200
            
    except Exception as e:
        logger.error(f"Erro inesperado no webhook: {e}", exc_info=True) # exc_info=True para logar o traceback completo
        return jsonify({"status": "error", "message": "Erro interno no servidor de webhook."}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint para verificação de saúde da aplicação e conectividade com a MEGA API.
    """
    mega_api_status = "disconnected"
    mega_api_response_detail = "N/A"
    try:
        # Tenta fazer uma requisição simples à URL base da MEGA API ou a um endpoint de status.
        # Isso verifica se a MEGA API está acessível pela rede.
        # Use o endpoint que a documentação da MEGA API sugere para health check, se houver.
        # Caso contrário, uma tentativa de conexão à URL base é um bom indicativo.
        test_url = f"{MEGA_API_BASE_URL}/rest/instance/{MEGA_INSTANCE_ID}/status" # Exemplo de endpoint de status
        headers = {
            'Authorization': f'Bearer {MEGA_API_TOKEN}' # ✅ CORREÇÃO APLICADA AQUI! (Token -> Bearer)
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

    return jsonify({
        "status": "healthy",
        "flask_app": "running",
        "mega_api_connectivity": mega_api_status,
        "mega_api_response_detail": mega_api_response_detail
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
    
    # Adicionar o sufixo @s.whatsapp.net se não estiver presente
    if not ("@s.whatsapp.net" in test_phone or "@g.us" in test_phone):
        test_phone_formatted = f"{test_phone}@s.whatsapp.net"
    else:
        test_phone_formatted = test_phone

    success = send_whatsapp_message(test_phone_formatted, test_message)

    if success:
        return jsonify({"status": "success", "message": f"Mensagem de teste enviada para {test_phone}"}), 200
    else:
        return jsonify({"status": "error", "message": f"Falha ao enviar mensagem de teste para {test_phone}"}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Iniciando WhatsApp AI Agent na porta {port} (Debug: {debug})")
    app.run(host='0.0.0.0', port=port, debug=debug)
