# Docker контейнеры и настройки

## Обзор сервисов

### Основные сервисы

#### Home Assistant (hass)
- **Образ**: `homeassistant/home-assistant:stable`
- **Порт**: 8123
- **Зависимости**: mosquitto, postgres
- **Особенности**: 
  - Интеграция с USB устройствами (`/dev/ttyUSB0`)
  - Health check каждые 30 секунд
  - Логирование с ограничением размера 50MB

#### AppDaemon
- **Сборка**: Кастомный образ из `./appdaemon/docker`
- **Зависимости**: hass
- **Особенности**: 
  - Автоматизация и скрипты
  - Логирование с ограничением 10MB

#### ESPHome
- **Образ**: `esphome/esphome:2025.6`
- **Порт**: 6052
- **Функционал**: Управление ESP устройствами

#### Zigbee2MQTT
- **Образ**: `koenkk/zigbee2mqtt:latest`
- **Порт**: 8080
- **Особенности**: Health check каждые 30 секунд

### Инфраструктурные сервисы

#### Mosquitto (MQTT брокер)
- **Сборка**: Кастомный образ из `./mosquitto/docker`
- **Порт**: 1883
- **Конфигурация**: `./mosquitto/settings/mqtt.env`

#### PostgreSQL
- **Образ**: `postgres:16.1`
- **Данные**: `./postgres/settings/data`
- **Конфигурация**: `./postgres/settings/postgres.env`

#### Nginx
- **Образ**: `nginx`
- **Порты**: 80, 443
- **SSL**: Интеграция с certbot
- **Конфигурация**: `./nginx/settings/site-confs`

#### Certbot
- **Сборка**: Кастомный образ из `./certbot/docker`
- **Порт**: 8081
- **Функционал**: Автоматическое обновление SSL сертификатов

### Специализированные сервисы

#### Matter Bridge
- **Образ**: `ghcr.io/t0bst4r/home-assistant-matter-hub:latest`
- **Порты**: 8482, 5353, 5540, 5541
- **Режим сети**: host
- **Интеграция**: Home Assistant через API токен

#### HomeConnect2MQTT
- **Сборка**: Кастомный образ из `./homeconnect2mqtt/docker`
- **Порт**: 5001
- **Функционал**: Интеграция бытовой техники Bosch/Siemens

#### Neptun2MQTT
- **Сборка**: Кастомный образ из `./neptun2mqtt/docker`
- **Конфигурация**: `./neptun2mqtt/settings/neptun.env`

#### DDNS
- **Сборка**: Кастомный образ из `./ddns/docker`
- **Конфигурация**: `./ddns/settings/token.env`
- **Субдомен**: home-fnv

#### Node-RED
- **Сборка**: Кастомный образ из `./node-red/docker`
- **Порт**: 1880
- **Зависимости**: hass
- **Функционал**: Визуальное программирование автоматизации

## Переменные окружения

### Общие настройки
- **TZ**: Europe/Moscow (для Node-RED)
- **Логирование**: JSON формат с ограничением размера файлов

### Специфичные настройки
- **HC_MQTT_HOST**: 192.168.1.6 (HomeConnect)
- **HC_MQTT_USER**: hass
- **HC_MQTT_PASSWORD**: mqttpass
- **HAMH_HOME_ASSISTANT_URL**: http://192.168.1.6:8123/
- **HAMH_LOG_LEVEL**: info

## Мониторинг и логирование

Все сервисы используют JSON логирование с ограничением размера:
- **Основные сервисы**: 50MB
- **Вспомогательные**: 10MB
- **Health checks**: Для hass и zigbee2mqtt

## Сеть и безопасность

- **Привилегированный режим**: Отключен для большинства сервисов
- **Network mode**: host только для matter-bridge
- **Порты**: Минимально необходимые для каждого сервиса
- **SSL**: Автоматическое управление через certbot 