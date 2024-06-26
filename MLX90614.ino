#include <Wire.h>
#include <Adafruit_MLX90614.h>
Adafruit_MLX90614 mlx = Adafruit_MLX90614();
void setup() {
  Serial.begin(9600);
  if(!mlx.begin()){
    Serial.println("error al conectar al sensor")
  } 
}
void loop() {
  float tempc = mlx.readAmbientTempC()
  float objtempc = mlx.readObjectTempC()
  if (!isnan(tempc) && !isnan(objtempc)){
    Serial.print("Ambiente = ");
    Serial.print(tempc); 
    Serial.print("ºC\tObjeto = "); 
    Serial.print(objtempc); 
    Serial.println("ºC");
  }
  delay(500);
}
