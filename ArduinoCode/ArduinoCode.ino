#include <SPI.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ThingSpeak.h>

// Setup WiFi
const char* ssid = "Andromax-M3Z-41B6";
const char* password =  "35660600";

//mqtt server info
const char* mqttServer = "postman.cloudmqtt.com";
const int mqttPort = 16478;
const char* mqttUser = "umekqjds";
const char* mqttPassword = "_788BdDux1m4";

//Thingspeak info
const char* apiKey = "IU4BYU7HNN29Z2OG";
unsigned long myChannelNumber = 819572;
 
//EthernetClient ethClient;
WiFiClient espClient;
PubSubClient client(espClient);

float EC;
int distance;
int tinggi;

/////////////////////////////////////////////////////////define EC/////////////////////////////////
#define TdsSensorPin A0
#define VREF 5.0      // analog reference voltage(Volt) of the ADC
#define SCOUNT  30           // sum of sample point
int analogBuffer[SCOUNT];    // store the analog value in the array, read from ADC
int analogBufferTemp[SCOUNT];
int analogBufferIndex = 0,copyIndex = 0;
float averageVoltage = 0,tdsValue = 0, ECValue = 0, temperature = 25;

/////////////////////////////////////////////////define ketinggian//////////////////////
const unsigned int TRIG_PIN=14; //D5
const unsigned int ECHO_PIN=12; //D6


void setup() {
  Serial.begin(115200);
    
  //setup EC
  pinMode(TdsSensorPin,INPUT);
  
  //setup ketinggian
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  //Ethernet.begin(mac, ip); 
   WiFi.begin(ssid, password);
 
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Connecting to WiFi..");
  }
  Serial.println("Connected to the WiFi network");

}
//===========================Function==========================//
//Code EC
int getMedianNum(int bArray[], int iFilterLen) 
{
      int bTab[iFilterLen];
      for (byte i = 0; i<iFilterLen; i++)
    bTab[i] = bArray[i];
      int i, j, bTemp;
      for (j = 0; j < iFilterLen - 1; j++) 
      {
    for (i = 0; i < iFilterLen - j - 1; i++) 
          {
      if (bTab[i] > bTab[i + 1]) 
            {
    bTemp = bTab[i];
          bTab[i] = bTab[i + 1];
    bTab[i + 1] = bTemp;
       }
    }
      }
      if ((iFilterLen & 1) > 0)
  bTemp = bTab[(iFilterLen - 1) / 2];
      else
  bTemp = (bTab[iFilterLen / 2] + bTab[iFilterLen / 2 - 1]) / 2;
      return bTemp;
}

void loop() {
  client.setServer(mqttServer, mqttPort);
  client.setCallback(callback);
 
  client.setServer(mqttServer, mqttPort);
  client.setCallback(callback);
 
  while (!client.connected()) {
    Serial.println("Connecting to MQTT...");
 
    if (client.connect("EgrianoA", mqttUser, mqttPassword )) {
 
      Serial.println("connected");  
 
    } else {
 
      Serial.print("failed with state ");
      Serial.print(client.state());
      delay(2000);
 
    }
  } 
  readEC();
  readKetinggian();
  client.loop();
  client.publish("input/EC", String(ECValue).c_str(), true);
  client.publish("input/tinggiAir", String(tinggi).c_str(), true);
  ThingSpeak.setField(1, ECValue);
  ThingSpeak.setField(2, tinggi);
  ThingSpeak.writeFields(myChannelNumber, apiKey);
  delay(10000);
}

//====================================MQTT FUNCTION============================//
void callback(char* topic, byte* payload, unsigned int length) {
 
  Serial.print("Message arrived in topic: ");
  Serial.println(topic);

  if (strcmp(topic,"output/out1")==0){
    Serial.print("Message output1: ");
    for (int i = 0; i < length; i++) {
      Serial.print((char)payload[i]);
    }
    payload[length] = '\0';
    String s = String((char*)payload);
    long f = atol((char*)payload);
    Serial.println();
    Serial.print("Output EC versi String= ");
    Serial.print(s);
    Serial.println();
    Serial.print("Output EC versi long= ");
    Serial.print(f);
  }

  if (strcmp(topic,"output/out2")==0){
    Serial.print("Message output2: ");
    for (int i = 0; i < length; i++) {
      Serial.print((char)payload[i]);
    }
     payload[length] = '\0';
    String s = String((char*)payload);
    long f = atol((char*)payload);
    Serial.println();
    Serial.print("Output Air versi String= ");
    Serial.print(s);
    Serial.println();
    Serial.print("Output Air versi long= ");
    Serial.print(f);
  }
 
  
 
  Serial.println();
  Serial.println("-----------------------");
 
}
//==========================VOID EC==============================//
void readEC(){
  //Code EC
  static unsigned long analogSampleTimepoint = millis();
   if(millis()-analogSampleTimepoint > 40U)     //every 40 milliseconds,read the analog value from the ADC
   {
     analogSampleTimepoint = millis();
     analogBuffer[analogBufferIndex] = analogRead(TdsSensorPin);    //read the analog value and store into the buffer
     analogBufferIndex++;
     if(analogBufferIndex == SCOUNT) 
         analogBufferIndex = 0;
   }   
   static unsigned long printTimepoint = millis();
   if(millis()-printTimepoint > 800U)
   {
      printTimepoint = millis();
      for(copyIndex=0;copyIndex<SCOUNT;copyIndex++)
        analogBufferTemp[copyIndex]= analogBuffer[copyIndex];
      averageVoltage = getMedianNum(analogBufferTemp,SCOUNT) * (float)VREF / 1024.0; // read the analog value more stable by the median filtering algorithm, and convert to voltage value
      float compensationCoefficient=1.0+0.02*(temperature-25.0);    //temperature compensation formula: fFinalResult(25^C) = fFinalResult(current)/(1.0+0.02*(fTP-25.0));
      float compensationVolatge=averageVoltage/compensationCoefficient;  //temperature compensation
      //Kalibrasi nilai TDS disini
      tdsValue=(133.42*compensationVolatge*compensationVolatge*compensationVolatge - 255.86*compensationVolatge*compensationVolatge + 857.39*compensationVolatge)*0.5*0.45723962743437764606265876375953; //convert voltage value to tds value
      ECValue=tdsValue * 2 /1000;
      Serial.print("voltage:");
      Serial.print(averageVoltage,2);
      Serial.print("V   ");
      Serial.println();
   }

   //print EC
  Serial.print("TDS Value: ");
  Serial.println(tdsValue);
  Serial.print("EC Value:");
  Serial.print(ECValue,2);
  Serial.println(" mS/s");
}

// Code ketinggian air
void readKetinggian(){
  //Code ketinggian air
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  const unsigned long duration= pulseIn(ECHO_PIN, HIGH);
  distance= duration/29/2;
  tinggi = 60-distance;

    //print ketinggian air
  if(duration==0){
   Serial.println("Warning: no pulse from sensor");
   } 
  else{
      Serial.print("Tinggi air: ");
      Serial.print(tinggi);
      Serial.print(" cm");
  }

  Serial.println("");
  Serial.println("");
  //delay(1000);
}
