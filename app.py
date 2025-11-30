"""Simple Tkinter UI for the Maharashtrian story generator."""
from __future__ import annotations

import os
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from dotenv import load_dotenv

from story_generator import GeminiClient, StoryConfig, build_prompt

load_dotenv()

GENRE_OPTIONS = [
    "Historical fiction",
    "Slice of life",
    "Coming-of-age drama",
    "Mystical realism",
    "Romantic drama",
    "Family saga",
    "Light-hearted comedy",
    "Suspenseful mystery",
]

STYLE_OPTIONS = [
    "Lyrical third-person narration",
    "Breezy conversational tone",
    "Reflective first-person diary",
    "Playful omniscient narrator",
    "Cinematic present-tense storytelling",
]

INSPIRATION_OPTIONS = [
    "Pu La Deshpande's observational humour",
    "Vinda Karandikar's poetic introspection",
    "Durga Bhagwat's reflective essays",
    "Baburao Bagul's gritty realism",
    "Vijay Tendulkar's dramatic structures",
]

LENGTH_OPTIONS = [
    ("Compact vignette (~600 words)", 600),
    ("Standard short story (~900 words)", 900),
    ("Roomy narrative (~1200 words)", 1200),
    ("Epic chaptered tale (~1500 words)", 1500),
]

CHAPTER_OPTIONS = [1, 2, 3, 4, 5]

PLOT_TWIST_OPTIONS = [
    "fight",
    "love",
    "injury",
    "change of heart",
    "Hidden talent changes the stakes",
    "A rumour masks a deeper truth",
]

ENDING_OPTIONS = [
    "Bittersweet but hopeful",
    "Triumphant yet grounded",
    "Open-ended contemplation",
    "Poignant reconciliation",
    "Joyful celebration",
]

MODEL_OPTIONS = [
    "gemini-2.0-flash",
    "gemini-2.0-pro",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.5-flash",
]


def _build_scrollable_text(parent: ttk.Frame, height: int = 8) -> tuple[tk.Text, ttk.Scrollbar]:
    text_widget = tk.Text(parent, height=height, wrap=tk.WORD)
    scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=text_widget.yview)
    text_widget.configure(yscrollcommand=scrollbar.set)
    return text_widget, scrollbar


