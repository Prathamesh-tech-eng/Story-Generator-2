"""Streamlit UI for the Maharashtrian story generator and translator."""
from __future__ import annotations

import os
from typing import List

import streamlit as st
from dotenv import load_dotenv

from story_generator import GeminiClient, StoryConfig, build_prompt

load_dotenv()

GENRE_OPTIONS = [
    "Historical fiction (ऐतिहासिक कथा)",
    "Slice of life (दैनंदिन जीवन)",
    "Coming-of-age drama (वयोमानाचा प्रवास)",
    "Mystical realism (आध्यात्मिक यथार्थवाद)",
    "Romantic drama (प्रेमकथा)",
    "Family saga (कौटुंबिक गोष्ट)",
    "Light-hearted comedy (हलक्या फुलक्या प्रकृतीची)",
    "Suspenseful mystery (थरारक गूढ )",
]

STYLE_OPTIONS = [
    "Lyrical third-person narration (गाण्यासारखी तृतीय-पुरुषी कथा)",
    "Breezy conversational tone (ओघवता संवाद)",
    "Reflective first-person diary (चिंतनशील डायरी)",
    "Playful omniscient narrator ( खेळकर सर्वज्ञ नरेटर)",
    "Cinematic present-tense storytelling (सिनेमाई वर्तमानकाल)",
]

INSPIRATION_OPTIONS = [
    "Pu La Deshpande's observational humour ( पु. ल. देशपांडे यांचे निरीक्षणात्मक विनोद)",
    "Vinda Karandikar's poetic introspection (विंदा करंदीकर यांचे काव्यात्मक आत्मनिरीक्षण)",
    "Durga Bhagwat's reflective essays (दुर्गा भागवत यांचे चिंतनशील निबंध)",
    "Baburao Bagul's gritty realism ( बाबुराव बागूल यांचे कठोर यथार्थवाद )",
    "Vijay Tendulkar's dramatic structures ( विजय तेंडुलकर यांची नाट्यमय रचना )",
]

WORD_LENGTH_OPTIONS = {
    "Compact vignette (~1000 words) ( लघु रेखाचित्र)": 1000,
    "Standard short story (~1500 words)": 1500,
    "Roomy narrative (~2000 words) ( विस्तृत कथन)": 2000,
    "Epic chaptered tale (~3500 words) (महाकाव्यात्मक कथा)": 3500,
}

CHAPTER_OPTIONS = [1, 2, 3, 4, 5]

PLOT_TWIST_OPTIONS = [
    "A forgotten family letter reappears (विसरलेले कुटुंबीय पत्र)",
    "Ancestral secret tied to a festival (सणाशी निगडीत पैत्रिक गुपित)",
    "Unexpected ally from a rival family (प्रतिस्पर्धी कुटुंबातून मित्र)",
    "Protagonist misreads an omen ( नायकाची चुकीची शकुनवाचन)",
    "Hidden talent changes the stakes (दडलेली प्रतिभा )",
    "A rumour masks a deeper truth (अफवेखालील खोल सत्य )",
    "fight ( झगडा )",
    "love ( प्रेम)",
    "injury (जखम )",
    "change of heart ()",
    "Hidden talent changes the stakes (मनःपरिवर्तन)",
]

ENDING_OPTIONS = [
    "Bittersweet but hopeful (मिश्रित पण आशावादी)",
    "Triumphant yet grounded (विजयी पण पाय जमिनीवर )",
    "Open-ended contemplation (उघडे शेवट)",
    "Poignant reconciliation (हृदयस्पर्शी समेट)",
    "Joyful celebration (आनंदोत्सव)",
    "Sad Ending (dukh)", 
]

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-pro",
    "gemini-2.0-flash",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
]

TRANSLATION_LANGUAGES = ["Marathi", "Hindi", "Sanskrit", "English"]


def _get_characters(raw_value: str) -> List[str]:
    return [name.strip() for name in raw_value.split(",") if name.strip()]


def _get_twists(selected: List[str], custom: str) -> List[str]:
    custom_parts = [item.strip() for item in custom.split(",") if item.strip()]
    return selected + custom_parts


def _require_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("Set GEMINI_API_KEY in your environment or .env file before running the app.")
        st.stop()
    return api_key


def _make_client(model: str) -> GeminiClient:
    api_key = _require_api_key()
    return GeminiClient(api_key=api_key, model=model)


def _build_story_config(form_values: dict) -> StoryConfig:
    characters = _get_characters(form_values["characters"])
    if not characters:
        raise ValueError("Please provide at least one character.")

    cfg = StoryConfig(
        story_description=form_values["description"].strip(),
        characters=characters,
        genre=form_values["genre"],
        writing_style=form_values["style"],
        literature_inspiration=form_values["inspiration"],
        word_length=form_values["word_length"],
        chapters=form_values["chapters"],
        plot_twists=_get_twists(form_values["twists"], form_values["custom_twists"]),
        ending_type=form_values["ending"],
    )
    cfg.validate()
    return cfg


