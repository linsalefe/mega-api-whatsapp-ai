# check_env.py

import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Lista de variáveis de ambiente obrigatórias
REQUIRED_ENV_VARS = [
    "MEGA_API_TOKEN",
    "OPENAI_API_KEY", 
    "WEBHOOK_URL",
    "SECRET_KEY",
    "FLASK_ENV",
]

def check_environment_variables():
    """
    Verifica se todas as variáveis de ambiente necessárias estão definidas.
    """
    missing_vars = []
    for var in REQUIRED_ENV_VARS:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("\n❌ ERRO: As seguintes variáveis de ambiente estão faltando ou estão vazias no seu arquivo .env:")
        for var in missing_vars:
            print(f"    - {var}")
        print("\nPor favor, certifique-se de que seu arquivo .env esteja configurado corretamente.")
        return False
    else:
        print("✅ Todas as variáveis de ambiente obrigatórias estão configuradas!")
        print(f"  - FLASK_ENV: {os.getenv('FLASK_ENV')}")
        print(f"  - WEBHOOK_URL: {os.getenv('WEBHOOK_URL')}")
        return True

if __name__ == "__main__":
    check_environment_variables()