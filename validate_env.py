#!/usr/bin/env python3
"""
Script de validação de ambiente para WhatsApp AI Agent com MEGA API
Verifica se todas as variáveis de ambiente necessárias estão configuradas
"""

import os
from dotenv import load_dotenv

def validate_environment():
    """Valida todas as variáveis de ambiente necessárias"""
    
    # Carrega variáveis do arquivo .env
    load_dotenv()
    
    print("🔍 Validando configurações de ambiente...\n")
    
    # Variáveis obrigatórias
    required_vars = {
        'SECRET_KEY': 'Chave secreta do Flask',
        'FLASK_ENV': 'Ambiente do Flask',
        'FLASK_DEBUG': 'Debug do Flask',
        'PORT': 'Porta do servidor',
        'MEGA_API_TOKEN': 'Token da MEGA API',
        'MEGA_API_URL': 'URL da MEGA API'
    }
    
    # Variáveis opcionais (para futuras integrações)
    optional_vars = {
        'WEBHOOK_URL': 'URL do webhook para receber mensagens',
        'WHATSAPP_PHONE_NUMBER_ID': 'ID do número do WhatsApp (se necessário)'
    }
    
    all_valid = True
    
    # Verifica variáveis obrigatórias
    print("📋 VARIÁVEIS OBRIGATÓRIAS:")
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mascarar valores sensíveis
            if 'KEY' in var or 'TOKEN' in var:
                display_value = f"{value[:8]}...{value[-8:]}" if len(value) > 16 else "***"
            else:
                display_value = value
            print(f"  ✅ {var}: {display_value} ({description})")
        else:
            print(f"  ❌ {var}: NÃO CONFIGURADA ({description})")
            all_valid = False
    
    print("\n📋 VARIÁVEIS OPCIONAIS:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value and value != "your_webhook_url_here":
            if 'URL' in var:
                display_value = value
            else:
                display_value = f"{value[:8]}...{value[-8:]}" if len(value) > 16 else "***"
            print(f"  ✅ {var}: {display_value} ({description})")
        else:
            print(f"  ⚠️  {var}: NÃO CONFIGURADA ({description})")
    
    # Validações específicas
    print("\n🔧 VALIDAÇÕES ESPECÍFICAS:")
    
    # Validar SECRET_KEY
    secret_key = os.getenv('SECRET_KEY')
    if secret_key and len(secret_key) >= 32:
        print(f"  ✅ SECRET_KEY tem comprimento adequado ({len(secret_key)} caracteres)")
    elif secret_key:
        print(f"  ⚠️  SECRET_KEY muito curta ({len(secret_key)} caracteres, recomendado: 32+)")
    
    # Validar MEGA_API_URL
    mega_url = os.getenv('MEGA_API_URL')
    if mega_url and mega_url.startswith('https://'):
        print(f"  ✅ MEGA_API_URL válida (HTTPS)")
    elif mega_url:
        print(f"  ⚠️  MEGA_API_URL sem HTTPS")
    
    # Validar PORT
    port = os.getenv('PORT')
    if port and port.isdigit():
        port_num = int(port)
        if 1000 <= port_num <= 65535:
            print(f"  ✅ PORT válida ({port})")
        else:
            print(f"  ⚠️  PORT fora do range recomendado ({port})")
    
    # Resultado final
    print("\n" + "="*50)
    if all_valid:
        print("🎉 CONFIGURAÇÃO BÁSICA VÁLIDA!")
        print("✅ Todas as variáveis obrigatórias estão configuradas.")
        print("📝 Configure as variáveis opcionais quando necessário.")
    else:
        print("❌ CONFIGURAÇÃO INCOMPLETA!")
        print("🔧 Configure as variáveis marcadas como ❌ antes de continuar.")
    
    return all_valid

if __name__ == "__main__":
    validate_environment()