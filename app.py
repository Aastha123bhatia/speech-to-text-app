import streamlit as st
import tempfile
import json
import os
from datetime import datetime

from speech.recognizer import recognize_speech


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Bilingual Voice Transcriber",
    page_icon="🎤",
    layout="centered"
)


# ============================================================
# SESSION STATE
# ============================================================

if "transcription_result" not in st.session_state:
    st.session_state.transcription_result = None

if "processed_audio_id" not in st.session_state:
    st.session_state.processed_audio_id = None

if "audio_input_key" not in st.session_state:
    st.session_state.audio_input_key = 0

if "success_message" not in st.session_state:
    st.session_state.success_message = None

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

if "edited_text" not in st.session_state:
    st.session_state.edited_text = ""

if "show_delete_all_confirmation" not in st.session_state:
    st.session_state.show_delete_all_confirmation = False


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
<style>
.stApp { background-color: var(--background-color); color: var(--text-color); }
.block-container { max-width: 900px; padding-top: 2rem; padding-bottom: 3.5rem; }

.hero { text-align: center; padding: 0.6rem 0 1.6rem 0; }
.hero-badge { display:inline-block; padding:.38rem .8rem; border:1px solid var(--border-color); border-radius:999px; background:var(--secondary-background-color); color:var(--text-color); opacity:.78; font-size:.75rem; font-weight:700; letter-spacing:.04em; margin-bottom:.8rem; }
.hero-icon { font-size:3rem; line-height:1; margin-bottom:.35rem; }
.hero-title { margin:0; color:var(--text-color); font-size:2.65rem; line-height:1.12; font-weight:800; letter-spacing:-.04em; }
.hero-title-accent { background:linear-gradient(90deg,#2563eb,#7c3aed); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.main-subtitle { text-align:center; color:var(--text-color); opacity:.68; font-size:1.04rem; line-height:1.6; margin-top:.75rem; }
.technology-text { text-align:center; color:var(--text-color); opacity:.5; font-size:.8rem; line-height:1.7; margin-top:.6rem; }

.section-kicker { color:var(--text-color); opacity:.55; font-size:.74rem; font-weight:750; letter-spacing:.09em; text-transform:uppercase; margin-bottom:.2rem; }

.recording-card { background:var(--secondary-background-color); border:1px solid var(--border-color); border-radius:20px; padding:1.4rem 1.5rem; margin:.35rem 0 1rem; box-shadow:0 10px 30px rgba(0,0,0,.04); }
.recording-title-row { display:flex; align-items:center; gap:.65rem; margin-bottom:.45rem; }
.recording-icon { width:40px; height:40px; display:flex; align-items:center; justify-content:center; border-radius:12px; background:rgba(37,99,235,.12); font-size:1.3rem; }
.recording-title { color:var(--text-color); font-size:1.16rem; font-weight:750; }
.recording-description { color:var(--text-color); opacity:.67; font-size:.93rem; line-height:1.6; }
.recording-hint { margin-top:.8rem; color:var(--text-color); opacity:.5; font-size:.77rem; }

.info-card { background:var(--secondary-background-color); border:1px solid var(--border-color); border-radius:16px; padding:1.05rem 1.15rem; text-align:center; min-height:108px; box-shadow:0 8px 24px rgba(0,0,0,.035); }
.info-card-title { color:var(--text-color); opacity:.56; font-size:.78rem; font-weight:700; margin-bottom:.55rem; }
.info-card-value { color:var(--text-color); font-size:1.25rem; font-weight:750; }
.word-count { color:var(--text-color); opacity:.58; font-size:.8rem; margin-bottom:1rem; }

.stButton > button, .stDownloadButton > button { width:100%; border-radius:11px; font-weight:650; min-height:45px; transition:transform .15s ease,box-shadow .15s ease; }
.stButton > button:hover, .stDownloadButton > button:hover { transform:translateY(-1px); box-shadow:0 6px 16px rgba(0,0,0,.08); }

audio { width:100%; }
.stCaption, [data-testid="stCaptionContainer"] { color:var(--text-color) !important; opacity:.68; }
[data-testid="stExpander"] { border-color:var(--border-color); border-radius:14px; overflow:hidden; }

.download-card { background:var(--secondary-background-color); border:1px solid var(--border-color); border-radius:15px; padding:.9rem 1rem .7rem; margin-bottom:.65rem; }
.download-title { color:var(--text-color); font-weight:700; font-size:.9rem; }
.download-description { color:var(--text-color); opacity:.55; font-size:.76rem; margin-top:.15rem; }
.new-recording-card { text-align:center; background:var(--secondary-background-color); border:1px dashed var(--border-color); border-radius:18px; padding:1.25rem; margin:.35rem 0 .8rem; }
.new-recording-title { color:var(--text-color); font-size:1rem; font-weight:700; }
.new-recording-description { color:var(--text-color); opacity:.58; font-size:.82rem; margin-top:.35rem; }
.history-summary { color:var(--text-color); opacity:.62; font-size:.84rem; margin-bottom:.65rem; }
.history-meta { color:var(--text-color); opacity:.6; font-size:.82rem; }
.history-transcript { background:var(--background-color); border:1px solid var(--border-color); border-radius:12px; padding:.9rem 1rem; color:var(--text-color); line-height:1.65; white-space:pre-wrap; word-break:break-word; margin-top:.35rem; }

@media (max-width:640px) {
  .block-container { padding:1.1rem 1rem 3rem; }
  .hero { padding-bottom:1.15rem; }
  .hero-title { font-size:2.05rem; }
  .hero-icon { font-size:2.7rem; }
  .main-subtitle { font-size:.95rem; }
  .recording-card { padding:1.15rem; }
}
</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# FUNCTIONS
# ============================================================

def get_language_name(language):
    """Convert language code into a user-friendly name."""

    language = str(language).lower().strip()

    if language == "en":
        return "English 🇬🇧"

    if language == "hi":
        return "Hindi 🇮🇳"

    return language.upper()


# ------------------------------------------------------------
# SAVE TRANSCRIPTION
# ------------------------------------------------------------

def save_transcription(
    text,
    language,
    probability,
    timestamp=None
):
    """Save one transcription as a JSON file."""

    os.makedirs("transcripts", exist_ok=True)

    if timestamp is None:
        timestamp = datetime.now()

    filename = timestamp.strftime(
        "transcript_%Y%m%d_%H%M%S_%f.json"
    )

    filepath = os.path.join(
        "transcripts",
        filename
    )

    data = {
        "timestamp": timestamp.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "language": language,
        "language_name": get_language_name(language),
        "confidence": float(probability),
        "transcript": text
    }

    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4
        )

    return filepath


# ------------------------------------------------------------
# LOAD HISTORY
# ------------------------------------------------------------

def load_history():
    """Load previous transcription JSON files."""

    history = []

    transcripts_folder = "transcripts"

    if not os.path.exists(transcripts_folder):
        return history

    try:
        filenames = os.listdir(transcripts_folder)
    except OSError:
        return history

    for filename in filenames:

        if not filename.lower().endswith(".json"):
            continue

        filepath = os.path.join(
            transcripts_folder,
            filename
        )

        try:

            with open(
                filepath,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            if isinstance(data, dict):

                # Internal field used only for
                # editing/deleting history.
                data["_filepath"] = filepath

                history.append(data)

        except (
            json.JSONDecodeError,
            OSError,
            UnicodeDecodeError
        ):
            continue

    history.sort(
        key=lambda item: item.get(
            "timestamp",
            ""
        ),
        reverse=True
    )

    return history


# ------------------------------------------------------------
# UPDATE HISTORY ITEM
# ------------------------------------------------------------

def update_history_file(
    filepath,
    text,
    language,
    probability,
    timestamp
):
    """Update an existing transcription JSON file."""

    data = {
        "timestamp": timestamp,
        "language": language,
        "language_name": get_language_name(language),
        "confidence": float(probability),
        "transcript": text
    }

    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4
        )


# ------------------------------------------------------------
# DELETE HISTORY ITEM
# ------------------------------------------------------------

def delete_history_file(filepath):
    """Delete a transcription history file."""

    if filepath and os.path.exists(filepath):

        os.remove(filepath)

        return True

    return False


# ------------------------------------------------------------
# TXT DOWNLOAD
# ------------------------------------------------------------

def create_txt_content(
    text,
    language_name,
    probability,
    timestamp
):
    """Create TXT download content."""

    return (
        "Speech-to-Text Transcript\n"
        "==========================\n\n"
        f"Date & Time: {timestamp}\n"
        f"Language: {language_name}\n"
        f"Confidence: {probability:.2%}\n\n"
        "Transcript:\n"
        "-----------\n"
        f"{text}\n"
    )


# ------------------------------------------------------------
# JSON DOWNLOAD
# ------------------------------------------------------------

def create_json_content(
    text,
    language,
    language_name,
    probability,
    timestamp
):
    """Create JSON download content."""

    data = {
        "timestamp": timestamp,
        "language": language,
        "language_name": language_name,
        "confidence": float(probability),
        "transcript": text
    }

    return json.dumps(
        data,
        ensure_ascii=False,
        indent=4
    )


# ------------------------------------------------------------
# PROCESS AUDIO
# ------------------------------------------------------------

def process_audio(
    audio_bytes,
    audio_id
):
    """Convert audio into text."""

    temp_audio_path = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav"
        ) as temp_audio:

            temp_audio.write(audio_bytes)
            temp_audio.flush()

            temp_audio_path = temp_audio.name

        with st.spinner(
            "🎧 Converting speech to text..."
        ):

            text, language, probability = recognize_speech(
                temp_audio_path
            )

        text = str(text).strip() if text else ""

        try:
            probability = float(probability)
        except (
            TypeError,
            ValueError
        ):
            probability = 0.0

        probability = max(
            0.0,
            min(1.0, probability)
        )

        language = str(
            language
        ).strip().lower()

        if not text:

            st.warning(
                "⚠️ No speech could be detected. "
                "Please try recording again."
            )

            return

        timestamp = datetime.now()

        result = {
            "text": text,
            "language": language,
            "probability": probability,
            "timestamp": timestamp.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        }

        # Store result
        st.session_state.transcription_result = result

        # Store processed audio ID
        st.session_state.processed_audio_id = audio_id

        # Exit edit mode if necessary
        st.session_state.edit_mode = False

        # Save history
        save_transcription(
            text,
            language,
            probability,
            timestamp
        )

        st.session_state.success_message = (
            "✅ Transcription completed and saved to history!"
        )

    except Exception as error:

        st.error(
            "❌ An error occurred while processing the audio."
        )

        st.exception(error)

    finally:

        if (
            temp_audio_path
            and os.path.exists(temp_audio_path)
        ):

            try:
                os.remove(temp_audio_path)

            except OSError:
                pass


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
<div class="hero">
    <div class="hero-badge">✨ AI-POWERED SPEECH RECOGNITION</div>
    <div class="hero-icon">🎙️</div>
    <h1 class="hero-title">Bilingual Voice <span class="hero-title-accent">Transcriber</span></h1>
    <div class="main-subtitle">Turn your voice into accurate text in seconds.<br>Speak naturally in English or Hindi.</div>
    <div class="technology-text">🇬🇧 English &nbsp;•&nbsp; 🇮🇳 Hindi &nbsp;•&nbsp; Automatic language detection<br>Powered by Python • Streamlit • faster-whisper</div>
