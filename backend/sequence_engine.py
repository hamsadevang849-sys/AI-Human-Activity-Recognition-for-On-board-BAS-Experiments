"""
Deterministic Sequence Validation Engine for BAS Experiments.
Detects nominal execution, skipped steps, and out-of-sequence protocol deviations.
"""
from datetime import datetime
from typing import List, Dict, Any
from .models import ExperimentStep, SequenceValidationResponse

DEFAULT_PROTOCOL_STEPS = [
    {
        "index": 1,
        "title": "Prepare equipment & sterile workspace",
        "action_description": "Align biological specimen payload rack & engage suction seal",
        "status": "VALIDATED",
        "badge_class": "validated",
        "confidence": "Demo confidence 97.4%"
    },
    {
        "index": 2,
        "title": "Retrieve sample container from storage bay",
        "action_description": "Unlock bay latch & extract microgravity cryo-vial container",
        "status": "COMPLETED",
        "badge_class": "validated",
        "confidence": "Demo confidence 96.8%"
    },
    {
        "index": 3,
        "title": "Place sample on payload centrifuge rack",
        "action_description": "Align vessel into centrifuge slot 03 until locking click",
        "status": "READY",
        "badge_class": "validated",
        "confidence": "Demo confidence 95.1%"
    },
    {
        "index": 4,
        "title": "Engage centrifuge & activate payload circuit",
        "action_description": "Toggle circuit breaker B4 & initiate 1200 RPM spin profile",
        "status": "AWAITING",
        "badge_class": "validated",
        "confidence": "Demo confidence 92.5%"
    },
    {
        "index": 5,
        "title": "Record observation telemetry in logbook",
        "action_description": "Verify optical density metrics and archive run timestamp",
        "status": "PENDING",
        "badge_class": "validated",
        "confidence": "Demo confidence 94.0%"
    }
]

