import RPi.GPIO as GPIO
from time import sleep
from pyrebase import pyrebase
from grove.display.grove_lcd import *  # Import everything from grove_lcd
import cv2
import time
import paho.mqtt.client as mqtt

# Firebase configuration
firebaseConfig = {
    "apiKey": "AIzaSyBJf82tOKBPoZtd0G3t_JwPXEsrliG2bZg",
    "authDomain": "smart-parking-system-b07b5.firebaseapp.com",
    "databaseURL": "https://smart-parking-system-b07b5-default-rtdb.firebaseio.com",
    "projectId": "smart-parking-system-b07b5",
    "storageBucket": "smart-parking-system-b07b5.appspot.com"
}

# Initialize Firebase
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
user = auth.sign_in_with_email_and_password("wongyeeen0822@gmail.com", "abc123")
db = firebase.database()
storage = firebase.storage()

# static file path
ENTRANCE_IMAGE_STORAGE_PATH = 'images/static_entrance_image.jpg'
EXIT_IMAGE_STORAGE_PATH = 'images/static_exit_image.jpg'


# MQTT Broker details
broker = "192.168.52.106"
topic = "test/topic"

# GPIO Pin numbers
IR1_GPIO_NO = 17
IR2_GPIO_NO = 27
IR_Entrance_GPIO = 22
IR_Exit_GPIO = 23
SERVO_GPIO = 12  # GPIO pin for the servo motor
SERVO_EXIT_GPIO = 26  # GPIO pin for the exit gate servo motor

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(IR1_GPIO_NO, GPIO.IN)  # IR1 Sensor input
GPIO.setup(IR2_GPIO_NO, GPIO.IN)  # IR2 Sensor input
GPIO.setup(IR_Entrance_GPIO, GPIO.IN)  # IR entrance sensor
GPIO.setup(IR_Exit_GPIO, GPIO.IN)  # IR exit sensor
GPIO.setup(SERVO_GPIO, GPIO.OUT)  # Servo motor output
GPIO.setup(SERVO_EXIT_GPIO, GPIO.OUT)  # Servo motor output for the exit gate

# Setup PWM for servo motors
servo_pwm = GPIO.PWM(SERVO_GPIO, 50)  # PWM on SERVO_GPIO at 50Hz
servo_exit_pwm = GPIO.PWM(SERVO_EXIT_GPIO, 50)  # PWM on SERVO_EXIT_GPIO at 50Hz
servo_pwm.start(0)  # Start PWM with 0 duty cycle (motor stopped)
servo_exit_pwm.start(0)  # Start PWM with 0 duty cycle (motor stopped)

# Initialize total parking slots
total_slots = 2
last_displayed_slots = None  # To keep track of the last displayed value on the LCD
total_cars_entered = 0  # Counter for total cars entered
total_cars_exited = 0  # Counter for total cars exited

# To track the last detected state of each IR sensor
last_ir1_detected = False
last_ir2_detected = False

previous_entrance_angle = None
previous_exit_angle = None

# Initialize MQTT client
mqtt_client = mqtt.Client()

# Function to connect to MQTT broker
def connect_mqtt():
    mqtt_client.connect(broker, 1883, 60)
    mqtt_client.loop_start()  # Start the MQTT loop

# Function to publish data to MQTT
def publish_data(ir1_status, ir2_status):
    message = f"IR1: {'Detected' if ir1_status else 'Not detected'}, IR2: {'Detected' if ir2_status else 'Not detected'}"
    mqtt_client.publish(topic, message)
    print(f"MQTT Message published: {message}")

def initialize_servo_motor_angles():
    initial_data = {
        "entrance_servo_motor_angle": 0,
        "exit_servo_motor_angle": 0
    }
    db.child("parking_system").update(initial_data)  # Push initial servo angles to Firebase
    
# Call the function after initializing Firebase
initialize_servo_motor_angles()

