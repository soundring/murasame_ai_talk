class AudioManager {
  constructor() {
    this.audioContext = null;
    this.audioQueue = [];
    this.isPlaying = false;
    this.isInitialized = false;
    this.queueEmptyResolvers = [];
    this.onTextDisplay = null;
  }

  async initialize() {
    if (this.isInitialized) return;

    this.audioContext = new (window.AudioContext ||
      window.webkitAudioContext)();
    await this.audioContext.resume();

    // iOS Safariのための無音再生
    const silent = this.audioContext.createBuffer(1, 1, 22050);
    const source = this.audioContext.createBufferSource();
    source.buffer = silent;
    source.connect(this.audioContext.destination);
    source.start(0);

    this.isInitialized = true;
  }

  async playAudio(audioUrl, text) {
    if (!this.isInitialized) {
      await this.initialize();
    }

    this.audioQueue.push({ url: audioUrl, text });

    if (!this.isPlaying) {
      await this.playNextAudio();
    }
  }

  async playNextAudio() {
    if (this.audioQueue.length === 0) {
      this.isPlaying = false;
      this.resolveQueueEmpty();
      return;
    }

    const nextAudio = this.audioQueue.shift();
    this.isPlaying = true;

    try {
      const response = await fetch(nextAudio.url);
      const arrayBuffer = await response.arrayBuffer();
      const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);

      const source = this.audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(this.audioContext.destination);

      source.onended = () => {
        this.isPlaying = false;
        this.playNextAudio();
      };

      source.start(0);

      if (this.onTextDisplay) {
        this.onTextDisplay(nextAudio.text);
      }
    } catch (error) {
      console.error('音声の再生に失敗:', error);
      this.isPlaying = false;
      this.playNextAudio();
    }
  }

  resolveQueueEmpty() {
    while (this.queueEmptyResolvers.length > 0) {
      const resolve = this.queueEmptyResolvers.shift();
      resolve();
    }
  }

  waitUntilAllAudioPlayed() {
    if (!this.isPlaying && this.audioQueue.length === 0) {
      return Promise.resolve();
    }

    return new Promise((resolve) => {
      this.queueEmptyResolvers.push(resolve);
    });
  }
}

export default AudioManager;