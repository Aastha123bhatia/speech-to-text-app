import streamlit as st
import tempfile
import json
import os
import uuid
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
# CONSTANTS
# ============================================================

TRANSCRIPTS_FOLDER = "transcripts"


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

if "show_delete_all_confirmation" not in st.session_state:
    st.session_state.show_delete_all_confirmation = False


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background-color: #f7f9fc;
}

.block-container {
    max-width: 900px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

h1 {
    text-align: center;
    font-size: 2.6rem !important;
    font-weight: 700 !important;
    margin-bottom: 0.3rem;
}

h2 {
    font-weight: 650 !important;
}

h3 {
    font-weight: 600 !important;
}

.main-subtitle {
    text-align: center;
    color: #6b7280;
    font-size: 1.1rem;
    line-height: 1.6;
    margin-bottom: 0.8rem;
}

.technology-text {
    text-align: center;
    color: #9ca3af;
    font-size: 0.85rem;
    margin-bottom: 1.5rem;
}

.recording-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 1.5rem;
    margin-top: 1rem;
    margin-bottom: 1.2rem;
}

.recording-title {
    font-size: 1.2rem;
    font-weight: 650;
    margin-bottom: 0.5rem;
}

.recording-description {
    color: #6b7280;
    font-size: 0.95rem;
    line-height: 1.6;
}

.info-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 1.2rem;
    text-align: center;
    min-height: 105px;
}

.info-card-title {
    color: #6b7280;
    font-size: 0.85rem;
    margin-bottom: 0.5rem;
}

.info-card-value {
    font-size: 1.25rem;
    font-weight: 650;
}

.word-count {
    color: #6b7280;
    font-size: 0.9rem;
    margin-top: 0.4rem;
    margin-bottom: 1rem;
}

.history-count {
    color: #6b7280;
    font-size: 0.9rem;
}

.stButton > button,
.stDownloadButton > button {
    width: 100%;
    border-radius: 10px;
    font-weight: 600;
    min-height: 45px;
}

audio {
    width: 100%;
}

@media (max-width: 600px) {

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        padding-top: 1rem;
    }

    h1 {
        font-size: 2rem !important;
    }

    .main-subtitle {
        font-size: 1rem;
    }

    .technology-text {
        font-size: 0.75rem;
    }

    .recording-card {
        padding: 1rem;
    }

    .info-card {
        padding: 1rem;
        min-height: 95px;
    }

}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_language_name(language):
    """
    Convert language code into a user-friendly language name.
    """

    language = str(language).strip().lower()

    if language == "en":
        return "English 🇬🇧"

    if language == "hi":
        return "Hindi 🇮🇳"

    return language.upper()


def safe_confidence(value):
    """
    Safely convert confidence value into a number between 0 and 1.
    """

    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0.0

    return max(0.0, min(1.0, value))


def generate_transcription_id():
    """
    Generate a unique ID for every transcription.
    """

    return uuid.uuid4().hex


def get_timestamp_filename(timestamp):
    """
    Convert timestamp into a filename-safe string.
    """

    try:
        dt = datetime.strptime(
            timestamp,
            "%Y-%m-%d %H:%M:%S"
        )

        return dt.strftime(
            "%Y%m%d_%H%M%S"
        )

    except (ValueError, TypeError):

        return datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )


# ============================================================
# HISTORY FUNCTIONS
# ============================================================

