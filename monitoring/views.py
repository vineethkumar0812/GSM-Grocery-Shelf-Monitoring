from .models import *
import re
from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from ultralytics import YOLO
from django.http import JsonResponse
from PIL import Image
import io
import base64
from django.http import StreamingHttpResponse
from django.views.decorators import gzip
import cv2
import pyttsx3
import threading
import numpy as np

def home(request):
    return render(request, 'index.html')

# Login view
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password")
    return render(request, 'login.html')


def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST.get('password2')  # Confirm password field
        phone_number = request.POST.get('phone_number')  # Phone number field

        if len(username) < 6:
            messages.error(
                request, "Username must be at least 6 characters long")
            return redirect('signup')

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messages.error(request, "Invalid email address")
            return redirect('signup')

        password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        if not re.match(password_pattern, password1):
            messages.error(
                request, "Password must be at least 8 characters long, include numbers, special characters, one uppercase letter, and one lowercase letter.")
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already taken")
            return redirect('signup')
        
        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect('signup')
        user = User.objects.create_user(
            username=username, email=email, password=password1)
        user.save()
        messages.success(request, "User added Successfully")
        return redirect('signup')

    return render(request, 'signup.html')


def logout_view(request):
    logout(request)
    return redirect('home')


# Load the trained YOLO model
model = YOLO('emptySpace_n.pt')  # Make sure this path is correct


def detect_empty_spaces(request):
    if request.method == 'POST':
        # Read the uploaded image file
        image_file = request.FILES['image']

        # Open the image using PIL
        image = Image.open(image_file)

        # Run prediction on the image
        # Save=False to prevent saving locally
        results = model.predict(source=image, save=False)

        # Convert PIL image to base64 for original image
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        original_img_str = base64.b64encode(buffered.getvalue()).decode()

        # Extract detected image
        detected_image = results[0].plot()  # Visualize detections on image
        detected_image_pil = Image.fromarray(detected_image)

        # Convert detected PIL image to base64
        buffered = io.BytesIO()
        detected_image_pil.save(buffered, format="PNG")
        detected_img_str = base64.b64encode(buffered.getvalue()).decode()

        # Return both original and detected images as JSON
        return JsonResponse({
            'original_image': original_img_str,
            'detected_image': detected_img_str
        })
    return render(request, 'detect_empty_spaces.html')


# Load the trained model
model = YOLO('emptySpace_n.pt')

# Initialize the text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Set the speed of speech

# Flag and lock to control alert playback
alert_playing = False
alert_playing_lock = threading.Lock()


def play_alert():
    """Function to play an alert sound."""
    engine.say("Alert! Empty shelf space detected.")
    engine.runAndWait()


def detect_empty_shelf(stream_url):
    """Generator function to process live video frames, detect empty shelves, and stream annotated frames."""
    global alert_playing

    # Capture video stream from RTSP or another source
    cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)

    # Ensure the stream opens
    if not cap.isOpened():
        print("Error: Could not open video stream.")
        return

    alert_thread = None  # Thread to handle audio alerts

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame. Attempting to reconnect...")
            # Re-attempt to open the stream if frame capture fails
            cap.release()
            cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
            continue

        # Run YOLO detection on the frame
        results = model.predict(source=frame, save=False, conf=0.25)

        # Check if empty space is detected in the frame
        with alert_playing_lock:
            if results[0].boxes and not alert_playing:
                # Start a new thread to play the alert sound
                alert_thread = threading.Thread(target=play_alert)
                alert_thread.start()
                alert_playing = True

            # Reset the alert flag once the alert thread has finished
            if alert_thread is not None and not alert_thread.is_alive():
                alert_playing = False

        # Annotate the frame with detection boxes and labels
        annotated_frame = results[0].plot()

        # Encode the frame as JPEG to stream it
        _, jpeg = cv2.imencode('.jpg', annotated_frame)
        frame_data = jpeg.tobytes()

        # Yield the frame as part of the HTTP response
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n\r\n')

    # Release the video capture when finished
    cap.release()


@gzip.gzip_page
def video_feed(request):
    """Django view to stream video with YOLO detection results."""
    # Replace with your actual RTSP or video stream URL
    stream_url = "rtsp://26.49.43.19:8080/h264.sdp"
    return StreamingHttpResponse(detect_empty_shelf(stream_url),
                                 content_type='multipart/x-mixed-replace; boundary=frame')
