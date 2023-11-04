#include "esphome.h"
#include <Bounce2.h>

#define CounterNum 2
#define COUNTER_COLD 0
#define COUNTER_HOT 1

static const char *TAG = "watercounter.sensor";

class WaterCountersSensor : public Component, public Sensor, public CustomAPIDevice {
 protected:
	int CounterPin[CounterNum] = {D2,D7};
	long CounterValues[CounterNum] = {};
	Bounce CounterBouncer[CounterNum] = {};

 public:
  Sensor *cold_sensor = new Sensor();
  Sensor *hot_sensor = new Sensor();
  bool initReadValues = false;

  globals::GlobalsComponent<float> *counter_cold_value;
  globals::GlobalsComponent<float> *counter_hot_value;

  void setup() override {
	register_service(&WaterCountersSensor::on_set_counter_values, "set_counter_values",
	                     {"cold_value", "hot_value"});

    // init flash variables
    counter_cold_value = new globals::GlobalsComponent<float>();
    App.register_component(counter_cold_value);
    counter_cold_value->set_restore_value(1547432152);

    counter_hot_value = new globals::GlobalsComponent<float>();
    App.register_component(counter_hot_value);
    counter_hot_value->set_restore_value(2087162808);

  	ESP_LOGD(TAG, "Initializing counters.");
	for (int i=0; i<CounterNum; i++) {
		pinMode(CounterPin[i], INPUT_PULLUP);
		CounterBouncer[i].attach(CounterPin[i]);
		CounterBouncer[i].interval(100);
	}
	ESP_LOGD(TAG, "Initialize done.");
  }

  void loop() override {
  	if (is_connected() && !initReadValues) {
	    ESP_LOGD(TAG, "Reading counters from fs.");
		for (int i=0; i<CounterNum; i++) {
			readCounterFromFile(i);
			sendCounterValue(i);
		}
		initReadValues = true;
	}
	for (int i=0; i<CounterNum; i++) {
		boolean changed = CounterBouncer[i].update();
		if ( changed ) {
			int value = CounterBouncer[i].read();
			if ( value == LOW) {
				ESP_LOGD(TAG, "Got counter %d 'tick'.", i);
				ESP_LOGD(TAG, "Incrementing value. Old: %d", CounterValues[i]);
				CounterValues[i] = CounterValues[i] + 10;
				ESP_LOGD(TAG, "New: %d", CounterValues[i]);
				sendCounterValue(i);
				writeFile(i);
				printState(i);
			}
		}
	}
  }
  
 //  void update() override {
	// for (int i=0; i<CounterNum; i++) {
	// 	sendCounterValue(i);
	// }
 //  }
  
  // --------------- HASS service call handling ----------------------------
  void on_set_counter_values(float cold_value, float hot_value) 
  {
    int cold_int = (int) (cold_value * 100.0);
    int hot_int = (int) (hot_value * 100.0);
    ESP_LOGD(TAG, "Saving values: cold - %d, hot - %d", cold_int, hot_int);

    CounterValues[COUNTER_COLD] = cold_int;
    CounterValues[COUNTER_HOT] = hot_int;

	for (int i=0; i<CounterNum; i++) {
    	writeFile(i);
    	sendCounterValue(i);
    }

    ESP_LOGD(TAG, "Save success.");
  }
  
  // --------------- functions ----------------------------
	void readCounterFromFile(int counterId) {
	  if (counterId == COUNTER_COLD) {
	  	CounterValues[COUNTER_COLD] = counter_cold_value->value();
	  }else if (counterId == COUNTER_HOT) {
	  	CounterValues[COUNTER_HOT] = counter_hot_value->value();
	  }
	}

	void writeFile(int counterId) {
	  if (counterId == COUNTER_COLD) {
	    counter_cold_value->value() = CounterValues[COUNTER_COLD];
	  }else if (counterId == COUNTER_HOT) {
	  	counter_hot_value->value() = CounterValues[COUNTER_HOT];
	  }
	  ESP_LOGD(TAG, "Saving done.");
	}

	void sendCounterValue(int counterId) {
	  if (counterId == COUNTER_COLD) {
	  	ESP_LOGD(TAG, "Publishing cold state.");
	  	float value = (float)CounterValues[counterId] / 100.0;
	  	cold_sensor->publish_state(value);
	  }else if (counterId == COUNTER_HOT) {
	  	ESP_LOGD(TAG, "Publishing hot state.");
	  	float value = (float)CounterValues[counterId] / 100.0;
	  	hot_sensor->publish_state(value);
	  }
	}
	
	String countrName(int Id) {
	  switch(Id) {
	    case COUNTER_HOT:
	      return "hot";
	    case COUNTER_COLD:
	      return "cold";
	  }
	  return "unknown";
	}

	void printState(int counterId) {
	  ESP_LOGD(TAG, "Counter[%d]=%d", counterId, CounterValues[counterId]);
	}
};