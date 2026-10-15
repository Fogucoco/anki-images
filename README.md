# Anki Images

![Anki Images app icon](assets/app-icon.png)

A macOS desktop app for creating Anki decks from pictures and word pairs, with Georgian pronunciation by Microsoft Eka.

> This app is fully vibecoded.

## Features

- One card list for images and text pairs, with checkboxes, filtering, previews, and inline direction selectors.
- Editing an image caption renames its file; text cards support independent front/back text.
- Export checked entries together into one `.apkg` deck. Choose forward, reverse, or both directions per entry.
- Find pictures on Wikimedia Commons, preview results, and import selected images with source/license credits. Search uses the query as entered; there is no automatic translation.
- Separate Voice Studio for immediate playback without saving audio files.
- English and Russian interfaces.

## Install

Use `Anki Images.dmg` from a release or build it below. Open the disk image and drag **Anki Images.app** onto **Applications**.

The current build targets **Apple Silicon and macOS 14+**. Builds are ad-hoc signed, without Apple notarization or a Developer ID certificate; macOS may require explicit permission to open them. Python is bundled in the app.

## Create a deck

1. In **Cards**, choose an image folder and/or click **Add Word Pair…**.
2. Uncheck unwanted entries; set each row's direction. Select a row to edit its text in the preview panel.
3. Set one deck name and optionally include Eka pronunciation.
4. Click **Export Anki Deck…**, save the `.apkg`, and import it into Anki.

Supported image extensions: JPG, JPEG, PNG, GIF, WEBP, SVG, BMP. Hidden files and subfolders are skipped. Select All / Deselect All affect both image and text entries, including filtered-out rows.

Changing an image caption renames its file in the chosen folder while preserving its extension; directions and imported-image credits are stored in `.anki-images.json`. The Remove button deletes the selected image file after confirmation, or removes a selected text pair. Text pairs are stored in the readable UTF-8 file `word-cards.json` beside the images, separately for each folder. Before choosing a folder, pairs exist only for the current session. Old pairs in macOS preferences are ignored and left untouched. Interface preferences remain in macOS application preferences. Download name collisions receive numbered filenames. Export replaces an existing destination only after successful package generation.

For text-only cards, Eka synthesizes **only Georgian letters** on either side; English/Russian text is silent. Deck audio is cached in `~/Library/Caches/Anki Images/audio`. Cached speech unused for more than 30 days is removed in the background at app startup; reusing a cached file refreshes its timestamp. Voice Studio uses memory only. New synthesis requires internet and sends text to Microsoft's speech service through the unofficial edge-tts client. Images are not sent for synthesis. Wikimedia search sends the query to Wikimedia; Google Images opens the query in your browser.

Keep deck names and entry identities unchanged to update existing notes. Changing a direction mode creates a distinct note identity; importing a new package does not remove cards already in Anki. Keep a backup when updating an existing collection.

## Run from source

Requires Python 3.10+ and macOS 14+ with the pinned Qt dependencies.

```bash
./start.sh
```

No arguments are accepted: this launcher runs the desktop app only. It creates/reuses `.venv`, installs runtime dependencies when the manifest changes, and runs the environment's Python. First setup needs internet.

## Test

```bash
.venv/bin/python -m unittest discover -s tests
```

`-m unittest` runs Python's standard-library test runner; `discover` finds tests; `-s tests` chooses the test directory. GUI tests run offscreen with temporary settings and folders. Live network synthesis is mocked in unit tests.

## Build app and DMG

On an Apple Silicon Mac:

```bash
./build.sh
```

The script installs build dependencies, runs tests, builds the app with **PyInstaller**, then creates a compressed disk image with macOS **hdiutil**. Outputs:

- `dist/Anki Images.app`
- `dist/Anki Images.dmg`, showing only the app and an Applications shortcut for drag-and-drop installation. The README is inside the app bundle at `Contents/Resources/Documentation`; licenses are in `Contents/Resources/licenses`.

`assets/app-icon.png` is the icon source; `tools/build_assets.py` generates its macOS icon sizes with Qt and packages them with `iconutil`. Finder icon positions are set with `ds-store`, without scripting Finder. `tools/package_dmg.py` embeds the same icon in the mounted volume and applies it to the local DMG file. Volume icons survive downloads; the DMG file's Finder icon uses macOS metadata that HTTP downloads may discard. Packaging requires Apple Command Line Tools (`iconutil`, `SetFile`, and `Rez`).

`AnkiImages.spec` defines packaging, bundle metadata, and the arm64 target. Intermediates and caches live under `work/`. Previous `.app` build artifacts are replaced; the previous DMG is replaced only after a new image is created successfully. `dist/`, `work/`, `.venv/`, personal images, and exported decks are ignored by Git.

## License

Copyright (C) 2026 Sergei Maliuk. Licensed under **GNU GPL v3 or later**; see [LICENSE](LICENSE). Third-party dependencies and downloaded images retain their own licenses. Image credits are retained in project metadata and exported deck descriptions.
