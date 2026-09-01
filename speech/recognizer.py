from faster_whisper import WhisperModel


print("Loading Whisper model...")

model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8"
)

print("Whisper model loaded!")


def recognize_speech(audio_file):
    segments, info = model.transcribe(
        audio_file,
        task="transcribe",
        beam_size=5
    )

    text = ""

    for segment in segments:
        text += segment.text

    return text.strip(), info.language, info.language_probability