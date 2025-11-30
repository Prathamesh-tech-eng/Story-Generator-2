#!/usr/bin/env python3
"""Command-line Maharashtrian story generator that calls Gemini."""
from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from dataclasses import dataclass, asdict
from typing import Callable, List, Sequence

import requests
from dotenv import load_dotenv


@dataclass
class StoryConfig:
    """Container for the user-controlled knobs."""

    story_description: str
    characters: List[str]
    genre: str
    writing_style: str
    literature_inspiration: str
    word_length: int
    chapters: int
    plot_twists: List[str]
    ending_type: str

    @classmethod
    def from_dict(cls, data: dict) -> "StoryConfig":
        def _list(value):
            if isinstance(value, list):
                return [str(item).strip() for item in value if str(item).strip()]
            if isinstance(value, str):
                return [item.strip() for item in value.split(",") if item.strip()]
            return []

        def _int(value, default):
            try:
                parsed = int(value)
                return parsed if parsed > 0 else default
            except (TypeError, ValueError):
                return default

        return cls(
            story_description=str(data.get("story_description", "")).strip(),
            characters=_list(data.get("characters", [])),
            genre=str(data.get("genre", "")).strip(),
            writing_style=str(data.get("writing_style", "")).strip(),
            literature_inspiration=str(data.get("literature_inspiration", "")).strip(),
            word_length=_int(data.get("word_length"), 900),
            chapters=_int(data.get("chapters"), 3),
            plot_twists=_list(data.get("plot_twists", [])),
            ending_type=str(data.get("ending_type", "")).strip(),
        )

    def validate(self) -> None:
        missing = [
            field
            for field, value in asdict(self).items()
            if isinstance(value, str) and not value.strip()
        ]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")


def prompt_user_for_config() -> StoryConfig:
    """Collect configuration interactively via stdin."""

    def ask(prompt_text: str, default: str | None = None) -> str:
        suffix = f" [{default}]" if default else ""
        value = input(f"{prompt_text}{suffix}: ").strip()
        return value or (default or "")

    def ask_list(prompt_text: str) -> List[str]:
        raw = input(f"{prompt_text} (comma separated): ").strip()
        return [item.strip() for item in raw.split(",") if item.strip()]

    def ask_int(prompt_text: str, default: int) -> int:
        raw = input(f"{prompt_text} [{default}]: ").strip()
        if not raw:
            return default
        try:
            parsed = int(raw)
            if parsed <= 0:
                raise ValueError
            return parsed
        except ValueError:
            print("Please enter a positive integer.")
            return ask_int(prompt_text, default)

    story_description = ask("Briefly describe the core story idea")
    characters = ask_list("List the main characters")
    genre = ask("What genre should the story follow?", "Historical fiction")
    writing_style = ask("Preferred writing style", "Lyrical third-person narration")
    literature_inspiration = ask("Literature inspiration", "Pu La Deshpande's observational humour")
    word_length = ask_int("Approximate total word length", 900)
    chapters = ask_int("How many chapters?", 3)
    plot_twists = ask_list("List desired plot twists")
    ending_type = ask("What kind of ending?", "Bittersweet but hopeful")

    cfg = StoryConfig(
        story_description=story_description,
        characters=characters,
        genre=genre,
        writing_style=writing_style,
        literature_inspiration=literature_inspiration,
        word_length=word_length,
        chapters=chapters,
        plot_twists=plot_twists,
        ending_type=ending_type,
    )
    cfg.validate()
    return cfg


def build_prompt(cfg: StoryConfig) -> str:
    """Create a tightly scoped prompt for Gemini."""

    character_lines = "\n".join(f"- {c}" for c in cfg.characters) or "- Introduce 1-3 fitting characters but keep them stable once named."
    twist_lines = "\n".join(f"- {t}" for t in cfg.plot_twists) or "- Subtle reveal tied to family legacy"

    template = f"""
    You are an accomplished English-language storyteller deeply familiar with Maharashtrian culture.
    Write a cohesive narrative that never contradicts previously stated facts and stays grounded in 
    authentic Maharashtrian settings, customs, food, and idioms.

    Story brief:
    - Core description: {cfg.story_description}
    - Characters to use consistently:
    {character_lines}
    - Genre: {cfg.genre}
    - Writing style: {cfg.writing_style}
    - Literary inspiration: {cfg.literature_inspiration}
    - Target length: about {cfg.word_length} words (±10%)
    - Chapter count: Exactly {cfg.chapters} chapters, each headed as "Chapter N: <title>"
    - Plot twists to integrate organically:
    {twist_lines}
    - Ending mood/type: {cfg.ending_type}

    Output rules:
    1. Deliver only the story prose broken into the requested chapters.
    2. Keep voice, tone, and character motivations steady throughout.
    3. Avoid bullet lists, explanations, or meta commentary.
    4. Ensure every chapter advances the plot and reflects Maharashtrian context (places, festivals, idioms).
    5. Close with the specified ending mood without introducing new characters in the final paragraph.
    """
    return textwrap.dedent(template).strip()


