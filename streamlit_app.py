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

# --- Configuração Inicial e Variáveis ---
load_dotenv()

# Configuração da página
st.set_page_config(
    page_title="MegaStart AI - Agente Inteligente",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurações
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("⚠️ OPENAI_API_KEY não encontrada! Verifique seu arquivo .env")
    st.stop()

# Timezone brasileiro
BRAZIL_TZ = pytz.timezone('America/Sao_Paulo')

# --- Funções Auxiliares ---

def get_current_time():
    """Retorna o horário atual no Brasil"""
    return datetime.now(BRAZIL_TZ).strftime("%d/%m/%Y %H:%M:%S")

def safe_initialize_chroma():
    """Inicializa o vectorstore do Chroma de forma segura"""
    try:
        # Garante que o diretório existe
        if not os.path.exists("./chroma_db"):
            os.makedirs("./chroma_db")
            
        vectorstore = Chroma(
            persist_directory="./chroma_db",
            embedding_function=OpenAIEmbeddings()
        )
        
        # Testa se a base está funcionando
        try:
            count = vectorstore._collection.count()
            if count == 0:
                st.info("📚 Base de conhecimento vazia. Faça upload de arquivos para treinar a IA!")
        except:
            st.info("📚 Base de conhecimento inicializada. Pronta para receber documentos!")
            
        return vectorstore
        
    except Exception as e:
        st.warning(f"⚠️ Criando nova base de conhecimento... ({str(e)})")
        # Remove diretório corrompido se existir
        if os.path.exists("./chroma_db"):
            shutil.rmtree("./chroma_db")
        os.makedirs("./chroma_db")
        
        vectorstore = Chroma(
            persist_directory="./chroma_db", 
            embedding_function=OpenAIEmbeddings()
        )
        return vectorstore

# Inicialização do session state
if 'vectorstore' not in st.session_state:
    st.session_state.vectorstore = safe_initialize_chroma()

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'documents_processed' not in st.session_state:
    st.session_state.documents_processed = []

def process_uploaded_files(uploaded_files):
    """Processa arquivos enviados e adiciona ao vectorstore"""
    if not uploaded_files:
        return False
    
    documents = []
    processed_files = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, uploaded_file in enumerate(uploaded_files):
        try:
            status_text.text(f"Processando: {uploaded_file.name}")
            
            # Salva arquivo temporariamente
            temp_path = f"./temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Carrega documento baseado na extensão
            if uploaded_file.name.endswith('.pdf'):
                loader = PyPDFLoader(temp_path)
            elif uploaded_file.name.endswith('.txt'):
                loader = TextLoader(temp_path)
            else:
                st.warning(f"Tipo de arquivo não suportado: {uploaded_file.name}")
                continue
            
            # Carrega e divide o documento
            docs = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            splits = text_splitter.split_documents(docs)
            
            # Adiciona metadados
            for split in splits:
                split.metadata['source'] = uploaded_file.name
                split.metadata['upload_time'] = get_current_time()
            
            documents.extend(splits)
            processed_files.append(uploaded_file.name)
            
            # Remove arquivo temporário
            os.remove(temp_path)
            
            # Atualiza progresso
            progress_bar.progress((i + 1) / len(uploaded_files))
            
        except Exception as e:
            st.error(f"Erro ao processar {uploaded_file.name}: {str(e)}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    # Adiciona documentos ao vectorstore
    if documents:
        try:
            st.session_state.vectorstore.add_documents(documents)
            st.session_state.documents_processed.extend(processed_files)
            status_text.text("✅ Processamento concluído!")
            return True
        except Exception as e:
            st.error(f"Erro ao adicionar documentos ao vectorstore: {str(e)}")
            return False
    
    return False

def get_rag_response(query, vectorstore):
    """Gera resposta usando RAG"""
    try:
        # Configura o retriever
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )
        
        # Configura o LLM
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=OPENAI_API_KEY
        )
        
        # Cria chain de QA
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )
        
        # Executa query
        result = qa_chain.invoke({"query": query})
        
        return {
            "answer": result["result"],
            "sources": [doc.metadata.get('source', 'Documento desconhecido') 
                       for doc in result["source_documents"]]
        }
        
    except Exception as e:
        st.error(f"Erro no RAG: {str(e)}")
        return None

