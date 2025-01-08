import RecognitionManager from './RecognitionManager.js';

const statusLabel = document.getElementById('status-label');
const chatContainer = document.getElementById('chat-container');
const recognitionManager = new RecognitionManager(statusLabel, chatContainer);

const startBtn = document.getElementById('start-btn');
startBtn.onclick = () => {
  recognitionManager.start();
};