</div>
""",
    unsafe_allow_html=True
)


# ============================================================
# RECORDING SECTION
# ============================================================

st.markdown(
    """
<div class="recording-card">
    <div class="recording-title-row">
        <div class="recording-icon">🎤</div>
        <div class="recording-title">Record Your Voice</div>
    </div>
    <div class="recording-description">Speak naturally and let the app automatically detect your language and convert your speech into text.</div>
    <div class="recording-hint">🔒 Your recording is processed only for transcription.</div>
</div>
""",
    unsafe_allow_html=True
)


# ============================================================
# AUDIO INPUT
# ============================================================

audio = st.audio_input(
    "Click the microphone button to start recording",
    sample_rate=16000,
    key=f"audio_input_{st.session_state.audio_input_key}"
)


# ============================================================
# AUDIO PROCESSING
# ============================================================

if audio:

    audio_bytes = audio.getvalue()

    audio_id = hash(audio_bytes)

    st.success(
        "✅ Recording captured successfully. Ready to transcribe!"
    )

    st.markdown(
        '<div class="section-kicker">YOUR RECORDING</div>',
        unsafe_allow_html=True
    )

    st.audio(audio_bytes)

    # --------------------------------------------------------
    # CONVERT BUTTON
    # --------------------------------------------------------

    if st.button(
        "📝 Convert to Text",
        use_container_width=True,
        type="primary"
    ):

        if (
            st.session_state.processed_audio_id
            == audio_id
            and
            st.session_state.transcription_result
            is not None
        ):

            st.info(
                "ℹ️ This recording has already been converted."
            )

        else:

            process_audio(
                audio_bytes,
                audio_id
            )


# ============================================================
# SUCCESS MESSAGE
# ============================================================

if st.session_state.success_message:

    st.success(
        st.session_state.success_message
    )

    st.session_state.success_message = None


# ============================================================
# CURRENT TRANSCRIPTION RESULT
# ============================================================

result = st.session_state.transcription_result


if result:

    text = result.get(
        "text",
        ""
    )

    language = result.get(
        "language",
        "unknown"
    )

    probability = result.get(
        "probability",
        0.0
    )

    timestamp = result.get(
        "timestamp",
        ""
    )

    language_name = get_language_name(
        language
    )

    # ========================================================
    # RECOGNITION RESULT
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="section-kicker">RESULT</div>',
        unsafe_allow_html=True
    )
    st.subheader(
        "📊 Recognition Result"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            f"""
