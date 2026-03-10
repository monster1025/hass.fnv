#include "esphome.h"

#define BLE_PIN D1

class HappyBubblesDevice : public Component, public CustomMQTTDevice {
protected:
    // char hostname[20] = "hall";
    const char* hostname = "hall";
    String buf = "";
    int txPower = -59;
    char ble_mac_addr[13];
    char ble_rssi [5];
    char ble_is_scan_resp [2];
    char ble_type [2];
    char ble_data[100];

    char tx_power [3];
    char beacon_uuid [33];
    char beacon_major [5];
    char beacon_minor [5];
    char instance_id [13];
    char json_ble_send[500];
    char topic [130];

    typedef struct {
        uint8_t type;
        uint8_t start;
        uint8_t end;
        uint8_t size;
    } ble_tok_t;

public:
    HappyBubblesDevice(const char* host_param) {
        hostname = host_param;
    } 
    void setup() override
    {
        Serial.begin(115200);
    }
    void loop() override
    {
        while (Serial.available() > 0) {
            char inChar = Serial.read();

            if (inChar == '\n') {
                //если буфер наполнен
                // parseData();
                char charBuf[120];
                buf.toCharArray(charBuf, 120);
                process_serial(charBuf);
                buf = "";
            }
            else if (inChar != '\r') {
                buf += inChar;
            }
        }
    }

    String getValue(String data, char separator, int index)
    {
        int found = 0;
        int strIndex[] = { 0, -1 };
        int maxIndex = data.length() - 1;

        for (int i = 0; i <= maxIndex && found <= index; i++) {
            if (data.charAt(i) == separator || i == maxIndex) {
                found++;
                strIndex[0] = strIndex[1] + 1;
                strIndex[1] = (i == maxIndex) ? i + 1 : i;
            }
        }

        return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
    }

    float calcDistance(int rssi, int txPower)
    {
        if (rssi == 0) {
            return -1.0;
        }

        float ratio = rssi * 1.0 / txPower;
        if (ratio < 1.0) {
            return pow(ratio, 10);
        }
        else {
            return (0.89976) * pow(ratio, 7.7095) + 0.111;
        }
    }

    String floatToString(float x, byte precision = 2)
    {
        char tmp[50];
        dtostrf(x, 0, precision, tmp);
        return String(tmp);
    }