# Function to control the servo motor (open and close the gate)
def move_servo(angle, is_exit=False):
    duty_cycle = 2 + (angle / 18)  # Formula to convert angle to duty cycle
    print(f"Moving servo to {angle} degrees (Duty Cycle: {duty_cycle})")  # Debug print
    
    # Update Firebase with the new angle
    if is_exit:
        servo_exit_pwm.ChangeDutyCycle(duty_cycle)
        sleep(1.5)  # Wait for the exit servo to move
        servo_exit_pwm.ChangeDutyCycle(0)  # Stop the PWM signal
        db.child("parking_system").update({"exit_servo_motor_angle": angle})  # Push the exit angle to Firebase
    else:
        servo_pwm.ChangeDutyCycle(duty_cycle)
        sleep(1.5)  # Wait for the entrance servo to move
        servo_pwm.ChangeDutyCycle(0)  # Stop the PWM signal
        db.child("parking_system").update({"entrance_servo_motor_angle": angle})  # Push the entrance angle to Firebase


         
# Function to push data to Firebase
def push_to_firebase(ir1_status, ir2_status, total_slots, total_cars_entered, total_cars_exited):
    data = {
        "available_slots": total_slots,       # Current available parking slots
        "IR1_status": ir1_status,            # Status of IR1 detection (true/false)
        "IR2_status": ir2_status,            # Status of IR2 detection (true/false)
        "total_cars_entered": total_cars_entered,  # Total cars that entered
        "total_cars_exited": total_cars_exited     # Total cars that exited
    }
    db.child("parking_system").update(data)  # Push data to Firebase under "parking_system" node


# Function to update Grove LCD display
def update_lcd_display(ir1_detected, ir2_detected):
    global last_displayed_slots
    if ir1_detected and ir2_detected:
        slots = 0
        display_message = "Slots Available: 0"
    elif ir1_detected or ir2_detected:
        slots = 1
        display_message = "Slots Available: 1"
    else:
        slots = 2
        display_message = "Slots Available: 2"
    
    if last_displayed_slots != slots:
        setText(display_message)  # Display the updated message
        last_displayed_slots = slots  # Update the last displayed value

# Capture image functions
def capture_image(camera_index, filename):
    cam = cv2.VideoCapture(camera_index)  # Camera index
    time.sleep(2)  # Allow the camera to warm up
    ret, image = cam.read()
    if ret:
        cv2.imwrite(filename, image)
        cam.release()
        return filename
    else:
        cam.release()
        raise Exception("Failed to capture image")

# Upload to Firebase Storage
def upload_to_firebase(image_path, storage_path):
    storage.child(storage_path).put(image_path, user['idToken'])
    print(f"Image uploaded to Firebase Storage at {storage_path}")

# Initial push to Firebase to set initial statuses
push_to_firebase(False, False, total_slots, total_cars_entered, total_cars_exited)

# Start the MQTT connection
connect_mqtt()

