import asyncio
import logging
import time
from typing import List, Dict, Optional
from telegram import Bot
from telegram.error import TelegramError, BadRequest, Forbidden
from database import Database

logger = logging.getLogger(__name__)

class AutoAdder:
    def __init__(self, bot_token: str, target_group_id: int):
        self.bot = Bot(token=bot_token)
        self.target_group_id = target_group_id
        self.db = Database()
        self.added_users = set()  # Cache de usuários já adicionados
        self.rate_limit_delay = 1  # Delay entre adições (segundos)
        self.max_additions_per_hour = 50  # Limite de adições por hora
        self.additions_count = 0
        self.last_reset_time = time.time()
        
    async def reset_rate_limit(self):
        """Reseta o contador de rate limit a cada hora"""
        current_time = time.time()
        if current_time - self.last_reset_time >= 3600:  # 1 hora
            self.additions_count = 0
            self.last_reset_time = current_time
            logger.info("Rate limit resetado")
    
    async def check_rate_limit(self) -> bool:
        """Verifica se ainda pode adicionar usuários"""
        await self.reset_rate_limit()
        return self.additions_count < self.max_additions_per_hour
    
    async def add_user_to_group(self, user_data: Dict) -> bool:
        """Adiciona um usuário ao grupo"""
        try:
            # Verifica rate limit
            if not await self.check_rate_limit():
                logger.warning("Rate limit atingido. Aguardando...")
                return False
            
            # Verifica se usuário já foi adicionado
            user_id = user_data.get('telegram_id')
            if not user_id or user_id in self.added_users:
                logger.info(f"Usuário {user_id} já foi adicionado ou ID inválido")
                return False
            
            # Tenta adicionar o usuário
            logger.info(f"Tentando adicionar usuário {user_id} ao grupo")
            
            await self.bot.add_chat_member(
                chat_id=self.target_group_id,
                user_id=user_id
            )
            
            # Marca como adicionado
            self.added_users.add(user_id)
            self.additions_count += 1
            
            # Salva no banco de dados
            self.db.add_user(
                user_id=user_id,
                username=user_data.get('username'),
                first_name=user_data.get('display_name', ''),
                last_name=''
            )
            
            logger.info(f"Usuário {user_id} adicionado com sucesso")
            
            # Delay para evitar spam
            await asyncio.sleep(self.rate_limit_delay)
            
            return True
            
        except Forbidden as e:
            logger.error(f"Usuário {user_id} bloqueou o bot ou não pode ser adicionado: {e}")
            return False
        except BadRequest as e:
            logger.error(f"Erro ao adicionar usuário {user_id}: {e}")
            return False
        except TelegramError as e:
            logger.error(f"Erro do Telegram ao adicionar usuário {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado ao adicionar usuário {user_id}: {e}")
            return False
    
    async def process_viewers(self, viewers_data: List[Dict]) -> Dict:
        """Processa lista de espectadores e adiciona ao grupo"""
        results = {
            'total_viewers': len(viewers_data),
            'added_successfully': 0,
            'failed': 0,
            'already_added': 0,
            'rate_limited': 0
        }
        
        logger.info(f"Processando {len(viewers_data)} espectadores")
        
        for viewer in viewers_data:
            try:
                # Simula conversão de dados do espectador para dados do Telegram
                # Em uma implementação real, você precisaria de uma forma de mapear
                # espectadores para IDs do Telegram (isso é muito complexo)
                
                # Para demonstração, vamos simular alguns IDs do Telegram
                simulated_telegram_id = self._simulate_telegram_id(viewer)
                
                if simulated_telegram_id:
                    viewer['telegram_id'] = simulated_telegram_id
                    
                    success = await self.add_user_to_group(viewer)
                    if success:
                        results['added_successfully'] += 1
                    else:
                        results['failed'] += 1
                else:
                    results['failed'] += 1
                    
            except Exception as e:
                logger.error(f"Erro ao processar espectador: {e}")
                results['failed'] += 1
        
        return results
    
    def _simulate_telegram_id(self, viewer: Dict) -> Optional[int]:
        """Simula um ID do Telegram baseado nos dados do espectador"""
        # ATENÇÃO: Esta é uma simulação!
        # Na realidade, não é possível obter IDs do Telegram de espectadores de lives
        # sem que eles forneçam voluntariamente
        
        username = viewer.get('username', '')
        if username:
            # Simula um ID baseado no hash do username
            import hashlib
            hash_obj = hashlib.md5(username.encode())
            # Gera um ID simulado (não é um ID real do Telegram)
            simulated_id = int(hash_obj.hexdigest()[:8], 16)
            return simulated_id
        
        return None
    
    async def send_summary_to_group(self, results: Dict, live_url: str):
        """Envia resumo das adições para o grupo"""
        try:
            summary_message = f"""
🎥 **CAPTURA DE LIVE CONCLUÍDA**

🔗 **Live:** {live_url}

📊 **Resultados:**
• Total de espectadores: {results['total_viewers']}
• Adicionados com sucesso: {results['added_successfully']}
• Falharam: {results['failed']}
• Já estavam no grupo: {results['already_added']}
• Rate limited: {results['rate_limited']}

⏰ **Timestamp:** {time.strftime('%d/%m/%Y %H:%M:%S')}
            """
            
            await self.bot.send_message(
                chat_id=self.target_group_id,
                text=summary_message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao enviar resumo: {e}")
    
    async def get_group_info(self) -> Dict:
        """Obtém informações do grupo"""
        try:
            chat = await self.bot.get_chat(self.target_group_id)
            return {
                'title': chat.title,
                'member_count': chat.member_count,
                'type': chat.type
            }
        except Exception as e:
            logger.error(f"Erro ao obter info do grupo: {e}")
            return {}
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do auto adder"""
        return {
            'added_users_count': len(self.added_users),
            'additions_this_hour': self.additions_count,
            'rate_limit_remaining': self.max_additions_per_hour - self.additions_count,
            'rate_limit_reset_in': 3600 - (time.time() - self.last_reset_time)
        }
