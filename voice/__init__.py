# JARVIS Voice Module
# Voice input/output pipeline (STT, TTS, VAD, push-to-talk)

__all__ = [
    'VoicePipeline',
    'STTEngine', 
    'TTSEngine',
    'AudioRecorder',
    'VADWrapper',
    'AudioOutput',
    'KeyboardHandler'
]


def __getattr__(name):
    """Lazy loading to avoid circular imports at module load time."""
    if name == 'VoicePipeline':
        from .pipeline import VoicePipeline
        return VoicePipeline
    elif name == 'STTEngine':
        from .stt import STTEngine
        return STTEngine
    elif name == 'TTSEngine':
        from .tts import TTSEngine
        return TTSEngine
    elif name == 'AudioRecorder':
        from .recorder import AudioRecorder
        return AudioRecorder
    elif name == 'VADWrapper':
        from .vad import VADWrapper
        return VADWrapper
    elif name == 'AudioOutput':
        from .audio_output import AudioOutput
        return AudioOutput
    elif name == 'KeyboardHandler':
        from .keyboard_handler import KeyboardHandler
        return KeyboardHandler
    raise AttributeError(f"module 'voice' has no attribute '{name}'")
