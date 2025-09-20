# Bot de Captura de Grupos - Telegram

Um bot do Telegram que **captura automaticamente** membros de grupos do Telegram e os **adiciona automaticamente** ao seu grupo, com opções para capturar todos os membros ou apenas quem está em lives, salvando os dados em SQLite e enviando relatórios detalhados.

## 🚀 Funcionalidades

### **Captura Automática:**
- ✅ **Captura TODOS os membros** de um grupo
- ✅ **Captura apenas quem está na live** (opção específica)
- ✅ **Verificação automática** para não duplicar membros
- ✅ **Adição automática** ao grupo de destino
- ✅ **Rate limiting** para evitar spam e bans
- ✅ **Proteções anti-spam** integradas

### **Funcionalidades Básicas:**
- ✅ Botão inline "Estou assistindo" durante lives
- ✅ Armazenamento automático de dados dos usuários em SQLite
- ✅ Envio automático de registros para grupo de contatos
- ✅ Estatísticas detalhadas de capturas
- ✅ Interface simples e intuitiva
- ✅ **Apenas administradores** podem usar os comandos
- ✅ **Mensagens são excluídas automaticamente** após uso
- ✅ **Feedback em tempo real** do progresso

### **Modos de Captura:**
- 👥 **Modo Completo** - Captura TODOS os membros do grupo
- 🎥 **Modo Live** - Captura apenas quem está na live
- 🔍 **Filtro Inteligente** - Não adiciona quem já está no seu grupo

## 📋 Pré-requisitos

- Python 3.7+
- Token do Bot do Telegram
- ID do grupo de contatos

## 🛠️ Instalação

1. **Clone ou baixe os arquivos do projeto**

2. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

3. **Configure o bot:**
   - Edite o arquivo `config.py`
   - Adicione seu token do bot em `BOT_TOKEN`
   - Adicione o ID do grupo de contatos em `CONTACTS_GROUP_ID`

## ⚙️ Configuração

### 1. Criar um Bot no Telegram

1. Fale com [@BotFather](https://t.me/botfather) no Telegram
2. Use o comando `/newbot`
3. Escolha um nome e username para seu bot
4. Copie o token fornecido

### 2. Obter ID do Grupo de Contatos

1. Adicione seu bot ao grupo de contatos
2. Envie uma mensagem no grupo
3. Acesse: `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates`
4. Procure pelo `chat.id` do grupo (será um número negativo)

### 3. Configurar o arquivo config.py

```python
BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"  # Seu token aqui
CONTACTS_GROUP_ID = -1001234567890  # ID do grupo (negativo)
```

## 🎯 Como Usar

1. **Iniciar o bot:**
```bash
python bot.py
```

2. **Comandos disponíveis:**
   - `/start` - Mensagem de boas-vindas
   - `/capture_group` - **Captura TODOS os membros de um grupo**
   - `/capture_live_only` - **Captura apenas quem está na live**
   - `/stop_capture` - Para captura em andamento
   - `/live` - Inicia uma live com botão de registro
   - `/stats` - Mostra estatísticas de usuários
   - `/auto_stats` - Mostra estatísticas do auto adder

3. **Captura de todos os membros:**
   - Use `/capture_group`
   - Envie o ID do grupo (ex: -1001234567890)
   - Bot captura TODOS os membros automaticamente
   - Filtra quem já está no seu grupo
   - Usuários são adicionados automaticamente

4. **Captura apenas da live:**
   - Use `/capture_live_only`
   - Envie o ID do grupo/canal (ex: @canal ou -1001234567890)
   - Bot captura apenas quem está na live
   - Filtra quem já está no seu grupo
   - Usuários são adicionados automaticamente

4. **Durante a live (modo manual):**
   - Use `/live` no chat onde quer o botão
   - Os usuários clicam em "Estou assistindo"
   - Dados são salvos automaticamente
   - Informações são enviadas para o grupo de contatos

## 📊 Dados Coletados

O bot coleta e armazena:
- ID único do usuário
- Nome de usuário (@username)
- Primeiro nome
- Último nome
- Data/hora do registro

## 🗄️ Banco de Dados

Os dados são armazenados em `users.db` (SQLite) com a seguinte estrutura:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);
```

## 🔧 Personalização

### Modificar mensagens:
Edite as strings no arquivo `bot.py` para personalizar as mensagens.

### Adicionar campos:
Modifique a tabela no `database.py` e atualize as funções correspondentes.

### Alterar comportamento:
O código está bem estruturado e comentado para facilitar modificações.

## 🚨 Solução de Problemas

### Bot não responde:
- Verifique se o token está correto
- Confirme se o bot está ativo no @BotFather

### Erro ao enviar para grupo:
- Verifique se o bot está no grupo de contatos
- Confirme se o ID do grupo está correto (deve ser negativo)

### Banco de dados não funciona:
- Verifique permissões de escrita na pasta
- Confirme se o SQLite está instalado

## 📝 Exemplo de Uso

```
Usuário: /live
Bot: [Mostra botão "Estou assistindo"]

Usuário: [Clica no botão]
Bot: ✅ Obrigado! Seus dados foram registrados...

[Grupo de contatos recebe:]
🆕 NOVO REGISTRO DE LIVE
👤 Dados do Usuário:
• ID: 123456789
• Nome: João Silva
• Username: @joaosilva
• Data/Hora: 2024-01-15 14:30:00
```

## 🤝 Suporte

Para dúvidas ou problemas, verifique:
1. Se todas as dependências estão instaladas
2. Se as configurações estão corretas
3. Se o bot tem as permissões necessárias

## 📄 Licença

Este projeto é de código aberto e pode ser usado livremente.
