# Home Assistant конфигурация

## Общая структура

### Основные файлы
- `configuration.yaml` - Основная конфигурация
- `automations.yaml` - Автоматизации
- `scripts.yaml` - Скрипты
- `scenes.yaml` - Сцены
- `ui-lovelace.yaml` - Пользовательский интерфейс

### Директории
- `packages/` - Пакеты конфигурации по категориям
- `custom_components/` - Пользовательские компоненты
- `blueprints/` - Шаблоны автоматизаций
- `www/` - Веб-ресурсы

## Устройства в packages

### Кофемашина (coffee_maker.yaml)
**Производитель**: Philips  
**Модель**: 5400 Series

#### Сенсоры
- `coffee_machine_power_status` - Статус питания
- `coffee_philips_5400_status` - Общий статус
- `coffee_philips_5400_coffee_grounds_container` - Контейнер кофейной гущи
- `coffee_philips_5400_coffee_pallet` - Поддон
- `coffee_philips_5400_grain_tray` - Кофейные зерна в лотке
- `coffee_philips_5400_system_status` - Системный статус
- `coffee_philips_5400_making_coffee` - Приготовление кофе
- `coffee_philips_5400_internal_temperature` - Температура ESP32
- `coffee_philips_5400_error_code` - Системные ошибки
- `coffee_philips_5400_free_mem_size` - Размер свободной памяти

#### Управление
- `select.coffee_philips_5400_drink` - Выбор кофейных напитков
- `select.coffee_philips_5400_cups` - Количество порций
- `select.coffee_philips_5400_grind` - Крепость (зерно/молотый)
- `number.coffee_philips_5400_soffee` - Объем кофе
- `number.coffee_philips_5400_milk` - Объем молока
- `button.coffee_philips_5400_prepare` - Показать рецепт
- `button.coffee_philips_5400_build_coffee` - Приготовить кофе

#### Автоматизация
- `input_boolean.kitchen_coffee_machine_auto_coffee_making` - Авто приготовление
- `counter.coffee_machine_making_coffee` - Счетчик авто приготовления

### Посудомоечная машина (dishwasher.yaml)
**Интеграция**: HomeConnect через MQTT

#### Сенсоры
- `hc_dishwasher_state` - Статус работы
- `hc_dishwasher_remaining` - Время до конца программы
- `hc_dishwasher_running` - Признак работы

#### Бинарные сенсоры
- `hc_dishwasher_door` - Состояние дверцы
- `hc_dishwasher_power` - Статус питания

#### Счетчики
- `dishwasher_door_open_count` - Счетчик открытий дверцы

### Система отопления (climate/)
**Тип**: Кондиционеры и управление температурой

### Освещение (light/)
**Тип**: Управление освещением по комнатам

### Безопасность (alarm_and_presence/)
**Тип**: Система сигнализации и присутствия

### Уведомления (notifications/)
**Тип**: Система уведомлений

### Энергетика (power/)
**Тип**: Мониторинг энергопотребления

### Телевизоры (tv/)
**Тип**: Управление телевизорами

### Водоснабжение (watercontrol.yaml)
**Тип**: Контроль водоснабжения

### Замок (aqara_lock.yaml)
**Производитель**: Aqara  
**Тип**: Умный замок

### Счетчик тепла (heat_counter.yaml)
**Тип**: Счетчик тепловой энергии

## ESPHome устройства

### Кондиционеры
- `ac_mainroom.yaml` - Гостиная
- `ac_kitchen.yaml` - Кухня  
- `ac_childroom.yaml` - Детская
- `ac_bedroom.yaml` - Спальня

### Освещение
- `svetlana_bedside_lamp.yaml` - Прикроватная лампа Светланы
- `danil_bedside_lamp.yaml` - Прикроватная лампа Данила

### Датчики присутствия
- `presence_bedroom.yaml` - Спальня
- `presence_kladovka.yaml` - Кладовка

### Специализированные устройства
- `coffee-philips-5400.yaml` - Кофемашина Philips
- `senseair.yaml` - Датчик качества воздуха

## Интеграции

### MQTT
- **Брокер**: Mosquitto (порт 1883)
- **Топики**: homeconnect/*, neptun/*

### Zigbee
- **Координатор**: Zigbee2MQTT
- **Порт**: 8080
- **Устройства**: Датчики, выключатели, замки

### Matter
- **Мост**: Matter Bridge
- **Порты**: 8482, 5353, 5540, 5541
- **Режим**: host

### HomeConnect
- **Интеграция**: HomeConnect2MQTT
- **Порт**: 5001
- **Устройства**: Посудомойка, стиральная машина

### Neptun
- **Интеграция**: Neptun2MQTT
- **Функционал**: Контроль водоснабжения

## Автоматизации

### Основные категории
- Управление освещением
- Контроль климата
- Безопасность и присутствие
- Уведомления
- Энергосбережение

### Примеры автоматизаций
- Автоматическое приготовление кофе
- Управление освещением по присутствию
- Контроль температуры в комнатах
- Мониторинг состояния бытовой техники 