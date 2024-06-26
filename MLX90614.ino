#include <Wire.h>
#include <Adafruit_MLX90614.h>
Adafruit_MLX90614 mlx = Adafruit_MLX90614();
void setup() {
  Serial.begin(9600);
  mlx.begin();  
}
void loop() {
  Serial.print("Ambiente = ");
  Serial.print(mlx.readAmbientTempC()); 
  Serial.print("ºC\tObjeto = "); 
  Serial.print(mlx.readObjectTempC()); 
  Serial.println("ºC");
  delay(500);
}
