/**
 * AI-HAR Astronaut Activity Recognition System
 * Module: Camera Manager (js/camera.js)
 * Manages live laptop webcam stream, permissions, canvas overlays, and real-time FPS monitoring.
 */

class CameraManager {
  constructor() {
    this.videoEl = null;
    this.canvasEl = null;
    this.ctx = null;
    this.stream = null;
    this.isStreaming = false;
    this.isDetectionPaused = false;
    
    // FPS tracking
    this.fps = 0;
    this.frameCount = 0;
    this.lastFpsUpdateTime = performance.now();
    this.lastFrameTime = performance.now();
    
    // Callbacks
    this.onFrameCallback = null;
    this.onStateChangeCallback = null;
    this.animationFrameId = null;
  }

  init(videoEl, canvasEl, onFrameCallback, onStateChangeCallback) {
    this.videoEl = videoEl;
    this.canvasEl = canvasEl;
    this.ctx = canvasEl ? canvasEl.getContext('2d', { willReadFrequently: true }) : null;
    this.onFrameCallback = onFrameCallback;
    this.onStateChangeCallback = onStateChangeCallback;

    // Handle window resize
    window.addEventListener('resize', () => this.syncCanvasDimensions());
  }

  syncCanvasDimensions() {
    if (!this.canvasEl || !this.videoEl) return;
    const parent = this.canvasEl.parentElement;
    if (parent) {
      this.canvasEl.width = parent.clientWidth || 1280;
      this.canvasEl.height = parent.clientHeight || 720;
    }
  }

  async startCamera() {
    try {
      if (this.isStreaming) return true;

      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Browser does not support navigator.mediaDevices.getUserMedia");
      }

      // Request actual laptop webcam
      const constraints = {
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: "user",
          frameRate: { ideal: 30, max: 60 }
        },
        audio: false
      };

      this.stream = await navigator.mediaDevices.getUserMedia(constraints);
      this.videoEl.srcObject = this.stream;

      await new Promise((resolve) => {
        this.videoEl.onloadedmetadata = () => {
          this.videoEl.play();
          resolve();
        };
      });

      this.isStreaming = true;
      this.isDetectionPaused = false;
      this.syncCanvasDimensions();

      // Start processing loop
      this.startLoop();

      if (this.onStateChangeCallback) {
        this.onStateChangeCallback({
          isStreaming: true,
          isDetectionPaused: false,
          error: null
        });
      }

      return true;
    } catch (err) {
      console.error("[CameraManager] Camera access error:", err);
      this.isStreaming = false;

      if (this.onStateChangeCallback) {
        this.onStateChangeCallback({
          isStreaming: false,
          isDetectionPaused: false,
          error: err.name === "NotAllowedError" 
            ? "Camera permission denied by user. Please allow webcam access in browser."
            : err.message || "Failed to access laptop camera."
        });
      }
      return false;
    }
  }

  stopCamera() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }

    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }

    if (this.videoEl) {
      this.videoEl.srcObject = null;
    }

    this.isStreaming = false;
    this.isDetectionPaused = false;
    this.fps = 0;

    // Clear canvas
    if (this.ctx && this.canvasEl) {
      this.ctx.clearRect(0, 0, this.canvasEl.width, this.canvasEl.height);
    }

    if (this.onStateChangeCallback) {
      this.onStateChangeCallback({
        isStreaming: false,
        isDetectionPaused: false,
        error: null
      });
    }
  }

  togglePauseDetection() {
    this.isDetectionPaused = !this.isDetectionPaused;
    if (this.onStateChangeCallback) {
      this.onStateChangeCallback({
        isStreaming: this.isStreaming,
        isDetectionPaused: this.isDetectionPaused,
        error: null
      });
    }
    return this.isDetectionPaused;
  }

  toggleFullscreen(containerEl) {
    const el = containerEl || this.canvasEl?.parentElement;
    if (!el) return;

    if (!document.fullscreenElement) {
      if (el.requestFullscreen) {
        el.requestFullscreen();
      } else if (el.webkitRequestFullscreen) {
        el.webkitRequestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  }

  startLoop() {
    const loop = (timestamp) => {
      if (!this.isStreaming) return;

      // Calculate real processing FPS over 1000ms rolling window
      this.frameCount++;
      const elapsedSinceFps = timestamp - this.lastFpsUpdateTime;
      if (elapsedSinceFps >= 1000) {
        this.fps = Math.round((this.frameCount * 1000) / elapsedSinceFps);
        this.frameCount = 0;
        this.lastFpsUpdateTime = timestamp;
      }

      const deltaMs = timestamp - this.lastFrameTime;
      this.lastFrameTime = timestamp;

      // Ensure canvas matches video aspect
      this.syncCanvasDimensions();

      // Render frame and execute CV pipeline if not paused
      if (this.onFrameCallback && this.videoEl && this.videoEl.readyState >= 2) {
        this.onFrameCallback({
          video: this.videoEl,
          canvas: this.canvasEl,
          ctx: this.ctx,
          fps: this.fps,
          isPaused: this.isDetectionPaused,
          deltaMs: deltaMs
        });
      }

      this.animationFrameId = requestAnimationFrame(loop);
    };

    this.animationFrameId = requestAnimationFrame(loop);
  }
}

// Export singleton to global namespace
window.cameraManager = new CameraManager();
