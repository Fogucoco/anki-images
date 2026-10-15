# SPDX-License-Identifier: GPL-3.0-or-later
"""Create an Anki deck from image filenames."""
import asyncio
import hashlib
import html
import logging
import os
import re
import time
from pathlib import Path
from typing import Callable
import shutil
import tempfile
import unicodedata
from i18n import tr
import genanki
import edge_tts
CACHE_DIR = Path.home() / 'Library' / 'Caches' / 'Anki Images' / 'audio'
EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'}
VOICE = 'ka-GE-EkaNeural'

def cleanup_audio_cache(cache: Path = CACHE_DIR, *, now: float | None = None) -> int:
    """Remove only owned audio files unused for more than 30 days."""
    cutoff = (time.time() if now is None else now) - 30 * 24 * 60 * 60
    removed = 0
    try:
        entries = list(cache.iterdir())
    except FileNotFoundError:
        return 0
    except OSError:
        logging.getLogger(__name__).warning('Could not read audio cache', exc_info=True)
        return 0
    for path in entries:
        if not re.fullmatch(r'anki_eka_[0-9a-f]{64}\.mp3', path.name):
            continue
        try:
            if not path.is_symlink() and path.is_file() and path.stat().st_mtime < cutoff:
                path.unlink()
                removed += 1
        except OSError:
            logging.getLogger(__name__).warning('Could not remove expired audio cache file', exc_info=True)
    return removed

def georgian_speech(text: str) -> str:
    return ' '.join(''.join((char if unicodedata.name(char, '').startswith('GEORGIAN') and unicodedata.category(char).startswith('L') else ' ' for char in text)).split())

async def generate_audio(text: str, destination: Path) -> None:
    for attempt in range(3):
        try:
            await asyncio.wait_for(edge_tts.Communicate(text, VOICE).save(str(destination)), timeout=60)
            if destination.stat().st_size == 0:
                raise RuntimeError(tr('The speech service returned empty audio'))
            return
        except Exception as error:
            if attempt == 2:
                raise RuntimeError(tr('Could not synthesize “{value0}”. Check your internet connection or turn off audio. Details: {value1}').format(value0=text, value1=error)) from error
            await asyncio.sleep(attempt + 1)

def audio_for(text: str, cache: Path) -> Path:
    cache.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(f'{VOICE}\x00{text}'.encode()).hexdigest()
    destination = cache / f'anki_eka_{key}.mp3'
    if destination.is_file() and destination.stat().st_size > 0:
        try:
            os.utime(destination, None)
        except OSError:
            logging.getLogger(__name__).warning('Could not refresh audio cache timestamp', exc_info=True)
        return destination
    with tempfile.TemporaryDirectory(dir=cache) as temporary:
        staging = Path(temporary) / 'audio.mp3'
        asyncio.run(generate_audio(text, staging))
        staging.replace(destination)
    return destination

def find_images(images: Path) -> list[Path]:
    if not images.is_dir():
        raise ValueError(tr('Image folder not found: {value0}').format(value0=images))
    return sorted((p for p in images.iterdir() if p.is_file() and (not p.name.startswith('.')) and (p.suffix.lower() in EXTENSIONS)), key=lambda p: p.name.casefold())

