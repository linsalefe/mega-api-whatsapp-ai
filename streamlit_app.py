import streamlit as st
import os
from datetime import datetime
import json

# Configuração da página
st.set_page_config(
    page_title="WhatsApp AI Agent - RAG System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado com paleta azul e branco
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Reset e configurações globais */
    .main {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Header principal */
    .main-header {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #60a5fa 100%);
        padding: 2rem 0;
        margin: -1rem -1rem 2rem -1rem;
        text-align: center;
        border-radius: 0 0 20px 20px;
        box-shadow: 0 8px 32px rgba(30, 64, 175, 0.3);
    }
    
    .main-title {
        color: white;
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        letter-spacing: -0.02em;
    }
    
    .main-subtitle {
        color: #dbeafe;
        font-size: 1.2rem;
        font-weight: 400;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    /* Cards e containers */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(30, 64, 175, 0.1);
        border: 1px solid #e2e8f0;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(30, 64, 175, 0.15);
    }
    
    .feature-card {
        background: linear-gradient(135deg, white 0%, #f8fafc 100%);
        padding: 2rem;
        border-radius: 20px;
        border: 2px solid #e2e8f0;
        margin: 1rem 0;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        border-color: #3b82f6;
        transform: translateY(-3px);
        box-shadow: 0 10px 40px rgba(59, 130, 246, 0.2);
    }
    
    /* Títulos e textos */
    .section-title {
        color: #1e40af;
        font-size: 2rem;
        font-weight: 600;
        margin: 2rem 0 1rem 0;
        text-align: center;
        position: relative;
    }
    
    .section-title::after {
        content: '';
        position: absolute;
        bottom: -8px;
        left: 50%;
        transform: translateX(-50%);
        width: 60px;
        height: 3px;
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
        border-radius: 2px;
    }
    
    .card-title {
        color: #1e40af;
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .card-subtitle {
        color: #64748b;
        font-size: 1rem;
        font-weight: 400;
        line-height: 1.6;
    }
    
    /* Métricas */
    .metric-value {
        color: #1e40af;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .metric-label {
        color: #64748b;
        font-size: 0.9rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.5rem;
    }
    
    /* Ícones e emojis */
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        display: block;
    }
    
    /* Sidebar customização */
    .css-1d391kg {
        background: linear-gradient(180deg, #1e40af 0%, #3b82f6 100%);
    }
    
    .css-1d391kg .css-1v0mbdj {
        color: white;
    }
    
    /* Botões */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
    }
    
    /* Alertas e notificações */
    .stAlert {
        border-radius: 12px;
        border: none;
        font-family: 'Inter', sans-serif;
    }
    
    /* Status indicators */
    .status-online {
        color: #10b981;
        font-weight: 600;
    }
    
    .status-offline {
        color: #ef4444;
        font-weight: 600;
    }
    
    /* Responsividade */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2rem;
        }
        
        .section-title {
            font-size: 1.5rem;
        }
        
        .feature-card {
            padding: 1.5rem;
        }
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
    
    .fade-in {
        animation: fadeInUp 0.6s ease-out;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header principal
    st.markdown("""
    <div class="main-header fade-in">
        <h1 class="main-title">🤖 WhatsApp AI Agent</h1>
        <p class="main-subtitle">Sistema RAG Inteligente para Atendimento Automatizado</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar para navegação
    with st.sidebar:
        st.markdown("### 🎯 Navegação")
        page = st.selectbox(
            "Escolha uma seção:",
            ["🏠 Dashboard", "�� Documentos", "🤖 Agente IA", "📊 Analytics", "⚙️ Configurações"]
        )
    
    # Conteúdo principal baseado na página selecionada
    if page == "🏠 Dashboard":
        dashboard_page()
    elif page == "�� Documentos":
        documents_page()
    elif page == "🤖 Agente IA":
        agent_page()
    elif page == "�� Analytics":
        analytics_page()
    elif page == "⚙️ Configurações":
        settings_page()

def dashboard_page():
    st.markdown('<h2 class="section-title fade-in">📊 Dashboard Principal</h2>', unsafe_allow_html=True)
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card fade-in">
            <div class="metric-value">156</div>
            <div class="metric-label">Conversas Hoje</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card fade-in">
            <div class="metric-value">98.5%</div>
            <div class="metric-label">Taxa de Sucesso</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card fade-in">
            <div class="metric-value">2.3s</div>
            <div class="metric-label">Tempo Resposta</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card fade-in">
            <div class="metric-value status-online">●</div>
            <div class="metric-label">Status Sistema</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Status do sistema
    st.markdown('<h3 class="section-title">🔧 Status do Sistema</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card fade-in">
            <span class="feature-icon">🟢</span>
            <h3 class="card-title">WhatsApp API</h3>
            <p class="card-subtitle">Conectado e funcionando perfeitamente</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card fade-in">
            <span class="feature-icon">🟢</span>
            <h3 class="card-title">Sistema RAG</h3>
            <p class="card-subtitle">Base de conhecimento atualizada</p>
        </div>
        """, unsafe_allow_html=True)

def documents_page():
    st.markdown('<h2 class="section-title fade-in">�� Gerenciamento de Documentos</h2>', unsafe_allow_html=True)
    
    # Upload de arquivos
    st.markdown("""
    <div class="feature-card fade-in">
        <span class="feature-icon">📤</span>
        <h3 class="card-title">Upload de Documentos</h3>
        <p class="card-subtitle">Adicione novos documentos à base de conhecimento</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Escolha os arquivos",
        type=['pdf', 'txt', 'docx'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} arquivo(s) carregado(s) com sucesso!")
        
        for file in uploaded_files:
            st.markdown(f"""
            <div class="metric-card">
                <div class="card-title">📄 {file.name}</div>
                <div class="card-subtitle">Tamanho: {file.size} bytes</div>
            </div>
            """, unsafe_allow_html=True)

def agent_page():
    st.markdown('<h2 class="section-title fade-in">🤖 Configuração do Agente IA</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card fade-in">
            <span class="feature-icon">🎯</span>
            <h3 class="card-title">Personalidade</h3>
            <p class="card-subtitle">Configure o tom e estilo do agente</p>
        </div>
        """, unsafe_allow_html=True)
        
        personality = st.selectbox(
            "Escolha a personalidade:",
            ["Profissional", "Amigável", "Técnico", "Casual"]
        )
    
    with col2:
        st.markdown("""
        <div class="feature-card fade-in">
            <span class="feature-icon">⚡</span>
            <h3 class="card-title">Modelo IA</h3>
            <p class="card-subtitle">Selecione o modelo de linguagem</p>
        </div>
        """, unsafe_allow_html=True)
        
        model = st.selectbox(
            "Modelo:",
            ["GPT-4", "Claude-3", "Gemini Pro"]
        )

def analytics_page():
    st.markdown('<h2 class="section-title fade-in">�� Analytics e Relatórios</h2>', unsafe_allow_html=True)
    
    # Gráficos de exemplo (placeholder)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card fade-in">
            <span class="feature-icon">📈</span>
            <h3 class="card-title">Conversas por Hora</h3>
            <p class="card-subtitle">Distribuição de conversas ao longo do dia</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card fade-in">
            <span class="feature-icon">🎯</span>
            <h3 class="card-title">Taxa de Resolução</h3>
            <p class="card-subtitle">Percentual de problemas resolvidos automaticamente</p>
        </div>
        """, unsafe_allow_html=True)

def settings_page():
    st.markdown('<h2 class="section-title fade-in">⚙️ Configurações do Sistema</h2>', unsafe_allow_html=True)
    
    # Configurações da API
    st.markdown("""
    <div class="feature-card fade-in">
        <span class="feature-icon">🔐</span>
        <h3 class="card-title">Configurações da API</h3>
        <p class="card-subtitle">Configure as chaves e tokens de acesso</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("🔑 Chaves de API"):
        openai_key = st.text_input("OpenAI API Key", type="password")
        whatsapp_token = st.text_input("WhatsApp Token", type="password")
        
        if st.button("💾 Salvar Configurações"):
            st.success("✅ Configurações salvas com sucesso!")

if __name__ == "__main__":
    main()