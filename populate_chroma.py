import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import logging
import shutil # Importar shutil para remover o diretório

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    logger.error("❌ OPENAI_API_KEY não encontrada. Certifique-se de que está configurada no .env")
    exit(1)

PERSIST_DIRECTORY = "./chroma_db"

def populate_chroma_db():
    logger.info("Iniciando o processo de popular o ChromaDB...")

    # --- SEUS DOCUMENTOS AQUI ---
    # Substitua este conteúdo pelos seus próprios textos, informações sobre seu app,
    # sua empresa, marketing e tecnologia. Quanto mais detalhado, melhor!
    docs_content = [
        "A Álefe Lins AI Solutions é uma empresa inovadora focada no desenvolvimento de agentes de inteligência artificial para otimização de marketing digital e automação de processos. Nosso objetivo é transformar a maneira como as empresas interagem com seus clientes, com foco em personalização e eficiência.",
        "Nosso principal produto, o 'AI Marketing Hub', será um aplicativo revolucionário que integra as últimas tendências em IA para análise de dados de campanhas, personalização de conteúdo, segmentação de público e otimização de funis de venda. Ele está previsto para ser lançado no final de 2025 e promete ser um divisor de águas no setor.",
        "Oferecemos consultoria especializada em implementação de IA e tecnologias de ponta para pequenas e médias empresas. Ajudamos a identificar oportunidades de automação, melhorar a performance de campanhas e integrar soluções de IA personalizadas. Nossos agentes são projetados para serem escaláveis e adaptáveis às necessidades específicas de cada cliente.",
        "Para iniciar um negócio de agentes de IA bem-sucedido, é crucial realizar uma pesquisa de mercado aprofundada para identificar um nicho com demanda clara. Em seguida, construir um MVP (Produto Mínimo Viável) rapidamente, coletar feedback de usuários reais e iterar sobre o produto. O foco na experiência do usuário e na entrega de valor contínuo são passos iniciais fundamentais para o sucesso."
    ]

    # Converte o conteúdo em objetos Document do LangChain
    documents = [Document(page_content=content) for content in docs_content]

    # Divide os documentos em chunks (pedaços menores para a IA processar)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,        # Tamanho máximo de cada pedaço de texto (ajuste se precisar)
        chunk_overlap=100      # Quanto os pedaços se sobrepõem para manter contexto
    )
    chunks = text_splitter.split_documents(documents)
    logger.info(f"Documentos divididos em {len(chunks)} chunks.")

    # Inicializa os embeddings (MESMO MODELO USADO NO APP.PY - IMPORTANTE!)
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", openai_api_key=OPENAI_API_KEY)

    # Remove o diretório persistente antes de criar um novo para garantir a compatibilidade
    # e evitar problemas de versões anteriores.
    if os.path.exists(PERSIST_DIRECTORY):
        try:
            shutil.rmtree(PERSIST_DIRECTORY)
            logger.info(f"Diretório '{PERSIST_DIRECTORY}' removido com sucesso para recriação.")
        except Exception as e:
            logger.error(f"Erro ao remover o diretório '{PERSIST_DIRECTORY}': {e}. Por favor, verifique permissões ou se o diretório não está em uso.")
            exit(1) # Sai se não conseguir remover

    # Cria ou carrega o ChromaDB e adiciona os chunks
    logger.info(f"Criando novo ChromaDB em '{PERSIST_DIRECTORY}' e adicionando documentos...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )
    # Salva o vectorstore no disco para uso futuro
    vectorstore.persist()
    logger.info(f"✅ ChromaDB populado com {len(chunks)} documentos e salvo!")
    logger.info("Processo de população concluído. Agora você pode reiniciar seu 'app.py'.")

if __name__ == "__main__":
    populate_chroma_db()