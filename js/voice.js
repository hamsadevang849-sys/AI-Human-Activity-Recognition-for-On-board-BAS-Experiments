/**
 * AI-HAR Astronaut Activity Recognition System
 * Module: Voice Assistant (js/voice.js)
 * Browser Web Speech API Guidance & Synthesized Mission Control Audio Cues.
 */

class VoiceAssistant {
  constructor() {
    this.voiceEnabled = true;
    this.audioCtx = null;
    this.lastSpokenText = '';
    this.lastSpokenTime = 0;
  }

  init() {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (AudioCtx) {
      this.audioCtx = new AudioCtx();
    }
  }

  toggleVoice() {
    this.voiceEnabled = !this.voiceEnabled;
    if (this.voiceEnabled) {
      this.playChime(1200, 0.1);
      this.speak("Voice guidance online.");
    }
    return this.voiceEnabled;
  }

  speak(phrase) {
    if (!this.voiceEnabled || !('speechSynthesis' in window)) return;

    // Prevent duplicate speech flooding within 2.5s
    const now = performance.now();
    if (phrase === this.lastSpokenText && (now - this.lastSpokenTime) < 2500) {
      return;
    }
    this.lastSpokenText = phrase;
    this.lastSpokenTime = now;

    try {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(phrase);
      utterance.rate = 1.02;
      utterance.pitch = 1.05;

      const voices = window.speechSynthesis.getVoices();
      const engVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Zira') || v.name.includes('Samantha')));
      if (engVoice) utterance.voice = engVoice;

      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn('[VoiceAssistant] Speech synthesis error:', e);
    }
  }

  playChime(freq = 1200, duration = 0.1) {
    if (!this.audioCtx) this.init();
    if (!this.audioCtx) return;

    try {
      if (this.audioCtx.state === 'suspended') {
        this.audioCtx.resume();
      }
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, this.audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(freq * 0.7, this.audioCtx.currentTime + duration);

      gain.gain.setValueAtTime(0.12, this.audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + duration);

      osc.connect(gain);
      gain.connect(this.audioCtx.destination);

      osc.start();
      osc.stop(this.audioCtx.currentTime + duration);
    } catch (e) {}
  }

  playAlertAlarm() {
    this.playChime(650, 0.2);
    setTimeout(() => this.playChime(650, 0.2), 160);
  }
}

// Export singleton to global namespace
window.voiceAssistant = new VoiceAssistant();
