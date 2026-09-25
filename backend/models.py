"""
Pydantic Data Models for AI Human Activity Recognition (HAR) on BAS
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ExperimentStep(BaseModel):
    index: int
    title: str
    action_description: str
    status: str = "AWAITING"
    badge_class: str = "validated"
    confidence: str = "Demo confidence 95.0%"

class SequenceValidationRequest(BaseModel):
    detected_step_index: int
    detected_action: Optional[str] = None
    confidence: Optional[float] = 0.96

class SequenceValidationResponse(BaseModel):
    timestamp: str
    status: str
    deviation_type: str  # "nominal", "skipped", "out_of_order"
    expected_step_index: int
    detected_step_index: int
    expected_step_title: str
    detected_step_title: str
    voice_alert_phrase: str
    next_recommended_step_title: str
    is_valid: bool

class LogEntry(BaseModel):
    timestamp: str
    step: str
    activity: str
    status: str
    outcome: str = "NOMINAL_AUDIT"

class StreamConfigRequest(BaseModel):
    destination_ip: str
    port: int = 8554
    protocol: str = "RTSP"
    bitrate_kbps: int = 4000

class StreamStatus(BaseModel):
    is_streaming: bool
    destination_ip: str
    port: int
    protocol: str
    packets_sent: int
    status_message: str

class StorageFile(BaseModel):
    filename: str
    duration: str
    size_mb: int
    recorded_at: str

class StorageInfo(BaseModel):
    total_capacity_gb: float
    used_capacity_gb: float
    free_capacity_gb: float
    percent_free: float
    recording_active: bool
    files: List[StorageFile]

class SystemStatus(BaseModel):
    mission: str = "BAS-EXP-001"
    ai_core: str = "ONLINE (STANDALONE EDGE TPU)"
    mode: str = "STANDALONE / NO CLOUD REQUIRED"
    camera_01: str = "ONLINE (1080p 60FPS)"
    comm_delay: str = "1.28s - 24m (GROUND CONSTRAINED)"
    local_inference_ms: float = 11.4
    active_protocol: str = "BAS-EXP-04: Biological Specimen Extraction"
    current_step: int = 2
    sequence_status: str = "VALIDATING"
    storage_state: str = "RECORDING ACTIVE"
