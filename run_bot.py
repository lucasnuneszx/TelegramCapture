#!/usr/bin/env python3
"""Ponto de entrada do bot: valida a configuração antes de iniciar."""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from bot import LiveBot
    from config import BOT_TOKEN, CONTACTS_GROUP_ID

    if BOT_TOKEN in ("SEU_TOKEN_AQUI", "SEU_BOT_TOKEN_AQUI"):
        print("ERRO: configure o BOT_TOKEN no arquivo config.py")
        sys.exit(1)

    if CONTACTS_GROUP_ID == -1001234567890:
        print("AVISO: CONTACTS_GROUP_ID ainda está com o valor de exemplo em config.py")

    print("Iniciando bot (Ctrl+C para parar)...")

    bot = LiveBot()
    bot.run()

except KeyboardInterrupt:
    print("\nBot interrompido.")

except ImportError as e:
    print(f"ERRO: dependência ou config.py não encontrado: {e}")
    print("Execute: pip install -r requirements.txt e copie config.example.py para config.py")

except Exception as e:
    print(f"ERRO: {e}")
