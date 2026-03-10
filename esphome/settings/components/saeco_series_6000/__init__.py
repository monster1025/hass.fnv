DEPENDENCIES = ["uart", "sensor"]

import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import uart, sensor, button
from esphome.const import CONF_ID, CONF_DEBUG
import esphome.automation as automation

CONF_STATE_SENSOR = "state_sensor"
CONF_B0_STATUS_SENSOR = "b0_status_sensor"
CONF_B5_STATUS_SENSOR = "b5_status_sensor"
CONF_BA_STATUS_SENSOR = "ba_status_sensor"
CONF_S90_STATUS_SENSOR = "s90_status_sensor"
CONF_S91_STATUS_SENSOR = "s91_status_sensor"
CONF_S93_STATUS_SENSOR = "s93_status_sensor"
CONF_WATER_SENSOR = "water_sensor"
CONF_COFFEE_GROUNDS_CONTAINER_SENSOR = "coffee_grounds_container_sensor"
CONF_PALLET_SENSOR = "pallet_sensor"
CONF_ERROR_CODE_SENSOR = "error_code_sensor"
CONF_GRAIN_TRAY_SENSOR = "grain_tray_sensor"
CONF_STATUS_TEXT_SENSOR = "status_text_sensor"
CONF_PACKETS = "packets"
CONF_SAECO_ID = "saeco_id"

saeco_series_6000_ns = cg.esphome_ns.namespace('saeco_series_6000')
SaecoSeries6000 = saeco_series_6000_ns.class_('SaecoSeries6000', cg.Component)

CONFIG_SCHEMA = cv.Schema({
    cv.Required(cv.CONF_ID): cv.declare_id(SaecoSeries6000),
    cv.Required('uart_display'): cv.use_id(uart.UARTComponent),
    cv.Required('uart_mainboard'): cv.use_id(uart.UARTComponent),
    cv.Optional(CONF_DEBUG, default=False): cv.boolean,
    cv.Optional(CONF_STATE_SENSOR): sensor.sensor_schema(),
}).extend(cv.COMPONENT_SCHEMA)

def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    yield cg.register_component(var, config)
    
    uart_display = yield cg.get_variable(config['uart_display'])
    cg.add(var.set_uart_display(uart_display))
    
    uart_mainboard = yield cg.get_variable(config['uart_mainboard'])
    cg.add(var.set_uart_mainboard(uart_mainboard))

    if config[CONF_DEBUG]:
        cg.add(var.set_debug(True))

    if CONF_STATE_SENSOR in config:
        sens = yield sensor.new_sensor(config[CONF_STATE_SENSOR])
        cg.add(var.set_status_sensor(sens)) 

def validate_packet(value):
    if isinstance(value, str):
        return [int(x, 16) for x in value.split()]
    return [cv.hex_uint8_t(x) for x in value]

SEND_PACKETS_ACTION_SCHEMA = cv.Schema({
    cv.Required(CONF_ID): cv.use_id(SaecoSeries6000),
    cv.Required(CONF_PACKETS): [cv.All(validate_packet)],
    cv.Optional("delay_ms", default=10): cv.positive_int,
})

SendPacketsAction = saeco_series_6000_ns.class_("SendPacketsAction", automation.Action)

@automation.register_action(
    "saeco_series_6000.send_packets",
    SendPacketsAction,
    SEND_PACKETS_ACTION_SCHEMA,
)
def send_packets_to_mainboard_action_to_code(config, action_id, template_arg, args):
    var = cg.new_Pvariable(action_id)
    parent = yield cg.get_variable(config[CONF_ID])
    var.set_parent(parent)
    var.set_packets(config[CONF_PACKETS])
    var.set_delay_ms(config.get("delay_ms", 10))
    return var 

SaecoSendPacketsButton = saeco_series_6000_ns.class_("SaecoSendPacketsButton", button.Button, cg.Component)

SAECO_SEND_PACKETS_BUTTON_SCHEMA = button.BUTTON_SCHEMA.extend({
    cv.GenerateID(): cv.declare_id(SaecoSendPacketsButton),
    cv.Required(CONF_ID): cv.use_id(SaecoSeries6000),
    cv.Required(CONF_PACKETS): [cv.All(validate_packet)],
    cv.Optional("delay_ms", default=10): cv.positive_int,
}).extend(cv.COMPONENT_SCHEMA)

async def saeco_send_packets_button_to_code(config):
    parent = await cg.get_variable(config[CONF_SAECO_ID])
    var = cg.new_Pvariable(config["id"])
    await cg.register_component(var, config)
    await button.register_button(var, config)
    cg.add(var.set_parent(parent))
    cg.add(var.set_packets(config[CONF_PACKETS]))
    cg.add(var.set_delay_ms(config.get("delay_ms", 10)))
    return var

button.register_button("saeco_series_6000", saeco_send_packets_button_to_code) 