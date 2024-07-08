#include <Wire.h>
#include "MAX30105.h"
#include "spo2_algorithm.h"
#include <Adafruit_MLX90614.h>
#include <ArduinoJson.hpp>
#include <ArduinoJson.h>

MAX30105 particleSensor;
Adafruit_MLX90614 mlx = Adafruit_MLX90614();

#define MAX_BRIGHTNESS 255

#if defined(__AVR_ATmega328P__) || defined(__AVR_ATmega168__)
uint16_t irBuffer[100]; // datos del sensor LED infrarrojo
uint16_t redBuffer[100]; // datos del sensor LED rojo
#else
uint32_t irBuffer[100]; // datos del sensor LED infrarrojo
uint32_t redBuffer[100]; // datos del sensor LED rojo
#endif

int32_t bufferLength; // longitud de datos
int32_t spo2; // valor de SPO2
int8_t validSPO2; // indicador para mostrar si el cálculo de SPO2 es válido
int32_t heartRate; // valor de la frecuencia cardíaca
int8_t validHeartRate; // indicador para mostrar si el cálculo de la frecuencia cardíaca es válido

byte pulseLED = 11; // Debe estar en un pin PWM
byte readLED = 13; // Parpadea con cada lectura de datos

void setup() {
  Serial.begin(9600); // inicializa la comunicación serie a 9600 bits por segundo

  pinMode(pulseLED, OUTPUT);
  pinMode(readLED, OUTPUT);

  // Inicializar el sensor MAX30105
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) { // Usa el puerto I2C predeterminado, velocidad de 400kHz
    Serial.println(F("No se encontró el MAX30105. Por favor, verifique la conexión/energía."));
    while (1);
  }

  Serial.println(F("Adjunte el sensor al dedo con una banda elástica. Presione cualquier tecla para comenzar la conversión"));
  while (Serial.available() == 0); // espera hasta que el usuario presione una tecla
  Serial.read();

  byte ledBrightness = 60; // Opciones: 0=Apagado a 255=50mA
  byte sampleAverage = 4; // Opciones: 1, 2, 4, 8, 16, 32
  byte ledMode = 2; // Opciones: 1 = Solo rojo, 2 = Rojo + IR, 3 = Rojo + IR + Verde
  byte sampleRate = 100; // Opciones: 50, 100, 200, 400, 800, 1000, 1600, 3200
  int pulseWidth = 411; // Opciones: 69, 118, 215, 411
  int adcRange = 4096; // Opciones: 2048, 4096, 8192, 16384

  particleSensor.setup(ledBrightness, sampleAverage, ledMode, sampleRate, pulseWidth, adcRange); // Configura el sensor con estos ajustes

  // Inicializar el sensor MLX90614
  if(!mlx.begin()){
    Serial.println("Error al conectar al sensor MLX90614");
  } 
}

void loop() {
  bufferLength = 100; // la longitud del buffer de 100 almacena 4 segundos de muestras funcionando a 25sps

  // lee las primeras 100 muestras y determina el rango de la señal
  for (byte i = 0; i < bufferLength; i++) {
    while (particleSensor.available() == false) // ¿tenemos nuevos datos?
      particleSensor.check(); // Verifica si hay nuevos datos en el sensor

    redBuffer[i] = particleSensor.getRed();
    irBuffer[i] = particleSensor.getIR();
    particleSensor.nextSample(); // Terminamos con esta muestra, así que pasamos a la siguiente

    StaticJsonDocument<300> doc;
    doc["red"] = redBuffer[i];
    doc["ir"] = irBuffer[i];
    String json;
    serializeJson(doc, json);
    Serial.println(json);
  }

  // calcula la frecuencia cardíaca y el SpO2 después de las primeras 100 muestras (primeros 4 segundos de muestras)
  maxim_heart_rate_and_oxygen_saturation(irBuffer, bufferLength, redBuffer, &spo2, &validSPO2, &heartRate, &validHeartRate);

  // Tomando muestras continuamente del MAX30102. La frecuencia cardíaca y el SpO2 se calculan cada 1 segundo
  while (1) {
    // descartando los primeros 25 conjuntos de muestras en la memoria y desplazando los últimos 75 conjuntos de muestras a la parte superior
    for (byte i = 25; i < 100; i++) {
      redBuffer[i - 25] = redBuffer[i];
      irBuffer[i - 25] = irBuffer[i];
    }

    bool fingerDetected = false; // Flag to check if finger is detected

    // toma 25 conjuntos de muestras antes de calcular la frecuencia cardíaca
    for (byte i = 75; i < 100; i++) {
      while (particleSensor.available() == false) // ¿tenemos nuevos datos?
        particleSensor.check(); // Verifica si hay nuevos datos en el sensor

      digitalWrite(readLED, !digitalRead(readLED)); // Parpadea el LED a bordo con cada lectura de datos

      redBuffer[i] = particleSensor.getRed();
      irBuffer[i] = particleSensor.getIR();
      particleSensor.nextSample(); // Terminamos con esta muestra, así que pasamos a la siguiente

      // Check if the finger is detected based on the IR signal value
      if (irBuffer[i] > 50000) { // You might need to adjust this threshold value based on your testing
        fingerDetected = true;
      }

      // Leer y mostrar la temperatura del sensor MLX90614
      float tempc = mlx.readAmbientTempC();
      float objtempc = mlx.readObjectTempC();
      if (!isnan(tempc) && !isnan(objtempc)){
        // Crear un documento JSON
        StaticJsonDocument<512> doc;
        doc["red"] = redBuffer[i];
        doc["ir"] = irBuffer[i];
        doc["heartRate"] = heartRate;
        doc["validHeartRate"] = validHeartRate;
        doc["spo2"] = spo2;
        doc["validSPO2"] = validSPO2;
        doc["ambientTempC"] = tempc;
        doc["objectTempC"] = objtempc;

        if (!fingerDetected) {
          doc["status"] = "Finger not detected";
        }
        // Serializar el JSON y enviarlo al puerto serie
        String json;
        serializeJson(doc, json);
        Serial.println(json);
      }
      
      //delay(500);
    }

    // Después de recopilar 25 nuevas muestras, recalcula FC y SpO2
    maxim_heart_rate_and_oxygen_saturation(irBuffer, bufferLength, redBuffer, &spo2, &validSPO2, &heartRate, &validHeartRate);

    if (!fingerDetected) {
      Serial.println("No se detecta un dedo. Por favor, coloque su dedo en el sensor.");
    }
  }
}