<div class="info-card">
<div class="info-card-title">🌐 Detected Language</div>
<div class="info-card-value">{language_name}</div>
</div>
""",
            unsafe_allow_html=True
        )

    with col2:

        st.markdown(
            f"""
<div class="info-card">
<div class="info-card-title">📊 Language Confidence</div>
<div class="info-card-value">{probability:.2%}</div>
</div>
""",
            unsafe_allow_html=True
        )

    st.write("")

    st.progress(
        probability
    )

    # ========================================================
    # TRANSCRIPT
    # ========================================================

    st.subheader(
        "📝 Transcript"
    )

    # --------------------------------------------------------
    # EDIT MODE
    # --------------------------------------------------------

    if st.session_state.edit_mode:

        edited_text = st.text_area(
            "Edit your transcript:",
            value=text,
            height=180,
            key="transcript_editor"
        )

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "💾 Save Changes",
                use_container_width=True,
                type="primary"
            ):

                edited_text = edited_text.strip()

                if not edited_text:

                    st.warning(
                        "⚠️ Transcript cannot be empty."
                    )

                else:

                    filepath = None

                    # Find matching history entry
                    history_items = load_history()

                    for item in history_items:

                        if (
                            item.get("transcript", "")
                            == text
                            and
                            item.get("timestamp", "")
                            == timestamp
                        ):

                            filepath = item.get(
                                "_filepath"
                            )

                            break

                    # Update history JSON
                    if filepath:

                        update_history_file(
                            filepath,
                            edited_text,
                            language,
                            probability,
                            timestamp
                        )

                    # Update current result
                    st.session_state.transcription_result[
                        "text"
                    ] = edited_text

                    st.session_state.edit_mode = False

                    st.success(
                        "✅ Transcript updated successfully!"
                    )

                    st.rerun()

        with col2:

            if st.button(
                "❌ Cancel",
                use_container_width=True
            ):

                st.session_state.edit_mode = False

                st.rerun()

    else:

        # ----------------------------------------------------
        # NORMAL TRANSCRIPT DISPLAY
        # ----------------------------------------------------

        with st.container(
            border=True
        ):

            st.write(text)

        word_count = len(
            text.split()
        )

        st.markdown(
            f"""
