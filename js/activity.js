/**
 * AI-HAR Astronaut Activity Recognition System
 * Module: Activity Recognition Engine (js/activity.js)
 * Multi-Modal Spatio-Temporal Feature Classification & Temporal Sequence Analysis.
 */

class ActivityRecognizer {
  constructor() {
    // Configurable prototype activity classes (Requirement 7)
    this.activityClasses = [
      'IDLE',
      'REACHING',
      'PICKING OBJECT',
      'HOLDING OBJECT',
      'MOVING OBJECT',
      'PLACING OBJECT',
      'OPENING VALVE',
      'TILTING CONTAINER',
      'SHAKING CONTAINER',
      'RETURNING OBJECT'
    ];

    this.currentActivity = 'IDLE';
    this.confidence = 0.88;
    this.activityStartTime = performance.now();
    this.durationSeconds = 0;

    // Temporal feature buffers
    this.handPositions = [];
    this.bufferSize = 25; // ~1 second window at 25-30 FPS
    this.lastHandVelocity = 0;
  }

  update(poseData, handData, objectData, deltaMs) {
    if (!poseData || !poseData.personDetected) {
      this.currentActivity = 'ASTRONAUT NOT DETECTED';
      this.confidence = 0.0;
      this.durationSeconds = 0;
      return this.getState();
    }

    const hand = handData && (handData.rightDetected || handData.leftDetected);
    const contact = handData ? handData.contactDetected : false;
    const grip = handData ? handData.gripState : 'IDLE';
    const targetObj = objectData && objectData.length > 0 ? objectData[0] : null;

    // Track wrist velocity across sliding buffer
    const wrist = handData && handData.rightHandLandmarks ? handData.rightHandLandmarks[0] : null;
    if (wrist) {
      this.handPositions.push({ x: wrist.x, y: wrist.y, t: performance.now() });
      if (this.handPositions.length > this.bufferSize) {
        this.handPositions.shift();
      }
    }

    // Compute velocity & oscillation frequency
    let velocity = 0;
    let oscillationCount = 0;
    if (this.handPositions.length >= 6) {
      const p1 = this.handPositions[this.handPositions.length - 1];
      const p0 = this.handPositions[this.handPositions.length - 5];
      const dt = (p1.t - p0.t) / 1000;
      if (dt > 0) {
        velocity = Math.sqrt((p1.x - p0.x) ** 2 + (p1.y - p0.y) ** 2) / dt;
      }

      // Check horizontal or vertical reversals for shaking
      for (let i = 2; i < this.handPositions.length; i++) {
        const d1 = this.handPositions[i].y - this.handPositions[i - 1].y;
        const d2 = this.handPositions[i - 1].y - this.handPositions[i - 2].y;
        if (d1 * d2 < -0.0001) oscillationCount++;
      }
    }
    this.lastHandVelocity = velocity;

    // Classify activity based on multi-modal features
    let detectedClass = 'IDLE';
    let conf = 0.85;

    if (!hand) {
      detectedClass = 'IDLE';
      conf = 0.94;
    } else if (contact && oscillationCount >= 2 && velocity > 0.4) {
      // Rapid oscillating movement with object in hand
      detectedClass = 'SHAKING CONTAINER';
      conf = 0.93;
    } else if (contact && poseData.metrics && poseData.metrics.elbowAngle > 105) {
      // Extended arm with container
      detectedClass = 'TILTING CONTAINER';
      conf = 0.91;
    } else if (contact && velocity > 0.25) {
      detectedClass = 'MOVING OBJECT';
      conf = 0.89;
    } else if (contact) {
      detectedClass = 'HOLDING OBJECT';
      conf = 0.95;
    } else if (handData.distanceMeters <= 0.08) {
      detectedClass = 'PICKING OBJECT';
      conf = 0.88;
    } else if (velocity > 0.15) {
      detectedClass = 'REACHING';
      conf = 0.86;
    } else {
      detectedClass = 'IDLE';
      conf = 0.92;
    }

    // Temporal hysteresis: only switch if sustained or new
    if (detectedClass !== this.currentActivity) {
      this.currentActivity = detectedClass;
      this.activityStartTime = performance.now();
      this.confidence = conf;
    } else {
      // Smooth confidence
      this.confidence = this.confidence * 0.9 + conf * 0.1;
    }

    this.durationSeconds = Math.round((performance.now() - this.activityStartTime) / 100) / 10;
    return this.getState();
  }

  forceActivity(activityName, customConfidence = 0.96) {
    if (this.activityClasses.includes(activityName)) {
      this.currentActivity = activityName;
      this.confidence = customConfidence;
      this.activityStartTime = performance.now();
      this.durationSeconds = 0;
    }
  }

  getState() {
    return {
      activity: this.currentActivity,
      confidence: Math.round(this.confidence * 100) / 100,
      duration: this.durationSeconds,
      velocity: Math.round(this.lastHandVelocity * 100) / 100
    };
  }
}

// Export singleton to global namespace
window.activityRecognizer = new ActivityRecognizer();
