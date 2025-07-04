# Facial-detection-car-based-security-system-code
A facial car-based security system uses facial recognition to allow only authorized users to start a vehicle. A camera scans the face, matches it with stored profiles, and grants or denies access. It enhances security by preventing unauthorized use and deterring vehicle theft.
how the code works: 
1. Hardware & Library Setup

Libraries used:

face_recognition: For detecting and recognizing faces.

picamera: For capturing video frames from the Raspberry Pi camera.

RPi.GPIO: For controlling LEDs, a relay (car ignition), a siren, and a button.

serial: For sending SMS alerts using a GSM module.

numpy: For image processing.

time: For timing delays and intervals.


GPIO pins:

Relay pin (17) – Simulates the car's ignition system.

Button pin (27) – Used to start/stop the car once a valid face is detected.

Siren pin (22) – Triggers an alarm when unauthorized faces are repeatedly detected.

LEDs:

Blue (5): Scanning mode

Green (6): Authorized access

Red (13): Unauthorized face





---

2. Face Recognition Setup

Loads an image (specimen1e3.jpg) of the authorized person at startup.

Extracts facial encoding (a digital representation of the face's features) using face_recognition.



---

3. Scanning & Recognition Loop

Runs continuously:

1. Scanning Mode: Turns on the blue LED.


2. Captures a frame with the camera.


3. Detects and encodes faces in the frame.


4. Compares detected faces to the authorized encoding.



If match is found:

Green LED lights up.

Waits for button press to start the car.

Starts the car by activating the relay and turning off LEDs.


If face is not recognized:

Red LED lights up.

Increments an unauthorized_count.

If 3 or more unauthorized faces are detected in a row:

Activates the siren.

Sends an SMS alert via the GSM module using send_sms().


4. Car Operation Logic

When the car is running:

Waits for the button to be pressed again to stop the car.

Turns off the relay and goes back to scanning mode.


5. Graceful Exit

When you press Ctrl+C, the program:

Cleans up the GPIO pins.

Closes the camera and GSM serial port.

6. GSM SMS Function

Configured to send an SMS to +256704730843 (replace with your own number).

Sends this message when unauthorized access is repeated.