class SequenceValidatorEngine:
    def __init__(self):
        self.reset()

    def reset(self):
        self.steps: List[Dict[str, Any]] = [dict(s) for s in DEFAULT_PROTOCOL_STEPS]
        self.current_step_index = 2
        self.last_status = "VALIDATING"
        self.last_alert = "NONE"

    def get_steps(self) -> List[Dict[str, Any]]:
        return self.steps

    def validate_action(self, detected_step_index: int, detected_action: str = None) -> SequenceValidationResponse:
        now_str = datetime.now().strftime("%H:%M:%S")
        expected_step = self.current_step_index + 1
        
        # Clamp bounds
        if expected_step > len(self.steps):
            expected_step = len(self.steps)

        expected_step_obj = self.steps[expected_step - 1]
        detected_step_obj = self.steps[min(detected_step_index, len(self.steps)) - 1]

        # 1. NOMINAL CASE: detected step matches next expected step
        if detected_step_index == expected_step:
            self.current_step_index = detected_step_index
            self.steps[detected_step_index - 1]["status"] = "VALIDATED"
            self.steps[detected_step_index - 1]["badge_class"] = "validated"
            
            # Next recommendation
            if self.current_step_index < len(self.steps):
                next_step = self.steps[self.current_step_index]
                next_step["status"] = "READY"
                next_rec_title = f"Step 0{next_step['index']} -- {next_step['title']}"
            else:
                next_rec_title = "Experiment Protocol Fully Concluded"

            self.last_status = "NOMINAL_VALIDATED"
            voice_alert = f"Step 0{detected_step_index} validated. Next recommended step: {next_rec_title}."

            return SequenceValidationResponse(
                timestamp=now_str,
                status="VALIDATED",
                deviation_type="nominal",
                expected_step_index=expected_step,
                detected_step_index=detected_step_index,
                expected_step_title=expected_step_obj["title"],
                detected_step_title=detected_step_obj["title"],
                voice_alert_phrase=voice_alert,
                next_recommended_step_title=next_rec_title,
                is_valid=True
            )

        # 2. SKIPPED STEP CASE: detected step jumped ahead of expected step
        elif detected_step_index > expected_step:
            skipped_step_index = expected_step
            skipped_obj = self.steps[skipped_step_index - 1]
            skipped_obj["status"] = "SKIPPED"
            skipped_obj["badge_class"] = "alert-skip"

            self.steps[detected_step_index - 1]["status"] = "UNEXPECTED"
            self.steps[detected_step_index - 1]["badge_class"] = "alert-skip"

            self.last_status = "SEQUENCE_DEVIATION"
            voice_alert = f"Sequence deviation. Step 0{skipped_step_index} has been skipped. Please return and complete {skipped_obj['title']}."

            return SequenceValidationResponse(
                timestamp=now_str,
                status="SEQUENCE DEVIATION",
                deviation_type="skipped",
                expected_step_index=expected_step,
                detected_step_index=detected_step_index,
                expected_step_title=expected_step_obj["title"],
                detected_step_title=detected_step_obj["title"],
                voice_alert_phrase=voice_alert,
                next_recommended_step_title=f"[ALERT] RETURN TO Step 0{skipped_step_index} -- {skipped_obj['title']}",
                is_valid=False
            )

        # 3. OUT-OF-SEQUENCE CASE: unexpected step detected out of order
        else:
            self.steps[detected_step_index - 1]["status"] = "OUT-OF-ORDER"
            self.steps[detected_step_index - 1]["badge_class"] = "alert-dev"

            self.last_status = "OUT_OF_SEQUENCE"
            voice_alert = f"Warning. Activity detected out of sequence. Expected step 0{expected_step}, but detected step 0{detected_step_index}."

            return SequenceValidationResponse(
                timestamp=now_str,
                status="PROTOCOL DEVIATION",
                deviation_type="out_of_order",
                expected_step_index=expected_step,
                detected_step_index=detected_step_index,
                expected_step_title=expected_step_obj["title"],
                detected_step_title=detected_step_obj["title"],
                voice_alert_phrase=voice_alert,
                next_recommended_step_title=f"[ALERT] PROTOCOL HALT: Verify Step 0{expected_step} status",
                is_valid=False
            )

    def process_camera_recognition(self, camera_id: str = "CAM_01", step_index: int = 2, deviation_type: str = "nominal", action_title: str = None) -> SequenceValidationResponse:
        now_str = datetime.now().strftime("%H:%M:%S")
        if deviation_type == "skipped":
            skipped_step_index = 3
            self.steps[skipped_step_index - 1]["status"] = "SKIPPED"
            self.steps[skipped_step_index - 1]["badge_class"] = "alert-skip"
            target_step = 4
            self.steps[target_step - 1]["status"] = "UNEXPECTED"
            self.steps[target_step - 1]["badge_class"] = "alert-skip"
            self.current_step_index = target_step
            self.last_status = "SEQUENCE_DEVIATION"
            voice_alert = f"Camera alert: Sequence deviation detected. Step 0{skipped_step_index} has been skipped. Please return and place sample in centrifuge."
            return SequenceValidationResponse(
                timestamp=now_str,
                status="SEQUENCE DEVIATION",
                deviation_type="skipped",
                expected_step_index=3,
                detected_step_index=4,
                expected_step_title=self.steps[2]["title"],
                detected_step_title=self.steps[3]["title"],
                voice_alert_phrase=voice_alert,
                next_recommended_step_title=f"[ALERT] RETURN TO Step 0{skipped_step_index} -- {self.steps[skipped_step_index - 1]['title']}",
                is_valid=False
            )
        elif deviation_type == "out_of_order":
            self.steps[0]["status"] = "OUT-OF-ORDER"
            self.steps[0]["badge_class"] = "alert-dev"
            self.last_status = "OUT_OF_SEQUENCE"
            voice_alert = "Warning. Camera detected activity out of sequence. Protocol halt."
            return SequenceValidationResponse(
                timestamp=now_str,
                status="PROTOCOL DEVIATION",
                deviation_type="out_of_order",
                expected_step_index=self.current_step_index + 1 if self.current_step_index < 5 else 5,
                detected_step_index=1,
                expected_step_title=self.steps[min(self.current_step_index, 4)]["title"],
                detected_step_title=self.steps[0]["title"],
                voice_alert_phrase=voice_alert,
                next_recommended_step_title="[ALERT] PROTOCOL HALT: Verify active step sequence",
                is_valid=False
            )
        else:
            step_idx = max(1, min(step_index, len(self.steps)))
            self.current_step_index = step_idx
            for i in range(step_idx):
                self.steps[i]["status"] = "VALIDATED"
                self.steps[i]["badge_class"] = "validated"
            if step_idx < len(self.steps):
                self.steps[step_idx]["status"] = "READY"
                next_rec_title = f"Step 0{self.steps[step_idx]['index']} -- {self.steps[step_idx]['title']}"
            else:
                next_rec_title = "Experiment Protocol Fully Concluded"

            self.last_status = "NOMINAL_VALIDATED"
            detected_obj = self.steps[step_idx - 1]
            voice_alert = f"Camera {camera_id}: Step 0{step_idx} validated. Next recommended step: {next_rec_title}."
            return SequenceValidationResponse(
                timestamp=now_str,
                status="VALIDATED",
                deviation_type="nominal",
                expected_step_index=step_idx,
                detected_step_index=step_idx,
                expected_step_title=detected_obj["title"],
                detected_step_title=detected_obj["title"],
                voice_alert_phrase=voice_alert,
                next_recommended_step_title=next_rec_title,
                is_valid=True
            )

sequence_engine = SequenceValidatorEngine()
