#include <Arduino.h>
#include <esp_camera.h>
#include <HTTPClient.h>
#include <WiFi.h>

/*
Description: Using camera module to capture images and send them via HTTP POST to
an HTTP server instance running on a local network.
Device Type: Ai Thinker ESP32-CAM module
*/

#define buttonPin 2

// Define camera pins
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM     0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM       5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// ---- WiFi credentials ---- //
const char* ssid = "arkan's iPhone";
const char* password = "position1144";

// ---- Interrupt handler ---- //
// External button interrupt flag
volatile bool startButton = false;
volatile unsigned long lastButtonPress = 0;
// Interrupt service routine for button press
void IRAM_ATTR handleButtonPress();

// ---- Helper functions ---- //
void dataPropertyToSerial(camera_fb_t * fb);
void httpPostData(camera_fb_t * fb);

void setup() {
  Serial.begin(115200);

  // ---- Connect to WiFi ---- //
  Serial.print("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");

  // ---- Setup camera ---- //
  Serial.println("Starting camera...");

  // Assigning to camera configuration structure
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 8000000;
  config.pixel_format = PIXFORMAT_JPEG;  // Assuming emission filter is used, only intensity data is needed
  config.frame_size = FRAMESIZE_SVGA;
  config.jpeg_quality = 10;
  config.fb_count = 2;

  // Camera initialization
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  camera_fb_t * fb = NULL;

  // Disable white balance and white balance gain
  sensor_t * sensor = esp_camera_sensor_get();
  sensor->set_whitebal(sensor, 0);       // 0 = disable , 1 = enable
  sensor->set_awb_gain(sensor, 0);       // 0 = disable , 1 = enable

  // ---- Set up button interrupt ---- //
  pinMode(buttonPin, INPUT_PULLDOWN); // Set button pin as input with internal pull-up resistor
  attachInterrupt(digitalPinToInterrupt(buttonPin), handleButtonPress, RISING); 
  Serial.println("Camera initialized successfully");
}

void loop() {
  camera_fb_t * fb = esp_camera_fb_get();

  if (startButton) {    // Periodic capture session is active
    // ---- Take a picture ---- //
    if (!fb) {
      Serial.println("Camera capture failed");
      return;
    }
    Serial.println("Picture taken!");

    // ---- Dump data size into serial monitor ---- //
    dataPropertyToSerial(fb);

    // ---- Prepare HTTP POST request ---- //
    httpPostData(fb);

    // ---- Return buffer to be reused ---- //
    esp_camera_fb_return(fb);

    delay(12000);
    return;
  }

  // ---- Return buffer to be reused ---- //
  esp_camera_fb_return(fb);

  Serial.println("Periodic capture session is inactive. Press the button to start.");
  delay(2000);
}

void IRAM_ATTR handleButtonPress() {
  unsigned long currentTime = millis();
  
  // Debounce: ignore presses within 200ms of last press
  if (currentTime - lastButtonPress > 200) {
    startButton = !startButton;
    lastButtonPress = currentTime;
    
    if (startButton) {
      Serial.println("Button pressed: Starting periodic capture session...");
    } else {
      Serial.println("Button pressed: Stopping periodic capture session...");
    }
  }
}

void dataPropertyToSerial(camera_fb_t * fb) {
  Serial.print("Data size: ");
  Serial.print(fb->len);
  Serial.println(" bytes");

  Serial.println("Data shape: [width, height, channels]");
  Serial.print("[");
  Serial.print(fb->width); 
  Serial.print(", ");
  Serial.print(fb->height);
  Serial.print(", ");
  Serial.print(fb->format == PIXFORMAT_GRAYSCALE ? "1" : "3"); // Assuming grayscale is 1 channel, RGB is 3 channels
  Serial.println("]");
}

void httpPostData(camera_fb_t * fb) {
  HTTPClient http;

  http.begin("http://172.20.10.5:8080/upload");
  http.addHeader("Content-Type", "data/jpeg");
  
  int httpResponseCode = http.POST(fb->buf, fb->len);
  Serial.printf("HTTP Response: %d\n", httpResponseCode);
  
  http.end();
}