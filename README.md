# Maharashtrian Story Generator

Command-line helper that gathers creative constraints, builds a tightly scoped prompt, and calls the Gemini API to return a culturally rooted, consistent story.

## Prerequisites

1. Python 3.9+
2. Google Gemini API key stored as an environment variable: `GEMINI_API_KEY`
3. Dependencies installed:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

## Usage

### Interactive mode

```powershell
python story_generator.py
```
You will be prompted for the description, characters, genre, style, inspiration, word length, chapter count, desired twists, and ending type. The script forms a prompt that insists on Maharashtrian context and coherent character arcs, then prints the story received from Gemini.

### JSON-driven mode

Provide a config file to skip interactive questions:

```powershell
python story_generator.py --config config/story_request.json --output outputs\festival_story.txt
```

Structure of the JSON file:

```json
{
  "story_description": "A young tabla player uncovers a family mystery during Ganeshotsav in Pune",
  "characters": ["Mira, an earnest tabla student", "Dadasaheb, her pragmatic grandfather"],
  "genre": "Literary mystery",
  "writing_style": "Lush descriptive prose with rhythmic cadences",
  "literature_inspiration": "Durga Bhagwat's reflective essays",
  "word_length": 1200,
  "chapters": 4,
  "plot_twists": [
    "The family's lost abhanga resurfaces in an unexpected raag",
    "A neighbour's rumour turns out to be misdirection"
  ],
  "ending_type": "Resolute yet hopeful"
}
```

### GUI mode

Prefer a point-and-click experience? Launch the Tkinter UI:

```powershell
python app.py
```

Pick from curated dropdowns for genre, style, inspirations, word lengths, chapter counts, twists, ending tones, and Gemini models. Enter your story description plus characters, click **Generate story**, and the response will appear in the built-in viewer.

Once a story is visible, click **Translate to Marathi** to fetch a faithful translation that preserves formatting and realism.

### Streamlit web app

Launch a browser-based experience suitable for local demos or hosting on Streamlit Cloud:

```powershell
streamlit run streamlit_app.py
```

The "Generate Story" tab mirrors the CLI inputs with dropdowns, multi-select twists, and Gemini model/temperature controls. The "Translate Story" tab lets you paste any prose (or re-use the latest generated output) and obtain an on-brand Marathi/Hindi/Sanskrit/English rendition that preserves realism. Add your `GEMINI_API_KEY` to the environment before deploying to Streamlit Cloud or any hosting provider.

### Translate an existing story (CLI)

Point the CLI at any text file to translate it (defaults to Marathi, but you can override the language):

```powershell
python story_generator.py --translate-file outputs\festival_story.txt --translate-language Marathi --output outputs\festival_story_mr.txt
```

The script builds a translation-only prompt that forbids summaries or commentary and prints the translated story text (and optionally saves it via `--output`).

### Prompt inspection

Use `--dry-run` to print the assembled prompt before calling Gemini:

```powershell
python story_generator.py --config request.json --dry-run
```

## Notes

- The generated prompt enforces consistency (no character drift, steady tone, chapter structure) and explicitly demands Maharashtrian cultural grounding to minimise deviation.
- Translation mode sends a strict instruction set so Gemini returns only the converted prose—no headers, comments, or extra narration.
- Adjust `--temperature` or `--model` if you need a calmer or more exploratory narrative.
- Stories are streamed back to stdout and optionally written to the file specified by `--output`.
