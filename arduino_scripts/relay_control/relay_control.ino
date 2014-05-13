const int regulate = 9;
const int mag_cycle = 6;
const int bridge_temp = 10;
const int mag_current = 19;
// Relay outputs

const int touch_50mk = 4;
const int touch_1k = 5;
const int touch_50k = 3;
// Touch sensors

const int hs_closing = 15;
const int hs_opening = 16;
// Heatswitch inputs
const int close_hs = 18;
const int open_hs = 14;

const int a = 97;
const int b = 98;
const int c = 99;
const int d = 100;
const int e = 101;
const int f = 102;
const int s = 115;
// Changing from bit values to human readable.

int message=0;
// Serial communication.

int regulate_active = 0;
int mag_current_active = 0;
int touch_50mk_active = 0;
int touch_1k_active = 0;
int touch_50k_active = 0;
int hs_opening_active = 0;
int hs_closing_active = 0;
// Status

void setup(){
  pinMode(touch_50mk,INPUT_PULLUP);
  pinMode(touch_1k,INPUT_PULLUP);
  pinMode(touch_50k,INPUT_PULLUP);
  // Touch inputs
  
  pinMode(hs_opening,INPUT_PULLUP);
  pinMode(hs_closing,INPUT_PULLUP);
  // Heatswitch inputs
  pinMode(open_hs,OUTPUT);
  pinMode(close_hs,OUTPUT);
  // Heatswitch outputs
  
  pinMode(regulate,OUTPUT);
  pinMode(mag_cycle,OUTPUT);
  pinMode(bridge_temp,OUTPUT);
  pinMode(mag_current,OUTPUT);
  
  Serial.begin(9600);
}

void loop(){
  if (Serial.available()>0){
    message=Serial.read();
    if (message == a){
      //Serial.println("Message is a");
      digitalWrite(regulate, HIGH);
      delay(1000);
      digitalWrite(regulate, LOW);
      regulate_active = 1;
    }
    if (message == b){
      //Serial.println("Message is b");
      digitalWrite(mag_cycle, HIGH);
      delay(1000);
      digitalWrite(mag_cycle, LOW);
      regulate_active = 0;
    }
    if (message == c){
      //Serial.println("Message is c");
      digitalWrite(mag_current, HIGH);
      delay(1000);
      digitalWrite(mag_current, LOW);
      mag_current_active = 1;
    }
    if (message == d){
      //Serial.println("Message is d");
      digitalWrite(bridge_temp, HIGH);
      delay(1000);
      digitalWrite(bridge_temp, LOW);
      mag_current_active = 0;
    }
    if (message == e){
      Serial.println("Message is e");
      digitalWrite(open_hs, HIGH);
      delay(1000);
      digitalWrite(open_hs, LOW);
    }
    if (message == f){
      Serial.println("Message is f");
      digitalWrite(close_hs, HIGH);
      delay(1000);
      digitalWrite(close_hs, LOW);
    }
    if (message == s){
      Serial.print(regulate_active);
      Serial.print(mag_current_active);
      Serial.print(digitalRead(touch_50mk));
      Serial.print(digitalRead(touch_1k));
      Serial.print(digitalRead(touch_50k));
      Serial.print(digitalRead(hs_opening));
      Serial.print(digitalRead(hs_closing));
      Serial.print('\n') ;
    }
  }
}
