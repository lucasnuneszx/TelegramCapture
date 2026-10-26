# TelegramCapture

Bot do Telegram que registra quem está acompanhando uma live (botão "Estou assistindo") e tenta levar membros de outro grupo para um grupo de destino. Os registros ficam em SQLite e cada novo registro é enviado para um grupo de contatos.

## Stack

- Python 3.8 a 3.12 (a versão 20.7 do python-telegram-bot não funciona no 3.13)
- [python-telegram-bot](https://python-telegram-bot.org/) 20.7
- SQLite

## Como rodar

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config.example.py config.py   # preencha os valores
python run_bot.py
```

`run_bot.py` valida a configuração antes de subir o bot; `python bot.py` também funciona.

## Configuração

Em `config.py` (não versionado):

- `BOT_TOKEN`: token do bot, gerado no @BotFather
- `CONTACTS_GROUP_ID`: ID do grupo de contatos/destino (número negativo)
- `DATABASE_PATH`: caminho do arquivo SQLite (padrão `users.db`)

O bot precisa estar no grupo de contatos e ser administrador nele.

## Comandos

Todos restritos a administradores do grupo (no chat privado com o bot não há restrição).

| Comando | O que faz |
| --- | --- |
| `/start` | Lista os comandos |
| `/live` | Publica a mensagem com o botão "Estou assistindo" |
| `/capture_group` | Pede o ID de um grupo e captura os membros |
| `/capture_live_only` | Igual ao anterior, só para canais/supergrupos com live |
| `/stop_capture` | Interrompe a captura em andamento |
| `/stats` | Total de registros e os 10 mais recentes |
| `/auto_stats` | Situação do grupo de destino e do limite de adições |

As respostas do bot são apagadas automaticamente depois de alguns segundos.

## Estrutura

```
bot.py                     handlers e comandos (classe LiveBot)
run_bot.py                 ponto de entrada com checagem da config
telegram_live_capture.py   leitura de membros dos grupos de origem e destino
auto_adder.py              adição ao grupo de destino com limite por hora
database.py                acesso ao SQLite (tabela users)
config.example.py          modelo de configuração
```

## Limitações

- A Bot API do Telegram não lista membros comuns de um grupo nem os espectadores de uma live. A captura só enxerga administradores, então o registro confiável é o do botão `/live`.
- `auto_adder.py` gera IDs a partir do username como placeholder, porque não há como obter o ID real do espectador. Na prática essas adições falham.
- O limite de adições é de 50 por hora, com 1 segundo de intervalo entre elas.
