import appdaemon.plugins.hass.hassapi as hass
import datetime
import globals

class BMSMonitor(hass.Hass):
    def initialize(self):
        # Получаем настройки из apps.yaml
        self.chat_id = self.args.get("chat_id")
        self.power_entity = self.args.get("power_sensor")
        self.soc_entity = self.args.get("soc_sensor")
        self.current_entity = self.args.get("current_sensor")
        self.voltage_entity = self.args.get("voltage_sensor")
        self.threshold = float(self.args.get("power_threshold", 5))
        self.interval = int(self.args.get("discharge_interval", 300))
        self.notification_target = self.args.get("notification_target", 'telegram')

        # Внутренние переменные состояния
        self.current_state = "IDLE" # IDLE, CHARGING, DISCHARGING
        self.timer_handle = None
        self.was_charging = False

        # Переменная для хранения времени начала отключения
        self.outage_start_time = None

        # Слушаем изменения мощности
        self.listen_state(self.on_power_change, self.power_entity)
        # Слушаем SOC для детектирования 100%
        self.listen_state(self.on_soc_change, self.soc_entity)

        self.log("BMS Monitor запущен. Ожидание изменений...")

    def on_power_change(self, entity, attribute, old, new, kwargs):
        try:
            power = float(new)
        except (ValueError, TypeError):
            return

        # Определяем новый режим
        if power > self.threshold:
            new_state = "CHARGING"
        elif power < -self.threshold:
            new_state = "DISCHARGING"
        else:
            new_state = "IDLE"

        # Логика переходов состояний
        if self.current_state != new_state:
            self.log(f"Смена состояния BMS: {self.current_state} -> {new_state}")

            # 1. Переход в разрядку (Отключили питание)
            if new_state == "DISCHARGING" and self.current_state != "DISCHARGING":
                # Фиксируем время начала отключения
                self.outage_start_time = datetime.datetime.now()

                self.send_telegram("⚠️ <b>ВНИМАНИЕ: Отключено питание!</b>\nБатарея перешла в режим разрядки.", "html")
                self.start_discharge_timer()

            # 2. Выход из разрядки (Питание восстановлено)
            # Срабатывает при переходе DISCHARGING -> IDLE или DISCHARGING -> CHARGING
            elif self.current_state == "DISCHARGING" and new_state in ("IDLE", "CHARGING"):
                duration_msg = ""
                if self.outage_start_time:
                    duration = datetime.datetime.now() - self.outage_start_time
                    duration_msg = f"\n⏱ <b>Время без электричества: {self._format_timedelta(duration)}</b>"
                    self.outage_start_time = None # Сбрасываем таймер

                self.send_telegram(f"✅ <b>Питание восстановлено!</b>\nБатарея вышла из режима разрядки.{duration_msg}", "html")
                self.stop_discharge_timer()

            # 3. Переход в простой после зарядки (Зарядка окончена)
            elif new_state == "IDLE" and self.current_state == "CHARGING":
                self.send_telegram("🔋 <b>Зарядка завершена!</b>\nБатарея полностью заряжена или нагрузка отключена.", "html")

            # 4. Переход IDLE -> CHARGING (если не было разрядки перед этим)
            elif new_state == "CHARGING" and self.current_state == "IDLE":
                # Можно добавить отдельное уведомление, если нужно
                pass

            self.current_state = new_state
            self.was_charging = (new_state == "CHARGING")

    def on_soc_change(self, entity, attribute, old, new, kwargs):
        # Дополнительная проверка на 100% SOC, если мощность еще не упала в ноль
        try:
            soc = float(new)
            if soc >= 100 and self.current_state == "CHARGING" and not self.was_charging:
                 # Небольшая защита от повторных уведомлений
                 self.was_charging = True
        except (ValueError, TypeError):
            pass

    def start_discharge_timer(self):
        if self.timer_handle is None:
            # Запускаем таймер: сразу первое сообщение, потом каждые N секунд
            self.send_status_report()
            self.timer_handle = self.run_every(self.periodic_status, datetime.datetime.now(), self.interval)
            self.log("Таймер статуса разрядки запущен")

    def stop_discharge_timer(self):
        if self.timer_handle is not None:
            self.cancel_timer(self.timer_handle)
            self.timer_handle = None
            self.log("Таймер статуса разрядки остановлен")

    def periodic_status(self, kwargs):
        # Проверяем, все ли еще в режиме разрядки перед отправкой
        if self.current_state == "DISCHARGING":
            self.send_status_report()
        else:
            self.stop_discharge_timer()

    def _format_timedelta(self, td):
        """Преобразует timedelta в строку вида 'X ч Y мин'"""
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        parts = []
        if hours > 0:
            parts.append(f"{hours} ч")
        parts.append(f"{minutes} мин")

        return " ".join(parts)

    def send_status_report(self):
        try:
            # Получаем значения напрямую
            power_raw = self.get_state(self.power_entity)
            soc_raw = self.get_state(self.soc_entity)
            current_raw = self.get_state(self.current_entity)
            voltage_raw = self.get_state(self.voltage_entity)

            # Преобразуем и округляем средствами Python
            power = round(float(power_raw), 1) if power_raw not in (None, 'unknown', 'unavailable') else 0
            soc = round(float(soc_raw), 1) if soc_raw not in (None, 'unknown', 'unavailable') else 0
            current = round(float(current_raw), 2) if current_raw not in (None, 'unknown', 'unavailable') else 0
            voltage = round(float(voltage_raw), 2) if voltage_raw not in (None, 'unknown', 'unavailable') else 0

            # Определяем цвет/иконку для направления тока
            direction = "🔻 Разряд" if power < 0 else "🔺 Заряд"

            # Добавляем время без электричества, если известно
            outage_info = ""
            if self.outage_start_time:
                duration = datetime.datetime.now() - self.outage_start_time
                outage_info = f"\n⏳ Без света: <b>{self._format_timedelta(duration)}</b>"

            msg = (
                f"📊 <b>Статус батареи (JK BMS)</b>\n\n"
                f"🔋 SOC: <b>{soc}%</b>\n"
                f"⚡ Мощность: <b>{power} Вт</b> ({direction})\n"
                f"🔌 Ток: <b>{current} А</b>\n"
                f"🔋 Напряжение: <b>{voltage} В</b>"
                f"{outage_info}\n"
                f"🕒 Время: {datetime.datetime.now().strftime('%H:%M:%S')}"
            )
            self.send_telegram(msg, "html")
        except Exception as e:
            self.log(f"Ошибка при отправке статуса: {e}")

    def send_telegram(self, message, parse_mode="html"):
        try:
            globals.send_telegram(self, message, target = self.notification_target, parse_mode = parse_mode)
        except Exception as e:
            self.log(f"Ошибка отправки Telegram: {e}")