<div class="word-count">
📝 {word_count} word(s)
</div>
""",
            unsafe_allow_html=True
        )

        # ----------------------------------------------------
        # COPY + EDIT
        # ----------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            # st.code provides a built-in copy button.
            # A small hidden duplicate is avoided by using
            # the code block only for copying.

            if st.button(
                "📋 Copy Transcript",
                use_container_width=True
            ):

                st.info(
                    "💡 Use the copy icon shown on the "
                    "transcript code box below."
                )

        with col2:

            if st.button(
                "✏️ Edit Transcript",
                use_container_width=True
            ):

                st.session_state.edit_mode = True

                st.rerun()

        # ----------------------------------------------------
        # COPYABLE TRANSCRIPT
        # ----------------------------------------------------

        st.caption(
            "📋 Copyable transcript:"
        )

        st.code(
            text,
            language=None
        )


    # ========================================================
    # DOWNLOAD SECTION
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="section-kicker">EXPORT</div>',
        unsafe_allow_html=True
    )
    st.subheader(
        "💾 Save Transcript"
    )
    st.caption("Keep a copy of your transcript in the format that suits you best.")

    txt_content = create_txt_content(
        text,
        language_name,
        probability,
        timestamp
    )

    json_content = create_json_content(
        text,
        language,
        language_name,
        probability,
        timestamp
    )

    download_timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.download_button(
            label="📄 Download TXT",
            data=txt_content,
            file_name=(
                f"transcript_{download_timestamp}.txt"
            ),
            mime="text/plain",
            use_container_width=True
        )

    with col2:

        st.download_button(
            label="📋 Download JSON",
            data=json_content,
            file_name=(
                f"transcript_{download_timestamp}.json"
            ),
            mime="application/json",
            use_container_width=True
        )


# ============================================================
# CLEAR CURRENT RECORDING
# ============================================================

st.divider()

st.markdown(
    '<div class="section-kicker">CONTINUE</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
<div class="new-recording-card">
    <div class="new-recording-title">🔄 Ready for another recording?</div>
    <div class="new-recording-description">Start fresh while keeping your saved transcription history.</div>
</div>
""",
    unsafe_allow_html=True
)

