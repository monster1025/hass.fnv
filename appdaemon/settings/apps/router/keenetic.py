import appdaemon.plugins.hass.hassapi as hass
import requests
from datetime import datetime

class TelegramInternetControl(hass.Hass):
    """
    Управление интернетом через Telegram команды.
    Поддерживает множественные MAC-адреса.
    """
    
    def initialize(self):
        """
        Инициализация приложения.
        """
        self.log("Telegram Internet Control initialized")
        
        # Конфигурация из apps.yaml
        self.api_url = self.args.get("api_url", "http://localhost:8000/run")
        self.api_user = self.args.get("api_user", "api_user")
        self.api_password = self.args.get("api_password", "strong_password")
        
        # Команды Telegram
        self.block_command = self.args.get("block_command", "Коля наказан").lower()
        self.unblock_command = self.args.get("unblock_command", "Включи Коле интернет").lower()
        
        # MAC адреса для управления (массив)
        self.target_macs = self.args.get("target_macs", [])
        if isinstance(self.target_macs, str):
            self.target_macs = [self.target_macs]
        
        # Разрешенные user_id (безопасность)
        self.allowed_users = self.args.get("allowed_users", [])
        if isinstance(self.allowed_users, int):
            self.allowed_users = [self.allowed_users]
        
        # Entity для прослушивания событий Telegram
        self.telegram_event_entity = self.args.get(
            "telegram_event_entity", 
            "event.home_assistant_fonvizina_update_event"
        )
        
        # Сервис для отправки ответов в Telegram
        self.notify_service = self.args.get("notify_service", "notify/telegram")
        
        # Сохраняем последнее обработанное время (для пропуска дублей)
        self.last_processed_time = None
        
        # Слушаем изменения состояния события Telegram
        self.listen_state(
            self.on_telegram_event,
            self.telegram_event_entity
        )
        
        self.log(f"Listening to: {self.telegram_event_entity}")
        self.log(f"Block command: '{self.block_command}'")
        self.log(f"Unblock command: '{self.unblock_command}'")
        self.log(f"Target MACs: {self.target_macs}")
        self.log(f"Allowed users: {self.allowed_users}")
        self.listen_event(self.yandex_intent, "yandex_intent")

    def yandex_intent(self, event_id, event_args, kwargs):
        self.log("{} {}".format(event_id, event_args))
        text = event_args['text']
        room = event_args['room']
        alice = event_args['entity_id']
        if text == self.block_command:
            self.handle_block_command('Monster1025')

    def say(self, entity_id, command):
      self.log('command = {}'.format(command))
      self.call_service('media_player/play_media', entity_id=entity_id, media_content_type='text', media_content_id=command)

    def on_telegram_event(self, entity, attribute, old, new, kwargs):
        """
        Обработка события Telegram.
        """
        try:
            # Получаем полный объект состояния с атрибутами
            state_data = self.get_state(entity, attribute="all")
            
            if state_data is None:
                self.log("State data is None")
                return
            
            # Получаем атрибуты
            attributes = state_data.get("attributes", {})
            
            if not attributes:
                self.log("No attributes in state data")
                return
            
            # Проверяем тип события (должно быть telegram_text)
            event_type = attributes.get("event_type", "")
            if event_type != "telegram_text":
                return
            
            # Получаем текст сообщения
            text = attributes.get("text", "").strip()
            if not text:
                return
            
            # Получаем user_id отправителя
            user_id = attributes.get("user_id")
            from_first = attributes.get("from_first", "Unknown")
            
            # Получаем время события для защиты от дублей
            event_time = attributes.get("date", "")
            
            # Пропускаем если уже обработали это событие
            if event_time == self.last_processed_time:
                self.log(f"Skipping duplicate event: {event_time}")
                return
            
            self.last_processed_time = event_time
            
            self.log(f"Telegram message from {from_first} (user_id: {user_id}): '{text}'")
            
            # Проверяем, разрешен ли пользователь
            if user_id not in self.allowed_users:
                self.log(f"User {user_id} not in allowed list. Ignoring.")
                return
            
            # Обрабатываем команды (регистронезависимо)
            text_lower = text.lower()
            
            if text_lower == self.block_command:
                self.handle_block_command(from_first)
            elif text_lower == self.unblock_command:
                self.handle_unblock_command(from_first)
                
        except Exception as e:
            self.log(f"Error processing Telegram event: {str(e)}")
            self.log(f"State data: {state_data if 'state_data' in locals() else 'N/A'}")
    
    def handle_block_command(self, user_name):
        """
        Блокировка интернета для всех MAC-адресов.
        """
        self.log(f"Blocking internet for {user_name}")
        
        if not self.target_macs:
            self.send_telegram_message(f"❌ {user_name}, не настроены MAC-адреса для блокировки!")
            self.log("No MAC addresses configured")
            return
        
        success_count = 0
        failed_macs = []
        
        for mac in self.target_macs:
            # Формируем команду для роутера
            command = f"ip hotspot host {mac} schedule schedule1"            
            self.log(f"Sending command: {command}")
            
            if self.send_to_router(command):
                success_count += 1
            else:
                failed_macs.append(mac)
        command = "system configuration save"
        self.log(f"Sending command: {command}")
        cmd = self.send_to_router(command)
        
        # Формируем отчет
        if success_count == len(self.target_macs):
            self.send_telegram_message(
                f"✅ {user_name}, интернет заблокирован для {success_count} устр-в!"
            )
            self.log(f"Internet blocked successfully for {success_count} devices")
        elif success_count > 0:
            self.send_telegram_message(
                f"⚠️ {user_name}, частично заблокировано: {success_count}/{len(self.target_macs)}. "
                f"Не удалось: {', '.join(failed_macs)}"
            )
            self.log(f"Partial block: {success_count}/{len(self.target_macs)}")
        else:
            self.send_telegram_message(f"❌ {user_name}, ошибка при блокировке интернета!")
            self.log("Failed to block internet")
    
    def handle_unblock_command(self, user_name):
        """
        Разблокировка интернета для всех MAC-адресов.
        """
        self.log(f"Unblocking internet for {user_name}")
        
        if not self.target_macs:
            self.send_telegram_message(f"❌ {user_name}, не настроены MAC-адреса для разблокировки!")
            self.log("No MAC addresses configured")
            return
        
        success_count = 0
        failed_macs = []
        
        for mac in self.target_macs:
            # Формируем команду для роутера
            command = f"ip hotspot host {mac} schedule schedule0"
            self.log(f"Sending command: {command}")
            cmd = self.send_to_router(command)

            if cmd:
                success_count += 1
            else:
                failed_macs.append(mac)
        command = "system configuration save"
        self.log(f"Sending command: {command}")
        cmd = self.send_to_router(command)
        
        # Формируем отчет
        if success_count == len(self.target_macs):
            self.send_telegram_message(
                f"✅ {user_name}, интернет включен для {success_count} устр-в!"
            )
            self.log(f"Internet unblocked successfully for {success_count} devices")
        elif success_count > 0:
            self.send_telegram_message(
                f"⚠️ {user_name}, частично включено: {success_count}/{len(self.target_macs)}. "
                f"Не удалось: {', '.join(failed_macs)}"
            )
            self.log(f"Partial unblock: {success_count}/{len(self.target_macs)}")
        else:
            self.send_telegram_message(f"❌ {user_name}, ошибка при включении интернета!")
            self.log("Failed to unblock internet")
    
    def send_to_router(self, command):
        """
        Отправка команды на роутер через API.
        """
        try:
            response = requests.post(
                self.api_url,
                json={"command": command},
                auth=(self.api_user, self.api_password),
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                exit_code = result.get("exit_code", -1)
                
                if exit_code == 0:
                    return True
                else:
                    stderr = result.get('stderr', '')
                    self.log(f"Router command failed with exit code: {exit_code}")
                    self.log(f"Stderr: {stderr}")
                    return False
            else:
                self.log(f"API request failed with status: {response.status_code}")
                self.log(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"Error sending command to router: {str(e)}")
            return False
    
    def send_telegram_message(self, message):
        """
        Отправка ответа в Telegram.
        """
        try:
            self.call_service(
                self.notify_service,
                message=message
            )
            self.log(f"Telegram message sent: {message}")
        except Exception as e:
            self.log(f"Error sending Telegram message: {str(e)}")