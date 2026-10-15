# SPDX-License-Identifier: GPL-3.0-or-later
"""English (US) / Russian application text; other system locales fall back to English."""
from pathlib import Path
from PySide6.QtCore import QLocale, QCoreApplication, QTranslator, QLibraryInfo

LANGUAGE = 'en_US'
RU = {'\nTry a simpler query or open Google Images.': '\nУпростите запрос или откройте Google Картинки.',
 '0 selected · 0 cards': 'Выбрано: 0 · Карточек: 0',
 'Add': 'Добавить',
 'Add Image to Folder…': 'Добавить картинку в папку…',
 'Add Word Pair': 'Добавить пару слов',
 'Add Word Pair…': 'Добавить пару слов…',
 'Add two sides in any language. Only Georgian text gets Eka audio. Checked pairs are exported together with checked images.': 'Добавьте '
                                                                                                                               'две '
                                                                                                                               'стороны '
                                                                                                                               'на '
                                                                                                                               'любом '
                                                                                                                               'языке. '
                                                                                                                               'Eka '
                                                                                                                               'озвучивает '
                                                                                                                               'только '
                                                                                                                               'грузинский '
                                                                                                                               'текст. '
                                                                                                                               'Отмеченные '
                                                                                                                               'пары '
                                                                                                                               'экспортируются '
                                                                                                                               'вместе '
                                                                                                                               'с '
                                                                                                                               'отмеченными '
                                                                                                                               'картинками.',
 'Added {value0}. It is selected in Flashcards. Source and license credits saved.': 'Добавлено: {value0}. '
                                                                                    'Картинка отмечена для '
                                                                                    'экспорта. Источник и '
                                                                                    'лицензия сохранены.',
 'Apply': 'Применить',
 'Audio plays here. No audio file is saved.\nInternet required; text is sent to Microsoft’s speech service.': 'Звук '
                                                                                                              'воспроизводится '
                                                                                                              'здесь, '
                                                                                                              'без '
                                                                                                              'сохранения '
                                                                                                              'файла.\n'
                                                                                                              'Нужен '
                                                                                                              'интернет; '
                                                                                                              'текст '
                                                                                                              'отправляется '
                                                                                                              'в '
                                                                                                              'службу '
                                                                                                              'озвучки '
                                                                                                              'Microsoft.',
 'Back': 'Обратная сторона',
 'Back → Front': 'Обратная → Лицевая',
 'Both sides of every word pair must contain text.': 'Обе стороны каждой пары должны содержать текст.',
 'Both ↔': 'Оба ↔',
 'Build picture decks. Practice Georgian pronunciation.': 'Создавайте колоды и тренируйте грузинское '
                                                          'произношение.',
 'Cancel': 'Отмена',
 'Card Direction': 'Направление',
 'Card direction for {value0}': 'Направление карточки: {value0}',
 'Choose Folder for Downloaded Image': 'Выбрать папку для картинки',
 'Choose Folder…': 'Выбрать папку…',
 'Choose Image Folder': 'Выбрать папку с картинками',
 'Choose a folder to preview your images': 'Выберите папку для просмотра картинок',
 'Choose which images to include, then export.': 'Отметьте нужные картинки, затем экспортируйте колоду.',
 'Could Not Save Word Edits': 'Не удалось сохранить правки слов',
 'Could not add the image: {value0}': 'Не удалось добавить картинку: {value0}',
 'Could not download the Wikimedia image. Try another result.': 'Не удалось загрузить картинку Wikimedia. '
                                                                'Выберите другую.',
 'Could not generate speech. Check your internet connection and try again.': 'Не удалось создать озвучку. '
                                                                             'Проверьте интернет и повторите '
                                                                             'попытку.',
 'Could not prepare this image.': 'Не удалось подготовить картинку.',
 'Could not reach Wikimedia Commons. Check your connection and try again.': 'Wikimedia Commons недоступна. '
                                                                            'Проверьте интернет и повторите '
                                                                            'попытку.',
 'Could not synthesize “{value0}”. Check your internet connection or turn off audio. Details: {value1}': 'Не '
                                                                                                         'удалось '
                                                                                                         'озвучить '
                                                                                                         '«{value0}». '
                                                                                                         'Проверьте '
                                                                                                         'интернет '
                                                                                                         'или '
                                                                                                         'отключите '
                                                                                                         'звук. '
                                                                                                         'Подробности: '
                                                                                                         '{value1}',
 'Deck name': 'Название колоды',
 'Deselect All': 'Снять выделение',
 'Double-click either side to edit. Choose the direction directly in each row.': 'Двойной щелчок по стороне '
                                                                                 '— редактирование. '
                                                                                 'Направление выбирается '
                                                                                 'прямо в строке.',
 'Downloading selected image…': 'Загрузка выбранной картинки…',
 'Enter a deck name.': 'Введите название колоды.',
 'Enter a search query first.': 'Сначала введите поисковый запрос.',
 'Enter text on both sides of each selected pair.': 'Заполните обе стороны каждой отмеченной пары.',
 'Enter the search query first.': 'Сначала введите поисковый запрос.',
 'Every selected image needs a word.': 'У каждой отмеченной картинки должно быть слово.',
 'Export Anki Deck': 'Экспорт колоды Anki',
 'Export Anki Deck…': 'Экспортировать в Anki…',
 'Export Failed': 'Ошибка экспорта',
 'Export failed. Your existing deck was not replaced.': 'Ошибка экспорта. Существующая колода не изменена.',
 'Exported {value0} cards from {value1} entries. Import the .apkg file into Anki.': 'Экспортировано '
                                                                                    'карточек: {value0}, '
                                                                                    'записей: {value1}. '
                                                                                    'Импортируйте файл .apkg '
                                                                                    'в Anki.',
 'Filter by word or filename…': 'Поиск по слову или имени файла…',
 'Find Images…': 'Найти картинки…',
 'Find a picture for your word': 'Найдите картинку к слову',
 'Finishing deck…': 'Завершение экспорта…',
 'Flashcards': 'Картинки',
 'Front': 'Лицевая сторона',
 'Front → Back': 'Лицевая → Обратная',
 'Generating Eka pronunciation…': 'Подготовка озвучки Eka…',
 'Generating speech…': 'Подготовка озвучки…',
 'Georgian · Microsoft Eka': 'Грузинский · Microsoft Eka',
 'Image / Word': 'Картинка / Слово',
 'Image Search': 'Поиск картинок',
 'Image folder not found: {value0}': 'Папка с картинками не найдена: {value0}',
 'Image search query': 'Запрос для поиска картинок',
 'Image → Word': 'Картинка → Слово',
 'Images to include in the deck': 'Картинки для колоды',
 'Include Eka pronunciation': 'Добавить озвучку Eka',
 'Incomplete Word Pair': 'Незаполненная пара слов',
 'Interface language': 'Язык интерфейса',
 'Invalid Word': 'Некорректное слово',
 'Invalid directions in .anki-images.json': 'Некорректные направления в .anki-images.json',
 'Invalid image credits in .anki-images.json': 'Некорректные источники картинок в .anki-images.json',
 'Invalid word edits in .anki-images.json': 'Некорректные правки слов в .anki-images.json',
 'Invalid word-pair data': 'Некорректные данные пары слов',
 'Invalid word-pair identity or direction.': 'Некорректный идентификатор или направление пары слов.',
 'Invalid {value0} in .anki-images.json': 'Некорректное поле {value0} в .anki-images.json',
 'Listen with Eka': 'Послушать Eka',
 'No folder selected': 'Папка не выбрана',
 'No images to preview': 'Нет картинок для просмотра',
 'No supported images found in this folder.': 'В этой папке нет поддерживаемых картинок.',
 'Only HTTPS Wikimedia image URLs can be downloaded.': 'Можно загружать только HTTPS-картинки с Wikimedia.',
 'Only the image you choose is downloaded into your folder. Source and license credits are saved with it. Google Images opens your browser.': 'В '
                                                                                                                                              'папку '
                                                                                                                                              'загружается '
                                                                                                                                              'только '
                                                                                                                                              'выбранная '
                                                                                                                                              'картинка. '
                                                                                                                                              'Источник '
                                                                                                                                              'и '
                                                                                                                                              'лицензия '
                                                                                                                                              'сохраняются '
                                                                                                                                              'вместе '
                                                                                                                                              'с '
                                                                                                                                              'ней. '
                                                                                                                                              'Google '
                                                                                                                                              'Картинки '
                                                                                                                                              'открываются '
                                                                                                                                              'в '
                                                                                                                                              'браузере.',
 'Open Google Images': 'Открыть Google Картинки',
 'Open Source Page': 'Открыть источник',
 'Operation in Progress': 'Выполняется операция',
 'Other system languages use English (US).': 'Для остальных языков системы используется English (US).',
 'Play': 'Воспроизвести',
 'Playback failed: {value0}': 'Ошибка воспроизведения: {value0}',
 'Playing Eka pronunciation': 'Воспроизведение Eka',
 'Playing with Eka. No audio file is saved.': 'Воспроизведение Eka. Звуковой файл не сохраняется.',
 'Please wait for the current operation to finish before closing.': 'Перед закрытием дождитесь окончания '
                                                                    'текущей операции.',
 'Preparing deck…': 'Подготовка колоды…',
 'Preview unavailable for this image': 'Предпросмотр этой картинки недоступен',
 'Preview unavailable; you can open the source page.': 'Предпросмотр недоступен. Можно открыть страницу '
                                                       'источника.',
 'Processing {value0} of {value1}: {value2}': 'Обработка {value0} из {value1}: {value2}',
 'Ready': 'Готово',
 'Ready. Audio was played without saving a file.': 'Готово. Звук воспроизведён без сохранения файла.',
 'Remove': 'Удалить',
 'Remove Image?': 'Удалить картинку?',
 'Remove {value0} from this folder? This cannot be undone.': 'Удалить {value0} из этой папки? Это действие нельзя отменить.',
 'Could Not Remove Image': 'Не удалось удалить картинку',
 'Could Not Rename Image': 'Не удалось переименовать картинку',
 'Invalid Image Name': 'Некорректное имя картинки',
 'Image names cannot be empty.': 'Имя картинки не может быть пустым.',
 'Image names cannot contain path separators.': 'Имя картинки не может содержать разделители пути.',
 'An image named {value0} already exists.': 'Картинка с именем {value0} уже существует.',
 'Replace Existing Deck?': 'Заменить существующую колоду?',
 'Replace {value0}?': 'Заменить {value0}?',
 'Saved word pairs are unreadable. Resolve the saved data before adding new pairs.': 'Сохранённые пары слов '
                                                                                     'повреждены. Исправьте '
                                                                                     'сохранённые данные '
                                                                                     'перед добавлением '
                                                                                     'новых пар.',
 'Saved word pairs could not be read. They have not been overwritten.': 'Не удалось прочитать сохранённые '
                                                                        'пары слов. Исходные данные не '
                                                                        'изменены.',
 'Search Images': 'Найти картинки',
 'Search Wikimedia Commons. Your query is used exactly as entered; no translation or API key needed.': 'Поиск '
                                                                                                       'в '
                                                                                                       'Wikimedia '
                                                                                                       'Commons '
                                                                                                       'по '
                                                                                                       'введённому '
                                                                                                       'запросу, '
                                                                                                       'без '
                                                                                                       'перевода '
                                                                                                       'и '
                                                                                                       'API-ключей.',
 'Search in any language, e.g. animal or ცხოველი': 'Запрос на любом языке: например, животное или ცხოველი',
 'Search query': 'Поисковый запрос',
 'Searching Wikimedia Commons…': 'Поиск в Wikimedia Commons…',
 'Select All': 'Выделить все',
 'Select a folder to get started.': 'Выберите папку или добавьте пары слов.',
 'Select a result to preview it': 'Выберите результат для предпросмотра',
 'Select an image to edit its word': 'Выберите картинку для редактирования слова',
 'Select at least one image or word pair.': 'Отметьте хотя бы одну картинку или пару слов.',
 'Selected images must have unique filenames.': 'Имена выбранных картинок должны быть уникальны.',
 'Set each image’s direction in its row. Edited words are used for cards and speech.\nNew audio needs internet. Image files stay on your Mac.': 'Направление '
                                                                                                                                                'задаётся '
                                                                                                                                                'в '
                                                                                                                                                'строке '
                                                                                                                                                'каждой '
                                                                                                                                                'картинки. '
                                                                                                                                                'Исправленные '
                                                                                                                                                'слова '
                                                                                                                                                'используются '
                                                                                                                                                'для '
                                                                                                                                                'карточек '
                                                                                                                                                'и '
                                                                                                                                                'озвучки.\n'
                                                                                                                                                'Для '
                                                                                                                                                'новой '
                                                                                                                                                'озвучки '
                                                                                                                                                'нужен '
                                                                                                                                                'интернет. '
                                                                                                                                                'Картинки '
                                                                                                                                                'остаются '
                                                                                                                                                'на '
                                                                                                                                                'вашем '
                                                                                                                                                'Mac.',
 'Settings': 'Настройки',
 'Settings…': 'Настройки…',
 'Show in Finder': 'Показать в Finder',
 'Speech Unavailable': 'Озвучка недоступна',
 'Speech unavailable': 'Озвучка недоступна',
 'Stop': 'Стоп',
 'System': 'Как в системе',
 'Text Too Long': 'Слишком длинный текст',
 'Text to speak': 'Текст для озвучки',
 'The image was saved, but its credits could not be saved.': 'Картинка сохранена, но не удалось сохранить её '
                                                             'источники.',
 'The image was saved, but the folder could not be loaded.': 'Картинка сохранена, но не удалось открыть '
                                                             'папку.',
 'The output file must end in .apkg.': 'Выходной файл должен иметь расширение .apkg.',
 'The request timed out.': 'Время ожидания запроса истекло.',
 'The selected result is not an image.': 'Выбранный результат не является картинкой.',
 'The speech service returned empty audio': 'Сервис озвучки вернул пустой файл.',
 'The speech service returned no audio.': 'Сервис озвучки не вернул звук.',
 'The word cannot contain slashes or control characters.': 'Слово не должно содержать слеши или управляющие '
                                                           'символы.',
 'This image could not be decoded, or is too large. Choose another result.': 'Не удалось открыть картинку '
                                                                             'или она слишком большая. '
                                                                             'Выберите другую.',
 'This image is too large. Choose another result.': 'Картинка слишком большая. Выберите другую.',
 'Type or paste Georgian text here…': 'Введите или вставьте грузинский текст…',
 'Unable to Open Folder': 'Не удалось открыть папку',
 'Unable to Read Word Edits': 'Не удалось прочитать правки слов',
 'Unable to Save Word Pairs': 'Не удалось сохранить пары слов',
 'Unknown card direction.': 'Неизвестное направление карточки.',
 'Unknown per-image card direction.': 'Неизвестное направление карточки с картинкой.',
 'Unsupported .anki-images.json format. The existing file was not changed.': 'Неподдерживаемый формат '
                                                                             '.anki-images.json. Исходный '
                                                                             'файл не изменён.',
 'Use 200 characters or fewer per search query.': 'Поисковый запрос должен быть не длиннее 200 символов.',
 'Use 5,000 characters or fewer per playback.': 'Для одного воспроизведения используйте не более 5000 '
                                                'символов.',
 'Use a shorter query for the image filename.': 'Используйте более короткий запрос для имени картинки.',
 'Voice Studio': 'Озвучка',
 'Wait for the current operation to finish before changing the language.': 'Дождитесь окончания текущей '
                                                                           'операции перед сменой языка.',
 'Wait for the deck export to finish before adding an image.': 'Дождитесь окончания экспорта перед '
                                                               'добавлением картинки.',
 'Wikimedia could not process this search query.': 'Wikimedia не смогла обработать запрос.',
 'Wikimedia image search results': 'Результаты поиска Wikimedia',
 'Word Cards': 'Слова',
 'Word Too Long': 'Слишком длинное слово',
 'Word on card': 'Слово на карточке',
 'Word on selected card': 'Слово на выбранной карточке',
 'Word → Image': 'Слово → Картинка',
 'Word ↔ word cards': 'Карточки «слово ↔ слово»',
 'Your edits still apply for this session, but could not be saved: {value0}': 'Правки действуют в текущем '
                                                                              'сеансе, но не сохранены: '
                                                                              '{value0}',
 'e.g. water': 'например, вода',
 'e.g. წყალი': 'например, წყალი',
 '{count} images · Query: {query}': 'Картинок: {count} · Запрос: {query}',
 '{value0}\n\n{value1}\n{value2}\nSearch: {value3}': '{value0}\n\n{value1}\n{value2}\nЗапрос: {value3}',
 '{value0} images + {value1} word pairs · {value2} cards': 'Картинок: {value0} · Пар слов: {value1} · '
                                                           'Карточек: {value2}',
 '{value0} of {value1} selected · {value2} cards': 'Выбрано: {value0} из {value1} · Карточек: {value2}'}


