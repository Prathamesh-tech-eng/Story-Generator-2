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

By default the generator now asks Gemini for each chapter separately. This keeps long stories consistent and avoids truncated outputs. If you ever need the legacy single-request behavior, append `--mode single`.

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

### Prompt inspection

Use `--dry-run` to print the assembled prompt before calling Gemini:

```powershell
python story_generator.py --config request.json --dry-run
```

With sequential mode you will see the Chapter 1 template; switch to `--mode single` to inspect the one-shot prompt.

## Notes

- The generated prompt enforces consistency (no character drift, steady tone, chapter structure) and explicitly demands Maharashtrian cultural grounding to minimise deviation.
- Adjust `--temperature` or `--model` if you need a calmer or more exploratory narrative.
- Stories are streamed back to stdout and optionally written to the file specified by `--output`.
- Sequential mode feeds each newly written chapter back into Gemini so part 2 continues exactly where part 1 stopped; the GUI shows partial chapters as they arrive.
