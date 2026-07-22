# AI System Rules & Guidelines

This document serves as the primary system rules for any AI agent working on the `JustSay` codebase.

## 1. UI/UX Design System
- **Wispr Flow Aesthetic**: JustSay aims for a highly polished, modern, premium UI inspired by Wispr Flow.
- **Key Elements**: Use glassmorphism (frosted glass), deep dark backgrounds (`#09090b`), soft rounded corners (`24px` for large cards), and glowing accents (`#3b82f6`).
- **Typography**: `Inter` is the primary font. Use it for a clean, legible, and professional look.

## 2. Versioning
- **IMPORTANT**: The dashboard sidebar contains a version tag (currently `v13`). **Whenever you implement a fix, update, or feature**, you MUST increment this version number in `server.py` and document the change.

## 3. Architecture Overview
- `server.py`: Flask backend serving the modern web UI dashboard.
- `main.py`: The entry point that orchestrates the transcriber, recorder, widget, and server.
- `widget.py`: PyQt6 floating widget that displays a sleek, glowing orb when recording.
- `transcriber.py`: Uses `faster_whisper` to transcribe audio locally.
- `database.py`: SQLite db handling history, dictionary, prompts, and settings.

## 4. Development Workflow
- When writing Python code, maintain thread-safety (especially with multiprocessing Queues).
- Keep all processing entirely offline/local. No external APIs should receive the audio data.