def _set_latest_story(story: str) -> None:
    st.session_state["latest_story"] = story


def _get_latest_story() -> str:
    return st.session_state.get("latest_story", "")


def main() -> None:
    st.set_page_config(page_title="Maharashtrian Story Studio", layout="wide")
    st.title("Maharashtrian Story Studio")
    st.caption(
        "Curate a Maharashtrian narrative with tight creative controls, then translate it faithfully into Marathi."
    )

    generate_tab, translate_tab = st.tabs(["Generate Story", "Translate Story"])

    with generate_tab:
        with st.form("story_form"):
            description = st.text_area(
                "Story description",
                placeholder="Describe the core idea, conflict, or setting…",
                height=120,
            )
            characters = st.text_input(
                "Characters (comma separated)",
                placeholder="Niraj, Kavya, Aaji",
            )

            col1, col2, col3 = st.columns(3)
            genre = col1.selectbox("Genre", GENRE_OPTIONS)
            style = col2.selectbox("Writing style", STYLE_OPTIONS)
            inspiration = col3.selectbox("Literary inspiration", INSPIRATION_OPTIONS)

            col4, col5, col6 = st.columns(3)
            length_label = col4.selectbox("Target length", list(WORD_LENGTH_OPTIONS.keys()), index=1)
            chapters = col5.selectbox("Chapter count", CHAPTER_OPTIONS, index=2)
            ending = col6.selectbox("Ending mood/type", ENDING_OPTIONS)

            twists = st.multiselect(
                "Plot twists to integrate (pick multiple)",
                PLOT_TWIST_OPTIONS,
                default=PLOT_TWIST_OPTIONS[:2],
            )
            custom_twists = st.text_input("Custom twists (comma separated)")

            col7, col8 = st.columns([2, 1])
            model = col7.selectbox("Gemini model", GEMINI_MODELS, index=0)
            temperature = col8.slider("Temperature", min_value=0.2, max_value=1.2, value=0.75, step=0.05)

            submitted = st.form_submit_button("Generate story")

        if submitted:
            if not description.strip():
                st.error("Please describe the story idea.")
            else:
                form_values = {
                    "description": description,
                    "characters": characters,
                    "genre": genre,
                    "style": style,
                    "inspiration": inspiration,
                    "word_length": WORD_LENGTH_OPTIONS[length_label],
                    "chapters": chapters,
                    "twists": twists,
                    "custom_twists": custom_twists,
                    "ending": ending,
                }
                try:
                    cfg = _build_story_config(form_values)
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    prompt = build_prompt(cfg)
                    try:
                        with st.spinner("Calling Gemini…"):
                            client = _make_client(model)
                            story = client.generate_story(prompt, temperature)
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"Failed to generate story: {exc}")
                    else:
                        st.success("Story ready!")
                        st.text_area("Generated story", value=story, height=400, key="story_output")
                        st.download_button(
                            label="Download story",
                            data=story,
                            file_name="maharashtrian_story.txt",
                            mime="text/plain",
                        )
                        _set_latest_story(story)

    with translate_tab:
        st.write("Translate any story into Marathi (or another supported language) without altering its realism.")
        translation_col1, translation_col2 = st.columns([3, 1])
        source_text = translation_col1.text_area(
            "Story to translate",
            value=_get_latest_story(),
            height=360,
            placeholder="Paste or reuse a generated story…",
        )
        target_language = translation_col2.selectbox("Target language", TRANSLATION_LANGUAGES, index=0)
        translation_temperature = translation_col2.slider(
            "Temperature", min_value=0.2, max_value=0.8, value=0.35, step=0.05
        )
        translation_model = translation_col2.selectbox("Gemini model", GEMINI_MODELS, index=0, key="translation_model")

        if st.button("Translate story"):
            if not source_text.strip():
                st.error("Provide a story to translate.")
            else:
                try:
                    with st.spinner("Translating via Gemini…"):
                        client = _make_client(translation_model)
                        translation = client.translate_text(
                            source_text,
                            target_language=target_language,
                            temperature=translation_temperature,
                        )
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Failed to translate story: {exc}")
                else:
                    st.success(f"Translation ready in {target_language}!")
                    st.text_area("Translated story", value=translation, height=360, key="translation_output")
                    st.download_button(
                        label="Download translation",
                        data=translation,
                        file_name=f"story_{target_language.lower()}.txt",
                        mime="text/plain",
                    )


if __name__ == "__main__":
    main()
