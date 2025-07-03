import face_recognition
import picamera
import numpy as np
import RPi.GPIO as GPIO
import serial
import time

# === GPIO SETUP ===
RELAY_PIN = 17        # Relay to simulate car ignition
BUTTON_PIN = 27       # Button for starting/stopping car
SIREN_PIN = 22        # Siren trigger pin

# LED pins
BLUE_LED_PIN = 5      # Scanning indicator
GREEN_LED_PIN = 6     # Authorized face detected
RED_LED_PIN = 13      # Unauthorized face detected

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Setup output pins
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.setup(SIREN_PIN, GPIO.OUT)
GPIO.setup(BLUE_LED_PIN, GPIO.OUT)
GPIO.setup(GREEN_LED_PIN, GPIO.OUT)
GPIO.setup(RED_LED_PIN, GPIO.OUT)
# Setup input pin
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Default states
GPIO.output(RELAY_PIN, GPIO.LOW)
GPIO.output(SIREN_PIN, GPIO.LOW)
GPIO.output(BLUE_LED_PIN, GPIO.LOW)
GPIO.output(GREEN_LED_PIN, GPIO.LOW)
GPIO.output(RED_LED_PIN, GPIO.LOW)

# === GSM SETUP ===
GSM_PORT = "/dev/serial0"
GSM_BAUDRATE = 9600
ser = serial.Serial(GSM_PORT, GSM_BAUDRATE, timeout=1)

def send_sms(message):
    print("Sending SMS alert...")
    ser.write(b'AT+CMGF=1\r')
    time.sleep(0.5)
    ser.write(b'AT+CMGS="+256704730843"\r')  # Change to your real number
    time.sleep(0.5)
    ser.write(message.encode() + b"\x1A")  # Ctrl+Z to send
    time.sleep(3)

# === LED Helper Functions ===
def scanning_mode():
    GPIO.output(BLUE_LED_PIN, GPIO.HIGH)
    GPIO.output(GREEN_LED_PIN, GPIO.LOW)
    GPIO.output(RED_LED_PIN, GPIO.LOW)

def authorized_mode():
    GPIO.output(BLUE_LED_PIN, GPIO.LOW)
    GPIO.output(GREEN_LED_PIN, GPIO.HIGH)
    GPIO.output(RED_LED_PIN, GPIO.LOW)

def unauthorized_mode():
    GPIO.output(BLUE_LED_PIN, GPIO.LOW)
    GPIO.output(GREEN_LED_PIN, GPIO.LOW)
    GPIO.output(RED_LED_PIN, GPIO.HIGH)

def all_leds_off():
    GPIO.output(BLUE_LED_PIN, GPIO.LOW)
    GPIO.output(GREEN_LED_PIN, GPIO.LOW)
    GPIO.output(RED_LED_PIN, GPIO.LOW)

# === FACE RECOGNITION SETUP ===
print("Loading authorized face image")
auth_image = face_recognition.load_image_file("specimen1e3.jpg")
authorized_encoding = face_recognition.face_encodings(auth_image)[0]

camera = picamera.PiCamera()
camera.resolution = (320, 240)
output = np.empty((240, 320, 3), dtype=np.uint8)

unauthorized_count = 0
UNAUTHORIZED_LIMIT = 3

car_started = False
ready_for_recognition = True

print("System is active. Looking for faces...")

try:
    while True:
        if not car_started and ready_for_recognition:
            scanning_mode()
            camera.capture(output, format="rgb")
            face_locations = face_recognition.face_locations(output)
            face_encodings = face_recognition.face_encodings(output, face_locations)

            if not face_encodings:
                print("No faces detected.")
                time.sleep(1)
                continue

            for face_encoding in face_encodings:
                match = face_recognition.compare_faces([authorized_encoding], face_encoding)
                if match[0]:
                    print("Authorized face detected!")
                    authorized_mode()
                    unauthorized_count = 0
                    ready_for_recognition = False  # Stop further scanning

                    # Now wait for button press to start car
                    print("Waiting for button to start the car...")
                    while GPIO.input(BUTTON_PIN) == GPIO.HIGH:
                        time.sleep(0.1)

                    print("Button pressed! Starting car...")
                    GPIO.output(RELAY_PIN, GPIO.HIGH)
                    car_started = True
                    all_leds_off()
                    time.sleep(2)
                else:
                    unauthorized_count += 1
                    print(f"Unauthorized face detected! Count: {unauthorized_count}")
                    unauthorized_mode()

                    if unauthorized_count >= UNAUTHORIZED_LIMIT:
                        print("Triggering siren and sending alert...")
                        GPIO.output(SIREN_PIN, GPIO.HIGH)
                        send_sms("ALERT: Unauthorized face detected multiple times!")
                        time.sleep(5)
                        GPIO.output(SIREN_PIN, GPIO.LOW)
                        unauthorized_count = 0

                    time.sleep(3)

        elif car_started:
            # Car is running, wait for button to stop it
            print("Car running... Waiting for button to stop.")
            while GPIO.input(BUTTON_PIN) == GPIO.HIGH:
                time.sleep(0.1)

            print("Button pressed again! Stopping car.")
            GPIO.output(RELAY_PIN, GPIO.LOW)
            car_started = False
            ready_for_recognition = True
            scanning_mode()
            time.sleep(2)  # Debounce delay

        else:
            # System idle/failsafe
            all_leds_off()
            time.sleep(1)

except KeyboardInterrupt:
    print("Shutting down...")
    GPIO.cleanup()
    camera.close()
    ser.close()