    void process_serial(char *buf)
    {
        os_printf("********* got serial to process %d **  %s \n\r", strlen(buf), buf);
        char * pch;
        pch = strtok(buf, "|");
        int i = 0;
                        
        memset(ble_mac_addr, 0, 12);
        memset(ble_rssi, 0, 5);
        memset(ble_is_scan_resp, 0, 1);
        memset(ble_type, 0, 1);
        memset(ble_data, 0, 100);
        
        while(pch != NULL)
        {
            switch(i) 
            {
                case 0:
                    {
                        strcpy(ble_mac_addr, pch);
                        break;
                    }
                case 1:
                    {
                        strcpy(ble_rssi, pch);
                        break;
                    }
                case 2:
                    {
                        strcpy(ble_is_scan_resp, pch);
                        break;
                    }
                case 3:
                    {
                        strcpy(ble_type, pch);
                        break;
                    }
                case 4:
                    {
                        strcpy(ble_data, pch);
                        break;
                    }
            }
            i++;
            //os_printf("token: %s\n", pch);
            pch = strtok(NULL, "|");
        }
        
        //basic filters
        //check mac is 12 chars
        int should_send = 0;
        if(strlen(ble_mac_addr) != 12)
        {
            os_printf("bad mac, not 12, %d, %s\n", strlen(ble_mac_addr), ble_mac_addr);
            should_send = 1;
        }
        //check mac is all hex
        if (!ble_mac_addr[strspn(ble_mac_addr, "0123456789abcdefABCDEF")] == 0) 
        {
            os_printf("bad mac, not all hex %s\n", ble_mac_addr);
            should_send = 2;
        }
        //check data is all hex
        if (strlen(ble_data) < 8 || !ble_data[strspn(ble_data, "0123456789abcdefABCDEF")] == 0 ) 
        {
            os_printf("bad data %s\n", ble_data);
            should_send = 3;
        }
        //check rssi is all numbers
        if (strlen(ble_rssi) < 1 || !ble_rssi[strspn(ble_rssi, "-0123456789")] == 0) 
        {
            os_printf("bad rssi %s\n", ble_rssi);
            should_send = 4;
        }
        //check scan_response is 0 or 1
        if (strlen(ble_is_scan_resp) < 1 || !ble_is_scan_resp[strspn(ble_is_scan_resp, "01")] == 0) 
        {
            os_printf("bad scanresp %s\n", ble_is_scan_resp);
            should_send = 5;
        }
        //check ble_type is hex
        if (strlen(ble_type) < 1 || !ble_type[strspn(ble_type, "0123456789abcdefABCDEF")] == 0) 
        {
            os_printf("bad type %s\n", ble_type);
            should_send = 6;
        }
        if(should_send == 0) 
        {
            //os_printf("^^^^^^^^^GOT THROUGH FILTERS!\r\n");
        }
        else 
        {
            //os_printf("xxxxxxxxxxFAIL FILTERS! %d \r\n", should_send);
            //os_printf("=====%s || %s || %s || %s || %s ===DONE\n", ble_mac_addr, ble_rssi, ble_is_scan_resp, ble_type, ble_data);
            return;
        }

        //what type of beacon is this?
        int beacon_type = 99;

        // iterate through the beacon data, but easier if it is bytes
        uint8_t adv_bytes[strlen(ble_data)/2];

        for(int i=0; i<(strlen(ble_data)/2); i++) {
            uint8_t d1 = 0;

            if(ble_data[i*2] > '9') {
                d1 += ((ble_data[i*2] - 'a' + 10) * 0x10);
            }
            else {
                d1 += ((ble_data[i*2] - '0') * 0x10);
            }

            if(ble_data[i*2+1] > '9') {
                d1 += ble_data[i*2+1] - 'a' + 10;
            }
            else {
                d1 += ble_data[i*2+1] - '0';
            }

            adv_bytes[i] = d1;
        }

        // start with 6 tokens
        ble_tok_t tokens[6];

        uint8_t token_i = 0;
        int stop = 0;
        int pos = 0;
        while(!stop) {
            tokens[token_i].size = adv_bytes[pos];
            tokens[token_i].type = adv_bytes[pos+1];
            tokens[token_i].start = pos+2;
            tokens[token_i].end = pos+tokens[token_i].size;

    /*
            printf("tok: %d, size: %02hhx, type: %02hhx, start: %d end: %d\n", token_i, tokens[token_i].size, tokens[token_i].type, tokens[token_i].start, tokens[token_i].end);
            for(int j=tokens[token_i].start; j<=tokens[token_i].end; j++) {
                printf("%02hhx", adv_bytes[j]);
            }
            printf("\n\n");
    */
            pos = tokens[token_i].end + 1;
            if(pos >= sizeof(adv_bytes)) {
                stop = 1;
            }
            token_i++;
        }

        // iterate through the tokens and determine what kind of beacon it is
        for(int i = 0; i <= token_i; i++) {
            // is iBeacon?
            if(tokens[i].type == 0xff
                    && adv_bytes[tokens[i].start] == 0x4c
                    && adv_bytes[tokens[i].start+1] == 0x00
                    && adv_bytes[tokens[i].start+2] == 0x02
                    && adv_bytes[tokens[i].start+3] == 0x15) {

                beacon_type = 1; //ibeacon

                //now extract uuid
                memset(beacon_uuid, 0, 33);
                memcpy(beacon_uuid, &ble_data[(tokens[i].start+4)*2], 32);
                beacon_uuid[32] = '\0';

                //extract major
                memset(beacon_major, 0, 5);
                memcpy(beacon_major, &ble_data[(tokens[i].start+20)*2], 4);
                beacon_major[4] = '\0';

                //extract minor
                memset(beacon_minor, 0, 5);
                memcpy(beacon_minor, &ble_data[(tokens[i].start+22)*2], 4);
                beacon_minor[4] = '\0';

                //extract tx_power
                memset(tx_power, 0, 3);
                memcpy(tx_power, &ble_data[(tokens[i].start+24)*2], 2);
                tx_power[3] = '\0';

                os_printf("^^^^^ ibeacon %s %s %s %s\n", beacon_uuid, beacon_major, beacon_minor, tx_power);
            }
        }
        
        //add some filters to
        if(beacon_type == 0) 
        {
            //os_printf("send some mqtt for eddystone %s ========\n", beacon_uuid);
            // sendMQTTeddystone(ble_mac_addr, beacon_uuid, instance_id, tx_power, ble_rssi);
        }
        else if(beacon_type == 1) 
        {
            //os_printf("send some mqtt for ibeacon %s ========\n", beacon_uuid);
            sendMQTTibeacon(ble_mac_addr, beacon_uuid, beacon_major, beacon_minor, tx_power, ble_rssi);
        }

        //os_printf("send some mqtt for mac %s =====%d===\n", ble_mac_addr, strlen(ble_mac_addr));
        // sendMQTTraw(ble_mac_addr, ble_rssi, ble_is_scan_resp, ble_type, ble_data);
    }

    // void sendMQTTeddystone(char *mac, char *namespace, char *instance_id, char *tx_power, char *rssi)
    // {
    //     return;
    // }
    void sendMQTTibeacon(char* mac, char* uuid, char* major, char* minor, char* tx_power, char* rssi)
    {
        float distance = calcDistance(atoi(rssi), 0x50);
        String distanceStr = floatToString(distance, 10);

        memset(json_ble_send, 0, 500);
        os_sprintf(json_ble_send, "{\"hostname\": \"%s\",\"beacon_type\": \"ibeacon\",\"id\": \"%s\",\"rssi\": %s,\"uuid\": \"%s\",\"major\": \"%s\",\"minor\": \"%s\",\"tx_power\": \"%s\", \"distance\": \"%s\"}", hostname, mac, rssi, uuid, major, minor, tx_power, distanceStr.c_str());
        memset(topic, 0, 130);
        os_sprintf(topic, "home/presence/%s", hostname);
        publish(topic, json_ble_send);
    }
    // void sendMQTTraw(char * mac, char * rssi, char * is_scan, char * type, char * data)
    // {
    //     memset(json_ble_send, 0, 500);
    //     os_sprintf(json_ble_send, "{\"hostname\": \"%s\",\"mac\": \"%s\",\"rssi\": %s,\"is_scan_response\": \"%s\",\"type\": \"%s\",\r\n\"data\": \"%s\"}", hostname, mac, rssi, is_scan, type, data);
    //     memset(topic, 0, 130);
    //     os_sprintf(topic, "happy-bubbles/ble/%s/raw/%s", hostname, mac);
    //     // publish(topic, json_ble_send);
    // }
};

class BleSwitch : public Component, public Switch {
public:
    void setup() override
    {
        // This will be called by App.setup()
        pinMode(BLE_PIN, OUTPUT);
        write_state(true);
    }
    void write_state(bool state) override
    {
        digitalWrite(BLE_PIN, !state);
        publish_state(state);
    }
};