from abc import ABC, abstractmethod
from typing import Optional

class IVoiceSynthesizer(ABC):
    @abstractmethod
    def synthesize(self, text: str) -> Optional[bytes]:
        pass

class VoicePeakSynthesizer(IVoiceSynthesizer):
    def __init__(self):
        from text2VoicePeak import generateVoicePeakAudio
        self.generate_audio = generateVoicePeakAudio

    def synthesize(self, text: str) -> Optional[bytes]:
        return self.generate_audio(text)

class VoiceVoxSynthesizer(IVoiceSynthesizer):
    def __init__(self):
        from text2VoiceVox import generateVoiceVoxAudio
        self.generate_audio = generateVoiceVoxAudio

    def synthesize(self, text: str) -> Optional[bytes]:
        return self.generate_audio(text)

class VoiceSynthesizer:
    def __init__(self):
        self.synthesizers = {
            'VoicePeak': VoicePeakSynthesizer(),
            'VoiceVox': VoiceVoxSynthesizer()
        }

    def synthesize(self, text: str, synthesis_type: str) -> Optional[bytes]:
        synthesizer = self.synthesizers.get(synthesis_type)
        if synthesizer:
            return synthesizer.synthesize(text)
        return None