try:
    while True:
        ir1_detected = GPIO.input(IR1_GPIO_NO) == GPIO.LOW  # IR1 detection status
        ir2_detected = GPIO.input(IR2_GPIO_NO) == GPIO.LOW  # IR2 detection status
        ir_entrance_detected = GPIO.input(IR_Entrance_GPIO) == GPIO.LOW  # IR entrance detection status
        ir_exit_detected = GPIO.input(IR_Exit_GPIO) == GPIO.LOW  # IR exit detection status

        # Publish data to MQTT
        publish_data(ir1_detected, ir2_detected)
        # Handle IR1 detection
        if ir1_detected and not last_ir1_detected:
            if total_slots > 0:
                total_slots -= 1  # Decrement available slots
                print("IR1 detected: Slots Available:", total_slots)
                push_to_firebase(True, last_ir2_detected, total_slots, total_cars_entered, total_cars_exited)  # Push data to Firebase
                update_lcd_display(True, last_ir2_detected)  # Update LCD display immediately

        # Handle IR1 no detection
        if not ir1_detected and last_ir1_detected:
            if total_slots < 2:
                total_slots += 1  # Increment available slots
                print("IR1 not detected: Slots Available:", total_slots)
                push_to_firebase(False, last_ir2_detected, total_slots, total_cars_entered, total_cars_exited)  # Push data to Firebase
                update_lcd_display(False, last_ir2_detected)  # Update LCD display immediately

        # Handle IR2 detection
        if ir2_detected and not last_ir2_detected:
            if total_slots > 0:
                total_slots -= 1  # Decrement available slots
                print("IR2 detected: Slots Available:", total_slots)
                push_to_firebase(last_ir1_detected, True, total_slots, total_cars_entered, total_cars_exited)  # Push data to Firebase
                update_lcd_display(last_ir1_detected, True)  # Update LCD display immediately

        # Handle IR2 no detection
        if not ir2_detected and last_ir2_detected:
            if total_slots < 2:
                total_slots += 1  # Increment available slots
                print("IR2 not detected: Slots Available:", total_slots)
                push_to_firebase(last_ir1_detected, False, total_slots, total_cars_entered, total_cars_exited)  # Push data to Firebase
                update_lcd_display(last_ir1_detected, False)  # Update LCD display immediately

        # Handle IR entrance detection, take picture, open the gate
        if ir_entrance_detected:
            total_cars_entered += 1
            print("Entrance detected: capturing image from entrance camera")
            entrance_image_path = capture_image(0, '/home/pi/entrance_image.jpg')  # Camera index 0
            print(f"Entrance image captured at {entrance_image_path}")
            upload_to_firebase(entrance_image_path, ENTRANCE_IMAGE_STORAGE_PATH)  # Use static storage path
            push_to_firebase(last_ir1_detected, last_ir2_detected, total_slots, total_cars_entered, total_cars_exited)

            # Open the gate (servo motor moves to 90 degrees)
            print("Opening the gate...")
            move_servo(90)
            sleep(1.5)  # Keep the gate open for 5 seconds

            # Close the gate (servo motor moves back to 0 degrees)
            print("Closing the gate...")
            move_servo(0)

        # Handle IR exit detection, take picture, open the exit gate
        if ir_exit_detected:
            total_cars_exited += 1
            print("Exit detected: capturing image from exit camera")
            exit_image_path = capture_image(2, '/home/pi/exit_image.jpg')  # Camera index 1
            print(f"Exit image captured at {exit_image_path}")
            upload_to_firebase(exit_image_path, EXIT_IMAGE_STORAGE_PATH)  # Use static storage path
            push_to_firebase(last_ir1_detected, last_ir2_detected, total_slots, total_cars_entered, total_cars_exited)

            # Open the exit gate (servo motor moves to 90 degrees)
            print("Opening the exit gate...")
            move_servo(90, is_exit=True)
            sleep(1.5)  # Keep the gate open for 5 seconds

            # Close the exit gate (servo motor moves back to 0 degrees)
            print("Closing the exit gate...")
            move_servo(0, is_exit=True)

        # Update the last detected states
        last_ir1_detected = ir1_detected
        last_ir2_detected = ir2_detected

        #Fetch angles from Firebase
        updates = db.child("parking_system").get(user['idToken'])
        
        for update in updates.each():
            if update.key() == "entrance_servo_motor_angle":
                entrance_angle = update.val()
                
            if update.key() == "exit_servo_motor_angle":
                exit_angle = update.val()
        
        
        # Check if entrance angle has changed
        if entrance_angle != previous_entrance_angle:
            print(f"Entrance servo angle changed: {entrance_angle}")
            move_servo(entrance_angle)  # Move the entrance servo motor
            previous_entrance_angle = entrance_angle  # Update the previous value
        
        # Check if exit angle has changed
        if exit_angle != previous_exit_angle:
            print(f"Exit servo angle changed: {exit_angle}")
            move_servo(exit_angle, is_exit=True)  # Move the exit servo motor
            previous_exit_angle = exit_angle  # Update the previous value
            
        sleep(0.1)  # Delay to reduce CPU usage


except KeyboardInterrupt:
    print("Cleaning up GPIO...")
finally:
    GPIO.cleanup()  # Clean up GPIO settings
    mqtt_client.loop_stop()  # Stop the MQTT loop
    mqtt_client.disconnect()  # Disconnect from the MQTT broker