class StoryApp:
    """Encapsulates Tkinter widgets and story generation logic."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Maharashtrian Story Generator")
        self.root.geometry("900x720")
        self.root.minsize(800, 650)

        self.status_var = tk.StringVar(value="Waiting for input…")
        self.genre_var = tk.StringVar(value=GENRE_OPTIONS[0])
        self.style_var = tk.StringVar(value=STYLE_OPTIONS[0])
        self.inspiration_var = tk.StringVar(value=INSPIRATION_OPTIONS[0])
        self.length_var = tk.StringVar(value=str(LENGTH_OPTIONS[1][1]))
        self.chapters_var = tk.StringVar(value=str(CHAPTER_OPTIONS[2]))
        self.ending_var = tk.StringVar(value=ENDING_OPTIONS[0])
        self.model_var = tk.StringVar(value=MODEL_OPTIONS[-1])
        self.temperature_var = tk.DoubleVar(value=0.75)

        self._build_layout()

    def _build_layout(self) -> None:
        root_frame = ttk.Frame(self.root, padding=16)
        root_frame.pack(fill=tk.BOTH, expand=True)

        form = ttk.Frame(root_frame)
        form.pack(fill=tk.X)

        # Row 1: description and characters
        description_label = ttk.Label(form, text="Story description")
        description_label.grid(row=0, column=0, sticky=tk.W)
        self.description_text, desc_scroll = _build_scrollable_text(form, height=4)
        self.description_text.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=(0, 12))
        desc_scroll.grid(row=1, column=2, sticky=tk.NS, pady=(0, 12))

        ttk.Label(form, text="Characters (comma separated)").grid(row=2, column=0, sticky=tk.W)
        self.characters_entry = ttk.Entry(form)
        self.characters_entry.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=(0, 12))

        # Row 2: dropdowns
        dropdown_frame = ttk.Frame(form)
        dropdown_frame.grid(row=4, column=0, columnspan=3, sticky=tk.EW)
        dropdown_frame.columnconfigure((0, 1, 2), weight=1)

        self._add_combo(dropdown_frame, "Genre", self.genre_var, GENRE_OPTIONS, 0)
        self._add_combo(dropdown_frame, "Writing style", self.style_var, STYLE_OPTIONS, 1)
        self._add_combo(dropdown_frame, "Literary inspiration", self.inspiration_var, INSPIRATION_OPTIONS, 2)

        length_frame = ttk.Frame(form)
        length_frame.grid(row=5, column=0, columnspan=3, sticky=tk.EW, pady=(12, 0))
        self._add_combo(length_frame, "Target length", self.length_var, [str(v[1]) for v in LENGTH_OPTIONS], 0)
        ttk.Label(length_frame, text="Word-length presets:").grid(row=0, column=1, padx=(16, 8))
        ttk.Label(length_frame, text=", ".join(label for label, _ in LENGTH_OPTIONS)).grid(row=0, column=2, sticky=tk.W)

        chapters_frame = ttk.Frame(form)
        chapters_frame.grid(row=6, column=0, columnspan=3, sticky=tk.EW, pady=(12, 0))
        self._add_combo(
            chapters_frame,
            "Chapter count",
            self.chapters_var,
            [str(num) for num in CHAPTER_OPTIONS],
            0,
        )
        ttk.Label(chapters_frame, text="Each chapter heading will read ‘Chapter N: <title>’ automatically.").grid(
            row=0, column=1, sticky=tk.W, padx=(16, 0)
        )

        ttk.Label(form, text="Plot twists (Ctrl/Cmd-click for multiple)").grid(row=7, column=0, sticky=tk.W, pady=(12, 4))
        twists_frame = ttk.Frame(form)
        twists_frame.grid(row=8, column=0, columnspan=3, sticky=tk.EW)
        self.twist_list = tk.Listbox(twists_frame, selectmode=tk.MULTIPLE, height=6)
        for option in PLOT_TWIST_OPTIONS:
            self.twist_list.insert(tk.END, option)
        self.twist_list.grid(row=0, column=0, sticky=tk.NSEW)
        twist_scroll = ttk.Scrollbar(twists_frame, orient=tk.VERTICAL, command=self.twist_list.yview)
        twist_scroll.grid(row=0, column=1, sticky=tk.NS)
        self.twist_list.configure(yscrollcommand=twist_scroll.set)
        ttk.Label(form, text="Custom twists (comma separated)").grid(row=9, column=0, sticky=tk.W, pady=(12, 0))
        self.custom_twists_entry = ttk.Entry(form)
        self.custom_twists_entry.grid(row=10, column=0, columnspan=3, sticky=tk.EW)

        ending_frame = ttk.Frame(form)
        ending_frame.grid(row=11, column=0, columnspan=3, sticky=tk.EW, pady=(12, 0))
        self._add_combo(ending_frame, "Ending mood/type", self.ending_var, ENDING_OPTIONS, 0)

        model_frame = ttk.Frame(form)
        model_frame.grid(row=12, column=0, columnspan=3, sticky=tk.EW, pady=(12, 0))
        self._add_combo(model_frame, "Gemini model", self.model_var, MODEL_OPTIONS, 0)
        ttk.Label(model_frame, text="Temperature").grid(row=0, column=1, padx=(16, 4))
        temperature_scale = ttk.Scale(model_frame, from_=0.2, to=1.2, orient=tk.HORIZONTAL, variable=self.temperature_var)
        temperature_scale.grid(row=0, column=2, sticky=tk.EW)

        button_frame = ttk.Frame(root_frame)
        button_frame.pack(fill=tk.X, pady=(12, 0))
        self.generate_btn = ttk.Button(button_frame, text="Generate story", command=self.on_generate)
        self.generate_btn.pack(side=tk.LEFT)
        self.translate_btn = ttk.Button(
            button_frame,
            text="Translate to Marathi",
            command=self.on_translate,
            state=tk.DISABLED,
        )
        self.translate_btn.pack(side=tk.LEFT, padx=(8, 0))
        ttk.Label(button_frame, textvariable=self.status_var).pack(side=tk.RIGHT)

        ttk.Label(root_frame, text="Story output").pack(anchor=tk.W, pady=(16, 4))
        output_frame = ttk.Frame(root_frame)
        output_frame.pack(fill=tk.BOTH, expand=True)
        self.output_text, output_scroll = _build_scrollable_text(output_frame, height=16)
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        output_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        root_frame.columnconfigure(0, weight=1)
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(2, weight=0)

    def _add_combo(self, parent: ttk.Frame, label: str, variable: tk.StringVar, options: list[str], column: int) -> None:
        ttk.Label(parent, text=label).grid(row=0, column=column, sticky=tk.W, padx=(0, 8))
        combo = ttk.Combobox(parent, textvariable=variable, values=options, state="readonly")
        combo.grid(row=1, column=column, sticky=tk.EW, padx=(0, 8))
        parent.columnconfigure(column, weight=1)

    def on_generate(self) -> None:
        try:
            config = self._gather_config()
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        self.generate_btn.configure(state=tk.DISABLED)
        self.status_var.set("Sending prompt to Gemini…")
        threading.Thread(target=self._generate_story_async, args=(config,), daemon=True).start()

    def on_translate(self) -> None:
        story_text = self.output_text.get("1.0", tk.END).strip()
        if not story_text:
            messagebox.showinfo("No story", "Generate a story before translating it to Marathi.")
            return

        self.generate_btn.configure(state=tk.DISABLED)
        self.translate_btn.configure(state=tk.DISABLED)
        self.status_var.set("Translating story to Marathi…")
        threading.Thread(target=self._translate_story_async, args=(story_text,), daemon=True).start()

    def _gather_config(self) -> StoryConfig:
        description = self.description_text.get("1.0", tk.END).strip()
        characters = [item.strip() for item in self.characters_entry.get().split(",") if item.strip()]
        if not description:
            raise ValueError("Please describe the story idea.")
        if not characters:
            raise ValueError("Please add at least one character.")

        selected_indices = self.twist_list.curselection()
        selected_twists = [self.twist_list.get(idx) for idx in selected_indices]
        custom_twists = [item.strip() for item in self.custom_twists_entry.get().split(",") if item.strip()]
        twists = selected_twists + custom_twists

        cfg = StoryConfig(
            story_description=description,
            characters=characters,
            genre=self.genre_var.get(),
            writing_style=self.style_var.get(),
            literature_inspiration=self.inspiration_var.get(),
            word_length=int(self.length_var.get()),
            chapters=int(self.chapters_var.get()),
            plot_twists=twists,
            ending_type=self.ending_var.get(),
        )
        cfg.validate()
        return cfg

    def _generate_story_async(self, config: StoryConfig) -> None:
        try:
            prompt = build_prompt(config)
            api_key = os.getenv("GEMINI_API_KEY")
            client = GeminiClient(api_key=api_key, model=self.model_var.get())
            story = client.generate_story(prompt=prompt, temperature=self.temperature_var.get())
        except Exception as exc:  # noqa: BLE001 - want clear UI feedback
            self.root.after(0, self._handle_error, exc, "Generation failed.")
            return
        self.root.after(0, self._handle_success, story)

    def _translate_story_async(self, story_text: str) -> None:
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            client = GeminiClient(api_key=api_key, model=self.model_var.get())
            translation = client.translate_text(story_text, target_language="Marathi", temperature=0.35)
        except Exception as exc:  # noqa: BLE001 - want clear UI feedback
            self.root.after(0, self._handle_error, exc, "Translation failed.")
            return
        self.root.after(0, self._handle_translation_success, translation)

    def _handle_error(self, exc: Exception, status_message: str) -> None:
        self.generate_btn.configure(state=tk.NORMAL)
        if self.output_text.get("1.0", tk.END).strip():
            self.translate_btn.configure(state=tk.NORMAL)
        else:
            self.translate_btn.configure(state=tk.DISABLED)
        self.status_var.set(status_message)
        messagebox.showerror("Gemini error", str(exc))

    def _handle_success(self, story: str) -> None:
        self.generate_btn.configure(state=tk.NORMAL)
        self.translate_btn.configure(state=tk.NORMAL)
        self.status_var.set("Story ready!")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, story)

    def _handle_translation_success(self, story: str) -> None:
        self.generate_btn.configure(state=tk.NORMAL)
        self.translate_btn.configure(state=tk.NORMAL)
        self.status_var.set("Marathi translation ready!")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, story)


def main() -> None:
    root = tk.Tk()
    StoryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
