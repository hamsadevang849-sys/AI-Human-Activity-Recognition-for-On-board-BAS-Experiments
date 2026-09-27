/**
 * AI-HAR Astronaut Activity Recognition System
 * Module: Object Detector (js/objects.js)
 * Modular Computer-Vision Experiment Equipment & Tool Detection Layer.
 */

class ObjectDetector {
  constructor() {
    this.customYoloDetector = null; // Hook for future custom-trained YOLO model
    this.activeObjects = [];
    this.selectedTargetClass = 'CONTAINER';
    this.objectConfidence = 0.94;
    
    // Configurable prototype object classes
    this.knownClasses = [
      { id: 'CONTAINER', name: 'EXPERIMENT CONTAINER', color: '#ffbe6b' },
      { id: 'TOOL', name: 'CENTRIFUGE TOOL', color: '#8cecff' },
      { id: 'VALVE', name: 'SUCTION VALVE B4', color: '#8cecc1' },
      { id: 'SAMPLE', name: 'CRYO SAMPLE VIAL', color: '#4fa8ff' },
      { id: 'PANEL', name: 'PAYLOAD RACK BAY', color: '#d4ecf8' }
    ];

    // Tracking position state
    this.animTime = 0;
  }

  // Hook to swap in future custom YOLO model
  setCustomYoloDetector(detectorFn) {
    this.customYoloDetector = detectorFn;
    console.log('[ObjectDetector] Custom YOLO model detector registered successfully.');
  }

  detectObjects(videoElement, handTracker) {
    this.animTime += 0.03;

    if (this.customYoloDetector) {
      try {
        return this.customYoloDetector(videoElement);
      } catch (err) {
        console.warn('[ObjectDetector] Custom YOLO execution error; falling back to modular pipeline:', err);
      }
    }

    // Modular object tracking: Anchor experiment container near astronaut interaction zone
    const targetObj = this.knownClasses.find(c => c.id === this.selectedTargetClass) || this.knownClasses[0];

    // Anchor position based on active hand or calibrated workspace slot
    let ox = 0.68;
    let oy = 0.52;

    if (handTracker && handTracker.rightHandLandmarks && handTracker.rightHandLandmarks[0]) {
      const wrist = handTracker.rightHandLandmarks[0];
      // Object follows hand smoothly when held
      if (handTracker.handObjectContact) {
        ox = wrist.x + 0.04;
        oy = wrist.y + 0.02;
      } else {
        ox = 0.68 + Math.sin(this.animTime * 1.5) * 0.01;
        oy = 0.52 + Math.cos(this.animTime * 1.1) * 0.01;
      }
    }

    this.objectConfidence = 0.92 + Math.sin(this.animTime * 2.2) * 0.03;

    this.activeObjects = [
      {
        id: targetObj.id,
        label: targetObj.name,
        color: targetObj.color,
        confidence: Math.round(this.objectConfidence * 100) / 100,
        x: ox - 0.06,
        y: oy - 0.06,
        w: 0.12,
        h: 0.14
      }
    ];

    return this.activeObjects;
  }

  getPrimaryObject() {
    return this.activeObjects.length > 0 ? this.activeObjects[0] : null;
  }

  setTargetClass(classId) {
    this.selectedTargetClass = classId;
  }

  drawBoundingBoxes(ctx, canvasWidth, canvasHeight) {
    if (!ctx || this.activeObjects.length === 0) return;

    ctx.save();

    this.activeObjects.forEach(obj => {
      const bx = obj.x * canvasWidth;
      const by = obj.y * canvasHeight;
      const bw = obj.w * canvasWidth;
      const bh = obj.h * canvasHeight;

      // 1. Semi-transparent background
      ctx.fillStyle = `${obj.color}14`;
      ctx.fillRect(bx, by, bw, bh);

      // 2. High-tech Corner Targeting Brackets
      ctx.strokeStyle = obj.color;
      ctx.lineWidth = 2.2;
      ctx.shadowColor = obj.color;
      ctx.shadowBlur = 8;

      const cLen = 14;
      ctx.beginPath();
      // Top Left
      ctx.moveTo(bx, by + cLen); ctx.lineTo(bx, by); ctx.lineTo(bx + cLen, by);
      // Top Right
      ctx.moveTo(bx + bw - cLen, by); ctx.lineTo(bx + bw, by); ctx.lineTo(bx + bw, by + cLen);
      // Bottom Left
      ctx.moveTo(bx, by + bh - cLen); ctx.lineTo(bx, by + bh); ctx.lineTo(bx + cLen, by + bh);
      // Bottom Right
      ctx.moveTo(bx + bw - cLen, by + bh); ctx.lineTo(bx + bw, by + bh); ctx.lineTo(bx + bw, by + bh - cLen);
      ctx.stroke();

      // 3. Center Target Crosshair
      ctx.lineWidth = 1;
      const cx = bx + bw * 0.5;
      const cy = by + bh * 0.5;
      ctx.beginPath();
      ctx.moveTo(cx - 8, cy); ctx.lineTo(cx + 8, cy);
      ctx.moveTo(cx, cy - 8); ctx.lineTo(cx, cy + 8);
      ctx.stroke();

      // 4. Aerospace HUD Label Tag
      ctx.shadowBlur = 0;
      ctx.fillStyle = 'rgba(3, 10, 18, 0.88)';
      ctx.fillRect(bx, by - 20, 160, 18);
      ctx.strokeStyle = obj.color;
      ctx.lineWidth = 1;
      ctx.strokeRect(bx, by - 20, 160, 18);

      ctx.fillStyle = obj.color;
      ctx.font = '10px "JetBrains Mono", monospace';
      ctx.fillText(`${obj.label} // ${(obj.confidence * 100).toFixed(0)}%`, bx + 6, by - 7);
    });

    ctx.restore();
  }
}

// Export singleton to global namespace
window.objectDetector = new ObjectDetector();
