import AudioManager from './AudioManager.js';

class RecognitionManager {
  constructor(labelElement, chatContainer) {
    this.label = labelElement;
    this.chatContainer = chatContainer;
    this.recognition = new (window.SpeechRecognition ||
      window.webkitSpeechRecognition)();
    this.recognition.lang = 'ja-JP';
    this.recognition.continuous = true;

    this.audioManager = new AudioManager();
    this.audioManager.onTextDisplay = (text) => {
      this.chatContainer.innerHTML += `<div class="message ai"><div class="bubble ai">AI: ${text}</div></div>`;
    };

    this.recognition.onstart = () => this.onStart();
    this.recognition.onend = () => this.onEnd();
    this.recognition.onresult = (event) => this.onResult(event);
    this.recognition.onerror = (event) => this.onError(event);
  }

  async start() {
    await this.audioManager.initialize();
    this.recognition.start();
  }

  stop() {
    this.recognition.stop();
  }

  onStart() {
    this.label.innerHTML = '音声認識中...';
  }

  onEnd() {
    this.label.innerHTML = '音声認識終了';
  }

  async onResult(event) {
    const selectedRadio = document.querySelector(
      'input[name="voiceEngine"]:checked'
    );
    const speechSynthesisType = selectedRadio.value;
    const transcript =
      event.results[event.results.length - 1][0].transcript;

    if (transcript == '') return;

    this.chatContainer.innerHTML += `<div class="message user"><div class="bubble user">あなた: ${transcript}</div></div>`;

    this.stop();

    try {
      const response = await fetch('https://192.168.0.80:5001/chatgpt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: transcript, speechSynthesisType }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        try {
          while (true) {
            const endIndex = buffer.indexOf('\n');
            if (endIndex === -1) break;

            const jsonString = buffer.slice(0, endIndex);
            buffer = buffer.slice(endIndex + 1);

            const item = JSON.parse(jsonString);

            if (item.text && item.audio) {
              const audioBlob = await (
                await fetch(`data:audio/wav;base64,${item.audio}`)
              ).blob();
              const audioUrl = URL.createObjectURL(audioBlob);
              await this.audioManager.playAudio(audioUrl, item.text);
            }
          }
        } catch (error) {
          console.error('メッセージのパースに失敗しました:', error);
        }
      }
    } catch (error) {
      console.error('サーバーとの通信でエラーが発生しました:', error);
    }

    await this.audioManager.waitUntilAllAudioPlayed();
    this.start();
  }

  onError(event) {
    console.error('音声認識中にエラーが発生しました:', event.error);
  }
}

export default RecognitionManager;