if st.button(
    "🔄 Start New Recording",
    use_container_width=True
):

    st.session_state.transcription_result = None
    st.session_state.processed_audio_id = None
    st.session_state.edit_mode = False
    st.session_state.audio_input_key += 1

    st.success(
        "✅ Current recording and transcript cleared."
    )

    st.rerun()


# ============================================================
# TRANSCRIPTION HISTORY
# ============================================================

st.divider()

st.markdown(
    '<div class="section-kicker">YOUR SAVED WORK</div>',
    unsafe_allow_html=True
)
st.subheader(
    "📚 Transcription History"
)

history = load_history()


if not history:

    st.info(
        "No previous transcriptions found."
    )

else:

    st.markdown(
        f'<div class="history-summary">{len(history)} saved transcription(s)</div>',
        unsafe_allow_html=True
    )

    for index, item in enumerate(history):

        language = item.get(
            "language",
            "unknown"
        )

        language_name = item.get(
            "language_name",
            get_language_name(language)
        )

        timestamp = item.get(
            "timestamp",
            "Unknown date"
        )

        confidence = item.get(
            "confidence",
            0.0
        )

        transcript = item.get(
            "transcript",
            ""
        )

        filepath = item.get(
            "_filepath",
            ""
        )

        try:

            confidence = float(
                confidence
            )

        except (
            TypeError,
            ValueError
        ):

            confidence = 0.0

        # ----------------------------------------------------
        # HISTORY EXPANDER
        # ----------------------------------------------------

        with st.expander(
            f"{language_name} — {timestamp}",
            expanded=False
        ):

            col1, col2 = st.columns(2)

            with col1:

                st.caption(
                    "🌐 Language"
                )

                st.write(
                    language_name
                )

            with col2:

                st.caption(
                    "📊 Confidence"
                )

                st.write(
                    f"{confidence:.2%}"
                )

            st.caption(
                "📝 Transcript"
            )

            with st.container(
                border=True
            ):

                if transcript:

                    st.write(
                        transcript
                    )

                else:

                    st.caption(
                        "No transcript available."
                    )

            st.caption(
                f"📝 {len(str(transcript).split())} word(s)"
            )

            # ------------------------------------------------
            # DELETE HISTORY
            # ------------------------------------------------

            if st.button(
                "🗑️ Delete This Transcription",
                key=f"delete_history_{index}",
                use_container_width=True
            ):

                try:

                    if delete_history_file(
                        filepath
                    ):

                        # If deleted history is the
                        # currently displayed result,
                        # clear current result too.

                        current_result = (
                            st.session_state.transcription_result
                        )

                        if current_result:

                            if (
                                current_result.get("text")
                                == transcript
                                and
                                current_result.get("timestamp")
                                == timestamp
                            ):

                                st.session_state.transcription_result = None

                        st.success(
                            "✅ Transcription deleted successfully!"
                        )

                        st.rerun()

                    else:

                        st.error(
                            "❌ Could not delete transcription."
                        )

                except OSError as error:

                    st.error(
                        f"❌ Unable to delete file: {error}"
                    )

