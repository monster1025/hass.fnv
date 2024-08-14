from pymodbus.client import ModbusTcpClient, ModbusTlsClient, ModbusSerialClient
from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder
from pymodbus.constants import Endian

import paho.mqtt.client as mqtt
import os
import time
import threading
import pymodbus
import time

MQTT_SERVER = os.getenv('MQTT_SERVER', "")
MQTT_PORT = os.getenv('MQTT_PORT', 1883)
MQTT_USER = os.getenv('MQTT_USER', "")
MQTT_PASS = os.getenv('MQTT_PASS', "")
QUERY_TIME = os.getenv('QUERY_TIME', 60)
PREFIX = os.getenv('PREFIX', 'home/watercontrol')
NEPTUN_IP = os.getenv('NEPTUN_IP', '192.168.1.147')
NEPTUN_ID = os.getenv('NEPTUN_ID', 240)
COUNTERS_SLOT = int(os.getenv('NEPTUN_WATER_COUNTERS_SLOT', 3))

###############################################################
slot_config = {1: [107, 109], 2:[111, 113], 3:[115, 117], 4:[119, 121]}

def prepare_mqtt():
	print("Connecting to MQTT server", MQTT_SERVER, ":", MQTT_PORT, "with username", MQTT_USER,":",MQTT_PASS)
	client = mqtt.Client()
	if (MQTT_USER != "" and MQTT_PASS != ""):
		client.username_pw_set(MQTT_USER, MQTT_PASS)
	client.connect(MQTT_SERVER, MQTT_PORT, 60)
 
	return client
 
def push_data(client, model, sid, data):
	for key, value in data.items():
		path = PATH_FMT.format(model=model,
							   sid=sid,
							   prop=key)
		client.publish(path, payload=value, qos=0, retain=True)

def on_mqtt_message(client, userdata, msg):
	print(msg.topic+" "+str(msg.payload))
	parts = msg.topic.replace(PREFIX, "").strip("/").split("/")
	print(parts)
	if (len(parts) != 2):
		return
	if (parts[0] == 'valves' and parts[1] == 'set'):
		value = msg.payload == b'ON'
		print('value: {}'.format(value))

		modbus = ModbusTcpClient(NEPTUN_IP, port=503, method='rtu')
		response = modbus.read_holding_registers(address=0, count=1, slave=NEPTUN_ID)
		decoder = BinaryPayloadDecoder.fromRegisters(response.registers, byteorder=Endian.Big, wordorder=Endian.Big)
		bits = decoder.decode_bits()
		bits[0] = value
		bits[1] = value
		builder = BinaryPayloadBuilder(wordorder=Endian.Big,byteorder=Endian.Big)
		builder.add_bits(bits)
		registers = builder.to_registers()
		print("new payload: {}".format(registers))
		modbus.write_register(0, registers[0], slave=NEPTUN_ID)
		modbus.close()
		value_str = "OFF"
		if value:
			value_str = "ON"
		client.publish(PREFIX + "/valves", payload=value_str, qos=0, retain=True)

def on_connect(client, userdata, rc, kwargs):
	client.subscribe(PREFIX + "/valves/set")
	client.subscribe(PREFIX + "/counter3_1/set")
	client.subscribe(PREFIX + "/counter3_2/set")
	config = '{"~": "' + PREFIX + '/valves", "name": "watercontrol_valves", "device_class": "switch", "state_topic": "~", "command_topic":"~/set","unique_id": "watercontrol_neptun_' + NEPTUN_IP + '"}'
	client.publish("homeassistant/switch/watercontrol/valves/config", payload=config, qos=0, retain=True)

def refresh_loop(client):
	while True:
		try:
			modbus = ModbusTcpClient(NEPTUN_IP, port=503, method='rtu')
			response = modbus.read_holding_registers(address=0, count=1, slave=NEPTUN_ID)
			decoder = BinaryPayloadDecoder.fromRegisters(response.registers, byteorder=Endian.Big, wordorder=Endian.Big)
			bits = decoder.decode_bits()
			valve1 = bits[0]
			valve2 = bits[1]
			print("config_decoded: {}, valve1: {}, valve2: {}".format(bits, valve1, valve2))
			value = "OFF"
			if valve1 and valve2:
				value = "ON"
			client.publish(PREFIX + "/valves", payload=value, qos=0, retain=True)

			reg_config = slot_config[COUNTERS_SLOT]
			reg_cold = reg_config[0]
			reg_hot = reg_config[1]

			response = modbus.read_holding_registers(reg_cold, count=2, slave=NEPTUN_ID)
			decoder = BinaryPayloadDecoder.fromRegisters(response.registers, byteorder=Endian.Big, wordorder=Endian.Big)
			value = decoder.decode_32bit_uint()/1000
			print("counter_cold: {}".format(value))
			client.publish("{}/counter{}_1".format(PREFIX, COUNTERS_SLOT), payload=value, qos=0, retain=True)

			response = modbus.read_holding_registers(reg_hot, count=2, slave=NEPTUN_ID)
			decoder = BinaryPayloadDecoder.fromRegisters(response.registers, byteorder=Endian.Big, wordorder=Endian.Big)
			value = decoder.decode_32bit_uint()/1000
			print("counter_hot: {}".format(value))
			client.publish("{}/counter{}_2".format(PREFIX, COUNTERS_SLOT), payload=value, qos=0, retain=True)

			alert_status_response = modbus.read_holding_registers(address=3, count=1, slave=NEPTUN_ID)
			decoder = BinaryPayloadDecoder.fromRegisters(alert_status_response.registers, byteorder=Endian.Big, wordorder=Endian.Big)
			bits = decoder.decode_bits()
			for i in range(1,5):
				print("alert_{}: {}".format(i, bits[i]))
				client.publish("{}/alert_{}".format(PREFIX, i), payload=bits[i-1], qos=0, retain=True)

			modbus.close()
		except Exception as e:
			print("ERROR", host, e, file=sys.stderr)
		time.sleep(QUERY_TIME)

if __name__ == "__main__":
	client = prepare_mqtt()

	client.on_message = on_mqtt_message
	client.on_connect = on_connect

	#start thread for lamp refresh loop
	t1 = threading.Thread(target=refresh_loop, args=[client])
	t1.start()

    # and process mqtt messages in this thread
	client.loop_forever()


