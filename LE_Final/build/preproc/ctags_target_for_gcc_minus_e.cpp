# 1 "C:\\Users\\taimu\\AppData\\Local\\Temp\\le_final_temp\\LE_Final.ino"
# 1 "C:\\Users\\taimu\\AppData\\Local\\Temp\\le_final_temp\\LE_Final.ino"

# 3 "C:\\Users\\taimu\\AppData\\Local\\Temp\\le_final_temp\\LE_Final.ino" 2

int cosineSamples[10];
int sineSamples[10];
# 21 "C:\\Users\\taimu\\AppData\\Local\\Temp\\le_final_temp\\LE_Final.ino"
int Lower_Bound = 0;


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
int sine_off = 0;
int cosine_off = 0;

# 40 "C:\\Users\\taimu\\AppData\\Local\\Temp\\le_final_temp\\LE_Final.ino" 2
# 41 "C:\\Users\\taimu\\AppData\\Local\\Temp\\le_final_temp\\LE_Final.ino" 2


# 42 "C:\\Users\\taimu\\AppData\\Local\\Temp\\le_final_temp\\LE_Final.ino"
void setup() {

  Wire.onRequest(transmitDataWire); // same as above, but master read event
  Wire.begin(address); // join i2c bus with address 0x54 
  //1 - 0x8
  //2 - 0x9
  //3 - 0xA
  //4 - 0xB
  //5 - 0xC
  //6 - 0xD
  Wire.onReceive(receiveEvent); // register event

  pinMode(10,1 /* used for pinMode() */);
  pinMode(11,1 /* used for pinMode() */);
  pinMode(12,1 /* used for pinMode() */);
  pinMode(5,1 /* used for pinMode() */);
  pinMode(6,1 /* used for pinMode() */);
  pinMode(7,1 /* used for pinMode() */);
//  
  digitalWrite(10,0 /* used for digitalWrite(), digitalRead(), openDrain() and attachInterrupt() */);
  digitalWrite(11,1 /* used for digitalWrite(), digitalRead(). There is no option for HIGH level interrupt provided by the hardware */);
  digitalWrite(12,1 /* used for digitalWrite(), digitalRead(). There is no option for HIGH level interrupt provided by the hardware */);
  digitalWrite(5,0 /* used for digitalWrite(), digitalRead(), openDrain() and attachInterrupt() */);
  digitalWrite(6,1 /* used for digitalWrite(), digitalRead(). There is no option for HIGH level interrupt provided by the hardware */);
  digitalWrite(7,1 /* used for digitalWrite(), digitalRead(). There is no option for HIGH level interrupt provided by the hardware */);
  cosine = analogRead(A6)-512 - cosine_off;
  sine = analogRead(A7)-512 - sine_off;
  current_distance = atan2(sine,cosine)*180/3.14159*1000/360+500;
  previous_distance = current_distance;
  absolute_distance = current_distance - previous_distance;
}

void loop() {

  // Take 10 samples
  for (int i = 0; i < 10; i++) {
    cosineSamples[i] = analogRead(A6) - 512 - cosine_off;
    sineSamples[i] = analogRead(A7) - 512 - sine_off;
    delayMicroseconds(100); // small delay between readings to allow ADC to stabilize
  }

    // Sort the samples to find the median
  sortArray(cosineSamples, 10);
  sortArray(sineSamples, 10);

  // Calculate and print the median
  cosine = calculateMedian(cosineSamples, 10);
  sine = calculateMedian(sineSamples, 10);


  current_distance = atan2(sine,cosine)*180/3.14159*1000/360+500;
  difference = current_distance - previous_distance;
  if (current_distance < Lower_Bound)
  {
    Lower_Bound = current_distance;
  }

  // Detect if distance changes abruptly. means a switch has happened
  if (
# 100 "C:\\Users\\taimu\\AppData\\Local\\Temp\\le_final_temp\\LE_Final.ino" 3
     __builtin_abs(
# 100 "C:\\Users\\taimu\\AppData\\Local\\Temp\\le_final_temp\\LE_Final.ino"
     difference
# 100 "C:\\Users\\taimu\\AppData\\Local\\Temp\\le_final_temp\\LE_Final.ino" 3
     ) 
# 100 "C:\\Users\\taimu\\AppData\\Local\\Temp\\le_final_temp\\LE_Final.ino"
                     > 500)
  {
      // Moving Up
      if (difference < 0)
      {
        absolute_distance += ((1000 - previous_distance) + (current_distance - Lower_Bound));
      }
     // Moving Down
      else
      {
        absolute_distance -= ((current_distance - 1000) + (previous_distance - Lower_Bound));
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
  digitalWrite(10,1 /* used for digitalWrite(), digitalRead(). There is no option for HIGH level interrupt provided by the hardware */);
  digitalWrite(11,1 /* used for digitalWrite(), digitalRead(). There is no option for HIGH level interrupt provided by the hardware */);
  digitalWrite(12,1 /* used for digitalWrite(), digitalRead(). There is no option for HIGH level interrupt provided by the hardware */);
  digitalWrite(5,1 /* used for digitalWrite(), digitalRead(). There is no option for HIGH level interrupt provided by the hardware */);
  digitalWrite(6,1 /* used for digitalWrite(), digitalRead(). There is no option for HIGH level interrupt provided by the hardware */);
  digitalWrite(7,1 /* used for digitalWrite(), digitalRead(). There is no option for HIGH level interrupt provided by the hardware */);
}

void set_RGB_on()
{
  digitalWrite(10,1 /* used for digitalWrite(), digitalRead(). There is no option for HIGH level interrupt provided by the hardware */);
  digitalWrite(11,1 /* used for digitalWrite(), digitalRead(). There is no option for HIGH level interrupt provided by the hardware */);
  digitalWrite(12,1 /* used for digitalWrite(), digitalRead(). There is no option for HIGH level interrupt provided by the hardware */);
  digitalWrite(5,1 /* used for digitalWrite(), digitalRead(). There is no option for HIGH level interrupt provided by the hardware */);
  digitalWrite(6,1 /* used for digitalWrite(), digitalRead(). There is no option for HIGH level interrupt provided by the hardware */);
  digitalWrite(7,1 /* used for digitalWrite(), digitalRead(). There is no option for HIGH level interrupt provided by the hardware */);
}

void set_RGB(char color)

{
  set_RGB_off();
  switch(color)
  {
    case 'D':
      digitalWrite(10,0 /* used for digitalWrite(), digitalRead(), openDrain() and attachInterrupt() */);
      digitalWrite(5,0 /* used for digitalWrite(), digitalRead(), openDrain() and attachInterrupt() */);
      break;
    case 'G':
      digitalWrite(11,0 /* used for digitalWrite(), digitalRead(), openDrain() and attachInterrupt() */);
      digitalWrite(6,0 /* used for digitalWrite(), digitalRead(), openDrain() and attachInterrupt() */);
      break;
    case 'B':
      digitalWrite(12,0 /* used for digitalWrite(), digitalRead(), openDrain() and attachInterrupt() */);
      digitalWrite(7,0 /* used for digitalWrite(), digitalRead(), openDrain() and attachInterrupt() */);
      break;
    case 'O':
      set_RGB_off();
    default:
      set_RGB_off();
  }
}
void transmitDataWire() {

  temp[0] = (absolute_distance >> 8) & 0xFF;
  temp[1] = absolute_distance & 0xFF;

  for(int i=0;i<2;i++)
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
