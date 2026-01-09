const int relayPin = 2;
int lastState = LOW;

void setup() {
  pinMode(relayPin,  INPUT_PULLUP);
  Serial.begin(9600);
}

int flag = 0;

void loop() {


  int currentState = digitalRead(relayPin);
  if (currentState == HIGH && lastState == LOW) {
    flag = flag + 1;
  } else if(currentState == HIGH && lastState == HIGH) {
     flag = flag + 1;
     if(flag > 30){
       flag = 0;
       Serial.println("C");
     }
  } else {
    flag = 0;
  }
  lastState = currentState;
  delay(200.);
}
