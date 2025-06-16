#include <Wire.h>
#include <SPI.h>
#include <Adafruit_PN532.h>

// Define the pins for the PN532
#define PN532_IRQ   (4)
#define PN532_RESET (3)  // Not connected by default

// Define SPI pins for ESP32
#define PN532_SCK  (18)
#define PN532_MOSI (23)
#define PN532_MISO (19)
#define PN532_SS   (5)  // Chip select pin

// Create an instance of the PN532 class using SPI
Adafruit_PN532 nfc(PN532_SS);

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10); // Wait for Serial to be ready
  
  Serial.println("\n\nESP32 NFC Reader Starting...");
  Serial.println("Initializing SPI...");
  
  // Initialize SPI
  SPI.begin(PN532_SCK, PN532_MISO, PN532_MOSI, PN532_SS);
  Serial.println("SPI Initialized");
  
  // Add a small delay after SPI initialization
  delay(100);
  
  Serial.println("Initializing PN532...");
  nfc.begin();
  Serial.println("PN532 begin() called");

  // Add a small delay after PN532 initialization
  delay(100);

  // Get the firmware version
  Serial.println("Checking firmware version...");
  uint32_t versiondata = nfc.getFirmwareVersion();
  if (!versiondata) {
    Serial.println("ERROR: Didn't find PN532 board");
    Serial.println("Please check your wiring and try again");
    Serial.println("Make sure:");
    Serial.println("1. SCK is connected to GPIO 18");
    Serial.println("2. MOSI is connected to GPIO 23");
    Serial.println("3. MISO is connected to GPIO 19");
    Serial.println("4. SS/CS is connected to GPIO 5");
    Serial.println("5. VCC is connected to 3.3V");
    Serial.println("6. GND is connected to GND");
    Serial.println("7. IRQ is connected to GPIO 4");
    Serial.println("\nTroubleshooting tips:");
    Serial.println("- Check if the module is getting power (measure VCC-GND)");
    Serial.println("- Try pressing the reset button on the ESP32");
    Serial.println("- Make sure all SPI connections are secure");
    while (1); // halt
  }
  
  // Got ok data, print it out!
  Serial.println("PN532 Found!");
  Serial.print("Found chip PN5"); Serial.println((versiondata >> 24) & 0xFF, HEX);
  Serial.print("Firmware ver. "); Serial.print((versiondata >> 16) & 0xFF, DEC);
  Serial.print('.'); Serial.println((versiondata >> 8) & 0xFF, DEC);

  // Configure the PN532 to read RFID tags
  Serial.println("Configuring SAM...");
  nfc.SAMConfig();
  Serial.println("SAM configured");
  
  Serial.println("System ready!");
  Serial.println("Waiting for an ISO14443A Card ...");
}

void printCardType(uint8_t cardType) {
  switch (cardType) {
    case PN532_MIFARE_ISO14443A:
      Serial.println("Card Type: MIFARE Classic 1K");
      break;
    default:
      Serial.println("Card Type: Unknown");
      break;
  }
}

void readMifareClassic(uint8_t uid[], uint8_t uidLength) {
  // Try to authenticate block 4 (first block of sector 1)
  uint8_t keyA[6] = { 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF }; // Default key
  uint8_t success = nfc.mifareclassic_AuthenticateBlock(uid, uidLength, 4, 0, keyA);
  
  if (success) {
    Serial.println("Authentication successful!");
    
    // Read blocks 4-7 (sector 1)
    for (uint8_t block = 4; block < 8; block++) {
      uint8_t data[16];
      success = nfc.mifareclassic_ReadDataBlock(block, data);
      
      if (success) {
        Serial.print("Block "); Serial.print(block); Serial.print(": ");
        for (uint8_t i = 0; i < 16; i++) {
          if (data[i] < 0x10) Serial.print("0");
          Serial.print(data[i], HEX);
          Serial.print(" ");
        }
        Serial.println();
      } else {
        Serial.print("Failed to read block "); Serial.println(block);
      }
    }
  } else {
    Serial.println("Authentication failed!");
  }
}

void loop() {
  uint8_t success;
  uint8_t uid[] = { 0, 0, 0, 0, 0, 0, 0 };  // Buffer to store the returned UID
  uint8_t uidLength;                        // Length of the UID (4 or 7 bytes depending on ISO14443A card type)

  // Wait for an ISO14443A type cards (Mifare, etc.).  When one is found
  // 'uid' will be populated with the UID, and uidLength will indicate
  // if the uid is 4 bytes (Mifare Classic) or 7 bytes (Mifare Ultralight)
  success = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength);

  if (success) {
    // Display basic information about the card
    Serial.println("\nFound an ISO14443A card");
    Serial.print("  UID Length: "); Serial.print(uidLength, DEC); Serial.println(" bytes");
    Serial.print("  UID Value: ");
    for (uint8_t i = 0; i < uidLength; i++) {
      Serial.print(" 0x"); Serial.print(uid[i], HEX);
    }
    Serial.println("");
    
    // Print card type
    printCardType(PN532_MIFARE_ISO14443A);
    
    // Try to read card data
    if (uidLength == 4) {
      Serial.println("Attempting to read card data...");
      readMifareClassic(uid, uidLength);
    }
    
    // Wait 1 second before continuing
    delay(1000);
  }
} 