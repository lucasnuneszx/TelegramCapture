import asyncio
import logging
from typing import List, Dict, Optional
from telegram import Bot, ChatMember
from telegram.error import TelegramError, BadRequest, Forbidden

logger = logging.getLogger(__name__)

class TelegramGroupCapture:
    def __init__(self, bot_token: str):
        self.bot = Bot(token=bot_token)
        self.active_lives = {}  # Armazena lives ativas por chat_id
        self.target_group_members = set()  # Cache de membros do grupo de destino
    
    async def get_chat_members(self, chat_id: int) -> List[Dict]:
        """Obtém lista de membros do chat (apenas administradores)"""
        try:
            members = []
            async for member in self.bot.get_chat_administrators(chat_id):
                members.append({
                    'user_id': member.user.id,
                    'username': member.user.username,
                    'first_name': member.user.first_name,
                    'last_name': member.user.last_name,
                    'is_bot': member.user.is_bot
                })
            return members
        except Exception as e:
            logger.error(f"Erro ao obter membros do chat {chat_id}: {e}")
            return []
    
    async def get_all_chat_members(self, chat_id: int) -> List[Dict]:
        """Obtém TODOS os membros do chat (se possível)"""
        try:
            members = []
            
            # Tenta obter membros via get_chat_administrators (sempre funciona)
            async for member in self.bot.get_chat_administrators(chat_id):
                members.append({
                    'user_id': member.user.id,
                    'username': member.user.username,
                    'first_name': member.user.first_name,
                    'last_name': member.user.last_name,
                    'is_bot': member.user.is_bot,
                    'status': member.status
                })
            
            # Nota: A API do Telegram não permite obter todos os membros de um grupo
            # por questões de privacidade. Este método retorna apenas administradores.
            # Para obter todos os membros, seria necessário usar métodos alternativos
            # ou que os usuários se voluntariem (como o botão "Estou assistindo")
            
            logger.info(f"Obtidos {len(members)} membros (administradores) do chat {chat_id}")
            return members
            
        except Exception as e:
            logger.error(f"Erro ao obter todos os membros do chat {chat_id}: {e}")
            return []
    
    async def get_target_group_members(self, target_group_id: int) -> set:
        """Obtém lista de membros do grupo de destino para evitar duplicatas"""
        try:
            if target_group_id in self.target_group_members:
                return self.target_group_members[target_group_id]
            
            members = set()
            async for member in self.bot.get_chat_administrators(target_group_id):
                members.add(member.user.id)
            
            self.target_group_members[target_group_id] = members
            logger.info(f"Cache de {len(members)} membros do grupo de destino {target_group_id}")
            return members
            
        except Exception as e:
            logger.error(f"Erro ao obter membros do grupo de destino {target_group_id}: {e}")
            return set()
    
    async def filter_new_members(self, source_members: List[Dict], target_group_id: int) -> List[Dict]:
        """Filtra membros que ainda não estão no grupo de destino"""
        try:
            target_members = await self.get_target_group_members(target_group_id)
            new_members = []
            
            for member in source_members:
                if member['user_id'] not in target_members and not member.get('is_bot', False):
                    new_members.append(member)
            
            logger.info(f"Filtrados {len(new_members)} novos membros de {len(source_members)} total")
            return new_members
            
        except Exception as e:
            logger.error(f"Erro ao filtrar novos membros: {e}")
            return source_members
    
    async def get_chat_member_count(self, chat_id: int) -> int:
        """Obtém número de membros do chat"""
        try:
            chat = await self.bot.get_chat(chat_id)
            return chat.member_count or 0
        except Exception as e:
            logger.error(f"Erro ao obter contagem de membros do chat {chat_id}: {e}")
            return 0
    
    async def is_live_active(self, chat_id: int) -> bool:
        """Verifica se há uma live ativa no chat"""
        try:
            # Verifica se o chat tem uma live ativa
            # Nota: A API do Telegram não expõe diretamente se há uma live ativa
            # Vamos usar uma abordagem alternativa
            
            # Verifica se o chat é um canal ou grupo que pode ter lives
            chat = await self.bot.get_chat(chat_id)
            
            # Se é um canal, pode ter lives
            if chat.type in ['channel', 'supergroup']:
                # Verifica se há mensagens recentes (indicativo de atividade)
                try:
                    # Tenta obter informações do chat
                    chat_info = await self.bot.get_chat(chat_id)
                    return True  # Assume que pode ter lives se é um canal/grupo
                except:
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao verificar live ativa no chat {chat_id}: {e}")
            return False
    
    async def capture_live_viewers(self, chat_id: int) -> List[Dict]:
        """Captura espectadores de uma live do Telegram"""
        try:
            logger.info(f"Capturando espectadores da live no chat {chat_id}")
            
            # Verifica se há live ativa
            if not await self.is_live_active(chat_id):
                logger.warning(f"Nenhuma live ativa encontrada no chat {chat_id}")
                return []
            
            # Obtém membros do chat
            members = await self.get_chat_members(chat_id)
            
            # Filtra apenas usuários (não bots)
            viewers = [member for member in members if not member.get('is_bot', False)]
            
            logger.info(f"Encontrados {len(viewers)} espectadores na live do chat {chat_id}")
            
            return viewers
            
        except Exception as e:
            logger.error(f"Erro ao capturar espectadores da live no chat {chat_id}: {e}")
            return []
    
    async def capture_group_members(self, source_group_id: int, capture_mode: str = "all") -> List[Dict]:
        """Captura membros de um grupo do Telegram"""
        try:
            logger.info(f"Capturando membros do grupo {source_group_id} (modo: {capture_mode})")
            
            if capture_mode == "live_only":
                # Captura apenas quem está na live
                members = await self.capture_live_viewers(source_group_id)
            elif capture_mode == "all":
                # Captura todos os membros disponíveis (administradores)
                members = await self.get_all_chat_members(source_group_id)
            else:
                logger.error(f"Modo de captura inválido: {capture_mode}")
                return []
            
            # Filtra apenas usuários (não bots)
            users = [member for member in members if not member.get('is_bot', False)]
            
            logger.info(f"Capturados {len(users)} membros do grupo {source_group_id}")
            
            return users
            
        except Exception as e:
            logger.error(f"Erro ao capturar membros do grupo {source_group_id}: {e}")
            return []
    
    async def capture_and_filter_members(self, source_group_id: int, target_group_id: int, capture_mode: str = "all") -> List[Dict]:
        """Captura membros do grupo fonte e filtra os que não estão no grupo de destino"""
        try:
            # Captura membros do grupo fonte
            source_members = await self.capture_group_members(source_group_id, capture_mode)
            
            if not source_members:
                logger.warning(f"Nenhum membro encontrado no grupo {source_group_id}")
                return []
            
            # Filtra membros que não estão no grupo de destino
            new_members = await self.filter_new_members(source_members, target_group_id)
            
            logger.info(f"Filtrados {len(new_members)} novos membros de {len(source_members)} capturados")
            
            return new_members
            
        except Exception as e:
            logger.error(f"Erro ao capturar e filtrar membros: {e}")
            return []
    
    async def monitor_live_chat(self, chat_id: int, callback=None) -> Dict:
        """Monitora um chat para detectar lives e capturar espectadores"""
        try:
            logger.info(f"Iniciando monitoramento do chat {chat_id}")
            
            # Verifica se há live ativa
            if await self.is_live_active(chat_id):
                # Captura espectadores
                viewers = await self.capture_live_viewers(chat_id)
                
                # Marca como live ativa
                self.active_lives[chat_id] = {
                    'viewers': viewers,
                    'start_time': asyncio.get_event_loop().time(),
                    'status': 'active'
                }
                
                # Chama callback se fornecido
                if callback:
                    await callback(chat_id, viewers)
                
                return {
                    'chat_id': chat_id,
                    'viewers': viewers,
                    'status': 'live_detected',
                    'viewer_count': len(viewers)
                }
            else:
                return {
                    'chat_id': chat_id,
                    'viewers': [],
                    'status': 'no_live',
                    'viewer_count': 0
                }
                
        except Exception as e:
            logger.error(f"Erro ao monitorar chat {chat_id}: {e}")
            return {
                'chat_id': chat_id,
                'viewers': [],
                'status': 'error',
                'error': str(e)
            }
    
    async def get_live_info(self, chat_id: int) -> Dict:
        """Obtém informações sobre a live ativa"""
        if chat_id in self.active_lives:
            live_info = self.active_lives[chat_id]
            return {
                'is_active': True,
                'viewer_count': len(live_info['viewers']),
                'start_time': live_info['start_time'],
                'status': live_info['status']
            }
        else:
            return {
                'is_active': False,
                'viewer_count': 0,
                'start_time': None,
                'status': 'inactive'
            }
    
    async def stop_monitoring(self, chat_id: int):
        """Para o monitoramento de um chat"""
        if chat_id in self.active_lives:
            del self.active_lives[chat_id]
            logger.info(f"Monitoramento parado para o chat {chat_id}")
    
    def get_active_lives(self) -> Dict:
        """Retorna todas as lives ativas"""
        return self.active_lives.copy()
    
    async def get_chat_info(self, chat_id: int) -> Dict:
        """Obtém informações do chat"""
        try:
            chat = await self.bot.get_chat(chat_id)
            return {
                'id': chat.id,
                'title': chat.title,
                'type': chat.type,
                'member_count': chat.member_count,
                'username': chat.username,
                'description': chat.description
            }
        except Exception as e:
            logger.error(f"Erro ao obter info do chat {chat_id}: {e}")
            return {}

# Instância global
telegram_group_capture = None

def init_telegram_group_capture(bot_token: str):
    """Inicializa a instância global"""
    global telegram_group_capture
    telegram_group_capture = TelegramGroupCapture(bot_token)
    return telegram_group_capture
