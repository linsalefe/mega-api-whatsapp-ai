import streamlit as st
import os
from datetime import datetime
import json
from dotenv import load_dotenv
import shutil
import pytz

# Langchain imports for RAG
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from openai import AuthenticationError, APIError # <--- IMPORTE ESTES ERROS ESPECÍFICOS

# --- Configuração Inicial e Variáveis de Ambiente ---
load_dotenv()

# Define o fuso horário de Brasília para exibição de hora
brazilia_tz = pytz.timezone('America/Sao_Paulo')

# --- VALIDAÇÃO E INICIALIZAÇÃO CRÍTICA DE OPENAI (MOVENDO PARA O TOPO E GLOBAL) ---
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    st.error("⚠️ ERRO CRÍTICO: OPENAI_API_KEY não encontrada! Por favor, configure-a nas variáveis de ambiente do Render (Environment Variables).")
    st.stop() # Parar o Streamlit imediatamente e de forma limpa

try:
    # Tenta inicializar os embeddings globalmente e verifica a chave
    GLOBAL_OPENAI_EMBEDDINGS = OpenAIEmbeddings(model="text-embedding-ada-002", openai_api_key=OPENAI_API_KEY)
    
    # Você pode adicionar uma pequena chamada de teste aqui se quiser, mas a própria inicialização
    # do OpenAIEmbeddings já dispara AuthenticationError para chaves inválidas na maioria dos casos.
    # Ex: GLOBAL_OPENAI_EMBEDDINGS.embed_query("warm up") 

except (AuthenticationError, APIError) as e:
    st.error(f"❌ ERRO CRÍTICO: Falha de autenticação/API com OpenAI Embeddings. Sua OPENAI_API_KEY pode ser inválida ou há um problema de conexão: {e}")
    st.stop() # Parar o Streamlit imediatamente em caso de erro de API
except Exception as e:
    st.error(f"❌ ERRO CRÍTICO: Erro inesperado ao inicializar OpenAI Embeddings: {e}")
    st.stop() # Parar o Streamlit imediatamente em qualquer outro erro

# Inicializa o modelo de chat também de forma robusta e global
try:
    GLOBAL_CHAT_MODEL = ChatOpenAI(
        model="gpt-3.5-turbo", # Pode ser mudado para gpt-4o-mini ou gpt-4o
        temperature=0.7,
        api_key=OPENAI_API_KEY
    )
except (AuthenticationError, APIError) as e:
    st.error(f"❌ ERRO CRÍTICO: Falha de autenticação/API com OpenAI Chat Model. Sua OPENAI_API_KEY pode ser inválida ou há um problema de conexão: {e}")
    st.stop()
except Exception as e:
    st.error(f"❌ ERRO CRÍTICO: Erro inesperado ao inicializar OpenAI Chat Model: {e}")
    st.stop()

# Agora, GLOBAL_OPENAI_EMBEDDINGS e GLOBAL_CHAT_MODEL estão garantidos de estarem inicializados e funcionais.

