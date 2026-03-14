import cv2
import numpy as np
import random
import time
import threading
import subprocess
import os

class FocusDetector:
    def __init__(self):
        # Face detection setup
        try:
            import dlib
            self.use_dlib = True
            self.detector = dlib.get_frontal_face_detector()
            print("Using dlib for face tracking")
        except:
            self.use_dlib = False
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            print("Using OpenCV Haar Cascades for face tracking")

        # Roasting messages (absence-themed)
        self.roasts = [
            "Where'd you go? Your work misses you!",
            "The screen is RIGHT HERE. Come back!",
            "Running away from your responsibilities again?",
            "Your deadline doesn't pause when you leave.",
            "The chair is still warm. Sit back down.",
            "Leaving won't make the bugs fix themselves.",
            "Your code is crying. Come back!",
            "You think success comes from staring at the wall?",
            "The computer needs you. Don't abandon it.",
            "Focus left the chat. Bring it back!",
            "Your goals aren't going to achieve themselves!",
            "Come back! The keyboard misses your fingers.",
            "Every second away is a second wasted.",
            "Your future self is disappointed right now.",
            "The screen is lonely without you.",
            "Did you forget you have work to do?",
            "Breaks are earned, not stolen!",
            "GET. BACK. TO. WORK. NOW.",
        ]

        self.last_roast_time = 0
        self.roast_cooldown = 3  # seconds between roasts
        self.current_roast = ""

        # Chrome YouTube playlist
        self.youtube_url = "https://www.youtube.com/watch?v=ksR0wDS-L_c&list=PLd0ilE1moz_cdyKMW5Wmwy8aBG6WbIAXb"
        self.chrome_open = False

        # Detection state tracking for stability
        self.absent_count = 0
        self.present_count = 0
        self.absent_threshold = 15   # ~0.5s of no face before triggering
        self.present_threshold = 5   # ~0.17s of face before closing

    def detect_face_absent(self, frame, gray):
        """Return True if no face is detected in the frame."""
        if self.use_dlib:
            faces = self.detector(gray)
            if len(faces) > 0:
                # Draw rectangle around detected face for debug
                for face in faces:
                    x1, y1, x2, y2 = face.left(), face.top(), face.right(), face.bottom()
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                return False
            return True
        else:
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            if len(faces) > 0:
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                return False
            return True

    def open_chrome_playlist(self):
        """Open YouTube playlist in Chrome (only if not already open)."""
        if self.chrome_open:
            return
        self.chrome_open = True

        def start_chrome():
            try:
                if os.name == 'posix':
                    if os.uname().sysname == 'Darwin':  # macOS
                        subprocess.Popen(
                            ['open', '-a', 'Google Chrome', self.youtube_url],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                    else:  # Linux
                        try:
                            subprocess.Popen(
                                ['google-chrome', self.youtube_url],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL
                            )
                        except FileNotFoundError:
                            subprocess.Popen(['xdg-open', self.youtube_url])
                else:  # Windows
                    os.startfile(self.youtube_url)
            except Exception as e:
                print(f"Could not open Chrome: {e}")
                self.chrome_open = False

        thread = threading.Thread(target=start_chrome, daemon=True)
        thread.start()

    def close_chrome_playlist(self):
        """Close only the Chrome tab with the YouTube playlist."""
        if not self.chrome_open:
            return
        self.chrome_open = False

        def stop_chrome():
            try:
                if os.name == 'posix' and os.uname().sysname == 'Darwin':
                    script = (
                        'tell application "Google Chrome"\n'
                        '    set windowList to every window\n'
                        '    repeat with w in windowList\n'
                        '        set tabList to every tab of w\n'
                        '        repeat with t in tabList\n'
                        '            if URL of t contains "PLd0ilE1moz_cdyKMW5Wmwy8aBG6WbIAXb" then\n'
                        '                close t\n'
                        '            end if\n'
                        '        end repeat\n'
                        '    end repeat\n'
                        'end tell\n'
                    )
                    subprocess.run(
                        ['osascript', '-e', script],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
            except Exception as e:
                print(f"Could not close Chrome tab: {e}")

        thread = threading.Thread(target=stop_chrome, daemon=True)
        thread.start()

    def show_roast(self, frame):
        """Display roasting message on frame."""
        current_time = time.time()

        if current_time - self.last_roast_time > self.roast_cooldown:
            self.current_roast = random.choice(self.roasts)
            self.last_roast_time = current_time

        # Create semi-transparent overlay
        overlay = frame.copy()
        h, w = frame.shape[:2]

        # Draw red warning background
        cv2.rectangle(overlay, (0, 0), (w, 150), (0, 0, 255), -1)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

        # Draw warning text
        cv2.putText(frame, "FACE NOT DETECTED!", (w//2 - 200, 50),
                   cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 3)

        # Draw roast message
        cv2.putText(frame, self.current_roast, (w//2 - 300, 100),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    def run(self):
        """Main loop"""
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("Error: Could not open webcam")
            return

        print("Focus Detector Started!")
        print("Looking for your face...")
        print("Press 'q' to quit")

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("Failed to grab frame")
                continue

            # Flip frame horizontally for mirror view
            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect face absence
            face_absent = self.detect_face_absent(frame, gray)

            # Stabilize detection with frame counting
            if face_absent:
                self.absent_count += 1
                self.present_count = 0
            else:
                self.present_count += 1
                self.absent_count = 0

            is_absent = self.absent_count >= self.absent_threshold
            is_present = self.present_count >= self.present_threshold

            if is_absent:
                self.show_roast(frame)
                self.open_chrome_playlist()
            elif is_present:
                cv2.putText(frame, "Welcome back! Stay focused!", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                self.close_chrome_playlist()
            else:
                cv2.putText(frame, "Monitoring...", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

            # Display frame
            cv2.imshow('Focus Detector', frame)

            # Exit on 'q'
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

        # Cleanup
        self.close_chrome_playlist()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    detector = FocusDetector()
    detector.run()