def resolve_language(preference='system', system=None):
    if preference in ('ru', 'en_US'):
        return preference
    locale = system or QLocale.system().name()
    return 'ru' if locale.lower().split('_')[0].split('-')[0] == 'ru' else 'en_US'


def set_language(preference='system', system=None):
    global LANGUAGE
    LANGUAGE = resolve_language(preference, system)
    QLocale.setDefault(QLocale('ru_RU' if LANGUAGE == 'ru' else 'en_US'))
    app = QCoreApplication.instance()
    if app is not None:
        previous = getattr(app, '_qt_translation', None)
        if previous is not None:
            app.removeTranslator(previous)
            previous.deleteLater()
            app._qt_translation = None
        if LANGUAGE == 'ru':
            translator = QTranslator(app)
            path = Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)) / 'qtbase_ru.qm'
            if translator.load(str(path)):
                app.installTranslator(translator)
                app._qt_translation = translator
    return LANGUAGE


def tr(text):
    return RU.get(text, text) if LANGUAGE == 'ru' else text

RU.update({'Cards': 'Карточки', 'Card': 'Карточка', 'Text · {front} ↔ {back}': 'Текст · {front} ↔ {back}', 'Images and word pairs belong to this deck. Choose each card’s direction in its row.': 'Картинки и пары слов входят в эту колоду. Направление выбирается в строке каждой карточки.'})

RU['Choose a folder or add a word pair to get started.'] = 'Выберите папку или добавьте пару слов.'
