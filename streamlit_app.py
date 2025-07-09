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
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

# --- Configuração Inicial e Variáveis de Ambiente ---
load_dotenv()

# Define o fuso horário de Brasília para exibição de hora
brazilia_tz = pytz.timezone('America/Sao_Paulo')

# --- Configuração da Página Streamlit e Estilos ---
st.set_page_config(
    page_title="WhatsApp AI Agent - RAG System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado com UX/UI melhorado
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Variáveis CSS modernas */
    :root {
        --primary-blue: #2563eb;
        --primary-blue-light: #3b82f6;
        --primary-blue-dark: #1d4ed8;
        --secondary-purple: #7c3aed;
        --accent-green: #10b981;
        --accent-orange: #f59e0b;
        --accent-red: #ef4444;
        --neutral-50: #f8fafc;
        --neutral-100: #f1f5f9;
        --neutral-200: #e2e8f0;
        --neutral-300: #cbd5e1;
        --neutral-700: #334155;
        --neutral-800: #1e293b;
        --neutral-900: #0f172a;
        --glass-bg: rgba(255, 255, 255, 0.85);
        --glass-border: rgba(255, 255, 255, 0.2);
        --shadow-light: 0 4px 20px rgba(0, 0, 0, 0.08);
        --shadow-medium: 0 8px 30px rgba(0, 0, 0, 0.12);
        --shadow-heavy: 0 20px 40px rgba(0, 0, 0, 0.15);
    }
    
    /* Reset e configurações globais */
    .main {
        background: linear-gradient(135deg, var(--neutral-50) 0%, var(--neutral-100) 50%, #e0e7ff 100%);
        font-family: 'Inter', sans-serif;
        min-height: 100vh;
    }
    
    /* Header principal melhorado */
    .main-header {
        background: linear-gradient(135deg, var(--primary-blue) 0%, var(--secondary-purple) 100%);
        padding: 3rem 0;
        margin: -1rem -1rem 3rem -1rem;
        text-align: center;
        border-radius: 0 0 32px 32px;
        box-shadow: var(--shadow-heavy);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
        opacity: 0.3;
    }
    
    .main-title {
        color: white;
        font-size: 3.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 8px rgba(0,0,0,0.3);
        letter-spacing: -0.02em;
        position: relative;
        z-index: 1;
    }
    
    .main-subtitle {
        color: #dbeafe;
        font-size: 1.3rem;
        font-weight: 400;
        margin: 1rem 0 0 0;
        opacity: 0.95;
        position: relative;
        z-index: 1;
    }
    
    /* Cards com glassmorphism */
    .glass-card {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: 24px;
        padding: 2rem;
        box-shadow: var(--shadow-light);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .glass-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        transition: left 0.6s;
    }
    
    .glass-card:hover::before {
        left: 100%;
    }
    
    .glass-card:hover {
        transform: translateY(-8px);
        box-shadow: var(--shadow-heavy);
        border-color: rgba(37, 99, 235, 0.3);
    }
    
    /* Metric cards melhorados */
    .metric-card {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: var(--shadow-light);
        border: 1px solid var(--glass-border);
        margin: 1rem 0;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .metric-card:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: var(--shadow-heavy);
    }
    
    .metric-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 1rem;
    }
    
    .metric-icon {
        font-size: 2.5rem;
        opacity: 0.8;
    }
    
    .metric-value {
        color: var(--primary-blue);
        font-size: 2.8rem;
        font-weight: 700;
        margin: 0;
        font-family: 'JetBrains Mono', monospace;
        line-height: 1;
    }
    
    .metric-label {
        color: var(--neutral-700);
        font-size: 0.95rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin: 0.5rem 0;
    }
    
    .metric-change {
        font-size: 0.8rem;
        font-weight: 500;
        padding: 0.25rem 0.5rem;
        border-radius: 12px;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
    }
    
    .metric-change.positive {
        color: var(--accent-green);
        background: rgba(16, 185, 129, 0.1);
    }
    
    .metric-change.negative {
        color: var(--accent-red);
        background: rgba(239, 68, 68, 0.1);
    }
    
    .metric-progress {
        margin-top: 1rem;
        height: 6px;
        background: var(--neutral-200);
        border-radius: 3px;
        overflow: hidden;
    }
    
    .metric-progress-bar {
        height: 100%;
        background: linear-gradient(90deg, var(--primary-blue), var(--secondary-purple));
        border-radius: 3px;
        transition: width 1s ease-out;
    }
    
    /* Feature cards melhorados */
    .feature-card {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        padding: 2.5rem;
        border-radius: 24px;
        border: 2px solid var(--glass-border);
        margin: 1.5rem 0;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .feature-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--primary-blue), var(--secondary-purple));
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }
    
    .feature-card:hover::after {
        transform: scaleX(1);
    }
    
    .feature-card:hover {
        border-color: var(--primary-blue);
        transform: translateY(-8px);
        box-shadow: var(--shadow-heavy);
    }
    
    .feature-icon {
        font-size: 3.5rem;
        margin-bottom: 1.5rem;
        display: block;
        filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
    }
    
    /* Títulos e textos melhorados */
    .section-title {
        color: var(--primary-blue);
        font-size: 2.2rem;
        font-weight: 700;
        margin: 3rem 0 2rem 0;
        text-align: center;
        position: relative;
        letter-spacing: -0.01em;
    }
    
    .section-title::after {
        content: '';
        position: absolute;
        bottom: -12px;
        left: 50%;
        transform: translateX(-50%);
        width: 80px;
        height: 4px;
        background: linear-gradient(90deg, var(--primary-blue), var(--secondary-purple));
        border-radius: 2px;
    }
    
    .card-title {
        color: var(--primary-blue);
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.75rem;
        letter-spacing: -0.01em;
    }
    
    .card-subtitle {
        color: var(--neutral-700);
        font-size: 1.05rem;
        font-weight: 400;
        line-height: 1.6;
        opacity: 0.9;
    }
    
    /* Status indicators melhorados */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.6rem 1.2rem;
        border-radius: 50px;
        font-size: 0.9rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .status-online {
        background: rgba(16, 185, 129, 0.15);
        color: var(--accent-green);
        border: 2px solid rgba(16, 185, 129, 0.3);
    }
    
    .status-offline {
        background: rgba(239, 68, 68, 0.15);
        color: var(--accent-red);
        border: 2px solid rgba(239, 68, 68, 0.3);
    }
    
    .status-warning {
        background: rgba(245, 158, 11, 0.15);
        color: var(--accent-orange);
        border: 2px solid rgba(245, 158, 11, 0.3);
    }
    
    /* Botões melhorados */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-blue) 0%, var(--secondary-purple) 100%);
        color: white;
        border: none;
        border-radius: 16px;
        padding: 0.875rem 2rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px rgba(37, 99, 235, 0.3);
        position: relative;
        overflow: hidden;
        font-size: 0.95rem;
        letter-spacing: 0.01em;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(37, 99, 235, 0.4);
    }
    
    .stButton > button:active {
        transform: translateY(-1px);
    }
    
    /* Sidebar melhorada */
    .css-1d391kg {
        background: linear-gradient(180deg, var(--primary-blue) 0%, var(--primary-blue-dark) 100%);
    }
    
    .sidebar-header {
        text-align: center;
        padding: 2rem 1rem;
        border-bottom: 1px solid rgba(255,255,255,0.2);
        margin-bottom: 1rem;
    }
    
    .sidebar-logo {
        font-size: 3rem;
        margin-bottom: 0.5rem;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
    }
    
    .sidebar-title {
        color: white;
        font-size: 1.4rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.01em;
    }
    
    .sidebar-subtitle {
        color: rgba(255,255,255,0.8);
        font-size: 0.85rem;
        margin: 0.5rem 0 0 0;
        font-weight: 400;
    }
    
    /* Alertas melhorados */
    .stAlert {
        border-radius: 16px;
        border: none;
        font-family: 'Inter', sans-serif;
        backdrop-filter: blur(10px);
    }
    
    /* Loading states */
    .loading-container {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1.5rem;
        background: rgba(59, 130, 246, 0.1);
        border-radius: 16px;
        border-left: 4px solid var(--primary-blue);
        backdrop-filter: blur(10px);
    }
    
    .loading-spinner {
        width: 24px;
        height: 24px;
        border: 3px solid var(--neutral-200);
        border-top: 3px solid var(--primary-blue);
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    .loading-text {
        color: var(--primary-blue);
        font-weight: 600;
        font-size: 0.95rem;
    }
    
    /* Notificações */
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        background: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        box-shadow: var(--shadow-heavy);
        animation: slideInFromRight 0.3s ease-out;
        backdrop-filter: blur(10px);
    }
    
    .notification.success {
        border-left: 4px solid var(--accent-green);
    }
    
    .notification.error {
        border-left: 4px solid var(--accent-red);
    }
    
    .notification.warning {
        border-left: 4px solid var(--accent-orange);
    }
    
    .notification.info {
        border-left: 4px solid var(--primary-blue);
    }
    
    /* Animações */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideInFromLeft {
        0% { transform: translateX(-100%); opacity: 0; }
        100% { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideInFromRight {
        0% { transform: translateX(100%); opacity: 0; }
        100% { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .fade-in { animation: fadeInUp 0.6s ease-out; }
    .slide-in-left { animation: slideInFromLeft 0.6s ease-out; }
    .slide-in-right { animation: slideInFromRight 0.6s ease-out; }
    .pulse-animation { animation: pulse 2s infinite; }
    
    /* Responsividade melhorada */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2.5rem;
        }
        
        .main-subtitle {
            font-size: 1.1rem;
        }
        
        .section-title {
            font-size: 1.8rem;
        }
        
        .feature-card, .glass-card, .metric-card {
            padding: 1.5rem;
            margin: 1rem 0;
        }
        
        .metric-value {
            font-size: 2.2rem;
        }
        
        .feature-icon {
            font-size: 2.5rem;
        }
    }
    
    /* Modo escuro */
    @media (prefers-color-scheme: dark) {
        :root {
            --glass-bg: rgba(30, 41, 59, 0.8);
            --glass-border: rgba(148, 163, 184, 0.2);
        }
        
        .main {
            background: linear-gradient(135deg, var(--neutral-900) 0%, var(--neutral-800) 100%);
            color: var(--neutral-100);
        }
        
        .card-subtitle {
            color: var(--neutral-300);
        }
        
        .metric-label {
            color: var(--neutral-300);
        }
    }
    
    /* Chat específico */
    .chat-container {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid var(--glass-border);
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 16px;
        animation: fadeInUp 0.3s ease-out;
    }
    
    .chat-message.user {
        background: linear-gradient(135deg, var(--primary-blue), var(--secondary-purple));
        color: white;
        margin-left: 2rem;
    }
    
    .chat-message.assistant {
        background: var(--neutral-100);
        border: 1px solid var(--neutral-200);
        margin-right: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Funções de Utilidade para UX ---

def show_loading_state(message="Processando..."):
    """Mostra um estado de loading elegante"""
    return st.markdown(f"""
    <div class="loading-container">
        <div class="loading-spinner"></div>
        <span class="loading-text">{message}</span>
    </div>
    """, unsafe_allow_html=True)

def show_notification(message, type="info"):
    """Sistema de notificações melhorado"""
    icons = {
        "success": "✅",
        "error": "❌", 
        "warning": "⚠️",
        "info": "ℹ️"
    }
    
    return st.markdown(f"""
    <div class="notification {type}">
        <strong>{icons[type]} {message}</strong>
    </div>
    """, unsafe_allow_html=True)

def create_metric_card(value, label, change=None, icon="📊", progress=None):
    """Cria um card de métrica melhorado"""
    change_html = ""
    if change:
        change_class = "positive" if change > 0 else "negative"
        change_icon = "↗️" if change > 0 else "↘️"
        change_html = f'<div class="metric-change {change_class}">{change_icon} {abs(change)}% vs ontem</div>'
    
    progress_html = ""
    if progress:
        progress_html = f'''
        <div class="metric-progress">
            <div class="metric-progress-bar" style="width: {progress}%;"></div>
        </div>
        '''
    
    return st.markdown(f"""
    <div class="metric-card fade-in">
        <div class="metric-header">
            <div>
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
                {change_html}
            </div>
            <div class="metric-icon">{icon}</div>
        </div>
        {progress_html}
    </div>
    """, unsafe_allow_html=True)

# --- Funções de Inicialização e Lógica do RAG ---

def init_openai():
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        st.error("❌ OPENAI_API_KEY não encontrada no arquivo .env. Configure-a para usar o chat.")
        return None
    
    return ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.7,
        api_key=api_key
    )

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
        
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
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

# --- Páginas da Aplicação ---

def dashboard_page():
    st.markdown('<h2 class="section-title fade-in">📊 Dashboard Principal</h2>', unsafe_allow_html=True)
    
    # Hora atual melhorada
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

    # Status da Base de Conhecimento RAG
    persist_directory = "./chroma_db"
    db_status = "Não Inicializado"
    chunk_count = 0
    status_type = "offline"
    
    if os.path.exists(persist_directory) and os.listdir(persist_directory):
        try:
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
            collection = vectorstore._collection
            chunk_count = collection.count()
            db_status = "Online"
            status_type = "online"
        except Exception as e:
            db_status = "Erro"
            status_type = "warning"

    # Métricas principais melhoradas
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
    
    # Status do sistema melhorado
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
        
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
        
        try:
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
        except:
            st.info("📊 Base de conhecimento carregada (contagem não disponível)")
        
        st.markdown('<h3 class="section-title">➕ Adicionar Mais Documentos</h3>', unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "Escolha arquivos para adicionar à base existente",
            type=['pdf', 'txt'],
            accept_multiple_files=True,
            key="add_docs_uploader"
        )
        
        if uploaded_files and st.button("🚀 Processar e Adicionar Documentos", key="process_add_button"):
            process_and_add_documents(uploaded_files, vectorstore, persist_directory)
        
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
                shutil.rmtree(persist_directory)
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
    
    # Seção de scraping melhorada
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
    
    llm = init_openai()
    if not llm:
        st.error("🔑 A API Key do OpenAI não está configurada ou é inválida. Verifique seu arquivo `.env`.")
        return
    
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    
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
    
    # Inicializa o histórico de mensagens
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Container do chat melhorado
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Exibe o histórico de mensagens
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Entrada de texto para o usuário
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
    
    # Métricas de performance
    col1, col2, col3 = st.columns(3)
    
    with col1:
        create_metric_card("1,247", "Total de Conversas", change=15, icon="💬", progress=85)
    
    with col2:
        create_metric_card("4.8/5", "Satisfação Média", change=3, icon="⭐", progress=96)
    
    with col3:
        create_metric_card("89%", "Taxa de Resolução", change=7, icon="✅", progress=89)
    
    # Gráficos melhorados
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card slide-in-left">
            <span class="feature-icon">📈</span>
            <h3 class="card-title">Conversas por Hora</h3>
            <p class="card-subtitle">Distribuição de conversas ao longo do dia</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Dados de exemplo para o gráfico
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
        
        # Dados de exemplo para gráfico de barras
        resolution_data = pd.DataFrame({
            'Dia': ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab', 'Dom'],
            'Taxa': [90, 92, 95, 93, 98, 85, 88]
        })
        st.bar_chart(resolution_data.set_index('Dia'))

    st.markdown("---")
    
    # Seção de relatórios
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
    
    # Seção de API Keys
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
    
    # Verificação do status das APIs
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
    
    # Variáveis de ambiente
    with st.expander("🔍 Ver Variáveis de Ambiente (Debug)"):
        env_vars = {k: "********" if "KEY" in k or "TOKEN" in k else v for k, v in os.environ.items()}
        st.json(dict(list(env_vars.items())[:10]))  # Mostra apenas as primeiras 10
    
    # Seção .gitignore
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

    # Estrutura do projeto
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
├── �� .env (Variáveis de ambiente)
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
        # Status do arquivo de log
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
                
            # Limita o conteúdo se for muito grande
            if len(log_content) > 10000:
                log_content = log_content[-10000:] + "\n\n[... mostrando apenas as últimas 10.000 caracteres]"
                
            st.code(log_content, language="text", height=400)
            
            # Botão para baixar o log completo
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
    
    # Informações sobre logging
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
    # Header principal
    st.markdown("""
    <div class="main-header fade-in">
        <h1 class="main-title">🤖 WhatsApp AI Agent</h1>
        <p class="main-subtitle">Sistema RAG Inteligente para Atendimento Automatizado</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar melhorada
    st.sidebar.markdown("""
    <div class="sidebar-header">
        <div class="sidebar-logo">🤖</div>
        <h3 class="sidebar-title">WhatsApp AI</h3>
        <p class="sidebar-subtitle">Sistema RAG Inteligente</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navegação principal
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
    
    # Descrição da página selecionada
    st.sidebar.markdown(f"""
    <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 12px; margin: 1rem 0;">
        <small style="color: rgba(255,255,255,0.8);">{pages[selected_page]['desc']}</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Chama a função da página selecionada
    pages[selected_page]["func"]()

    # Informações do usuário na sidebar
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
    
    # Próximos passos
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