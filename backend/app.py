"""
Main FastAPI Application for AI Human Activity Recognition on BAS.
Serves REST APIs, WebSockets, and the 3D Frontend Interface.
"""
import os
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse, HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .models import (
    SystemStatus, SequenceValidationRequest, SequenceValidationResponse,
    LogEntry, StreamConfigRequest, StreamStatus, StorageInfo,
    CameraRecognitionRequest, CameraSelectRequest
)
from .sequence_engine import sequence_engine
from .storage_manager import storage_manager
from .ip_streamer import ip_streamer
from .edge_inference import edge_inference
from .opencv_service import opencv_service

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML = os.path.join(ROOT_DIR, "index.html")
DASHBOARD_HTML = os.path.join(ROOT_DIR, "dashboard.html")
THREE_JS = os.path.join(ROOT_DIR, "three.min.js")

app = FastAPI(
    title="AI Human Activity Recognition for On-board BAS Experiments",
    description="Autonomous Standalone Edge AI Assistant for Microgravity Scientific Experiments",
    version="4.8.2"
)

# Enable CORS for development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- STATIC FRONTEND ROUTES -----------------

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    if os.path.exists(INDEX_HTML):
        return FileResponse(INDEX_HTML)
    return HTMLResponse("<h1>AI-HAR Frontend file not found</h1>", status_code=404)

@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    if os.path.exists(DASHBOARD_HTML):
        return FileResponse(DASHBOARD_HTML)
    if os.path.exists(INDEX_HTML):
        return FileResponse(INDEX_HTML)
    return HTMLResponse("<h1>Dashboard file not found</h1>", status_code=404)

@app.get("/three.min.js")
async def serve_three():
    if os.path.exists(THREE_JS):
        return FileResponse(THREE_JS)
    return PlainTextResponse("three.min.js not found", status_code=404)

# Mount JS modules directory for modular frontend architecture
JS_DIR = os.path.join(ROOT_DIR, "js")
os.makedirs(JS_DIR, exist_ok=True)
app.mount("/js", StaticFiles(directory=JS_DIR), name="js")

# ----------------- SYSTEM STATUS & PROTOCOL -----------------

@app.get("/api/status", response_model=SystemStatus)
async def get_system_status():
    act = edge_inference.infer_current_frame()
    return SystemStatus(
        current_step=sequence_engine.current_step_index,
        sequence_status=sequence_engine.last_status,
        deviation_type=edge_inference.deviation_type,
        detected_activity=act["detected_activity"],
        confidence=act["confidence"],
        active_camera=edge_inference.active_camera,
        storage_state="RECORDING ACTIVE" if storage_manager.recording_active else "RECORDING PAUSED",
        vocal_alert="NONE" if sequence_engine.last_status == "NOMINAL_VALIDATED" else sequence_engine.last_status
    )

@app.get("/api/protocol")
async def get_protocol_steps():
    return {
        "protocol_id": "BAS-EXP-04",
        "title": "Biological Specimen Extraction & Centrifuge Activation",
        "steps": sequence_engine.get_steps(),
        "current_step_index": sequence_engine.current_step_index
    }

@app.post("/api/protocol/reset")
async def reset_protocol():
    sequence_engine.reset()
    storage_manager.add_log("RESET", "Protocol re-initialized to initial nominal state.", "VALIDATED")
    return {"status": "RESET_SUCCESSFUL", "steps": sequence_engine.get_steps()}

# ----------------- SEQUENCE VALIDATION -----------------

@app.post("/api/sequence/validate", response_model=SequenceValidationResponse)
async def validate_sequence_step(req: SequenceValidationRequest):
    res = sequence_engine.validate_action(
        detected_step_index=req.detected_step_index,
        detected_action=req.detected_action
    )

    # Automatically record in persistent audit log
    step_label = f"STEP 0{req.detected_step_index}"
    log_status = "VALIDATED" if res.is_valid else ("SKIPPED" if res.deviation_type == "skipped" else "ALERT")
    storage_manager.add_log(step_label, res.detected_step_title, log_status, outcome=res.deviation_type.upper())

    return res

# ----------------- AUDIT LOGS & EXPORT -----------------

@app.get("/api/logs")
async def get_audit_logs():
    return {"logs": storage_manager.get_logs()}

@app.post("/api/logs")
async def add_audit_log(entry: LogEntry):
    added = storage_manager.add_log(entry.step, entry.activity, entry.status, entry.outcome)
    return {"status": "LOG_RECORDED", "entry": added}

@app.get("/api/logs/export")
async def export_audit_log_file():
    text_content = storage_manager.export_structured_text()
    return PlainTextResponse(
        text_content,
        headers={
            "Content-Disposition": f"attachment; filename=BAS_EXP_001_AUDIT_LOG.txt",
            "Content-Type": "text/plain; charset=utf-8"
        }
    )

# ----------------- LOCAL STORAGE & RECORDING -----------------

