import streamlit as st
import os
from datetime import datetime
import json

# Configuração da página
st.set_page_config(
    page_title="WhatsApp AI Agent - CENAT",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para melhorar a aparência
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header principal
    st.markdown('<h1 class="main-header">🤖 WhatsApp AI Agent - RAG System</h1>', unsafe_allow_html=True)
    
    # Sidebar para navegação
    with st.sidebar:
        st.image("https://via.placeholder.com/200x100/1f77b4/ffffff?text=AI+Agent", width=200)
        st.markdown("### 📋 Painel de Controle")
        
        page = st.selectbox(
            "Escolha uma seção:",
            ["🏠 Dashboard", "📄 Gerenciar Documentos", "🔧 Configurações", "💬 Chat de Teste", "📊 Analytics"]
        )
        
        st.markdown("---")
        st.markdown("### 📈 Status do Sistema")
        st.markdown('<p class="status-success">✅ Sistema Online</p>', unsafe_allow_html=True)
        st.markdown('<p class="status-success">✅ WhatsApp Conectado</p>', unsafe_allow_html=True)
        st.markdown('<p class="status-warning">⚠️ RAG em Configuração</p>', unsafe_allow_html=True)

    # Conteúdo principal baseado na seleção
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "📄 Gerenciar Documentos":
        show_document_manager()
    elif page == "🔧 Configurações":
        show_settings()
    elif page == "💬 Chat de Teste":
        show_chat_test()
    elif page == "📊 Analytics":
        show_analytics()

def show_dashboard():
    st.markdown("## �� Dashboard Principal")
    
    # Métricas em colunas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📱 Mensagens Hoje",
            value="127",
            delta="12"
        )
    
    with col2:
        st.metric(
            label="📄 Documentos Ativos",
            value="8",
            delta="2"
        )
    
    with col3:
        st.metric(
            label="🤖 Respostas IA",
            value="89%",
            delta="5%"
        )
    
    with col4:
        st.metric(
            label="⚡ Tempo Resposta",
            value="2.3s",
            delta="-0.5s"
        )
    
    st.markdown("---")
    
    # Seções de funcionalidades
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-box">
            <h3>🚀 Funcionalidades Ativas</h3>
            <ul>
                <li>✅ WhatsApp Web Integration</li>
                <li>✅ OpenAI GPT Integration</li>
                <li>✅ Processamento de Texto</li>
                <li>🔄 RAG System (em desenvolvimento)</li>
                <li>🔄 Upload de Documentos</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-box">
            <h3>📋 Próximas Implementações</h3>
            <ul>
                <li>🔄 Upload de PDFs</li>
                <li>🔄 Scraping de Sites</li>
                <li>🔄 Base de Conhecimento</li>
                <li>🔄 Analytics Avançados</li>
                <li>🔄 Multi-agentes</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

def show_document_manager():
    st.markdown("## 📄 Gerenciador de Documentos")
    
    # Upload de arquivos
    st.markdown("### 📤 Upload de Documentos")
    
    uploaded_files = st.file_uploader(
        "Escolha os arquivos para treinar a IA:",
        type=['pdf', 'txt', 'docx'],
        accept_multiple_files=True,
        help="Formatos suportados: PDF, TXT, DOCX"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} arquivo(s) carregado(s)!")
        
        for file in uploaded_files:
            with st.expander(f"📄 {file.name}"):
                st.write(f"**Tamanho:** {file.size} bytes")
                st.write(f"**Tipo:** {file.type}")
                
                if st.button(f"Processar {file.name}", key=f"process_{file.name}"):
                    with st.spinner("Processando documento..."):
                        # Aqui será implementado o processamento RAG
                        st.success("✅ Documento processado e adicionado à base de conhecimento!")
    
    st.markdown("---")
    
    # URL Scraping
    st.markdown("### 🌐 Scraping de Sites")
    
    url_input = st.text_input(
        "URL do site para extrair conteúdo:",
        placeholder="https://exemplo.com"
    )
    
    if st.button("🔍 Extrair Conteúdo"):
        if url_input:
            with st.spinner("Extraindo conteúdo do site..."):
                # Aqui será implementado o scraping
                st.success("✅ Conteúdo extraído e processado!")
        else:
            st.error("❌ Por favor, insira uma URL válida")

def show_settings():
    st.markdown("## 🔧 Configurações do Sistema")
    
    # Configurações da IA
    with st.expander("🤖 Configurações da IA", expanded=True):
        model = st.selectbox(
            "Modelo OpenAI:",
            ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"]
        )
        
        temperature = st.slider(
            "Temperatura (Criatividade):",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1
        )
        
        max_tokens = st.number_input(
            "Máximo de Tokens:",
            min_value=100,
            max_value=4000,
            value=1000
        )
    
    # Configurações do WhatsApp
    with st.expander("📱 Configurações WhatsApp"):
        auto_reply = st.checkbox("Resposta Automática", value=True)
        response_delay = st.slider("Delay de Resposta (segundos):", 1, 10, 3)
        
        st.text_area(
            "Prompt do Sistema:",
            value="Você é um assistente inteligente integrado ao WhatsApp...",
            height=100
        )
    
    # Salvar configurações
    if st.button("💾 Salvar Configurações"):
        st.success("✅ Configurações salvas com sucesso!")

def show_chat_test():
    st.markdown("## 💬 Chat de Teste")
    
    st.info("🧪 Use esta seção para testar as respostas da IA antes de implementar no WhatsApp")
    
    # Histórico de chat
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Exibir mensagens
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Input do usuário
    if prompt := st.chat_input("Digite sua mensagem..."):
        # Adicionar mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Resposta da IA (simulada por enquanto)
        with st.chat_message("assistant"):
            response = f"🤖 Resposta simulada para: '{prompt}'"
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

def show_analytics():
    st.markdown("## 📊 Analytics e Métricas")
    
    # Gráficos simulados
    import pandas as pd
    import numpy as np
    
    # Dados simulados
    dates = pd.date_range('2024-01-01', periods=30, freq='D')
    messages_data = pd.DataFrame({
        'Data': dates,
        'Mensagens': np.random.randint(50, 200, 30),
        'Respostas IA': np.random.randint(40, 180, 30)
    })
    
    st.markdown("### 📈 Mensagens por Dia")
    st.line_chart(messages_data.set_index('Data'))
    
    st.markdown("### 📊 Distribuição de Tipos de Consulta")
    chart_data = pd.DataFrame({
        'Tipo': ['Informações Gerais', 'Suporte Técnico', 'Vendas', 'Outros'],
        'Quantidade': [45, 30, 15, 10]
    })
    st.bar_chart(chart_data.set_index('Tipo'))

if __name__ == "__main__":
    main()