#include "saeco_series_6000.h"
#include "esphome/core/log.h"
#include <vector>

namespace esphome {
namespace saeco_series_6000 {

static const char *TAG = "saeco_series_6000";
static uint32_t last_activity_time = 0;

void SaecoSeries6000::loop() {
  uint8_t byte;
  
  // Bridge from uart_display (display) to uart_mainboard (mainboard)
  while (uart_display_->available()) {
    uart_display_->read_byte(&byte);
    uart_mainboard_->write_byte(byte);  // Mirror byte immediately
    process_display_byte(byte); // Process the "sniffed" byte
  }
  
  // Bridge from uart_mainboard (mainboard) to uart_display (display)
  while (uart_mainboard_->available()) {
    uart_mainboard_->read_byte(&byte);
    uart_display_->write_byte(byte);  // Mirror byte immediately
    process_mainboard_byte(byte); // Process the "sniffed" byte
  }
  // Контроль активности UART (выключение через 15 сек)
  static uint32_t last_check = 0;
  uint32_t now = millis();
  if (now - last_check > 1000) { // проверяем каждую секунду
    last_check = now;
    if (now - last_activity_time > 15000) {
      pub_status(2); // публикуем статус "выключено"
      last_activity_time = now; // чтобы не публиковать повторно
    }
  }
}

void SaecoSeries6000::process_display_byte(uint8_t byte) {
    // Если получили первый 0xAA — начинаем новый пакет
    if (byte == 0xAA && display_buffer_pos_ == 0) {
        display_buffer_[display_buffer_pos_++] = byte;
        return;
    }
    // Если уже начали собирать пакет
    if (display_buffer_pos_ > 0 && display_buffer_pos_ < DISPLAY_BUFFER_SIZE) {
        display_buffer_[display_buffer_pos_++] = byte;
        if (byte == 0x55) {
            parse_display_packet(display_buffer_, display_buffer_pos_);
            display_buffer_pos_ = 0;
        }
    }
}

void SaecoSeries6000::process_mainboard_byte(uint8_t byte) {
    // Если получили первый 0xAA — начинаем новый пакет
    if (byte == 0xAA && mainboard_buffer_pos_ == 0) {
        mainboard_buffer_[mainboard_buffer_pos_++] = byte;
        return;
    }
    // Если уже начали собирать пакет
    if (mainboard_buffer_pos_ > 0 && mainboard_buffer_pos_ < MAINBOARD_BUFFER_SIZE) {
        mainboard_buffer_[mainboard_buffer_pos_++] = byte;
        if (byte == 0x55) {
            parse_mainboard_packet(mainboard_buffer_, mainboard_buffer_pos_);
            mainboard_buffer_pos_ = 0;
        }
    }
}

void SaecoSeries6000::update_display_counter_from_packet(const uint8_t* buffer, uint16_t size) {
    if (size > 4 && buffer[3] != 0xFF) {
        last_display_counter_ = buffer[4];
    }
}

void SaecoSeries6000::parse_display_packet(const uint8_t* buffer, uint16_t size) {
    if (debug_) {
        std::vector<char> hex_buffer;
        hex_buffer.resize(size * 3 + 1);
        for (uint16_t i = 0; i < size; i++) {
            sprintf(hex_buffer.data() + i * 3, "%02X ", buffer[i]);
        }
        if (size > 4 && buffer[3] != 0xFF){
            ESP_LOGI(TAG, "Packet from Display: %s", hex_buffer.data());
        }
    }
    update_display_counter_from_packet(buffer, size);
    // Здесь больше не парсим B0-пакеты, только debug
}

// Разбор пакета B0 (системные статусы кофемашины)
// buffer[6], buffer[7], buffer[9] содержат коды состояния
void SaecoSeries6000::parse_b0_packet(const uint8_t* buffer, uint16_t size) {
    if (size < 10) return;
    if (buffer[6] == 0x0E) {
        if (buffer[9] == 0x00) {
            pub_status(20); // 20: "Опорож. контейнер для коф. гущи"
        } else {
            if ((buffer[9] & 0x40) != 0) {
                pub_status(22); // 22: "Воды нет"
            } else {
                pub_status(17); // 17: "Вода есть"
            }
            if ((buffer[9] & 0x80) != 0) {
                pub_status(23); // 23: "Извлечен контейнер для жмыха"
            } else {
                pub_status(18); // 18: "Вставлен контейнер для жмыха"
            }
        }
    } else if (buffer[6] == 0x06) {
        pub_status(21); // 21: "Готово/Выберите напиток"
    } else if (buffer[6] == 0x0C) {
        if (buffer[7] == 0x01) {
            pub_status(8); // 8: "Наслаждайтесь"
        } else if (buffer[7] == 0x02) {
            pub_status(15); // 15: "Что-то (07 0C 02)"
        }
    } else if (buffer[6] == 0x07) {
        if (buffer[7] == 0x0E) {
            pub_status(9); // 9: "Нагрев воды"
        } else if (buffer[7] == 0x0D) {
            pub_status(10); // 10: "Перемалываем зерна"
        } else if (buffer[7] == 0x10) {
            pub_status(3); // 3: "Наливаем молоко"
        } else if (buffer[7] == 0x11) {
            pub_status(4); // 4: "Наливаем кофе"
        } else if (buffer[7] == 0x12) {
            pub_status(5); // 5: "Предварительное дозирование"
        } else if (buffer[7] == 0x13) {
            pub_status(6); // 6: "Создание пара для молока"
        } else if (buffer[7] == 0x14) {
            pub_status(7); // 7: "Заварочный узел в положение заваривания"
        } else if (buffer[7] == 0x15) {
            pub_status(15); // 15: "Наслаждайтесь"
        }
    } else if (buffer[6] == 0x08) {
        if (buffer[7] == 0x0E) {
            pub_status(14); // 14: "Нагревание"
        } else if (buffer[7] == 0x02) {
            pub_status(11); // 11: "Промывка"
        } else if (buffer[7] == 0x14) {
            pub_status(13); // 13: "Что-то (07 08 14)"
        } else if (buffer[7] == 0x05) {
            pub_status(12); // 12: "Зерна закончились"
        } else if (buffer[7] == 0x16) {
            pub_status(24); // 24: "Удаление накипи стадия 1"
        } else if (buffer[7] == 0x18) {
            pub_status(25); // 25: "Удаление накипи стадия 2"
        }
    } else if (buffer[7] == 0x00) {
        if (buffer[6] == 0x01) {
            pub_status(1); // 1: "Что-то (07 01 00)"
        } else if (buffer[6] == 0x05) {
            pub_status(2); // 2: "Выключено"
        }
    }
}

// Разбор пакета B5 (коды ошибок кофемашины)
// buffer[10], buffer[11] содержат коды ошибок
void SaecoSeries6000::parse_b5_packet(const uint8_t* buffer, uint16_t size) {
    if (size <= 12) return;
    if (buffer[10] == 0x00) {
        if (buffer[11] == 0x00) pub_status(30); // 30: "Ошибка 0x00"
        else if (buffer[11] == 0x0B) pub_status(31); // 31: "Ошибка 0x0B"
        else if (buffer[11] == 0xE6) pub_status(32); // 32: "Ошибка 0xE6"
        else if (buffer[11] == 0x80) pub_status(33); // 33: "Ошибка 0x80"
        else if (buffer[11] == 0xCB) pub_status(34); // 34: "Ошибка 0xCB"
        else if (buffer[11] == 0xFF) pub_status(35); // 35: "Ошибка 0xFF"
        else if (buffer[11] == 0xA0) pub_status(36); // 36: "Ошибка 0xA0"
    } else if (buffer[10] == 0x01) {
        pub_status(37); // 37: "Статус2 0x01"
    }
}

void SaecoSeries6000::parse_mainboard_packet(const uint8_t* buffer, uint16_t size) {
    last_activity_time = millis(); // сбрасываем таймер активности при любом пакете
    if (debug_) {
        // std::vector<char> hex_buffer;
        // hex_buffer.resize(size * 3 + 1);
        // for (uint16_t i = 0; i < size; i++) {
        //     sprintf(hex_buffer.data() + i * 3, "%02X ", buffer[i]);
        // }
        //ESP_LOGD(TAG, "Packet from Mainboard: %s", hex_buffer.data());
        //ESP_LOGD(TAG, "parse_mainboard_packet: size=%u", size);
    }
    // Парсим B0
    if (size > 4 && buffer[3] == 0xB0) {
        parse_b0_packet(buffer, size);
    } else if (size > 12 && buffer[3] == 0xB5) {
        parse_b5_packet(buffer, size);
    }
}

void SaecoSeries6000::pub_status(uint8_t status) {
    if (status_sensor_ != nullptr) {
        status_sensor_->publish_state(status);
    }
}

void SaecoSeries6000::dump_config() {
    ESP_LOGCONFIG(TAG, "Saeco Series 6000 UART Bridge");
    ESP_LOGCONFIG(TAG, "  UART Display (uart_display): %p", uart_display_);
    ESP_LOGCONFIG(TAG, "  UART Mainboard (uart_mainboard): %p", uart_mainboard_);
    ESP_LOGCONFIG(TAG, "  Debug mode: %s", ONOFF(this->debug_));
}

void SaecoSeries6000::send_packet_to_mainboard(const std::vector<uint8_t> &data) {
    ESP_LOGI(TAG, "Send to Mainboard pressed.");
    for (auto b : data) {
        uart_mainboard_->write_byte(b);
    }
}

const uint8_t SaecoSeries6000::BitReverse[256] = {
  0x00,0x80,0x40,0xC0,0x20,0xA0,0x60,0xE0,0x10,0x90,0x50,0xD0,0x30,0xB0,0x70,0xF0,
  0x08,0x88,0x48,0xC8,0x28,0xA8,0x68,0xE8,0x18,0x98,0x58,0xD8,0x38,0xB8,0x78,0xF8,
  0x04,0x84,0x44,0xC4,0x24,0xA4,0x64,0xE4,0x14,0x94,0x54,0xD4,0x34,0xB4,0x74,0xF4,
  0x0C,0x8C,0x4C,0xCC,0x2C,0xAC,0x6C,0xEC,0x1C,0x9C,0x5C,0xDC,0x3C,0xBC,0x7C,0xFC,
  0x02,0x82,0x42,0xC2,0x22,0xA2,0x62,0xE2,0x12,0x92,0x52,0xD2,0x32,0xB2,0x72,0xF2,
  0x0A,0x8A,0x4A,0xCA,0x2A,0xAA,0x6A,0xEA,0x1A,0x9A,0x5A,0xDA,0x3A,0xBA,0x7A,0xFA,
  0x06,0x86,0x46,0xC6,0x26,0xA6,0x66,0xE6,0x16,0x96,0x56,0xD6,0x36,0xB6,0x76,0xF6,
  0x0E,0x8E,0x4E,0xCE,0x2E,0xAE,0x6E,0xEE,0x1E,0x9E,0x5E,0xDE,0x3E,0xBE,0x7E,0xFE,
  0x01,0x81,0x41,0xC1,0x21,0xA1,0x61,0xE1,0x11,0x91,0x51,0xD1,0x31,0xB1,0x71,0xF1,
  0x09,0x89,0x49,0xC9,0x29,0xA9,0x69,0xE9,0x19,0x99,0x59,0xD9,0x39,0xB9,0x79,0xF9,
  0x05,0x85,0x45,0xC5,0x25,0xA5,0x65,0xE5,0x15,0x95,0x55,0xD5,0x35,0xB5,0x75,0xF5,
  0x0D,0x8D,0x4D,0xCD,0x2D,0xAD,0x6D,0xED,0x1D,0x9D,0x5D,0xDD,0x3D,0xBD,0x7D,0xFD,
  0x03,0x83,0x43,0xC3,0x23,0xA3,0x63,0xE3,0x13,0x93,0x53,0xD3,0x33,0xB3,0x73,0xF3,
  0x0B,0x8B,0x4B,0xCB,0x2B,0xAB,0x6B,0xEB,0x1B,0x9B,0x5B,0xDB,0x3B,0xBB,0x7B,0xFB,
  0x07,0x87,0x47,0xC7,0x27,0xA7,0x67,0xE7,0x17,0x97,0x57,0xD7,0x37,0xB7,0x77,0xF7,
  0x0F,0x8F,0x4F,0xCF,0x2F,0xAF,0x6F,0xEF,0x1F,0x9F,0x5F,0xDF,0x3F,0xBF,0x7F,0xFF
};

uint32_t SaecoSeries6000::calc_crc(const std::vector<uint8_t>& data, size_t start, size_t end) {
    uint32_t crc = 0xFFFFFFFF;
    const uint32_t POLY = 0x04C11DB7;
    if (start >= end) return 0;
    // start
    uint8_t val = data[start];
    ((uint8_t*)(&crc))[3] ^= BitReverse[val];
    for (uint8_t j = 0; j < 8; j++) {
        if (crc & 0x80000000) {
            crc = (crc << 1) ^ POLY;
        } else {
            crc <<= 1;
        }
    }
    // остальные байты
    for (size_t i = start + 1; i < end; i++) {
        uint8_t v = data[i];
        ((uint8_t*)(&crc))[3] ^= BitReverse[v];
        for (uint8_t j = 0; j < 8; j++) {
            if (crc & 0x80000000) {
                crc = (crc << 1) ^ POLY;
            } else {
                crc <<= 1;
            }
        }
    }
    uint32_t t32 = 0;
    ((uint8_t*)(&t32))[0] = BitReverse[((uint8_t*)(&crc))[3]];
    ((uint8_t*)(&t32))[1] = BitReverse[((uint8_t*)(&crc))[2]];
    ((uint8_t*)(&t32))[2] = BitReverse[((uint8_t*)(&crc))[1]];
    ((uint8_t*)(&t32))[3] = BitReverse[((uint8_t*)(&crc))[0]];
    crc = t32 ^ 0xFFFFFFFF;
    return crc;
}

std::vector<uint8_t> SaecoSeries6000::parse_hex_string_to_bytes(const std::string& hex_string) {
    std::vector<uint8_t> pkt;
    size_t pos = 0;
    while (pos < hex_string.size()) {
        while (pos < hex_string.size() && isspace(hex_string[pos])) ++pos;
        if (pos >= hex_string.size()) break;
        char* endptr = nullptr;
        uint8_t byte = static_cast<uint8_t>(std::strtoul(hex_string.c_str() + pos, &endptr, 16));
        pkt.push_back(byte);
        if (endptr == nullptr || endptr == hex_string.c_str() + pos) break;
        pos = endptr - hex_string.c_str();
    }
    return pkt;
}

void SaecoSeries6000::send_packets_to_mainboard(const std::string& hex_packet, uint32_t delay_ms) {
    std::vector<std::vector<uint8_t>> pkts = {parse_hex_string_to_bytes(hex_packet)};
    send_packets_to_mainboard(pkts, delay_ms);
}

void SaecoSeries6000::send_packets_to_mainboard(const std::vector<std::string>& hex_packets, uint32_t delay_ms) {
    std::vector<std::vector<uint8_t>> pkts;
    for (const auto& s : hex_packets) {
        pkts.push_back(parse_hex_string_to_bytes(s));
    }
    send_packets_to_mainboard(pkts, delay_ms);
}

void SaecoSeries6000::send_packets_to_mainboard(const std::vector<std::vector<uint8_t>> &packets, uint32_t delay_ms) {
    uint8_t counter = (last_display_counter_ + 1) & 0xFF;
    for (size_t i = 0; i < packets.size(); ++i) {
        std::vector<uint8_t> pkt = packets[i];
        // Заменяем байт счетчика (4-й байт)
        if (pkt.size() > 4) {
            pkt[4] = counter;
        }
        // Пересчёт CRC: ищем преамбулу 0xAA 0xAA 0xAA, считаем CRC по данным между преамбулой и последними 5 байтами
        if (pkt.size() > 8) {
            size_t preamble = 0;
            if (pkt[0] == 0xAA && pkt[1] == 0xAA && pkt[2] == 0xAA) {
                preamble = 3;
            }
            size_t crc_start = preamble;
            size_t crc_end = pkt.size() - 5; // не включаем 4 CRC и 0x55
            uint32_t crc = calc_crc(pkt, crc_start, crc_end);
            // Заменяем последние 4 байта перед 0x55 на новую CRC
            pkt[pkt.size()-2] = (crc >> 24) & 0xFF;
            pkt[pkt.size()-3] = (crc >> 16) & 0xFF;
            pkt[pkt.size()-4] = (crc >> 8) & 0xFF;
            pkt[pkt.size()-5] = crc & 0xFF;
            // pkt[pkt.size()-5] = (crc >> 24) & 0xFF;
            // pkt[pkt.size()-4] = (crc >> 16) & 0xFF;
            // pkt[pkt.size()-3] = (crc >> 8) & 0xFF;
            // pkt[pkt.size()-2] = (crc) & 0xFF;
        }
        // Логируем пакет перед отправкой
        std::string log_str;
        char buf[8];
        for (auto b : pkt) {
            snprintf(buf, sizeof(buf), "%02X ", b);
            log_str += buf;
        }
        ESP_LOGI(TAG, "Send to Mainboard: %s", log_str.c_str());
        send_packet_to_mainboard(pkt);
        counter = (counter + 1) & 0xFF;
        delay(delay_ms);
    }
    last_display_counter_ = (counter - 1) & 0xFF;
}

// Реализация SendPacketsAction полностью в header (saeco_series_6000.h)

}  // namespace saeco_series_6000
}  // namespace esphome 