def build_chapter_prompt(cfg: StoryConfig, chapter_number: int, previous_chapters: Sequence[str]) -> str:
    """Prompt for a single chapter while preserving previously generated context."""

    character_lines = "\n".join(f"- {c}" for c in cfg.characters) or "- Introduce 1-3 fitting characters but keep them stable once named."
    twist_lines = "\n".join(f"- {t}" for t in cfg.plot_twists) or "- Subtle reveal tied to family legacy"
    previous_text = "\n\n".join(previous_chapters).strip()
    if previous_text:
        history_block = f"Previously delivered chapters (do not rewrite them, only reference as needed):\n{previous_text}"
    else:
        history_block = "No chapters have been written yet."

    target_words = max(200, cfg.word_length // max(1, cfg.chapters))
    is_final = chapter_number == cfg.chapters

    template = f"""
    You are continuing an English-language Maharashtrian story. Maintain tone, pacing, and all factual details.

    Global story brief (apply to every chapter):
    - Core description: {cfg.story_description}
    - Characters to reuse consistently:
    {character_lines}
    - Genre: {cfg.genre}
    - Writing style: {cfg.writing_style}
    - Literary inspiration: {cfg.literature_inspiration}
    - Plot twists to weave across chapters:
    {twist_lines}
    - Ending mood/type: {cfg.ending_type}

    Previously written material:
    {history_block}

    Task:
    - Write Chapter {chapter_number} of {cfg.chapters}, roughly {target_words} words.
    - Begin with the heading "Chapter {chapter_number}: <concise title>".
    - Keep all characters' motivations, relationships, and cultural details consistent with earlier chapters.
    - Advance the plot meaningfully; reference earlier events naturally.
    - Avoid summarising past chapters verbatim.
    - {'Resolve all arcs with the specified ending mood.' if is_final else 'End with a natural beat that leads into the next chapter without cliffhangers that derail tone.'}

    Output only the prose for this chapter.
    """
    return textwrap.dedent(template).strip()


def _generate_story_sequential(
    cfg: StoryConfig,
    client: "GeminiClient",
    *,
    temperature: float,
    part_callback: Callable[[int, str], None] | None = None,
) -> str:
    previous: list[str] = []
    outputs: list[str] = []
    for chapter_number in range(1, cfg.chapters + 1):
        prompt = build_chapter_prompt(cfg, chapter_number, previous)
        part = client.generate_story(prompt, temperature).strip()
        outputs.append(part)
        previous.append(part)
        if part_callback:
            part_callback(chapter_number, part)
    return "\n\n".join(outputs)


def generate_story_text(
    cfg: StoryConfig,
    client: "GeminiClient",
    *,
    temperature: float,
    mode: str = "sequential",
    part_callback: Callable[[int, str], None] | None = None,
) -> str:
    """Generate a story either in one shot or chapter-by-chapter."""

    if mode == "single":
        prompt = build_prompt(cfg)
        story = client.generate_story(prompt, temperature).strip()
        if part_callback:
            part_callback(1, story)
        return story
    if mode != "sequential":
        raise ValueError("mode must be 'single' or 'sequential'")
    return _generate_story_sequential(cfg, client, temperature=temperature, part_callback=part_callback)


class GeminiClient:
    """Minimal wrapper around the Gemini REST endpoint."""

    def __init__(self, api_key: str | None, model: str) -> None:
        if not api_key:
            raise ValueError("Set GEMINI_API_KEY in your environment.")
        self.api_key = api_key
        self.model = model
        self.endpoint = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent"

    def generate_story(self, prompt: str, temperature: float) -> str:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "topP": 0.9,
                "maxOutputTokens": 4096,
            },
        }
        response = requests.post(
            self.endpoint,
            params={"key": self.api_key},
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected Gemini response: {json.dumps(data, indent=2)}") from exc


def load_config(path: str | None) -> StoryConfig:
    if not path:
        return prompt_user_for_config()
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    cfg = StoryConfig.from_dict(data)
    cfg.validate()
    return cfg


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Maharashtrian story with Gemini")
    parser.add_argument("--config", help="Path to JSON file containing story parameters")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini model name")
    parser.add_argument("--temperature", type=float, default=0.75, help="Sampling temperature")
    parser.add_argument("--output", help="File path to save the generated story")
    parser.add_argument("--dry-run", action="store_true", help="Print the prompt without calling Gemini")
    parser.add_argument(
        "--mode",
        choices=["sequential", "single"],
        default="sequential",
        help="Use chapter-by-chapter requests (default) or a single long request",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()
    try:
        cfg = load_config(args.config)
    except (OSError, ValueError) as err:
        print(f"Error loading config: {err}", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        if args.mode == "single":
            print(build_prompt(cfg))
        else:
            print(build_chapter_prompt(cfg, 1, []))
        return

    api_key = os.getenv("GEMINI_API_KEY")
    try:
        client = GeminiClient(api_key=api_key, model=args.model)
        story = generate_story_text(
            cfg,
            client,
            temperature=args.temperature,
            mode=args.mode,
        )
    except Exception as err:  # noqa: BLE001 - surface full context to user
        print(f"Failed to generate story: {err}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(story)
    print(story)


if __name__ == "__main__":
    main()
