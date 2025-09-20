#!/usr/bin/env python3
"""
Script para executar o bot de live
Execute este arquivo para iniciar o bot
"""

import sys
import os

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from bot import LiveBot
    
    print("🤖 Iniciando Bot de Live...")
    print("📋 Verificando configurações...")
    
    # Verificar se o token está configurado
    from config import BOT_TOKEN, CONTACTS_GROUP_ID
    
    if BOT_TOKEN == "SEU_BOT_TOKEN_AQUI":
        print("❌ ERRO: Configure o BOT_TOKEN no arquivo config.py")
        print("📝 Edite o arquivo config.py e adicione seu token do bot")
        sys.exit(1)
    
    if CONTACTS_GROUP_ID == -1001234567890:
        print("⚠️  AVISO: Configure o CONTACTS_GROUP_ID no arquivo config.py")
        print("📝 Edite o arquivo config.py e adicione o ID do grupo de contatos")
    
    print("✅ Configurações OK!")
    print("🚀 Iniciando bot...")
    print("💡 Use Ctrl+C para parar o bot")
    print("-" * 50)
    
    # Iniciar o bot
    bot = LiveBot()
    bot.run()
    
except KeyboardInterrupt:
    print("\n🛑 Bot interrompido pelo usuário")
    print("👋 Até logo!")
    
except ImportError as e:
    print(f"❌ ERRO: Dependência não encontrada: {e}")
    print("📦 Execute: pip install -r requirements.txt")
    
except Exception as e:
    print(f"❌ ERRO: {e}")
    print("🔧 Verifique as configurações e tente novamente")
