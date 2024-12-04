from ultralytics import YOLO
import cv2

# Load the trained model
model = YOLO('emptySpace_n.pt')  # Update this path to the correct model path

# Initialize video capture object
cap = cv2.VideoCapture(0)  # 0 is the default webcam

# Check if the webcam is opened correctly
if not cap.isOpened():
    print("Error: Could not open video stream from webcam.")
    exit()

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to grab frame from webcam.")
        break

    # Run detection
    # Adjust conf threshold if needed
    results = model.predict(source=frame, save=False, conf=0.25)

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