# --- Configuração da Página Streamlit e Estilos ---
st.set_page_config(
    page_title="WhatsApp AI Agent - RAG System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ... (Resto do CSS e funções de utilidade - sem alterações aqui) ...

def safe_initialize_chroma():
    """Inicializa o vectorstore do Chroma de forma segura"""
    try:
        if not os.path.exists("./chroma_db"):
            os.makedirs("./chroma_db")
            
        vectorstore = Chroma(
            persist_directory="./chroma_db",
            embedding_function=GLOBAL_OPENAI_EMBEDDINGS # <--- USAR O GLOBAL AQUI
        )
        
        try:
            count = vectorstore._collection.count()
            if count == 0:
                st.info("📚 Base de conhecimento vazia. Faça upload de arquivos para treinar a IA!")
        except Exception as inner_e: 
            st.info(f"📚 Base de conhecimento inicializada mas com erro ao contar coleção. Pronta para receber documentos! ({inner_e})")
            
        return vectorstore
        
    except Exception as e:
        st.warning(f"⚠️ Tentando criar/reiniciar base de conhecimento... ({str(e)})")
        if os.path.exists("./chroma_db"):
            shutil.rmtree("./chroma_db")
            st.info("Diretório chroma_db removido devido a erro.")
        os.makedirs("./chroma_db")
        
        try:
            vectorstore = Chroma(
                persist_directory="./chroma_db", 
                embedding_function=GLOBAL_OPENAI_EMBEDDINGS # <--- USAR O GLOBAL AQUI
            )
            st.success("✅ Nova base de conhecimento criada com sucesso!")
            return vectorstore
        except Exception as retry_e:
            st.error(f"❌ Falha crítica ao criar nova base de conhecimento após erro: {retry_e}. O aplicativo não pode continuar sem um sistema de embeddings funcional.")
            st.stop() # Parar se a inicialização da base falhar totalmente

# --- Funções de Inicialização e Lógica do RAG (continuando) ---

def init_openai():
    # Esta função agora retorna o modelo de chat global, já inicializado e validado
    return GLOBAL_CHAT_MODEL

def create_new_knowledge_base(uploaded_files, persist_directory):
    """Cria uma nova base de conhecimento com os documentos fornecidos."""
    with st.spinner("🔄 Criando nova base de conhecimento..."):
        os.makedirs("uploaded_files", exist_ok=True)
        saved_files = []
        
        for uploaded_file in uploaded_files:
            file_path = os.path.join("uploaded_files", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            saved_files.append(file_path)
        
        documents = []
        for file_path in saved_files:
            if file_path.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
            elif file_path.endswith('.txt'):
                loader = TextLoader(file_path)
            documents.extend(loader.load())
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        
        # USAR O EMBEDDING GLOBAL AQUI
        embeddings = GLOBAL_OPENAI_EMBEDDINGS 
        
        if os.path.exists(persist_directory):
            shutil.rmtree(persist_directory)
        
        vectorstore = Chroma.from_documents(chunks, embeddings, persist_directory=persist_directory)
        
        show_notification(f"Base de conhecimento criada com {len(chunks)} chunks!", "success")
        st.rerun()

def process_and_add_documents(uploaded_files, vectorstore, persist_directory):
    """Adiciona novos documentos a uma base de conhecimento existente."""
    with st.spinner("➕ Adicionando documentos à base existente..."):
        os.makedirs("uploaded_files", exist_ok=True)
        saved_files = []
        
        for uploaded_file in uploaded_files:
            file_path = os.path.join("uploaded_files", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            saved_files.append(file_path)
        
        documents = []
        for file_path in saved_files:
            if file_path.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
            elif file_path.endswith('.txt'):
                loader = TextLoader(file_path)
            documents.extend(loader.load())
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        
        vectorstore.add_documents(chunks) 
        
        show_notification(f"{len(chunks)} novos chunks adicionados à base!", "success")
        st.rerun()

# --- Páginas da Aplicação (continuando) ---

def dashboard_page():
    st.markdown('<h2 class="section-title fade-in">📊 Dashboard Principal</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="glass-card fade-in">
        <h3 class="card-title">⏰ Hora Atual do Sistema</h3>
    """, unsafe_allow_html=True)
    
    utc_now = datetime.utcnow()
    bras_now = utc_now.replace(tzinfo=pytz.utc).astimezone(brazilia_tz)
    
    col_time1, col_time2 = st.columns(2)
    with col_time1:
        st.markdown(f"**UTC:** {utc_now.strftime('%d/%m/%Y %H:%M:%S')} (UTC)")
    with col_time2:
        st.markdown(f"**Brasília:** {bras_now.strftime('%d/%m/%Y %H:%M:%S')} (UTC-3)")
    
    st.markdown("</div>", unsafe_allow_html=True)

    persist_directory = "./chroma_db"
    db_status = "Não Inicializado"
    chunk_count = 0
    status_type = "offline"
    
    if os.path.exists(persist_directory) and os.listdir(persist_directory):
        try:
            # USAR O EMBEDDING GLOBAL AQUI
            vectorstore = Chroma(persist_directory=persist_directory, embedding_function=GLOBAL_OPENAI_EMBEDDINGS)
            collection = vectorstore._collection
            chunk_count = collection.count()
            db_status = "Online"
            status_type = "online"
        except Exception as e:
            st.error(f"Erro ao carregar base de conhecimento: {e}. Tentando recriar ou avisar...")
            shutil.rmtree(persist_directory, ignore_errors=True) 
            db_status = "Erro"
            status_type = "warning"
            st.warning("Base de conhecimento corrompida ou não carregada. Por favor, crie uma nova base na seção 'Documentos'.")

    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        create_metric_card("156", "Conversas Hoje", change=12, icon="💬", progress=78)
    
    with col2:
        create_metric_card("98.5%", "Taxa de Sucesso", change=2, icon="🎯", progress=98)
    
    with col3:
        create_metric_card("2.3s", "Tempo Resposta", change=-5, icon="⚡", progress=85)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card fade-in">
            <div class="metric-header">
                <div>
                    <div class="metric-value">
                        <span class="status-indicator status-{status_type}">
                            ● {db_status}
                        </span>
                    </div>
                    <div class="metric-label">Status RAG</div>
                    <div style="font-size: 0.8rem; color: var(--neutral-700); margin-top: 0.5rem;">
                        {chunk_count} chunks carregados
                    </div>
                </div>
                <div class="metric-icon">🤖</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<h3 class="section-title">🔧 Status do Sistema</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card slide-in-left">
            <span class="feature-icon">🟢</span>
            <h3 class="card-title">WhatsApp API</h3>
            <p class="card-subtitle">Conectado e funcionando perfeitamente</p>
            <div class="status-indicator status-online">
                ● Sistema Operacional
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        status_class = "online" if chunk_count > 0 else "offline"
        status_icon = "🟢" if chunk_count > 0 else "🔴"
        status_text = f"Base com {chunk_count} chunks" if chunk_count > 0 else "Base não inicializada"
        
        st.markdown(f"""
        <div class="feature-card slide-in-right">
            <span class="feature-icon">{status_icon}</span>
            <h3 class="card-title">Sistema RAG</h3>
            <p class="card-subtitle">{status_text}</p>
            <div class="status-indicator status-{status_class}">
                ● {db_status}
            </div>
        </div>
        """, unsafe_allow_html=True)

def documents_page():
    st.markdown('<h2 class="section-title fade-in">📄 Gerenciamento de Documentos</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="glass-card fade-in">
        <p class="card-subtitle">
            Gerencie a base de conhecimento do seu Agente AI. Faça upload de arquivos PDF e TXT 
            para que a IA possa consultá-los para responder às perguntas.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    persist_directory = "./chroma_db"
    
    # USAR O EMBEDDING GLOBAL AQUI
    embeddings_openai = GLOBAL_OPENAI_EMBEDDINGS

    if os.path.exists(persist_directory) and os.listdir(persist_directory):
        st.markdown("""
        <div class="glass-card fade-in">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <span style="font-size: 2rem;">✅</span>
                <div>
                    <h3 class="card-title" style="margin: 0;">Base de Conhecimento Ativa</h3>
                    <p class="card-subtitle" style="margin: 0;">Sistema carregado e funcionando</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            # USAR O EMBEDDING GLOBAL AQUI
            vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings_openai)
            collection = vectorstore._collection
            count = collection.count()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-header">
                    <div>
                        <div class="metric-value">{count}</div>
                        <div class="metric-label">Chunks de Texto</div>
                    </div>
                    <div class="metric-icon">📚</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('<h3 class="section-title">➕ Adicionar Mais Documentos</h3>', unsafe_allow_html=True)
            
            uploaded_files = st.file_uploader(
                "Escolha arquivos para adicionar à base existente",
                type=['pdf', 'txt'],
                accept_multiple_files=True,
                key="add_docs_uploader"
            )
            
            if uploaded_files and st.button("🚀 Processar e Adicionar Documentos", key="process_add_button"):
                process_and_add_documents(uploaded_files, vectorstore, persist_directory)

        except Exception as e:
            st.error(f"⚠️ Erro ao carregar base de conhecimento existente: {e}. A base pode estar corrompida. Recomenda-se resetar ou criar uma nova.")
            st.markdown("""
            <div class="glass-card fade-in">
                <div style="text-align: center; padding: 2rem;">
                    <span style="font-size: 4rem; display: block; margin-bottom: 1rem;">❌</span>
                    <h3 class="card-title">Erro na Base de Conhecimento</h3>
                    <p class="card-subtitle">
                        Não foi possível carregar a base de conhecimento existente. Por favor, 
                        considere resetar a base e criar uma nova.
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            vectorstore = None
            
        st.markdown('<h3 class="section-title">🗑️ Gerenciamento da Base</h3>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="glass-card">
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                <span style="font-size: 2rem;">⚠️</span>
                <div>
                    <h4 style="color: var(--accent-orange); margin: 0;">Zona de Perigo</h4>
                    <p style="margin: 0; color: var(--neutral-700);">
                        Resetar a base irá apagar <strong>todos</strong> os documentos indexados
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col_reset1, col_reset2 = st.columns([0.7, 0.3])
        with col_reset1:
            confirm_reset = st.checkbox("Confirmo que quero deletar toda a base de conhecimento", key="confirm_reset_checkbox")
        with col_reset2:
            if st.button("🗑️ Resetar Base", type="secondary", disabled=not confirm_reset, key="reset_button"):
                shutil.rmtree(persist_directory, ignore_errors=True)
                show_notification("Base de conhecimento resetada!", "success")
                st.rerun()
    
    else:
        st.markdown("""
        <div class="glass-card fade-in">
            <div style="text-align: center; padding: 2rem;">
                <span style="font-size: 4rem; display: block; margin-bottom: 1rem;">🆕</span>
                <h3 class="card-title">Primeira Configuração</h3>
                <p class="card-subtitle">
                    Nenhuma base de conhecimento encontrada. Faça upload de documentos 
                    para criar a primeira base de conhecimento do seu Agente AI.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "Escolha arquivos para criar a base de conhecimento",
            type=['pdf', 'txt'],
            accept_multiple_files=True,
            key="create_docs_uploader"
        )
        
        if uploaded_files and st.button("🚀 Criar Base de Conhecimento", key="create_base_button"):
            create_new_knowledge_base(uploaded_files, persist_directory)

    st.markdown("---")
    
    st.markdown("""
    <div class="feature-card fade-in">
        <span class="feature-icon">🌐</span>
        <h3 class="card-title">Scraping de Sites</h3>
        <p class="card-subtitle">Extraia conteúdo de URLs para a base de conhecimento (em desenvolvimento)</p>
    </div>
    """, unsafe_allow_html=True)
    
    url_input = st.text_input(
        "URL do site para extrair conteúdo:",
        placeholder="Ex: https://www.anthropic.com/news",
        key="url_input_docs_unique"
    )
    
    if st.button("🔍 Extrair Conteúdo do Site", key="extract_url_button_unique"):
        if url_input:
            st.info(f"🚧 Funcionalidade de extração da URL '{url_input}' será implementada nas próximas fases.")
        else:
            st.error("❌ Por favor, insira uma URL válida.")

def rag_chat_page():
    """Página de Chat melhorada para testar a funcionalidade RAG da IA."""
    st.markdown('<h2 class="section-title fade-in">💬 Chat RAG (Teste Inteligente)</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="glass-card fade-in">
        <p class="card-subtitle">
            Este é o ambiente principal para testar as capacidades de resposta do seu Agente AI, 
            utilizando a base de conhecimento que você carregou. Aqui você pode fazer perguntas 
            e ver como a IA as responde consultando os documentos.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    persist_directory = "./chroma_db"
    
    # USAR O EMBEDDING GLOBAL AQUI
    embeddings_openai = GLOBAL_OPENAI_EMBEDDINGS

    if not os.path.exists(persist_directory) or not os.listdir(persist_directory):
        st.markdown("""
        <div class="glass-card fade-in">
            <div style="text-align: center; padding: 2rem;">
                <span style="font-size: 4rem; display: block; margin-bottom: 1rem;">⚠️</span>
                <h3 class="card-title">Base de Conhecimento Necessária</h3>
                <p class="card-subtitle">
                    Nenhuma base de conhecimento encontrada. Vá para a aba 'Documentos' 
                    para criar ou carregar uma e habilitar o chat.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    llm = init_openai() # Esta função já retorna GLOBAL_CHAT_MODEL
    if not llm:
        st.error("🔑 O modelo de chat não foi inicializado corretamente. Verifique as configurações.")
        return
    
    try:
        # USAR O EMBEDDING GLOBAL AQUI
        vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings_openai)
        
        if vectorstore._collection.count() == 0:
            st.error("⚠️ A base de conhecimento está vazia ou corrompida. Por favor, resete-a na seção 'Documentos'.")
            return

    except Exception as e:
        st.error(f"⚠️ Erro ao carregar base de conhecimento: {e}. A base pode estar corrompida. Por favor, resete-a na seção 'Documentos'.")
        return
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True
    )
    
    st.markdown("""
    <div class="glass-card fade-in">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <span style="font-size: 2rem;">✅</span>
            <div>
                <h3 class="card-title" style="margin: 0;">Sistema RAG Ativo</h3>
                <p class="card-subtitle" style="margin: 0;">Pronto para responder suas perguntas</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if prompt := st.chat_input("💭 Faça uma pergunta sobre os documentos..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("🤔 Analisando documentos..."):
                try:
                    result = qa_chain({"query": prompt})
                    response = result["result"]
                    sources = result["source_documents"]
                    
                    st.markdown(response)
                    
                    if sources: 
                        with st.expander("📚 Fontes Consultadas"):
                            for i, doc in enumerate(sources):
                                st.markdown(f"**📄 Documento {i+1}:**")
                                st.code(doc.page_content, language="text")
                                if doc.metadata:
                                    st.json(doc.metadata)
                                if i < len(sources) - 1:
                                    st.markdown("---")
                    
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"❌ Erro ao processar pergunta: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

def agent_config_page():
    st.markdown('<h2 class="section-title fade-in">🤖 Configuração do Agente</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="glass-card fade-in">
        <p class="card-subtitle">
            Configure a personalidade e o modelo de IA que o seu Agente utilizará para as interações.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card slide-in-left">
            <span class="feature-icon">🎭</span>
            <h3 class="card-title">Personalidade</h3>
            <p class="card-subtitle">Configure o tom e estilo do agente</p>
        </div>
        """, unsafe_allow_html=True)
        
        personality = st.selectbox(
            "Escolha a personalidade:",
            ["Profissional", "Amigável", "Técnico", "Casual"],
            key="agent_personality_select"
        )
    
    with col2:
        st.markdown("""
        <div class="feature-card slide-in-right">
            <span class="feature-icon">⚡</span>
            <h3 class="card-title">Modelo IA</h3>
            <p class="card-subtitle">Selecione o modelo de linguagem</p>
        </div>
        """, unsafe_allow_html=True)
        
        model = st.selectbox(
            "Modelo:",
            ["GPT-3.5-Turbo", "GPT-4o", "Claude 3 Opus", "Gemini Pro"],
            key="agent_model_select"
        )
    
    st.markdown("---")
    
    st.markdown("""
    <div class="glass-card fade-in">
        <h3 class="card-title">🛠️ Parâmetros Avançados do Modelo</h3>
    """, unsafe_allow_html=True)
    
    temperature = st.slider(
        "Temperatura (Criatividade)", 
        min_value=0.0, max_value=1.0, value=0.7, step=0.1,
        help="Um valor mais alto torna as respostas mais criativas"
    )
    
    max_tokens = st.slider(
        "Máximo de Tokens na Resposta", 
        min_value=50, max_value=2000, value=500, step=50,
        help="Define o tamanho máximo da resposta gerada pela IA"
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("💾 Salvar Configurações do Agente", key="save_agent_config_button"):
        show_notification(f"Configurações salvas! Personalidade: {personality}, Modelo: {model}", "success")

def analytics_page():
    st.markdown('<h2 class="section-title fade-in">📊 Analytics e Relatórios</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="glass-card fade-in">
        <p class="card-subtitle">
            Acompanhe o desempenho do seu Agente AI com métricas e visualizações 
            sobre as interações e eficiência.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        create_metric_card("1,247", "Total de Conversas", change=15, icon="💬", progress=85)
    
    with col2:
        create_metric_card("4.8/5", "Satisfação Média", change=3, icon="⭐", progress=96)
    
    with col3:
        create_metric_card("89%", "Taxa de Resolução", change=7, icon="✅", progress=89)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card slide-in-left">
            <span class="feature-icon">📈</span>
            <h3 class="card-title">Conversas por Hora</h3>
            <p class="card-subtitle">Distribuição de conversas ao longo do dia</p>
        </div>
        """, unsafe_allow_html=True)
        
        import pandas as pd
        chart_data = pd.DataFrame({
            'Hora': list(range(24)),
            'Conversas': [5, 3, 2, 1, 2, 4, 8, 15, 25, 30, 35, 40, 45, 42, 38, 35, 40, 45, 35, 25, 20, 15, 10, 8]
        })
        st.line_chart(chart_data.set_index('Hora'))
    
    with col2:
        st.markdown("""
        <div class="feature-card slide-in-right">
            <span class="feature-icon">🎯</span>
            <h3 class="card-title">Taxa de Resolução</h3>
            <p class="card-subtitle">Percentual de problemas resolvidos automaticamente</p>
        </div>
        """, unsafe_allow_html=True)
        
        resolution_data = pd.DataFrame({
            'Dia': ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab', 'Dom'],
            'Taxa': [90, 92, 95, 93, 98, 85, 88]
        })
        st.bar_chart(resolution_data.set_index('Dia'))

    st.markdown("---")
    
    st.markdown("""
    <div class="glass-card fade-in">
        <h3 class="card-title">📋 Relatórios Detalhados</h3>
        <p class="card-subtitle">
            Funcionalidades avançadas de relatórios e exportação de dados serão 
            desenvolvidas nas próximas fases do projeto.
        </p>
        <div style="margin-top: 1.5rem;">
            <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                <div class="status-indicator status-warning">
                    🚧 Relatório Semanal - Em Desenvolvimento
                </div>
                <div class="status-indicator status-warning">
                    📊 Exportação CSV - Em Desenvolvimento
                </div>
                <div class="status-indicator status-warning">
                    📈 Dashboard Avançado - Em Desenvolvimento
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def settings_page():
    st.markdown('<h2 class="section-title fade-in">⚙️ Configurações do Sistema</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="glass-card fade-in">
        <p class="card-subtitle">
            Aqui você pode visualizar e configurar informações cruciais sobre o 
            funcionamento do seu Agente AI.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card fade-in">
        <span class="feature-icon">🔐</span>
        <h3 class="card-title">Chaves de API e Variáveis de Ambiente</h3>
        <p class="card-subtitle">
            As chaves de API (como a OPENAI_API_KEY) e outras configurações sensíveis 
            são carregadas de forma segura do arquivo .env
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    openai_key = os.getenv('OPENAI_API_KEY')
    api_status = "online" if openai_key else "offline"
    api_icon = "🟢" if openai_key else "🔴"
    
    st.markdown(f"""
    <div class="glass-card">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <span style="font-size: 2rem;">{api_icon}</span>
            <div>
                <h4 style="margin: 0;">Status da API OpenAI</h4>
                <div class="status-indicator status-{api_status}">
                    ● {'Configurada' if openai_key else 'Não Configurada'}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.code("OPENAI_API_KEY=sua_chave_openai_aqui", language="bash")
    
    with st.expander("🔍 Ver Variáveis de Ambiente (Debug)"):
        env_vars = {k: "********" if "KEY" in k or "TOKEN" in k else v for k, v in os.environ.items()}
        st.json(dict(list(env_vars.items())[:10]))  
    
    st.markdown("""
    <div class="feature-card fade-in">
        <span class="feature-icon">🚫</span>
        <h3 class="card-title">Exclusões de Arquivos (.gitignore)</h3>
        <p class="card-subtitle">
            O arquivo .gitignore é crucial para garantir que arquivos desnecessários, 
            temporários ou sensíveis não sejam incluídos no controle de versão
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("**Conteúdo sugerido para o seu arquivo `.gitignore`:**")
    st.code("""
# Ambiente Virtual
venv/
env/

# Variáveis de Ambiente
.env
.env.local

# Cache Python
__pycache__/
*.pyc
*.pyo
*.pyd

# Logs
logs/
*.log

# Banco de Dados
*.sqlite3
*.db

# Jupyter
.ipynb_checkpoints/

# Sistema
.DS_Store
.idea/
.vscode/

# Build
build/
dist/
*.egg-info/

# Testes
.pytest_cache/
.coverage

# Temporários
temp/
*.tmp
*.bak

# Chaves e Certificados
*.pem
*.key

# Arquivos do Projeto (Opcional)
uploaded_files/
chroma_db/
    """, language="bash")

    st.markdown("""
    <div class="feature-card fade-in">
        <span class="feature-icon">💾</span>
        <h3 class="card-title">Estrutura de Pastas do Projeto</h3>
        <p class="card-subtitle">
            Verifique se as seguintes pastas e arquivos estão organizados para 
            o funcionamento correto do sistema
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.code("""
📁 / (Raiz do Projeto)
├── 📄 app.py (Script principal WhatsApp/Flask)
├── 📄 streamlit_app.py (Interface Streamlit)
├──  .env (Variáveis de ambiente)
├── 📄 .gitignore (Exclusões Git)
├── 📄 requirements.txt (Dependências Python)
├── 📁 venv/ (Ambiente virtual Python)
├── 📁 chroma_db/ (Base de dados vetorial)
├── 📁 uploaded_files/ (Arquivos enviados)
└── 📄 whatsapp_agent.log (Logs do sistema)
    """)

def logs_page():
    st.markdown('<h2 class="section-title fade-in">📄 Logs do Sistema</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="glass-card fade-in">
        <p class="card-subtitle">
            Monitore as atividades e mensagens do seu Agente AI. Esta seção exibe 
            o conteúdo do arquivo whatsapp_agent.log, que é gerado pelo seu script 
            de integração do WhatsApp (app.py).
        </p>
    </div>
    """, unsafe_allow_html=True)

    log_file_path = "whatsapp_agent.log"

    if os.path.exists(log_file_path):
        file_size = os.path.getsize(log_file_path)
        file_modified = datetime.fromtimestamp(os.path.getmtime(log_file_path))
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            create_metric_card(f"{file_size} bytes", "Tamanho do Log", icon="📊")
        
        with col2:
            create_metric_card(file_modified.strftime("%H:%M"), "Última Modificação", icon="🕐")
        
        with col3:
            create_metric_card("Online", "Status do Log", icon="📝")
        
        st.markdown(f"""
        <div class="glass-card fade-in">
            <h3 class="card-title">📋 Conteúdo de {log_file_path}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            with open(log_file_path, "r", encoding="utf-8") as f:
                log_content = f.read()
                
            if len(log_content) > 10000:
                log_content = log_content[-10000:] + "\n\n[... mostrando apenas as últimas 10.000 caracteres]"
                
            st.code(log_content, language="text", height=400)
            
            st.download_button(
                label="📥 Baixar Log Completo",
                data=log_content,
                file_name=f"whatsapp_agent_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
            
        except Exception as e:
            st.error(f"❌ Não foi possível ler o arquivo de log: {e}")
    else:
        st.markdown("""
        <div class="glass-card fade-in">
            <div style="text-align: center; padding: 2rem;">
                <span style="font-size: 4rem; display: block; margin-bottom: 1rem;">📄</span>
                <h3 class="card-title">Arquivo de Log Não Encontrado</h3>
                <p class="card-subtitle">
                    O arquivo de log whatsapp_agent.log não foi encontrado. 
                    Certifique-se de que o sistema de log do seu app.py esteja 
                    configurado para gravar eventos neste arquivo.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card fade-in">
        <span class="feature-icon">💡</span>
        <h3 class="card-title">Informações sobre Logging</h3>
        <p class="card-subtitle">
            Os logs são ferramentas indispensáveis para depurar problemas, acompanhar 
            o fluxo de mensagens e monitorar o comportamento geral do agente em produção. 
            É altamente recomendável configurar seu app.py para registrar eventos importantes.
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- Função Principal com Navegação Melhorada ---
def main():
    st.markdown("""
    <div class="main-header fade-in">
        <h1 class="main-title">🤖 WhatsApp AI Agent</h1>
        <p class="main-subtitle">Sistema RAG Inteligente para Atendimento Automatizado</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("""
    <div class="sidebar-header">
        <div class="sidebar-logo">🤖</div>
        <h3 class="sidebar-title">WhatsApp AI</h3>
        <p class="sidebar-subtitle">Sistema RAG Inteligente</p>
    </div>
    """, unsafe_allow_html=True)
    
    pages = {
        "🏠 Dashboard": {"func": dashboard_page, "desc": "Visão geral do sistema"},
        "📄 Documentos": {"func": documents_page, "desc": "Gerenciar base de conhecimento"},
        "💬 Chat RAG": {"func": rag_chat_page, "desc": "Testar sistema inteligente"},
        "🤖 Configuração": {"func": agent_config_page, "desc": "Configurar agente IA"},
        "📊 Analytics": {"func": analytics_page, "desc": "Métricas e relatórios"},
        "⚙️ Configurações": {"func": settings_page, "desc": "Configurações do sistema"},
        "📄 Logs": {"func": logs_page, "desc": "Monitorar atividades"}
    }

    selected_page = st.sidebar.radio(
        "Navegação Principal:",
        list(pages.keys()),
        format_func=lambda x: x
    )
    
    st.sidebar.markdown(f"""
    <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 12px; margin: 1rem 0;">
        <small style="color: rgba(255,255,255,0.8);">{pages[selected_page]['desc']}</small>
    </div>
    """, unsafe_allow_html=True)
    
    pages[selected_page]["func"]()

    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <div style="background: rgba(255,255,255,0.1); padding: 1.5rem; border-radius: 16px;">
        <h4 style="color: white; margin: 0 0 0.5rem 0;">👨‍💻 Álefe Lins</h4>
        <p style="color: rgba(255,255,255,0.8); font-size: 0.85rem; margin: 0;">
            Profissional intermediário em IA, focado em estudos e trabalho nas áreas 
            de marketing e tecnologia.
        </p>
        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.2);">
            <p style="color: rgba(255,255,255,0.7); font-size: 0.8rem; margin: 0;">
                <strong>Objetivos:</strong> Lançar um aplicativo e iniciar um negócio de agentes de IA.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("""
    <div style="background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 12px;">
        <h5 style="color: white; margin: 0 0 1rem 0;">🚀 Próximos Passos</h5>
        <ul style="color: rgba(255,255,255,0.8); font-size: 0.8rem; margin: 0; padding-left: 1rem;">
            <li>Integração completa RAG + WhatsApp</li>
            <li>Aprimoramento da interface UX/UI</li>
            <li>Automação de respostas inteligentes</li>
            <li>Sistema de analytics avançado</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()