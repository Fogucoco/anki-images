# Repository Guidelines

## Structure and Architecture

This repository contains the macOS desktop app only. `app.py` owns the unified card list, settings, playback, and background tasks. `deck_builder.py` generates Anki packages and cached Eka audio; it is a library, not a console entry point. `word_cards.py` manages text pairs in the same list. `search_ui.py` and `search_service.py` implement Wikimedia search/import. `i18n.py` contains English (US)/Russian localization. Tests live in `tests/`.

Keep personal media and exports out of Git. Use `work/` for temporary files and caches and `dist/` for release artifacts. Preserve existing user images and application preferences.

## Development and Packaging

Run `./start.sh` without arguments to create/reuse `.venv`, install runtime dependencies, and open the GUI. Do not restore the removed command-line exporter.

Run `.venv/bin/python -m unittest discover -s tests` for tests: `-m unittest` invokes Python's test runner; `discover` finds tests; `-s tests` selects the directory. Tests must use explicit temporary INI settings, not native user preferences.

Run `./build.sh` on Apple Silicon macOS 14+ to install build dependencies, run tests, and produce `dist/Anki Images.app` and `dist/Anki Images.dmg`. Packaging is defined by `AnkiImages.spec` and `tools/package_dmg.py`; the script uses PyInstaller and hdiutil. Preserve the embedded volume icon and local DMG Finder icon. Existing build artifacts are replaced. The app is ad-hoc signed, not notarized.

## Code and Interface

Use four-space indentation, snake_case functions/variables, PascalCase classes, and pathlib paths. No formatter is configured. Keep network access and deck generation off the GUI thread. Preserve native macOS file dialogs.

Localize interface text through `i18n.py`. System Russian maps to Russian; all other system locales fall back to English (US). Retain the manual language override. Tab order: Cards, Image Search, Voice Studio. Images and text pairs share selection, filtering, per-row directions, and one export.

## Validation and Contributions

Add unittest regression tests for meaningful behavior changes. Check mixed exports, Georgian-only text-pair audio, stable identities, cache reuse, failure handling, and language switching. Inspect generated notes/cards/media and visually verify UI changes.

Use imperative commit subjects. PRs should describe behavior, tests, and limitations, link applicable issues, and include screenshots for UI changes. Do not commit credentials, generated bundles, environments, caches, or personal media. Retain image attribution, bound network requests with timeouts, and replace exports atomically.

## License and Documentation

Project code is GPL-3.0-or-later. Preserve third-party licenses. Keep README.md synchronized with current behavior and build commands.

Store text pairs in UTF-8 `word-cards.json` inside the selected image folder. Keep folders independent; never read or migrate old pairs from native preferences automatically. Preserve interface preferences and existing user files.

Keep only the approved `assets/app-icon.png`; generate ICNS during the build. DMG root contains only the app and Applications shortcut; documents belong inside the bundle. Audio cache cleanup removes only owned MP3s unused for over 30 days, in a background task at startup.