def save_transcription(
    text,
    language,
    probability,
    timestamp=None
):
    """
    Save a transcription as a JSON file.
    """

    os.makedirs(
        TRANSCRIPTS_FOLDER,
        exist_ok=True
    )

    if timestamp is None:
        timestamp = datetime.now()

    transcription_id = generate_transcription_id()

    timestamp_string = timestamp.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    filename = (
        f"transcript_"
        f"{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"
        f"_{transcription_id[:8]}.json"
    )

    filepath = os.path.join(
        TRANSCRIPTS_FOLDER,
        filename
    )

    data = {
        "id": transcription_id,
        "timestamp": timestamp_string,
        "language": language,
        "language_name": get_language_name(language),
        "confidence": safe_confidence(probability),
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

    return transcription_id, filepath


def load_history():
    """
    Load all previous transcription JSON files.
    """

    history = []

    if not os.path.exists(TRANSCRIPTS_FOLDER):
        return history

    try:
        filenames = os.listdir(
            TRANSCRIPTS_FOLDER
        )
    except OSError:
        return history

    for filename in filenames:

        if not filename.lower().endswith(".json"):
            continue

        filepath = os.path.join(
            TRANSCRIPTS_FOLDER,
            filename
        )

        try:

            with open(
                filepath,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            if not isinstance(data, dict):
                continue

            # ------------------------------------------------
            # Backward compatibility
            # ------------------------------------------------

            if not data.get("id"):

                data["id"] = (
                    "legacy_"
                    + os.path.splitext(filename)[0]
                )

            if not data.get("language_name"):

                data["language_name"] = (
                    get_language_name(
                        data.get(
                            "language",
                            "unknown"
                        )
                    )
                )

            if "confidence" not in data:

                data["confidence"] = 0.0

            if "transcript" not in data:

                data["transcript"] = ""

            # Internal path.
            # It is not included in downloaded JSON.
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


def update_history_file(
    filepath,
    transcription_id,
    text,
    language,
    probability,
    timestamp
):
    """
    Update an existing history JSON file.
    """

    data = {
        "id": transcription_id,
        "timestamp": timestamp,
        "language": language,
        "language_name": get_language_name(language),
        "confidence": safe_confidence(probability),
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


def delete_history_file(filepath):
    """
    Delete one history JSON file.
    """

    if not filepath:
        return False

    if not os.path.exists(filepath):
        return False

    os.remove(filepath)

    return True


def delete_all_history():
    """
    Delete all transcription history JSON files.
    """

    if not os.path.exists(TRANSCRIPTS_FOLDER):
        return 0

    deleted_count = 0

    try:

        filenames = os.listdir(
            TRANSCRIPTS_FOLDER
        )

    except OSError:

        return 0

    for filename in filenames:

        if not filename.lower().endswith(".json"):
            continue

        filepath = os.path.join(
            TRANSCRIPTS_FOLDER,
            filename
        )

        try:

            os.remove(filepath)

            deleted_count += 1

        except OSError:
            continue

    return deleted_count


# ============================================================
# DOWNLOAD FUNCTIONS
# ============================================================

def create_txt_content(
    text,
    language_name,
    probability,
    timestamp
):
    """
    Create TXT download content.
    """

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


def create_json_content(
    transcription_id,
    text,
    language,
    language_name,
    probability,
    timestamp
):
    """
    Create JSON download content.
    """

    data = {
        "id": transcription_id,
        "timestamp": timestamp,
        "language": language,
        "language_name": language_name,
        "confidence": safe_confidence(probability),
        "transcript": text
    }

    return json.dumps(
        data,
        ensure_ascii=False,
        indent=4
    )


# ============================================================
# PROCESS AUDIO
# ============================================================

def process_audio(
    audio_bytes,
    audio_id
):
    """
    Convert recorded audio into text.
    """

    temp_audio_path = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav"
        ) as temp_audio:

            temp_audio.write(
                audio_bytes
            )

            temp_audio.flush()

            temp_audio_path = (
                temp_audio.name
            )

        with st.spinner(
            "🎧 Converting speech to text..."
        ):

            text, language, probability = recognize_speech(
                temp_audio_path
            )

        text = (
            str(text).strip()
            if text
            else ""
        )

        probability = safe_confidence(
            probability
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

        timestamp_string = timestamp.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # ----------------------------------------------------
        # Save to history
        # ----------------------------------------------------

        transcription_id, filepath = save_transcription(
            text,
            language,
            probability,
            timestamp
        )

        # ----------------------------------------------------
        # Current result
        # ----------------------------------------------------

        result = {
            "id": transcription_id,
            "filepath": filepath,
            "text": text,
            "language": language,
            "probability": probability,
            "timestamp": timestamp_string
        }

        st.session_state.transcription_result = result

        st.session_state.processed_audio_id = audio_id

        st.session_state.edit_mode = False

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

                os.remove(
                    temp_audio_path
                )

            except OSError:
                pass


# ============================================================
# HEADER
# ============================================================

st.title(
    "🎤 Bilingual Voice Transcriber"
)

st.markdown(
    """
<div class="main-subtitle">
Convert your voice into text instantly<br>
English 🇬🇧 &nbsp;•&nbsp; Hindi 🇮🇳
</div>
""",
    unsafe_allow_html=True
)

st.markdown(
    """
<div class="technology-text">
Powered by Python • Streamlit • faster-whisper
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
<div class="recording-title">🎙️ Record Your Voice</div>
<div class="recording-description">
Speak naturally in English or Hindi.<br>
The application automatically detects the language
and converts your speech into text.
</div>
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

    audio_id = hash(
        audio_bytes
    )

    st.success(
        "✅ Audio recorded successfully!"
    )

    st.subheader(
        "🔊 Your Recording"
    )

    st.audio(
        audio_bytes
    )

    st.divider()

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

    probability = safe_confidence(
        result.get(
            "probability",
            0.0
        )
    )

    timestamp = result.get(
        "timestamp",
        ""
    )

    transcription_id = result.get(
        "id",
        ""
    )

    filepath = result.get(
        "filepath",
        ""
    )

    language_name = get_language_name(
        language
    )

    # ========================================================
    # RECOGNITION RESULT
    # ========================================================

    st.divider()

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

        st.caption(
            "✏️ Make changes to your transcript below."
        )

        edited_text = st.text_area(
            "Edit Transcript",
            value=text,
            height=180,
            key="transcript_editor",
            label_visibility="collapsed"
        )

        edited_word_count = len(
            edited_text.strip().split()
        )

        edited_character_count = len(
            edited_text.strip()
        )

        st.markdown(
            f"""
<div class="word-count">
📝 {edited_word_count} word(s)
&nbsp;•&nbsp;
🔤 {edited_character_count} character(s)
</div>
""",
            unsafe_allow_html=True
        )

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "💾 Save Changes",
                use_container_width=True,
                type="primary"
            ):

                edited_text = (
                    edited_text.strip()
                )

                if not edited_text:

                    st.warning(
                        "⚠️ Transcript cannot be empty."
                    )

                else:

                    try:

                        # ------------------------------------
                        # Update JSON history file
                        # ------------------------------------

                        if filepath and os.path.exists(filepath):

                            update_history_file(
                                filepath,
                                transcription_id,
                                edited_text,
                                language,
                                probability,
                                timestamp
                            )

                        else:

                            # --------------------------------
                            # Find file using unique ID
                            # --------------------------------

                            history_items = load_history()

                            for item in history_items:

                                if (
                                    item.get("id")
                                    == transcription_id
                                ):

                                    filepath = item.get(
                                        "_filepath",
                                        ""
                                    )

                                    break

                            if filepath:

                                update_history_file(
                                    filepath,
                                    transcription_id,
                                    edited_text,
                                    language,
                                    probability,
                                    timestamp
                                )

                        # ------------------------------------
                        # Update current result
                        # ------------------------------------

                        st.session_state.transcription_result[
                            "text"
                        ] = edited_text

                        st.session_state.edit_mode = False

                        st.session_state.success_message = (
                            "✅ Transcript updated successfully!"
                        )

                        st.rerun()

                    except OSError as error:

                        st.error(
                            f"❌ Unable to save changes: {error}"
                        )

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

            if text:

                st.write(text)

            else:

                st.caption(
                    "No transcript available."
                )

        word_count = len(
            text.split()
        )

        character_count = len(
            text
        )

        st.markdown(
            f"""
<div class="word-count">
📝 {word_count} word(s)
&nbsp;•&nbsp;
🔤 {character_count} character(s)
</div>
""",
            unsafe_allow_html=True
        )

        # ----------------------------------------------------
        # EDIT BUTTON
        # ----------------------------------------------------

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
            "📋 Copy transcript:"
        )

        st.code(
            text,
            language=None
        )

        st.caption(
            "💡 Click the copy icon in the transcript box."
        )


    # ========================================================
    # DOWNLOAD CURRENT TRANSCRIPT
    # ========================================================

    st.divider()

    st.subheader(
        "💾 Save Transcript"
    )

    txt_content = create_txt_content(
        text,
        language_name,
        probability,
        timestamp
    )

    json_content = create_json_content(
        transcription_id,
        text,
        language,
        language_name,
        probability,
        timestamp
    )

    filename_timestamp = (
        get_timestamp_filename(
            timestamp
        )
    )

    col1, col2 = st.columns(2)

    with col1:

        st.download_button(
            label="📄 Download TXT",
            data=txt_content,
            file_name=(
                f"transcript_"
                f"{filename_timestamp}.txt"
            ),
            mime="text/plain",
            use_container_width=True
        )

    with col2:

        st.download_button(
            label="📋 Download JSON",
            data=json_content,
            file_name=(
                f"transcript_"
                f"{filename_timestamp}.json"
            ),
            mime="application/json",
            use_container_width=True
        )


# ============================================================
# NEW RECORDING
# ============================================================

st.divider()

st.subheader(
    "🔄 New Recording"
)

st.caption(
    "Start a new recording without deleting your saved history."
)

if st.button(
    "🔄 Start New Recording",
    use_container_width=True
):

    st.session_state.transcription_result = None

    st.session_state.processed_audio_id = None

    st.session_state.edit_mode = False

    st.session_state.audio_input_key += 1

    st.session_state.success_message = None

    st.rerun()


# ============================================================
# TRANSCRIPTION HISTORY
# ============================================================

st.divider()

st.subheader(
    "📚 Transcription History"
)

history = load_history()


# ============================================================
# HISTORY EMPTY
# ============================================================

if not history:

    st.info(
        "No previous transcriptions found."
    )


else:

    # --------------------------------------------------------
    # HISTORY HEADER
    # --------------------------------------------------------

    st.markdown(
        f"""
<div class="history-count">
📚 {len(history)} transcription(s) saved
</div>
""",
        unsafe_allow_html=True
    )

    st.write("")

    # --------------------------------------------------------
    # SEARCH + FILTER
    # --------------------------------------------------------

    search_text = st.text_input(
        "🔎 Search history",
        placeholder="Search by transcript text...",
        key="history_search"
    )

    language_filter = st.selectbox(
        "🌐 Filter by language",
        [
            "All Languages",
            "English",
            "Hindi"
        ],
        key="history_language_filter"
    )

    # --------------------------------------------------------
    # FILTER HISTORY
    # --------------------------------------------------------

    filtered_history = []

    for item in history:

        transcript = str(
            item.get(
                "transcript",
                ""
            )
        )

        language = str(
            item.get(
                "language",
                ""
            )
        ).lower()

        language_name = item.get(
            "language_name",
            get_language_name(language)
        )

        # Search filter
        if search_text:

            if search_text.lower() not in transcript.lower():

                continue

        # Language filter
        if language_filter == "English":

            if language != "en":

                continue

        elif language_filter == "Hindi":

            if language != "hi":

                continue

        filtered_history.append(
            item
        )

    # --------------------------------------------------------
    # FILTER RESULT
    # --------------------------------------------------------

    if not filtered_history:

        st.info(
            "🔎 No matching transcriptions found."
        )

    else:

        st.caption(
            f"Showing {len(filtered_history)} "
            f"of {len(history)} transcription(s)"
        )

        # ----------------------------------------------------
        # HISTORY ITEMS
        # ----------------------------------------------------

        for index, item in enumerate(
            filtered_history
        ):

            item_id = item.get(
                "id",
                f"history_{index}"
            )

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

            transcript = str(
                item.get(
                    "transcript",
                    ""
                )
            )

            confidence = safe_confidence(
                item.get(
                    "confidence",
                    0.0
                )
            )

            filepath = item.get(
                "_filepath",
                ""
            )

            # ------------------------------------------------
            # HISTORY EXPANDER
            # ------------------------------------------------

            with st.expander(
                f"{language_name} — {timestamp}",
                expanded=False
            ):

                # --------------------------------------------
                # DETAILS
                # --------------------------------------------

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

                history_word_count = len(
                    transcript.split()
                )

                history_character_count = len(
                    transcript
                )

                st.markdown(
                    f"""
<div class="word-count">
📝 {history_word_count} word(s)
&nbsp;•&nbsp;
🔤 {history_character_count} character(s)
</div>
""",
                    unsafe_allow_html=True
                )

                # --------------------------------------------
                # COPY
                # --------------------------------------------

                st.caption(
                    "📋 Copy transcript:"
                )

                st.code(
                    transcript,
                    language=None
                )

                # --------------------------------------------
                # DOWNLOAD HISTORY ITEM
                # --------------------------------------------

                history_txt = create_txt_content(
                    transcript,
                    language_name,
                    confidence,
                    timestamp
                )

                history_json = create_json_content(
                    item_id,
                    transcript,
                    language,
                    language_name,
                    confidence,
                    timestamp
                )

                history_filename_timestamp = (
                    get_timestamp_filename(
                        timestamp
                    )
                )

                st.write("")

                download_col1, download_col2 = (
                    st.columns(2)
                )

                with download_col1:

                    st.download_button(
                        label="📄 Download TXT",
                        data=history_txt,
                        file_name=(
                            f"transcript_"
                            f"{history_filename_timestamp}.txt"
                        ),
                        mime="text/plain",
                        use_container_width=True,
                        key=(
                            f"history_txt_"
                            f"{item_id}"
                        )
                    )

                with download_col2:

                    st.download_button(
                        label="📋 Download JSON",
                        data=history_json,
                        file_name=(
                            f"transcript_"
                            f"{history_filename_timestamp}.json"
                        ),
                        mime="application/json",
                        use_container_width=True,
                        key=(
                            f"history_json_"
                            f"{item_id}"
                        )
                    )

                # --------------------------------------------
                # DELETE
                # --------------------------------------------

                st.write("")

                if st.button(
                    "🗑️ Delete This Transcription",
                    key=f"delete_history_{item_id}",
                    use_container_width=True
                ):

                    try:

                        if delete_history_file(
                            filepath
                        ):

                            current_result = (
                                st.session_state.transcription_result
                            )

                            if current_result:

                                if (
                                    current_result.get("id")
                                    == item_id
                                ):

                                    st.session_state.transcription_result = None

                                    st.session_state.processed_audio_id = None

                            st.session_state.success_message = (
                                "✅ Transcription deleted successfully!"
                            )

                            st.rerun()

                        else:

                            st.error(
                                "❌ Could not delete transcription."
                            )

                    except OSError as error:

                        st.error(
                            f"❌ Unable to delete transcription: {error}"
                        )


    # ========================================================
    # DELETE ALL HISTORY
    # ========================================================

    st.divider()

    if not st.session_state.show_delete_all_confirmation:

        if st.button(
            "🗑️ Delete All History",
            use_container_width=True
        ):

            st.session_state.show_delete_all_confirmation = True

            st.rerun()

    else:

        st.warning(
            "⚠️ Are you sure you want to delete ALL "
            "transcription history? This action cannot be undone."
        )

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "🗑️ Yes, Delete All",
                use_container_width=True,
                type="primary"
            ):

                deleted_count = (
                    delete_all_history()
                )

                st.session_state.show_delete_all_confirmation = False

                st.session_state.transcription_result = None

                st.session_state.processed_audio_id = None

                st.success(
                    f"✅ {deleted_count} transcription(s) deleted."
                )

                st.rerun()

        with col2:

            if st.button(
                "❌ Cancel",
                use_container_width=True
            ):

                st.session_state.show_delete_all_confirmation = False

                st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🎤 Bilingual Voice Transcriber • "
    "English & Hindi Speech Recognition"
)