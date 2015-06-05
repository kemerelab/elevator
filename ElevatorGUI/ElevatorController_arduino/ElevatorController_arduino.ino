#include <Wire.h>
#include <Streaming.h>
#include <Adafruit_MotorShield.h>
#include "utility/Adafruit_PWMServoDriver.h"

#define F 1
#define B 2

#define S 1
#define D 2
#define I 3
#define M 4

int motorSteps = 200; // NEMA 17 number of steps per revolution
int motorPort = 2; // indicates motor connected to M3 & M4 terminals on shield

// create motor object
Adafruit_MotorShield AFMS = Adafruit_MotorShield(); 
Adafruit_StepperMotor *myStepper = AFMS.getStepper(motorSteps, motorPort); 

String input_speed; 
String input_step;  
char input_direction; 
char input_mode; 

int motor_speed; 
int motor_step; 
int motor_direction; 
int motor_mode; 

void setup(){
  Serial.begin(115200); 
  AFMS.begin(); // initialize I2C communication with motor
}

void loop(){
  if(Serial.available()){
    String data = Serial.readString(); 
    input_speed = data.substring(1,5);
    input_step = data.substring(6,10);
    input_direction = data.charAt(11);
    input_mode = data.charAt(13); 
    
    motor_speed = input_speed.toInt(); 
    motor_step = input_step.toInt();
    
    if(input_direction == 'F')
      motor_direction = F; 
    else if (input_direction == 'B')
      motor_direction = B; 
    
    if(input_mode == 'D')
      motor_mode = D; 
    else if(input_mode == 'S')
      motor_mode = S; 
    else if(input_mode == 'I')
      motor_mode = I; 
    else if(input_mode == 'M')
      motor_mode = M; 

    myStepper -> setSpeed(motor_speed);
    myStepper -> step(motor_step, motor_direction, motor_mode); // values passed to function are dictated by user 
    
    Serial.println(motor_speed); 
    Serial.println(motor_step);
    Serial.println(motor_direction);
    Serial.println(motor_mode);
    Serial.println(); 
  }
}
