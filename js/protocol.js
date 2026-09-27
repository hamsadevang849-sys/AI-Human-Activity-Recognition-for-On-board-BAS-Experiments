/**
 * AI-HAR Astronaut Activity Recognition System
 * Module: Protocol Validator (js/protocol.js)
 * Mission Workflow State Machine, Step Sequencing, and Real-Time Protocol Verification.
 */

class ProtocolValidator {
  constructor() {
    this.missionId = "BAS-01";
    this.experimentName = "CONTAINER HANDLING";
    
    // Experiment Workflow Steps (Requirement 8)
    this.steps = [
      {
        index: 1,
        title: "Pick Container",
        expectedAction: "PICK CONTAINER",
        validActivities: ['PICKING OBJECT', 'HOLDING OBJECT'],
        status: 'PENDING', // 'PENDING' | 'IN PROGRESS' | 'VALID' | 'WARNING'
        guidance: "Extract microgravity container from payload storage bay"
      },
      {
        index: 2,
        title: "Tilt Container",
        expectedAction: "TILT CONTAINER",
        validActivities: ['TILTING CONTAINER'],
        status: 'PENDING',
        guidance: "Incline container 45° to observe fluid meniscus"
      },
      {
        index: 3,
        title: "Shake Container",
        expectedAction: "SHAKE CONTAINER",
        validActivities: ['SHAKING CONTAINER'],
        status: 'PENDING',
        guidance: "Oscillate container at 2 Hz to homogenize specimen"
      },
      {
        index: 4,
        title: "Place Container",
        expectedAction: "PLACE CONTAINER",
        validActivities: ['PLACING OBJECT', 'RETURNING OBJECT'],
        status: 'PENDING',
        guidance: "Lock container back into payload centrifuge rack"
      }
    ];

    this.currentStepIndex = 1;
    this.validationState = 'VALIDATING'; // 'VALIDATING' | 'VALID' | 'UNEXPECTED' | 'CONCLUDED'
    this.lastValidationMessage = 'WAITING FOR ASTRONAUT ACTION';
    this.unexpectedActionTitle = null;

    // Time in current step
    this.stepStartTime = performance.now();
    this.matchDuration = 0;
    this.hasAdvanced = false;

    // Callbacks
    this.onStepValidatedCallback = null;
    this.onDeviationCallback = null;

    this.initFirstStep();
  }

  initFirstStep() {
    this.currentStepIndex = 1;
    this.steps.forEach((s, idx) => {
      s.status = idx === 0 ? 'IN PROGRESS' : 'PENDING';
    });
    this.validationState = 'VALIDATING';
    this.lastValidationMessage = 'WAITING FOR STEP 01 ACTION';
    this.unexpectedActionTitle = null;
    this.stepStartTime = performance.now();
  }

  getCurrentStep() {
    return this.steps[this.currentStepIndex - 1] || this.steps[this.steps.length - 1];
  }

  getNextStep() {
    if (this.currentStepIndex < this.steps.length) {
      return this.steps[this.currentStepIndex];
    }
    return { title: "EXPERIMENT PROTOCOL CONCLUDED", guidance: "All protocol steps verified." };
  }

  evaluateStep(detectedActivity, confidence = 0.9) {
    if (this.validationState === 'CONCLUDED') return this.getState();

    const cur = this.getCurrentStep();
    if (!cur) return this.getState();

    // Check if detected activity matches valid activities for current step
    const isMatch = cur.validActivities.includes(detectedActivity);

    // Filter out generic IDLE or non-astronaut state
    if (detectedActivity === 'IDLE' || detectedActivity === 'ASTRONAUT NOT DETECTED') {
      return this.getState();
    }

    if (isMatch) {
      this.matchDuration += 0.05;
      // Require ~0.8s continuous match for automatic validation
      if (this.matchDuration >= 0.8 && !this.hasAdvanced) {
        this.confirmStepValid(cur, detectedActivity, confidence);
      }
    } else {
      this.matchDuration = 0;
      // Check if unexpected activity indicates an out-of-order action
      const otherStep = this.steps.find(s => s.validActivities.includes(detectedActivity));
      if (otherStep && otherStep.index !== cur.index) {
        this.flagUnexpectedAction(cur, detectedActivity);
      }
    }

    return this.getState();
  }

  confirmStepValid(stepObj, detectedActivity, confidence) {
    this.hasAdvanced = true;
    stepObj.status = 'VALID';
    this.validationState = 'VALID';
    this.lastValidationMessage = `✓ STEP ${stepObj.index} VALID: ${stepObj.title.toUpperCase()}`;

    if (this.onStepValidatedCallback) {
      this.onStepValidatedCallback({
        stepIndex: stepObj.index,
        stepTitle: stepObj.title,
        detectedActivity: detectedActivity,
        confidence: confidence
      });
    }

    // Auto advance after 1.4s confirmation display
    setTimeout(() => {
      this.advanceToNextStep();
    }, 1400);
  }

  flagUnexpectedAction(currentStepObj, detectedActivity) {
    this.validationState = 'UNEXPECTED';
    this.unexpectedActionTitle = detectedActivity;
    this.lastValidationMessage = `⚠️ UNEXPECTED ACTION: ${detectedActivity} (EXPECTED: ${currentStepObj.expectedAction})`;

    if (this.onDeviationCallback) {
      this.onDeviationCallback({
        stepIndex: currentStepObj.index,
        expectedAction: currentStepObj.expectedAction,
        detectedActivity: detectedActivity
      });
    }
  }

  advanceToNextStep() {
    this.hasAdvanced = false;
    this.matchDuration = 0;

    if (this.currentStepIndex < this.steps.length) {
      this.currentStepIndex++;
      this.steps[this.currentStepIndex - 1].status = 'IN PROGRESS';
      this.validationState = 'VALIDATING';
      this.lastValidationMessage = `PROCEEDING TO STEP 0${this.currentStepIndex}`;
    } else {
      this.validationState = 'CONCLUDED';
      this.lastValidationMessage = '✓ MISSION EXPERIMENT PROTOCOL CONCLUDED';
    }
    this.stepStartTime = performance.now();
  }

  reset() {
    this.initFirstStep();
  }

  // Simulation test overrides
  forceStep(stepIndex) {
    if (stepIndex >= 1 && stepIndex <= this.steps.length) {
      this.currentStepIndex = stepIndex;
      this.steps.forEach((s, idx) => {
        if (idx < stepIndex - 1) s.status = 'VALID';
        else if (idx === stepIndex - 1) s.status = 'IN PROGRESS';
        else s.status = 'PENDING';
      });
      this.validationState = 'VALID';
      const cur = this.getCurrentStep();
      this.confirmStepValid(cur, cur.expectedAction, 0.96);
    }
  }

  forceUnexpected() {
    const cur = this.getCurrentStep();
    this.flagUnexpectedAction(cur, 'PLACING OBJECT PREMATURELY');
  }

  getState() {
    const cur = this.getCurrentStep();
    const next = this.getNextStep();
    return {
      missionId: this.missionId,
      experimentName: this.experimentName,
      currentStepIndex: this.currentStepIndex,
      totalSteps: this.steps.length,
      currentStepTitle: cur ? cur.title : '',
      currentStepGuidance: cur ? cur.guidance : '',
      expectedAction: cur ? cur.expectedAction : '',
      nextStepTitle: next ? next.title : '',
      nextStepGuidance: next ? next.guidance : '',
      validationState: this.validationState,
      validationMessage: this.lastValidationMessage,
      steps: this.steps
    };
  }
}

// Export singleton to global namespace
window.protocolValidator = new ProtocolValidator();