def build_files(files: list[Path], output: Path, name: str, audio: bool=True, cache: Path=CACHE_DIR, progress: Callable[[int, int, str], None] | None=None, words: dict[str, str] | None=None, direction: str='both', credits: dict[str, dict] | None=None, directions: dict[str, str] | None=None, word_pairs: list[dict] | None=None) -> int:
    word_pairs = word_pairs or []
    if not files and (not word_pairs):
        raise ValueError(tr('Select at least one image or word pair.'))
    for pair in word_pairs:
        if not pair.get('front', '').strip() or not pair.get('back', '').strip():
            raise ValueError(tr('Both sides of every word pair must contain text.'))
        if not pair.get('id') or pair.get('direction', 'both') not in ('both', 'forward', 'reverse'):
            raise ValueError(tr('Invalid word-pair identity or direction.'))
    if not name.strip():
        raise ValueError(tr('Enter a deck name.'))
    if output.suffix.lower() != '.apkg':
        raise ValueError(tr('The output file must end in .apkg.'))
    if len({p.name for p in files}) != len(files):
        raise ValueError(tr('Selected images must have unique filenames.'))
    if direction not in {'both', 'forward', 'reverse'}:
        raise ValueError(tr('Unknown card direction.'))
    words = words or {}
    labels = {p.name: words.get(p.name, p.stem).strip() for p in files}
    if any((not word for word in labels.values())):
        raise ValueError(tr('Every selected image needs a word.'))
    modes = {p.name: (directions or {}).get(p.name, direction) for p in files}
    if any((mode not in ('both', 'forward', 'reverse') for mode in modes.values())):
        raise ValueError(tr('Unknown per-image card direction.'))
    templates = [{'name': 'Word → image', 'qfmt': '{{Title}}', 'afmt': '{{Image}}'}, {'name': 'Image → word', 'qfmt': '{{Image}}', 'afmt': '{{Title}}'}]
    models = {}
    for mode in set(modes.values()):
        selected_templates = templates if mode == 'both' else [templates[0 if mode == 'forward' else 1]]
        models[mode] = genanki.Model({'both': 1834109276, 'forward': 1834109277, 'reverse': 1834109278}[mode], f'Filename to image ({mode})', fields=[{'name': 'Title'}, {'name': 'Image'}], templates=selected_templates, css='.card { font-family: Arial; font-size: 28px; text-align: center; } img { max-width: 100%; max-height: 80vh; }')
    deck_id = int.from_bytes(hashlib.sha256(name.encode()).digest()[:4], 'big') % (1 << 30) + (1 << 30)
    attribution = []
    for path in files:
        credit = (credits or {}).get(path.name)
        if credit:
            attribution.append('<p>' + html.escape(path.name) + ': ' + html.escape(credit.get('title', '')) + '<br>' + html.escape(credit.get('artist', '')) + '<br>' + html.escape(credit.get('license', '')) + '<br>' + html.escape(credit.get('license_url', '')) + '<br>' + html.escape(credit.get('source_url', '')) + '<br>' + html.escape(credit.get('changes', '')) + '</p>')
    deck = genanki.Deck(deck_id, name, description=''.join(attribution))
    with tempfile.TemporaryDirectory(prefix='anki-images-') as temporary:
        media = []
        added_audio = set()
        for index, path in enumerate(files):
            if progress:
                progress(index, len(files) + len(word_pairs), labels[path.name])
            key = hashlib.sha256(path.name.encode()).hexdigest()
            media_name = f'anki_image_{key}{path.suffix.lower()}'
            target = Path(temporary) / media_name
            shutil.copyfile(path, target)
            media.append(str(target))
            title = html.escape(labels[path.name])
            if audio:
                sound = audio_for(labels[path.name], cache)
                if sound not in added_audio:
                    media.append(str(sound))
                    added_audio.add(sound)
                title += f'<br>[sound:{sound.name}]'
            deck.add_note(genanki.Note(model=models[modes[path.name]], fields=[title, f'<img src="{media_name}">'], guid=genanki.guid_for(name, path.name) if modes[path.name] == 'both' else genanki.guid_for(name, path.name, modes[path.name])))
        text_models = {}
        for pair_index, pair in enumerate(word_pairs):
            mode = pair.get('direction', 'both')
            if mode not in text_models:
                text_templates = [{'name': 'Front → Back', 'qfmt': '{{Front}}', 'afmt': '{{Back}}'}, {'name': 'Back → Front', 'qfmt': '{{Back}}', 'afmt': '{{Front}}'}]
                if mode != 'both':
                    text_templates = [text_templates[0 if mode == 'forward' else 1]]
                text_models[mode] = genanki.Model({'both': 1934109276, 'forward': 1934109277, 'reverse': 1934109278}[mode], f'Word to word ({mode})', fields=[{'name': 'Front'}, {'name': 'Back'}], templates=text_templates, css='.card {font-family: Arial; font-size: 28px; text-align: center;}')
            if progress:
                progress(len(files) + pair_index, len(files) + len(word_pairs), pair['front'])
            fields = []
            for text in (pair['front'], pair['back']):
                field = html.escape(text.strip())
                spoken = georgian_speech(text)
                if audio and spoken:
                    sound = audio_for(spoken, cache)
                    if sound not in added_audio:
                        media.append(str(sound))
                        added_audio.add(sound)
                    field += f'<br>[sound:{sound.name}]'
                fields.append(field)
            deck.add_note(genanki.Note(model=text_models[mode], fields=fields, guid=genanki.guid_for(name, 'word-pair', pair['id'], mode)))
        output.parent.mkdir(parents=True, exist_ok=True)
        package = genanki.Package(deck)
        package.media_files = media
        with tempfile.TemporaryDirectory(dir=output.parent) as staging:
            archive = Path(staging) / 'deck.apkg'
            package.write_to_file(str(archive))
            archive.replace(output)
    if progress:
        progress(len(files) + len(word_pairs), len(files) + len(word_pairs), 'Complete')
    return len(files) + len(word_pairs)