# ============================================================
# DELETE ALL HISTORY
# ============================================================

st.divider()

st.markdown(
    '<div class="section-kicker">HISTORY MANAGEMENT</div>',
    unsafe_allow_html=True
)

st.subheader("🗑️ Manage History")

st.caption(
    "Permanently remove all saved transcription history from this app."
)

if not st.session_state.show_delete_all_confirmation:

    if st.button(
        "🗑️ Delete All History",
        use_container_width=True,
        type="primary",
        key="delete_all_history"
    ):
        st.session_state.show_delete_all_confirmation = True
        st.rerun()

else:

    st.warning(
        "⚠️ This will permanently delete all saved transcription "
        "history. This action cannot be undone."
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "✅ Yes, Delete Everything",
            use_container_width=True,
            type="primary",
            key="confirm_delete_all_history"
        ):

            deleted_count = 0
            delete_failed = 0

            for item in load_history():

                filepath = item.get("_filepath", "")

                try:

                    if delete_history_file(filepath):
                        deleted_count += 1
                    else:
                        delete_failed += 1

                except OSError:
                    delete_failed += 1

            st.session_state.transcription_result = None
            st.session_state.processed_audio_id = None
            st.session_state.edit_mode = False
            st.session_state.show_delete_all_confirmation = False

            if delete_failed:
                st.error(
                    f"❌ Deleted {deleted_count} transcription(s), "
                    f"but {delete_failed} could not be deleted."
                )
            else:
                st.success(
                    f"✅ All history deleted successfully! "
                    f"{deleted_count} transcription(s) removed."
                )

            st.rerun()

    with col2:

        if st.button(
            "❌ Cancel",
            use_container_width=True,
            key="cancel_delete_all_history"
        ):
            st.session_state.show_delete_all_confirmation = False
            st.rerun()
