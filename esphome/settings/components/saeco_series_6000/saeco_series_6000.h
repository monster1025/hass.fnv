#pragma once

#include "esphome/core/component.h"
#include "esphome/components/uart/uart.h"
#include "esphome/components/sensor/sensor.h"
#include "esphome/core/automation.h"
#include "esphome/components/button/button.h"

namespace esphome {
namespace saeco_series_6000 {

// Buffer sizes for packet sniffing
constexpr size_t DISPLAY_BUFFER_SIZE = 128;
constexpr size_t MAINBOARD_BUFFER_SIZE = 128;

class SaecoSeries6000 : public Component {
 public:
  void set_uart_display(uart::UARTComponent *uart_display) { uart_display_ = uart_display; }
  void set_uart_mainboard(uart::UARTComponent *uart_mainboard) { uart_mainboard_ = uart_mainboard; }
  void set_debug(bool debug) { debug_ = debug; }
  void set_status_sensor(sensor::Sensor *sensor) { status_sensor_ = sensor; }
  void loop() override;
  void dump_config() override;
  void send_packet_to_mainboard(const std::vector<uint8_t> &data);
  void send_packets_to_mainboard(const std::vector<std::vector<uint8_t>> &packets, uint32_t delay_ms = 10);
  void send_packets_to_mainboard(const std::vector<std::string>& hex_packets, uint32_t delay_ms = 10);
  void send_packets_to_mainboard(const std::string& hex_packet, uint32_t delay_ms = 10);

 protected:
  uart::UARTComponent *uart_display_;
  uart::UARTComponent *uart_mainboard_;
  bool debug_{false};
  sensor::Sensor *status_sensor_{nullptr};

 private:
  uint8_t display_buffer_[DISPLAY_BUFFER_SIZE];
  uint16_t display_buffer_pos_{0};

  uint8_t mainboard_buffer_[MAINBOARD_BUFFER_SIZE];
  uint16_t mainboard_buffer_pos_{0};

  uint8_t display_last_bytes_[3] = {0, 0, 0};
  uint8_t mainboard_last_bytes_[3] = {0, 0, 0};
  
  uint8_t display_sync_count_{0};
  uint8_t mainboard_sync_count_{0};

  uint8_t last_display_counter_{0};
  void update_display_counter_from_packet(const uint8_t* buffer, uint16_t size);
  
  void process_display_byte(uint8_t byte);
  void process_mainboard_byte(uint8_t byte);

  void parse_display_packet(const uint8_t* buffer, uint16_t size);
  void parse_mainboard_packet(const uint8_t* buffer, uint16_t size);
  void parse_b0_packet(const uint8_t* buffer, uint16_t size);
  void parse_b5_packet(const uint8_t* buffer, uint16_t size);
  void pub_status(uint8_t status);
  static const uint8_t BitReverse[256];
  uint32_t calc_crc(const std::vector<uint8_t>& data, size_t start, size_t end);
  std::vector<uint8_t> parse_hex_string_to_bytes(const std::string& hex_string);
};

class SaecoSendPacketsButton : public esphome::button::Button, public esphome::Component {
 public:
  void set_parent(SaecoSeries6000 *parent) { parent_ = parent; }
  void set_packets(const std::vector<std::vector<uint8_t>> &packets) { packets_ = packets; }
  void set_delay_ms(uint32_t delay_ms) { delay_ms_ = delay_ms; }
  void press_action() override {
    if (parent_ != nullptr) {
      parent_->send_packets_to_mainboard(packets_, delay_ms_);
    }
  }
 private:
  SaecoSeries6000 *parent_{nullptr};
  std::vector<std::vector<uint8_t>> packets_;
  uint32_t delay_ms_{10};
};

}  // namespace saeco_series_6000
}  // namespace esphome 