@app.get("/api/storage", response_model=StorageInfo)
async def get_storage_status():
    return storage_manager.get_storage_info()

@app.post("/api/storage/record/toggle")
async def toggle_recording_state():
    is_active = storage_manager.toggle_recording()
    status_str = "RECORDING ACTIVE" if is_active else "RECORDING PAUSED"
    storage_manager.add_log("STORAGE", f"Local NVMe recording state changed: {status_str}", "NOMINAL")
    return {"recording_active": is_active, "status_message": status_str}

# ----------------- IP VIDEO STREAMING INTERFACE -----------------

@app.get("/api/stream/status", response_model=StreamStatus)
async def get_stream_status():
    return ip_streamer.get_status()

@app.post("/api/stream/start", response_model=StreamStatus)
async def start_ip_stream(req: StreamConfigRequest):
    status = ip_streamer.start_stream(req)
    storage_manager.add_log("STREAM", f"Stream connected to destination: {req.destination_ip}:{req.port}", "CONNECT")
    return status

@app.post("/api/stream/stop", response_model=StreamStatus)
async def stop_ip_stream():
    status = ip_streamer.stop_stream()
    storage_manager.add_log("STREAM", "Stream disconnected", "DISCONNECT")
    return status

# ----------------- EDGE AI INFERENCE & TELEMETRY -----------------

@app.get("/api/ai/frame")
async def get_ai_frame_telemetry():
    return edge_inference.infer_current_frame(sequence_engine.current_step_index)

@app.post("/api/ai/recognize", response_model=SequenceValidationResponse)
async def process_camera_recognition_event(req: CameraRecognitionRequest):
    res = sequence_engine.process_camera_recognition(
        camera_id=req.camera_id,
        step_index=req.step_index,
        deviation_type=req.deviation_type or "nominal",
        action_title=req.action_title
    )
    edge_inference.set_recognition_event(
        camera_id=req.camera_id,
        step_index=res.detected_step_index,
        deviation_type=res.deviation_type,
        activity_name=res.detected_step_title,
        confidence=req.confidence or 0.968
    )
    step_label = f"STEP 0{res.detected_step_index}"
    log_status = "VALIDATED" if res.is_valid else ("SKIPPED" if res.deviation_type == "skipped" else "ALERT")
    storage_manager.add_log(f"[{req.camera_id}] {step_label}", res.detected_step_title, log_status, outcome=res.deviation_type.upper())
    return res

@app.post("/api/camera/select")
async def select_active_camera(req: CameraSelectRequest):
    edge_inference.set_camera(req.camera_id)
    storage_manager.add_log("CAMERA", f"Active optical channel switched to {req.camera_id.upper()}", "NOMINAL")
    return {
        "status": "CAMERA_SWITCHED",
        "active_camera": edge_inference.active_camera,
        "telemetry": edge_inference.infer_current_frame()
    }

# ----------------- OPENCV COMPUTER VISION LIVE STREAM -----------------

@app.get("/api/camera/video_feed")
async def get_camera_video_feed():
    """Live MJPEG video stream from laptop webcam processed with OpenCV Computer Vision."""
    if not opencv_service.is_running:
        opencv_service.start_camera(0)
    return StreamingResponse(
        opencv_service.get_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.post("/api/camera/opencv/start")
async def start_opencv_camera():
    success = opencv_service.start_camera(0)
    if success:
        storage_manager.add_log("OPENCV_CAM", "Laptop camera optical sensor connected via OpenCV Computer Vision", "VALIDATED")
    return {"status": "SUCCESS" if success else "FAILED", "is_running": opencv_service.is_running}

@app.post("/api/camera/opencv/stop")
async def stop_opencv_camera():
    opencv_service.stop_camera()
    storage_manager.add_log("OPENCV_CAM", "OpenCV camera sensor disconnected and released", "NOMINAL")
    return {"status": "STOPPED", "is_running": False}

@app.get("/api/camera/opencv/telemetry")
async def get_opencv_telemetry():
    return opencv_service.latest_telemetry

@app.post("/api/camera/opencv/mode")
async def set_opencv_mode(payload: dict):
    mode = payload.get("mode", "cybernetic")
    success = opencv_service.set_vision_mode(mode)
    storage_manager.add_log("OPENCV_CAM", f"Vision filter mode switched to {mode.upper()}", "NOMINAL")
    return {"status": "SUCCESS" if success else "INVALID_MODE", "mode": opencv_service.vision_mode}

# ----------------- WEBSOCKET FOR REAL-TIME TELEMETRY -----------------

@app.websocket("/ws/telemetry")
async def websocket_telemetry_feed(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            telemetry = edge_inference.infer_current_frame(sequence_engine.current_step_index)
            telemetry["stream_status"] = ip_streamer.get_status().dict()
            telemetry["sequence_status"] = sequence_engine.last_status
            telemetry["active_camera"] = edge_inference.active_camera
            await websocket.send_json(telemetry)
            await asyncio.sleep(0.1)  # 10 Hz telemetry stream
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
