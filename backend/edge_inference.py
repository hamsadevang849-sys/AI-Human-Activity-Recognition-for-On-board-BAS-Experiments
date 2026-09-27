"""
Edge Computer Vision & Human Activity Recognition Inference Pipeline.
Provides real-time telemetry, object bounding boxes, and activity predictions.
"""
import time
import math
from typing import Dict, Any, List

class EdgeInferenceEngine:
    def __init__(self):
        self.active_model = "ViTPose-Edge + SpatioTemporalTransformer"
        self.device = "Rad-Hardened Edge TPU"
        self.quantization = "INT8"
        self.latency_ms = 11.4
        self.active_camera = "CAM_01"
        self.current_step = 2
        self.deviation_type = "nominal"
        self.custom_activity = None
        self.custom_confidence = None

    def set_camera(self, camera_id: str):
        self.active_camera = camera_id.upper()

    def set_recognition_event(self, camera_id: str = "CAM_01", step_index: int = 2, deviation_type: str = "nominal", activity_name: str = None, confidence: float = None):
        self.active_camera = camera_id.upper()
        self.current_step = step_index
        self.deviation_type = deviation_type
        self.custom_activity = activity_name
        self.custom_confidence = confidence

    def infer_current_frame(self, step_index: int = None, camera_id: str = None) -> Dict[str, Any]:
        t = time.time()
        active_step = step_index if step_index is not None else self.current_step
        cam = (camera_id or self.active_camera).upper()

        # Biometric & kinetic kinematics simulation
        sway = math.sin(t * 1.8) * 12.0
        knee_angle = 42.0 + abs(math.sin(t * 2.5)) * 36.0
        spine_pitch = 11.2 + math.sin(t * 1.5) * 4.0

        activities_map = {
            1: {"name": "PREPARE STERILE WORKSPACE", "confidence": 0.974, "grip": "SUCTION_ALIGN", "dist": 0.08},
            2: {"name": "RETRIEVE SAMPLE CONTAINER", "confidence": 0.968, "grip": "ACTIVE_PINCH", "dist": 0.04},
            3: {"name": "PLACE SAMPLE ON PAYLOAD RACK", "confidence": 0.951, "grip": "CAROUSEL_INSERT", "dist": 0.02},
            4: {"name": "ENGAGE CENTRIFUGE PAYLOAD", "confidence": 0.925, "grip": "TOGGLE_CIRCUIT", "dist": 0.01},
            5: {"name": "RECORD OBSERVATION TELEMETRY", "confidence": 0.940, "grip": "STYLUS_INTERFACE", "dist": 0.05}
        }

        if self.deviation_type == "skipped":
            act_data = {"name": "SEQUENCE DEVIATION: STEP 03 SKIPPED", "confidence": 0.985, "grip": "BYPASS_ENGAGED", "dist": 0.12}
        elif self.deviation_type == "out_of_order":
            act_data = {"name": "PROTOCOL ERROR: OUT-OF-SEQUENCE ACTION", "confidence": 0.979, "grip": "ANOMALOUS_ACTION", "dist": 0.18}
        elif self.custom_activity:
            act_data = {"name": self.custom_activity, "confidence": self.custom_confidence or 0.965, "grip": "ACTIVE_HAR", "dist": 0.03}
        else:
            act_data = activities_map.get(active_step, activities_map[2])

        # Step-specific and Camera-specific Bounding Boxes
        bbox_profiles = {
            1: [
                {"class": "ASTRONAUT", "confidence": 0.985, "box": [130, 50, 240, 230]},
                {"class": "STERILE_BAY_RACK", "confidence": 0.974, "box": [360, 100, 480, 240]},
                {"class": "SUCTION_SEAL_LATCH", "confidence": 0.962, "box": [340, 190, 410, 235]}
            ],
            2: [
                {"class": "ASTRONAUT", "confidence": 0.982, "box": [140, 60, 240, 220]},
                {"class": "SAMPLE_VIAL_RACK", "confidence": 0.971, "box": [380, 110, 490, 230]},
                {"class": "CRYO_CONTAINER", "confidence": 0.954, "box": [320, 140, 365, 175]}
            ],
            3: [
                {"class": "ASTRONAUT", "confidence": 0.988, "box": [150, 55, 250, 225]},
                {"class": "CENTRIFUGE_ROTOR", "confidence": 0.976, "box": [350, 90, 470, 210]},
                {"class": "SPECIMEN_VESSEL_03", "confidence": 0.964, "box": [330, 130, 385, 180]}
            ],
            4: [
                {"class": "ASTRONAUT", "confidence": 0.979, "box": [160, 70, 260, 230]},
                {"class": "CIRCUIT_BREAKER_B4", "confidence": 0.981, "box": [390, 80, 460, 150]},
                {"class": "RPM_CONTROLLER", "confidence": 0.942, "box": [370, 160, 440, 220]}
            ],
            5: [
                {"class": "ASTRONAUT", "confidence": 0.984, "box": [145, 60, 245, 220]},
                {"class": "OPTICAL_DENSITY_METER", "confidence": 0.969, "box": [360, 95, 470, 205]},
                {"class": "MISSION_LOG_TERMINAL", "confidence": 0.958, "box": [340, 170, 430, 240]}
            ]
        }

        boxes = bbox_profiles.get(active_step, bbox_profiles[2])
        if self.deviation_type == "skipped":
            boxes = [
                {"class": "ASTRONAUT", "confidence": 0.982, "box": [140, 60, 240, 220]},
                {"class": "[ALERT] BYPASSED_SLOT_03", "confidence": 0.989, "box": [350, 90, 470, 210]},
                {"class": "PREMATURE_CIRCUIT_B4", "confidence": 0.945, "box": [390, 80, 460, 150]}
            ]
        elif self.deviation_type == "out_of_order":
            boxes = [
                {"class": "ASTRONAUT", "confidence": 0.985, "box": [140, 60, 240, 220]},
                {"class": "[CONFLICT] UNEXPECTED_STATE", "confidence": 0.978, "box": [340, 110, 480, 230]}
            ]

        return {
            "timestamp": time.strftime("%H:%M:%S"),
            "camera_id": cam,
            "model": self.active_model,
            "device": self.device,
            "latency_ms": round(11.0 + (math.sin(t * 3) * 0.8), 1),
            "fps": 60.0,
            "current_step": active_step,
            "deviation_type": self.deviation_type,
            "detected_activity": act_data["name"],
            "confidence": act_data["confidence"],
            "kinematics": {
                "knee_angle_deg": round(knee_angle, 1),
                "spine_pitch_deg": round(spine_pitch, 1),
                "astronaut_offset_px": round(sway, 2)
            },
            "bounding_boxes": boxes,
            "hand_object_interaction": {
                "grip_state": act_data.get("grip", "ACTIVE_PINCH"),
                "contact_distance_meters": act_data.get("dist", 0.04),
                "confidence": round(act_data["confidence"] - 0.01, 3)
            }
        }

edge_inference = EdgeInferenceEngine()