def get_regular_response(query):
    """Gera resposta usando chat normal"""
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=OPENAI_API_KEY
        )
        
        response = llm.invoke(query)
        return response.content
        
    except Exception as e:
        st.error(f"Erro no chat: {str(e)}")
        return "Desculpe, ocorreu um erro ao processar sua mensagem."

def clear_knowledge_base():
    """Limpa a base de conhecimento"""
    try:
        if os.path.exists("./chroma_db"):
            shutil.rmtree("./chroma_db")
        
        st.session_state.vectorstore = safe_initialize_chroma()
        st.session_state.documents_processed = []
        st.success("🗑️ Base de conhecimento limpa com sucesso!")
        
    except Exception as e:
        st.error(f"Erro ao limpar base: {str(e)}")

# --- Interface Principal ---

def main():
    # Header customizado
    st.markdown("""
    <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 10px; margin-bottom: 2rem;">
        <h1 style="color: white; text-align: center; margin: 0;">
            🚀 MegaStart AI - Agente Inteligente
        </h1>
        <p style="color: rgba(255,255,255,0.8); text-align: center; margin: 0.5rem 0 0 0;">
            Powered by OpenAI GPT-4 + RAG System
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📚 Gestão de Conhecimento")
        
        # Upload de arquivos
        uploaded_files = st.file_uploader(
            "Envie seus documentos:",
            type=['pdf', 'txt'],
            accept_multiple_files=True,
            help="Formatos suportados: PDF, TXT"
        )
        
        if uploaded_files:
            if st.button("📤 Processar Arquivos", type="primary"):
                with st.spinner("Processando documentos..."):
                    if process_uploaded_files(uploaded_files):
                        st.success(f"✅ {len(uploaded_files)} arquivo(s) processado(s)!")
                        st.rerun()
        
        # Documentos processados
        if st.session_state.documents_processed:
            st.markdown("### 📄 Documentos Ativos")
            for doc in st.session_state.documents_processed:
                st.markdown(f"• {doc}")
        
        # Botão para limpar base
        if st.session_state.documents_processed:
            if st.button("🗑️ Limpar Base", type="secondary"):
                clear_knowledge_base()
                st.rerun()
        
        # Informações do sistema
        st.markdown("---")
        st.markdown("### ℹ️ Informações")
        st.markdown(f"**Horário:** {get_current_time()}")
        st.markdown(f"**Documentos:** {len(st.session_state.documents_processed)}")
        st.markdown(f"**Conversas:** {len(st.session_state.chat_history)}")
    
    # Chat Interface
    st.markdown("### 💬 Chat com IA")
    
    # Exibe histórico do chat
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "sources" in message:
                with st.expander("📚 Fontes utilizadas"):
                    for source in message["sources"]:
                        st.markdown(f"• {source}")
    
    # Input do usuário
    if prompt := st.chat_input("Digite sua mensagem..."):
        # Adiciona mensagem do usuário
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Gera resposta
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                # Verifica se deve usar RAG ou chat normal
                if st.session_state.documents_processed:
                    # Usa RAG se há documentos
                    rag_result = get_rag_response(prompt, st.session_state.vectorstore)
                    if rag_result:
                        st.markdown(rag_result["answer"])
                        
                        # Adiciona ao histórico com fontes
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": rag_result["answer"],
                            "sources": rag_result["sources"]
                        })
                        
                        # Mostra fontes
                        if rag_result["sources"]:
                            with st.expander("📚 Fontes utilizadas"):
                                for source in set(rag_result["sources"]):
                                    st.markdown(f"• {source}")
                    else:
                        # Fallback para chat normal
                        response = get_regular_response(prompt)
                        st.markdown(response)
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": response
                        })
                else:
                    # Chat normal se não há documentos
                    response = get_regular_response(prompt)
                    st.markdown(response)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response
                    })
    
    # Botão para limpar chat
    if st.session_state.chat_history:
        if st.button("🗑️ Limpar Conversa"):
            st.session_state.chat_history = []
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                padding: 1.5rem; border-radius: 10px; margin-top: 2rem;">
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