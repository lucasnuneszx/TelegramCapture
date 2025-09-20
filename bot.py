import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from database import Database
from config import BOT_TOKEN, CONTACTS_GROUP_ID
from telegram_live_capture import init_telegram_group_capture
from auto_adder import AutoAdder

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Inicializar banco de dados
db = Database()

class LiveBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.auto_adder = AutoAdder(BOT_TOKEN, CONTACTS_GROUP_ID)
        self.telegram_group_capture = init_telegram_group_capture(BOT_TOKEN)
        self.capturing = False
        self.setup_handlers()
    
    async def is_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Verifica se o usuário é administrador do grupo"""
        try:
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            
            # Se é um chat privado, permite (para testes)
            if update.effective_chat.type == 'private':
                return True
            
            # Verifica se é administrador do grupo
            member = await context.bot.get_chat_member(chat_id, user_id)
            return member.status in ['creator', 'administrator']
            
        except Exception as e:
            logger.error(f"Erro ao verificar admin: {e}")
            return False
    
    async def delete_message_after_delay(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, delay: int = 10):
        """Exclui mensagem após um delay"""
        try:
            await asyncio.sleep(delay)
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            logger.error(f"Erro ao excluir mensagem: {e}")
    
    def setup_handlers(self):
        """Configura os handlers do bot"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("live", self.start_live))
        self.application.add_handler(CommandHandler("capture_group", self.capture_group_command))
        self.application.add_handler(CommandHandler("capture_live_only", self.capture_live_only_command))
        self.application.add_handler(CommandHandler("stop_capture", self.stop_capture_command))
        self.application.add_handler(CommandHandler("stats", self.show_stats))
        self.application.add_handler(CommandHandler("auto_stats", self.show_auto_stats))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_group_id_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        # Verifica se é administrador
        if not await self.is_admin(update, context):
            error_msg = await update.message.reply_text(
                "❌ **Acesso Negado!**\n\n"
                "Apenas administradores podem usar este bot.",
                parse_mode='Markdown'
            )
            # Exclui a mensagem após 5 segundos
            asyncio.create_task(self.delete_message_after_delay(
                context, update.effective_chat.id, error_msg.message_id, 5
            ))
            return
        
        welcome_message = """
🎥 **Bot de Captura de Grupos - Telegram**

Olá! Este bot captura membros de grupos do Telegram e os adiciona automaticamente ao seu grupo.

**Comandos disponíveis:**
• `/capture_group` - Captura TODOS os membros de um grupo
• `/capture_live_only` - Captura apenas quem está na live
• `/stop_capture` - Para a captura em andamento
• `/live` - Inicia uma nova live com botão de registro
• `/stats` - Mostra estatísticas de usuários cadastrados
• `/auto_stats` - Mostra estatísticas do auto adder

**Funcionalidades:**
• Captura automática de membros de grupos
• Verificação para não duplicar membros
• Adição automática ao grupo de destino
• Rate limiting para evitar bans
• Mensagens são excluídas automaticamente

⚠️ **AVISO:** Este bot adiciona usuários automaticamente ao grupo.
        """
        msg = await update.message.reply_text(welcome_message, parse_mode='Markdown')
        # Exclui a mensagem após 15 segundos
        asyncio.create_task(self.delete_message_after_delay(
            context, update.effective_chat.id, msg.message_id, 15
        ))
    
    async def start_live(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /live - Cria o botão 'Estou assistindo'"""
        keyboard = [
            [InlineKeyboardButton("🎥 Estou assistindo", callback_data="watching_live")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        live_message = """
🎥 **LIVE INICIADA**

Clique no botão abaixo para confirmar que está assistindo:

👥 Total de pessoas assistindo: 0
        """
        
        await update.message.reply_text(
            live_message, 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa o clique no botão 'Estou assistindo'"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "watching_live":
            user = query.from_user
            
            # Salvar dados do usuário no banco
            success = db.add_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            if success:
                # Enviar confirmação para o usuário
                await query.edit_message_text(
                    f"✅ **Obrigado, {user.first_name}!**\n\n"
                    f"Seus dados foram registrados com sucesso!\n"
                    f"👤 ID: {user.id}\n"
                    f"📝 Nome: {user.first_name} {user.last_name or ''}\n"
                    f"🔗 Username: @{user.username or 'N/A'}",
                    parse_mode='Markdown'
                )
                
                # Enviar dados para o grupo de contatos
                await self.send_to_contacts_group(user, context)
                
                # Atualizar contador na mensagem original
                await self.update_live_counter(query, context)
            else:
                await query.edit_message_text(
                    "❌ Erro ao registrar seus dados. Tente novamente.",
                    parse_mode='Markdown'
                )
    
    async def send_to_contacts_group(self, user, context: ContextTypes.DEFAULT_TYPE):
        """Envia os dados do usuário para o grupo de contatos"""
        try:
            contact_message = f"""
🆕 **NOVO REGISTRO DE LIVE**

👤 **Dados do Usuário:**
• ID: `{user.id}`
• Nome: {user.first_name} {user.last_name or ''}
• Username: @{user.username or 'N/A'}
• Data/Hora: {context.bot_data.get('current_time', 'N/A')}

📊 Total de registros: {db.get_user_count()}
            """
            
            await context.bot.send_message(
                chat_id=CONTACTS_GROUP_ID,
                text=contact_message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao enviar para grupo de contatos: {e}")
    
    async def update_live_counter(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Atualiza o contador de pessoas assistindo"""
        try:
            # Buscar a mensagem original e atualizar o contador
            total_users = db.get_user_count()
            
            keyboard = [
                [InlineKeyboardButton("🎥 Estou assistindo", callback_data="watching_live")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            updated_message = f"""
🎥 **LIVE ATIVA**

Clique no botão abaixo para confirmar que está assistindo:

👥 Total de pessoas assistindo: {total_users}
            """
            
            # Nota: Não podemos editar a mensagem original aqui pois já foi editada
            # Em uma implementação mais avançada, você poderia manter referência à mensagem original
            
        except Exception as e:
            logger.error(f"Erro ao atualizar contador: {e}")
    
    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /stats - Mostra estatísticas"""
        # Verifica se é administrador
        if not await self.is_admin(update, context):
            error_msg = await update.message.reply_text(
                "❌ **Acesso Negado!**\n\n"
                "Apenas administradores podem usar este comando.",
                parse_mode='Markdown'
            )
            asyncio.create_task(self.delete_message_after_delay(
                context, update.effective_chat.id, error_msg.message_id, 5
            ))
            return
        
        total_users = db.get_user_count()
        recent_users = db.get_all_users()[:10]  # Últimos 10 usuários
        
        stats_message = f"""
📊 **ESTATÍSTICAS DO BOT**

👥 **Total de usuários registrados:** {total_users}

🕒 **Últimos registros:**
        """
        
        for user in recent_users:
            username = f"@{user[2]}" if user[2] else "Sem username"
            stats_message += f"\n• {user[3]} {user[4] or ''} ({username}) - {user[5]}"
        
        stats_message += "\n\n⏰ **Esta mensagem será excluída em 20 segundos**"
        
        msg = await update.message.reply_text(stats_message, parse_mode='Markdown')
        # Exclui a mensagem após 20 segundos
        asyncio.create_task(self.delete_message_after_delay(
            context, update.effective_chat.id, msg.message_id, 20
        ))
    
    async def capture_group_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /capture_group - Captura TODOS os membros de um grupo"""
        # Verifica se é administrador
        if not await self.is_admin(update, context):
            error_msg = await update.message.reply_text(
                "❌ **Acesso Negado!**\n\n"
                "Apenas administradores podem usar este comando.",
                parse_mode='Markdown'
            )
            asyncio.create_task(self.delete_message_after_delay(
                context, update.effective_chat.id, error_msg.message_id, 5
            ))
            return
        
        if self.capturing:
            msg = await update.message.reply_text(
                "⚠️ **Captura já está ativa!**\n\n"
                "Use `/stop_capture` para parar a captura atual.",
                parse_mode='Markdown'
            )
            asyncio.create_task(self.delete_message_after_delay(
                context, update.effective_chat.id, msg.message_id, 5
            ))
            return
        
        msg = await update.message.reply_text(
            "👥 **CAPTURA DE TODOS OS MEMBROS**\n\n"
            "Envie o ID do grupo que você quer capturar TODOS os membros.\n\n"
            "**Como obter o ID:**\n"
            "• Para grupos: -1001234567890\n"
            "• Para canais: @nome_do_canal\n"
            "• Para usar o chat atual: envie 'atual'\n\n"
            "⚠️ **AVISO:** Esta funcionalidade captura TODOS os membros e os adiciona automaticamente ao seu grupo.",
            parse_mode='Markdown'
        )
        
        # Exclui a mensagem após 20 segundos
        asyncio.create_task(self.delete_message_after_delay(
            context, update.effective_chat.id, msg.message_id, 20
        ))
        
        # Marca que está aguardando ID do grupo
        context.user_data['waiting_for_group_id'] = True
        context.user_data['capture_mode'] = 'all'
    
    async def capture_live_only_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /capture_live_only - Captura apenas quem está na live"""
        # Verifica se é administrador
        if not await self.is_admin(update, context):
            error_msg = await update.message.reply_text(
                "❌ **Acesso Negado!**\n\n"
                "Apenas administradores podem usar este comando.",
                parse_mode='Markdown'
            )
            asyncio.create_task(self.delete_message_after_delay(
                context, update.effective_chat.id, error_msg.message_id, 5
            ))
            return
        
        if self.capturing:
            msg = await update.message.reply_text(
                "⚠️ **Captura já está ativa!**\n\n"
                "Use `/stop_capture` para parar a captura atual.",
                parse_mode='Markdown'
            )
            asyncio.create_task(self.delete_message_after_delay(
                context, update.effective_chat.id, msg.message_id, 5
            ))
            return
        
        msg = await update.message.reply_text(
            "🎥 **CAPTURA APENAS QUEM ESTÁ NA LIVE**\n\n"
            "Envie o ID do grupo/canal onde está acontecendo a live.\n\n"
            "**Como obter o ID:**\n"
            "• Para grupos: -1001234567890\n"
            "• Para canais: @nome_do_canal\n"
            "• Para usar o chat atual: envie 'atual'\n\n"
            "⚠️ **AVISO:** Esta funcionalidade captura apenas quem está na live e os adiciona automaticamente ao seu grupo.",
            parse_mode='Markdown'
        )
        
        # Exclui a mensagem após 20 segundos
        asyncio.create_task(self.delete_message_after_delay(
            context, update.effective_chat.id, msg.message_id, 20
        ))
        
        # Marca que está aguardando ID do grupo
        context.user_data['waiting_for_group_id'] = True
        context.user_data['capture_mode'] = 'live_only'
    
    async def handle_group_id_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa mensagens com ID do grupo"""
        if not context.user_data.get('waiting_for_group_id', False):
            return
        
        # Verifica se é administrador
        if not await self.is_admin(update, context):
            error_msg = await update.message.reply_text(
                "❌ **Acesso Negado!**\n\n"
                "Apenas administradores podem usar este comando.",
                parse_mode='Markdown'
            )
            asyncio.create_task(self.delete_message_after_delay(
                context, update.effective_chat.id, error_msg.message_id, 5
            ))
            return
        
        group_input = update.message.text.strip()
        capture_mode = context.user_data.get('capture_mode', 'all')
        
        # Determina o group_id
        if group_input.lower() == 'atual':
            group_id = update.effective_chat.id
        elif group_input.startswith('@'):
            # Username do canal
            group_id = group_input
        elif group_input.startswith('-') and group_input[1:].isdigit():
            # ID numérico do grupo
            group_id = int(group_input)
        else:
            msg = await update.message.reply_text(
                "❌ **ID do grupo inválido!**\n\n"
                "Formato aceito:\n"
                "• @nome_do_canal\n"
                "• -1001234567890\n"
                "• atual (para usar o chat atual)",
                parse_mode='Markdown'
            )
            asyncio.create_task(self.delete_message_after_delay(
                context, update.effective_chat.id, msg.message_id, 10
            ))
            return
        
        # Inicia captura
        context.user_data['waiting_for_group_id'] = False
        self.capturing = True
        
        mode_text = "TODOS os membros" if capture_mode == 'all' else "apenas quem está na live"
        
        msg = await update.message.reply_text(
            f"🚀 **Iniciando captura...**\n\n"
            f"👥 **Grupo:** {group_input}\n"
            f"🎯 **Modo:** {mode_text}\n"
            f"⏳ Aguarde enquanto capturo os membros...",
            parse_mode='Markdown'
        )
        
        # Exclui a mensagem após 30 segundos
        asyncio.create_task(self.delete_message_after_delay(
            context, update.effective_chat.id, msg.message_id, 30
        ))
        
        # Executa captura em background
        asyncio.create_task(self.execute_group_capture(update, context, group_id, capture_mode))
    
    async def execute_group_capture(self, update: Update, context: ContextTypes.DEFAULT_TYPE, group_id, capture_mode):
        """Executa a captura de membros de um grupo"""
        try:
            # Captura membros do grupo com filtro para não duplicar
            members_data = await self.telegram_group_capture.capture_and_filter_members(
                group_id, CONTACTS_GROUP_ID, capture_mode
            )
            
            if not members_data:
                mode_text = "TODOS os membros" if capture_mode == 'all' else "quem está na live"
                await update.message.reply_text(
                    f"❌ **Erro na captura!**\n\n"
                    f"Não foi possível capturar {mode_text} deste grupo.\n"
                    f"Possíveis motivos:\n"
                    f"• Bot não tem permissões no grupo\n"
                    f"• Grupo não é válido\n"
                    f"• Todos os membros já estão no seu grupo",
                    parse_mode='Markdown'
                )
                self.capturing = False
                return
            
            # Processa e adiciona usuários
            results = await self.auto_adder.process_viewers(members_data)
            
            # Envia resumo
            await self.auto_adder.send_summary_to_group(results, f"Grupo: {group_id}")
            
            # Resposta para o usuário
            mode_text = "TODOS os membros" if capture_mode == 'all' else "quem estava na live"
            summary_message = f"""
✅ **CAPTURA CONCLUÍDA!**

👥 **Grupo:** {group_id}
🎯 **Modo:** {mode_text}

📊 **Resultados:**
• Membros encontrados: {results['total_viewers']}
• Adicionados ao grupo: {results['added_successfully']}
• Falharam: {results['failed']}
• Já estavam no grupo: {results['total_viewers'] - results['added_successfully'] - results['failed']}

📈 **Estatísticas do Auto Adder:**
• Total adicionados hoje: {len(self.auto_adder.added_users)}
• Rate limit restante: {self.auto_adder.max_additions_per_hour - self.auto_adder.additions_count}

⏰ **Esta mensagem será excluída em 30 segundos**
            """
            
            msg = await update.message.reply_text(summary_message, parse_mode='Markdown')
            # Exclui a mensagem de resultado após 30 segundos
            asyncio.create_task(self.delete_message_after_delay(
                context, update.effective_chat.id, msg.message_id, 30
            ))
            
        except Exception as e:
            logger.error(f"Erro na captura: {e}")
            msg = await update.message.reply_text(
                f"❌ **Erro durante a captura!**\n\n"
                f"Erro: {str(e)}\n\n"
                f"Tente novamente ou verifique se o grupo é válido.\n\n"
                f"⏰ **Esta mensagem será excluída em 15 segundos**",
                parse_mode='Markdown'
            )
            # Exclui a mensagem de erro após 15 segundos
            asyncio.create_task(self.delete_message_after_delay(
                context, update.effective_chat.id, msg.message_id, 15
            ))
        finally:
            self.capturing = False
    
    async def stop_capture_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /stop_capture - Para captura"""
        # Verifica se é administrador
        if not await self.is_admin(update, context):
            error_msg = await update.message.reply_text(
                "❌ **Acesso Negado!**\n\n"
                "Apenas administradores podem usar este comando.",
                parse_mode='Markdown'
            )
            asyncio.create_task(self.delete_message_after_delay(
                context, update.effective_chat.id, error_msg.message_id, 5
            ))
            return
        
        if not self.capturing:
            msg = await update.message.reply_text(
                "ℹ️ **Nenhuma captura ativa!**\n\n"
                "Use `/capture_group` ou `/capture_live_only` para iniciar uma captura.",
                parse_mode='Markdown'
            )
            asyncio.create_task(self.delete_message_after_delay(
                context, update.effective_chat.id, msg.message_id, 5
            ))
            return
        
        self.capturing = False
        context.user_data['waiting_for_group_id'] = False
        
        msg = await update.message.reply_text(
            "🛑 **Captura interrompida!**\n\n"
            "A captura automática foi parada com sucesso.\n\n"
            "⏰ **Esta mensagem será excluída em 10 segundos**",
            parse_mode='Markdown'
        )
        # Exclui a mensagem após 10 segundos
        asyncio.create_task(self.delete_message_after_delay(
            context, update.effective_chat.id, msg.message_id, 10
        ))
    
    async def show_auto_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /auto_stats - Mostra estatísticas do auto adder"""
        # Verifica se é administrador
        if not await self.is_admin(update, context):
            error_msg = await update.message.reply_text(
                "❌ **Acesso Negado!**\n\n"
                "Apenas administradores podem usar este comando.",
                parse_mode='Markdown'
            )
            asyncio.create_task(self.delete_message_after_delay(
                context, update.effective_chat.id, error_msg.message_id, 5
            ))
            return
        
        stats = self.auto_adder.get_stats()
        group_info = await self.auto_adder.get_group_info()
        
        stats_message = f"""
🤖 **ESTATÍSTICAS DO AUTO ADDER**

👥 **Grupo de Destino:**
• Nome: {group_info.get('title', 'N/A')}
• Membros: {group_info.get('member_count', 'N/A')}
• Tipo: {group_info.get('type', 'N/A')}

📊 **Capturas:**
• Usuários adicionados hoje: {stats['added_users_count']}
• Adições nesta hora: {stats['additions_this_hour']}
• Rate limit restante: {stats['rate_limit_remaining']}
• Reset do rate limit em: {int(stats['rate_limit_reset_in'])} segundos

🔄 **Status:**
• Captura ativa: {'Sim' if self.capturing else 'Não'}

⏰ **Esta mensagem será excluída em 20 segundos**
        """
        
        msg = await update.message.reply_text(stats_message, parse_mode='Markdown')
        # Exclui a mensagem após 20 segundos
        asyncio.create_task(self.delete_message_after_delay(
            context, update.effective_chat.id, msg.message_id, 20
        ))
    
    def run(self):
        """Inicia o bot"""
        logger.info("Iniciando bot...")
        self.application.run_polling()

if __name__ == "__main__":
    bot = LiveBot()
    bot.run()
