int sine_off=48;
int cosine_off=60;
int address=11;

#define SAMPLE_SIZE 10
int cosineSamples[SAMPLE_SIZE];
int sineSamples[SAMPLE_SIZE];

#define LED_RED_1     10
#define LED_GREEN_1   11
#define LED_BLUE_1    12
#define LED_RED_2     5
#define LED_GREEN_2   6
#define LED_BLUE_2    7
#define COS_IN        A6
#define SIN_IN        A7
#define RED 'D'
#define GREEN 'G'
#define BLUE 'B'
#define OFF 'O'

#define Upper_Bound 1000
int Lower_Bound = 0; 
#define Switch_Bound 500

//cosine 632 - 542 - Mean 587
//sine   631 - 532 - Mean 582

int difference;
char temp[10];
int absolute_distance=0;
int previous_distance=0;
int start_distance=1;
int current_distance=1;
bool FLAG_MOVING_UP=0;
bool FLAG_MOVING_DOWN=0;
bool SWITCH_DETECTED=0;
int sine=0;
int cosine=0;

#include <Wire.h>
#include <math.h>

void setup() {

  Wire.onRequest(transmitDataWire); // same as above, but master read event
  Wire.begin(address);                 // join i2c bus with address 0x54 
  //1 - 0x8
  //2 - 0x9
  //3 - 0xA
  //4 - 0xB
  //5 - 0xC
  //6 - 0xD
  Wire.onReceive(receiveEvent); // register event

  pinMode(LED_RED_1,OUTPUT);
  pinMode(LED_GREEN_1,OUTPUT);
  pinMode(LED_BLUE_1,OUTPUT);
  pinMode(LED_RED_2,OUTPUT);
  pinMode(LED_GREEN_2,OUTPUT);
  pinMode(LED_BLUE_2,OUTPUT);
//  
  digitalWrite(LED_RED_1,LOW); 
  digitalWrite(LED_GREEN_1,HIGH);
  digitalWrite(LED_BLUE_1,HIGH);
  digitalWrite(LED_RED_2,LOW);
  digitalWrite(LED_GREEN_2,HIGH);
  digitalWrite(LED_BLUE_2,HIGH);
  cosine = analogRead(COS_IN)-512 - cosine_off;
  sine = analogRead(SIN_IN)-512 - sine_off;
  current_distance = atan2(sine,cosine)*180/3.14159*1000/360+500;
  previous_distance = current_distance;
  absolute_distance = current_distance - previous_distance;
}

void loop() {

  // Take 10 samples
  for (int i = 0; i < SAMPLE_SIZE; i++) {
    cosineSamples[i] = analogRead(COS_IN) - 512 - cosine_off;
    sineSamples[i] = analogRead(SIN_IN) - 512 - sine_off;
    delayMicroseconds(100); // small delay between readings to allow ADC to stabilize
  }

    // Sort the samples to find the median
  sortArray(cosineSamples, SAMPLE_SIZE);
  sortArray(sineSamples, SAMPLE_SIZE);

  // Calculate and print the median
  cosine = calculateMedian(cosineSamples, SAMPLE_SIZE);
  sine = calculateMedian(sineSamples, SAMPLE_SIZE);

  
  current_distance = atan2(sine,cosine)*180/3.14159*1000/360+500;
  difference = current_distance - previous_distance;
  if (current_distance < Lower_Bound)
  {
    Lower_Bound = current_distance;
  }

  // Detect if distance changes abruptly. means a switch has happened
  if (abs(difference) > Switch_Bound)
  {
      // Moving Up
      if (difference < 0)
      {
        absolute_distance += ((Upper_Bound - previous_distance) + (current_distance - Lower_Bound));
      }
     // Moving Down
      else
      {
        absolute_distance -= ((current_distance - Upper_Bound) + (previous_distance - Lower_Bound));
      }
  }
  else
  {
    absolute_distance += difference;
  }

  previous_distance = current_distance;

  delayMicroseconds(100);
}

// void transmitDataWire() {
 
//  temp[0] = (cosine >> 8) & 0xFF;
//  temp[1] = cosine & 0xFF;
//  temp[2] = (sine >> 8) & 0xFF;
//  temp[3] = sine & 0xFF;
//  temp[4] = (current_distance >> 8) & 0xFF;
//  temp[5] = current_distance & 0xFF;
//  temp[6] = (absolute_distance >> 8) & 0xFF;
//  temp[7] = absolute_distance & 0xFF;
//  temp[8] = (Lower_Bound >> 8) & 0xFF;
//  temp[9] = Lower_Bound & 0xFF;
 
//  for(int i=0;i<10;i++)
//  {
//    Wire.write(temp[i]);
//  }
// }


void set_RGB_off()
{
  digitalWrite(LED_RED_1,HIGH); 
  digitalWrite(LED_GREEN_1,HIGH);
  digitalWrite(LED_BLUE_1,HIGH);
  digitalWrite(LED_RED_2,HIGH);
  digitalWrite(LED_GREEN_2,HIGH);
  digitalWrite(LED_BLUE_2,HIGH);
}

void set_RGB_on()
{
  digitalWrite(LED_RED_1,HIGH); 
  digitalWrite(LED_GREEN_1,HIGH);
  digitalWrite(LED_BLUE_1,HIGH);
  digitalWrite(LED_RED_2,HIGH);
  digitalWrite(LED_GREEN_2,HIGH);
  digitalWrite(LED_BLUE_2,HIGH);
}

void set_RGB(char color)

{
  set_RGB_off();
  switch(color)
  {
    case RED:
      digitalWrite(LED_RED_1,LOW); 
      digitalWrite(LED_RED_2,LOW);
      break;
    case GREEN:
      digitalWrite(LED_GREEN_1,LOW);
      digitalWrite(LED_GREEN_2,LOW);
      break;
    case BLUE:
      digitalWrite(LED_BLUE_1,LOW);
      digitalWrite(LED_BLUE_2,LOW);
      break;
    case OFF:
      set_RGB_off();
    default:
      set_RGB_off();      
  }
}
void transmitDataWire() {
  
  temp[0] = (absolute_distance >> 8) & 0xFF;
  temp[1] = absolute_distance & 0xFF;
  temp[2] = (cosine >> 8) & 0xFF;
  temp[3] = cosine & 0xFF;
  temp[4] = (sine >> 8) & 0xFF;
  temp[5] = sine & 0xFF;
  
  for(int i=0;i<6;i++)
  {
    Wire.write(temp[i]);
  }
}

void receiveEvent(int howMany) {
  while (Wire.available()) { // loop through all but the last
    char c = Wire.read(); // receive byte as a character
    if (c == 'R')
    {
      absolute_distance=0;
    }
    else 
    {
      set_RGB(c);
    }
  }
}

void sortArray(int arr[], int size) {
  for (int i = 0; i < size - 1; i++) {
    for (int j = 0; j < size - i - 1; j++) {
      if (arr[j] > arr[j + 1]) {
        int temp = arr[j];
        arr[j] = arr[j + 1];
        arr[j + 1] = temp;
      }
    }
  }
}

int calculateMedian(int arr[], int size) {
  if (size % 2 != 0)
    return arr[size / 2]; // if size is odd, return the middle number
  else
    return (arr[(size - 1) / 2] + arr[size / 2]) / 2; // if size is even, return the average of the two middle numbers
}
