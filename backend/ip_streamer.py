"""
IP Video Streaming Manager for BAS Experiment Video Feed.
Handles configuration, destination socket binding simulation, and streaming status.
"""
from typing import Dict, Any
from .models import StreamConfigRequest, StreamStatus

class IPVideoStreamer:
    def __init__(self):
        self.is_streaming = False
        self.destination_ip = "192.168.1.140"
        self.port = 8554
        self.protocol = "RTSP"
        self.packets_sent = 0
        self.status_message = "STANDBY // BACKEND INTEGRATION READY"

    def start_stream(self, config: StreamConfigRequest) -> StreamStatus:
        self.destination_ip = config.destination_ip
        self.port = config.port
        self.protocol = config.protocol
        self.is_streaming = True
        self.status_message = f"ACTIVE // STREAMING TO {self.destination_ip}:{self.port} VIA {self.protocol}"
        return self.get_status()

    def stop_stream(self) -> StreamStatus:
        self.is_streaming = False
        self.status_message = "DISCONNECTED // STANDBY"
        return self.get_status()

    def get_status(self) -> StreamStatus:
        if self.is_streaming:
            self.packets_sent += 60  # increment 60 fps packet simulation
        return StreamStatus(
            is_streaming=self.is_streaming,
            destination_ip=self.destination_ip,
            port=self.port,
            protocol=self.protocol,
            packets_sent=self.packets_sent,
            status_message=self.status_message
        )

ip_streamer = IPVideoStreamer()
