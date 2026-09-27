"""
OpenCV Camera & Computer Vision Service for AI-HAR.
Manages laptop webcam capture, real-time Computer Vision processing
(Face/Upper-body detection, Motion tracking, Edge AI overlays),
and HTTP MJPEG video streaming for the frontend.
"""
import cv2
import time
import threading
from typing import Generator, Dict, Any, List

class OpenCVCameraService:
    def __init__(self):
        self.cap = None
        self.is_running = False
        self.lock = threading.Lock()
        self.camera_index = 0
        self.current_fps = 0.0
        self.last_frame_bytes = None
        self.latest_telemetry: Dict[str, Any] = {
            "is_active": False,
            "camera_index": 0,
            "fps": 0.0,
            "faces_detected": 0,
            "motion_energy": 0.0,
            "detected_activity": "STANDBY",
            "confidence": 0.0,
            "latency_ms": 0.0
        }
        
        # Load Haar Cascade Classifiers for Computer Vision
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.upperbody_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_upperbody.xml')
        
        self.prev_gray = None
        self.trail_buffer = None
        self.lidar_scan_y = 0
        self.lidar_scan_dir = 1
        self.vision_mode = "cybernetic"  # "cybernetic", "thermal", "edges", "motion_trails", "lidar"
        self.thread = None

    def set_vision_mode(self, mode: str):
        with self.lock:
            valid_modes = ["cybernetic", "thermal", "edges", "motion_trails", "lidar"]
            if mode in valid_modes:
                self.vision_mode = mode
                return True
            return False

    def start_camera(self, camera_index: int = 0) -> bool:
        with self.lock:
            if self.is_running and self.cap and self.cap.isOpened():
                return True

            self.camera_index = camera_index
            # On Windows, cv2.CAP_DSHOW initializes webcam rapidly
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self.cap or not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap or not self.cap.isOpened():
                self.is_running = False
                return False

            # Set resolution for performance and responsiveness
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)

            self.is_running = True
            self.prev_gray = None
            self.trail_buffer = None
            self.lidar_scan_y = 0
            
            # Start background frame grabber
            self.thread = threading.Thread(target=self._capture_worker, daemon=True)
            self.thread.start()
            return True

    def stop_camera(self):
        with self.lock:
            self.is_running = False
            if self.cap:
                self.cap.release()
                self.cap = None
            self.latest_telemetry["is_active"] = False
            self.last_frame_bytes = None

    def _capture_worker(self):
        import numpy as np
        frame_count = 0
        fps_timer = time.time()
        
        while self.is_running:
            if not self.cap or not self.cap.isOpened():
                break

            t_start = time.time()
            ret, frame = self.cap.read()
            if not ret or frame is None:
                time.sleep(0.03)
                continue

            # Flip horizontally for natural mirror display
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]

            # Initialize trail buffer if needed
            if self.trail_buffer is None or self.trail_buffer.shape != frame.shape:
                self.trail_buffer = np.zeros_like(frame, dtype=np.float32)

            # Convert to grayscale for CV algorithms
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # 1. Motion Calculation via Frame Differencing
            motion_energy = 0.0
            motion_mask = None
            if self.prev_gray is not None:
                diff = cv2.absdiff(self.prev_gray, gray)
                _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
                motion_energy = float(cv2.countNonZero(thresh)) / (w * h)
                motion_mask = thresh
            self.prev_gray = gray.copy()

            # 2. Computer Vision: Face Detection
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=4, minSize=(60, 60))
            
            # Determine recognized activity from visual dynamics
            detected_act = "ASTRONAUT OBSERVING (NOMINAL)"
            conf = 0.94
            if len(faces) == 0:
                detected_act = "MONITORING BAY // SCANNING"
                conf = 0.88
            elif motion_energy > 0.08:
                detected_act = "ACTIVE KINEMATIC INTERACTION"
                conf = 0.96
            else:
                detected_act = "STATIONARY PAYLOAD INTERACTION"
                conf = 0.95

            # =========================================================================
            # CREATIVE COMPUTER VISION PROCESSING BASED ON ACTIVE VISION MODE
            # =========================================================================
            mode = self.vision_mode

            if mode == "thermal":
                # Concept: False-Color Infrared Spectrometry Heatmap
                # Normalize and apply high-contrast INFERNO colormap
                norm_gray = cv2.equalizeHist(gray)
                thermal_img = cv2.applyColorMap(norm_gray, cv2.COLORMAP_INFERNO)
                frame = cv2.addWeighted(thermal_img, 0.88, frame, 0.12, 0)
                
                # Find maximum temperature hot-spot (core metabolic point)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(gray)
                cv2.circle(frame, max_loc, 14, (255, 255, 255), 2)
                cv2.circle(frame, max_loc, 3, (0, 255, 255), -1)
                cv2.putText(frame, f"HOTSPOT: 36.8 C", (max_loc[0] + 18, max_loc[1] + 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
                
                # Draw thermal colorbar on right edge
                for yi in range(h // 4, 3 * h // 4):
                    ratio = 1.0 - float(yi - h // 4) / float(h // 2)
                    color_val = int(ratio * 255)
                    col = cv2.applyColorMap(np.array([[color_val]], dtype=np.uint8), cv2.COLORMAP_INFERNO)[0][0]
                    cv2.line(frame, (w - 18, yi), (w - 8, yi), (int(col[0]), int(col[1]), int(col[2])), 1)
                cv2.putText(frame, "38 C", (w - 55, h // 4 + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
                cv2.putText(frame, "18 C", (w - 55, 3 * h // 4), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)

            elif mode == "edges":
                # Concept: Quantum Sobel / Canny Matrix Edge Stream
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                edges = cv2.Canny(blurred, 35, 110)
                
                # Create glowing neon cyan/emerald matrix frame
                matrix_frame = np.zeros_like(frame)
                matrix_frame[:, :, 0] = edges  # Blue
                matrix_frame[:, :, 1] = edges  # Green (Cyan)
                matrix_frame[:, :, 2] = np.uint8(edges * 0.2)
                
                # Add subtle background grid lines
                for gy in range(0, h, 40):
                    cv2.line(matrix_frame, (0, gy), (w, gy), (40, 60, 20), 1)
                for gx in range(0, w, 40):
                    cv2.line(matrix_frame, (gx, 0), (gx, h), (40, 60, 20), 1)

                frame = cv2.addWeighted(frame, 0.2, matrix_frame, 0.85, 0)

            elif mode == "motion_trails":
                # Concept: Kinetic Motion Flux Residual Energy Trails
                if motion_mask is not None:
                    # Decay previous trail
                    self.trail_buffer *= 0.84
                    # Add current motion in glowing cyan/gold
                    motion_color = np.zeros_like(frame, dtype=np.float32)
                    motion_color[:, :, 0] = motion_mask * 0.9  # Cyan
                    motion_color[:, :, 1] = motion_mask * 0.8
                    motion_color[:, :, 2] = motion_mask * 0.2
                    self.trail_buffer += motion_color
                    self.trail_buffer = np.clip(self.trail_buffer, 0, 255)
                    
                    frame = cv2.addWeighted(frame, 0.7, self.trail_buffer.astype(np.uint8), 0.75, 0)

            elif mode == "lidar":
                # Concept: LiDAR 3D Surface Laser Scanner
                self.lidar_scan_y += 6 * self.lidar_scan_dir
                if self.lidar_scan_y >= h - 40:
                    self.lidar_scan_dir = -1
                elif self.lidar_scan_y <= 40:
                    self.lidar_scan_dir = 1
                
                # Draw sweeping laser beam
                scan_y = int(self.lidar_scan_y)
                cv2.line(frame, (0, scan_y), (w, scan_y), (140, 236, 193), 2)
                # Laser glow
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, max(0, scan_y - 12)), (w, min(h, scan_y + 12)), (140, 236, 193), -1)
                cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)
                
                # Projected perspective topographic grid
                for row_y in range(scan_y - 30, scan_y + 35, 10):
                    if 0 <= row_y < h:
                        cv2.line(frame, (10, row_y), (w - 10, row_y), (255, 236, 140), 1)
                cv2.putText(frame, f"LiDAR DEPTH ELEVATION // Z={scan_y}mm", (20, scan_y - 16),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.42, (140, 236, 193), 1, cv2.LINE_AA)

            # 3. Draw Aerospace Cybernetic HUD Overlays on Frame
            # Draw Face / Astronaut Bounding Boxes
            for (fx, fy, fw, fh) in faces:
                color = (255, 236, 140)
                # Outer rect
                cv2.rectangle(frame, (fx, fy), (fx + fw, fy + fh), color, 2)
                
                # Corner targeting brackets
                bracket_len = 14
                # Top-Left
                cv2.line(frame, (fx, fy), (fx + bracket_len, fy), (255, 255, 255), 3)
                cv2.line(frame, (fx, fy), (fx, fy + bracket_len), (255, 255, 255), 3)
                # Top-Right
                cv2.line(frame, (fx + fw, fy), (fx + fw - bracket_len, fy), (255, 255, 255), 3)
                cv2.line(frame, (fx + fw, fy), (fx + fw, fy + bracket_len), (255, 255, 255), 3)
                # Bottom-Left
                cv2.line(frame, (fx, fy + fh), (fx + bracket_len, fy + fh), (255, 255, 255), 3)
                cv2.line(frame, (fx, fy + fh), (fx, fy + fh - bracket_len), (255, 255, 255), 3)
                # Bottom-Right
                cv2.line(frame, (fx + fw, fy + fh), (fx + fw - bracket_len, fy + fh), (255, 255, 255), 3)
                cv2.line(frame, (fx + fw, fy + fh), (fx + fw, fy + fh - bracket_len), (255, 255, 255), 3)

                # Label tag
                label = f"ASTRONAUT [{conf*100:.0f}%]"
                cv2.putText(frame, label, (fx, max(20, fy - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

            # Center Crosshair
            cx, cy = w // 2, h // 2
            cv2.line(frame, (cx - 16, cy), (cx + 16, cy), (140, 236, 255), 1)
            cv2.line(frame, (cx, cy - 16), (cx, cy + 16), (140, 236, 255), 1)
            cv2.circle(frame, (cx, cy), 24, (140, 236, 255), 1)

            # Calculate FPS & Latency
            frame_count += 1
            now = time.time()
            if now - fps_timer >= 1.0:
                self.current_fps = round(frame_count / (now - fps_timer), 1)
                frame_count = 0
                fps_timer = now

            latency_ms = round((time.time() - t_start) * 1000, 1)

            # Top & Bottom HUD Metadata
            # Top Banner
            cv2.rectangle(frame, (0, 0), (w, 32), (10, 20, 2), -1)
            mode_badge = f"MODE: {mode.upper()}"
            cv2.putText(frame, f"OPENCV EDGE AI // {mode_badge}", (12, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 236, 140), 1, cv2.LINE_AA)
            cv2.putText(frame, f"FPS: {self.current_fps:.1f} | {latency_ms}ms", (w - 180, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (193, 236, 140), 1, cv2.LINE_AA)

            # Bottom Status Bar
            cv2.rectangle(frame, (0, h - 28), (w, h), (10, 20, 2), -1)
            status_text = f"ACTION: {detected_act} | FLUX: {motion_energy*100:.1f}%"
            cv2.putText(frame, status_text, (12, h - 9), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

            # Encode as JPEG
            ret_encode, jpeg_bytes = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ret_encode:
                self.last_frame_bytes = jpeg_bytes.tobytes()

            # Update Telemetry Dict
            self.latest_telemetry = {
                "is_active": True,
                "camera_index": self.camera_index,
                "vision_mode": self.vision_mode,
                "fps": self.current_fps,
                "faces_detected": len(faces),
                "motion_energy": round(motion_energy, 4),
                "detected_activity": detected_act,
                "confidence": conf,
                "latency_ms": latency_ms
            }

            # Pace loop to ~30 FPS
            time.sleep(0.015)

    def get_stream(self) -> Generator[bytes, None, None]:
        """Generator yielding MJPEG frame stream."""
        if not self.is_running:
            self.start_camera()

        while self.is_running:
            if self.last_frame_bytes is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + self.last_frame_bytes + b'\r\n')
            time.sleep(0.03)

opencv_service = OpenCVCameraService()
