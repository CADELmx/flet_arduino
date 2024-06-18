#include <DHT.h>
#include <DHT_U.h>
#include <ArduinoJson.hpp>
#include <ArduinoJson.h>

const int DHTPin = 22;
const int ledR = 11;
const int ledG = 10;
const int ledB = 9;
DHT dht(DHTPin, DHT11);

void setup()
{
  pinMode(ledR, OUTPUT);
  pinMode(ledG, OUTPUT);
  pinMode(ledB, OUTPUT);
  Serial.begin(9600);
  dht.begin();
}

void loop()
{
  if (Serial.available() > 0)
  {
    String payload = Serial.readStringUntil('\n');
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, payload);
    if (!error)
    {
      int r = doc["red"];
      int g = doc["green"];
      int b = doc["blue"];
      analogWrite(ledR, r);
      analogWrite(ledG, g);
      analogWrite(ledB, b);
    }
    else
    {
      Serial.println("Error en la deserialización del JSON");
    }
  }

  float hum = dht.readHumidity();
  float temc = dht.readTemperature();
  float temf = dht.readTemperature(true);

  if (!isnan(hum) && !isnan(temc) && !isnan(temf))
  {
    StaticJsonDocument<300> doc;
    doc["humedad"] = hum;
    doc["temperatura"] = temc;
    doc["tempf"] = temf;

    String json;
    serializeJson(doc, json);
    Serial.println(json);
  }
  else
  {
    Serial.println("Error al leer el sensor DHT");
  }
  delay(2000);
}
