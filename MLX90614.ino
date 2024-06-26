#include <Wire.h>
#include <Adafruit_MLX90614.h>
Adafruit_MLX90614 mlx = Adafruit_MLX90614();
void setup() {
  Serial.begin(9600);
  mlx.begin();  
}
void loop() {
  double tempc = mlx.readAmbientTempC()
  double objtempc = mlx.readObjectTempC()
  if (!isnan(tempc) && !isnan(objtempc)){
    Serial.print("Ambiente = ");
    Serial.print(tempc); 
    Serial.print("ºC\tObjeto = "); 
    Serial.print(objtempc); 
    Serial.println("ºC");
  }
  delay(500);
}
