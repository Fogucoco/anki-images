# SPDX-License-Identifier: GPL-3.0-or-later
from i18n import tr
'Wikimedia Commons image search and downloads.'
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import html
from itertools import zip_longest
import re
from urllib.parse import urlparse
import requests
HEADERS = {'User-Agent': 'AnkiImages/2.0 (personal vocabulary image search)'}

@dataclass
class ImageResult:
    title: str
    source_url: str
    image_url: str
    thumbnail: bytes
    thumbnail_url: str
    artist: str
    license: str
    license_url: str
    query: str

    def credit(self):
        return {'title': self.title, 'source_url': self.source_url, 'artist': self.artist, 'license': self.license, 'license_url': self.license_url, 'changes': 'Wikimedia thumbnail converted to PNG for the card.'}

def plain(value):
    return html.unescape(re.sub('<[^>]*>', '', value or '')).strip()

def image_bytes(url, limit=20 * 1024 * 1024):
    host = urlparse(url).hostname or ''
    if urlparse(url).scheme != 'https' or not (host == 'wikimedia.org' or host.endswith('.wikimedia.org')):
        raise ValueError(tr('Only HTTPS Wikimedia image URLs can be downloaded.'))
    try:
        with requests.get(url, headers=HEADERS, timeout=(10, 20), stream=True) as response:
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '').split(';')[0]
            if not content_type.startswith('image/'):
                raise ValueError(tr('The selected result is not an image.'))
            data = bytearray()
            for part in response.iter_content(64 * 1024):
                data.extend(part)
                if len(data) > limit:
                    raise ValueError(tr('This image is too large. Choose another result.'))
            return bytes(data)
    except requests.RequestException:
        raise RuntimeError(tr('Could not download the Wikimedia image. Try another result.')) from None

def search_one(query):
    try:
        response = requests.get('https://commons.wikimedia.org/w/api.php', headers=HEADERS, params={'action': 'query', 'format': 'json', 'generator': 'search', 'gsrsearch': query + ' filetype:bitmap', 'gsrnamespace': 6, 'gsrlimit': 10, 'prop': 'imageinfo', 'iiprop': 'url|extmetadata|mime', 'iiurlwidth': 960}, timeout=(10, 25))
        response.raise_for_status()
        data = response.json()
        if 'error' in data:
            raise RuntimeError(tr('Wikimedia could not process this search query.'))
        return sorted(data.get('query', {}).get('pages', {}).values(), key=lambda p: p.get('index', 0))
    except requests.RequestException:
        raise RuntimeError(tr('Could not reach Wikimedia Commons. Check your connection and try again.')) from None

def search_images(query):
    queries = [query.strip()] if query.strip() else []
    pages = []
    groups = []
    errors = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [(q, pool.submit(search_one, q)) for q in queries]
        for query, future in futures:
            try:
                groups.append([(query, p) for p in future.result()])
            except Exception as error:
                errors.append(f'{query}: {error}')
    for group in zip_longest(*groups):
        pages.extend((page for page in group if page is not None))
    seen = set()
    results = []
    for query, page in pages:
        info = (page.get('imageinfo') or [{}])[0]
        if not info.get('mime', '').startswith('image/') or page['title'] in seen:
            continue
        seen.add(page['title'])
        meta = info.get('extmetadata', {})

        def value(key):
            return plain(meta.get(key, {}).get('value', ''))
        results.append(ImageResult(page['title'].removeprefix('File:'), info.get('descriptionurl', ''), info.get('thumburl', info.get('url', '')), b'', info.get('thumburl', info.get('url', '')), value('Artist'), value('LicenseShortName'), value('LicenseUrl'), query))

    def thumbnail(result):
        try:
            result.thumbnail = image_bytes(result.thumbnail_url, 5 * 1024 * 1024)
        except Exception:
            pass
        return result
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(thumbnail, results))
    return (results, errors)
