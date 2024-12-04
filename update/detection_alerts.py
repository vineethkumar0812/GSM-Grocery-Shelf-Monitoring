from ultralytics import YOLO
import cv2
import pyttsx3
import threading

# Load the trained model
model = YOLO('emptySpace_n.pt')  # Update this path to the correct model path

# Initialize the text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Set the speed of speech (optional)

# Initialize video capture object
cap = cv2.VideoCapture(0)  # 0 is the default webcam

# Check if the webcam is opened correctly
if not cap.isOpened():
    print("Error: Could not open video stream from webcam.")
    exit()

# Function to play alert sound


def play_alert():
    engine.say("Alert! Empty shelf space detected.")
    engine.runAndWait()


# Flag to track if an alert is already playing
alert_playing = False

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to grab frame from webcam.")
        break

    # Run detection
    results = model.predict(source=frame, save=False, conf=0.25)

    # Check if empty space is detected in the results
    # Assuming detection results contain bounding boxes if empty space is found
    if results[0].boxes and not alert_playing:
        # Start the alert in a new thread
        alert_thread = threading.Thread(target=play_alert)
        alert_thread.start()
        alert_playing = True

    # Reset the alert flag after the alert thread finishes
    if not alert_thread.is_alive():
        alert_playing = False

    # Draw the bounding boxes and labels on the frame
    annotated_frame = results[0].plot()  # Plot the results on the frame

    # Display the resulting frame
    cv2.imshow('YOLO Empty Shelf Detection', annotated_frame)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture object and close display window
cap.release()
cv2.destroyAllWindows()
