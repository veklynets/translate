# refactored_translator.py
# Для роботи програми потрібно встановити додаткові бібліотеки:
# pip install google-cloud-translate gTTS pygame pytesseract pillow mss colorama

import os
import sys
import contextlib
import datetime
from typing import Dict, Optional
import pygame
import pytesseract
from PIL import Image
import mss
import tkinter as tk
from google.cloud import translate_v2 as translate
from gtts import gTTS
from colorama import init as colorama_init, Fore, Style
from joustick import JoystickHandler


# --- РОЗШИРЕНА ЛОГІКА ВИЗНАЧЕННЯ РОЗКЛАДКИ (тільки для Windows) ---
IS_WINDOWS = os.name == 'nt'
WINDOWS_LAYOUT_DETECTION = False
if IS_WINDOWS:
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        user32.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
        user32.GetKeyboardLayout.restype = wintypes.HKL
        user32.GetKeyboardLayout.argtypes = (wintypes.DWORD,)
        WINDOWS_LAYOUT_DETECTION = True
    except (ImportError, OSError):
        print(f"{Fore.YELLOW}Попередження: Не вдалося завантажити Windows API через ctypes.")
else:
    print(f"{Fore.YELLOW}Попередження: Автоматичне визначення розкладки працює тільки на Windows.")

# --- КОНФІГУРАЦІЯ ТА КОНСТАНТИ ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
# ОПТИМІЗАЦІЯ: "Магічні числа" винесено в константи
LANG_ID_UKRAINIAN = 0x0422
LANG_ID_ENGLISH_US = 0x0409
LANG_ID_ENGLISH_UK = 0x0809

class TerminalTranslator:
    """
    Клас, що інкапсулює логіку термінального перекладача,
    включаючи OCR, озвучення та авто-визначення мови вводу.
    """

    def __init__(self):
        colorama_init(autoreset=True)
        self.NEUTRAL_COLOR = Fore.LIGHTBLUE_EX

        # --- Налаштування стану ---
        self.translate_client: Optional[translate.Client] = None
        self.sound_enabled: bool = False
        self.selected_monitor: Optional[Dict] = None
        # ОПТИМІЗАЦІЯ: Зберігаємо індекс монітора для швидкого доступу
        self.selected_monitor_idx: Optional[int] = None
        self.last_target_lang: Optional[str] = None
        self.last_english_text: Optional[str] = None
        self.log_file_path: Optional[str] = None

        # --- Налаштування команд ---
        self.commands = {
            "HELP#": self._show_help,
            "SOUND#": self._speak_last_text,
            "SCR#": self._handle_ocr_and_translate,
            "SET_MONITOR#": self._select_monitor_interactive,
            "SET_SOUND#": self._toggle_sound,
            "EXIT#": self._exit,
        }

    @staticmethod
    def _get_keyboard_language() -> Optional[str]:
        """Визначає мову розкладки клавіатури для активного вікна."""
        if not WINDOWS_LAYOUT_DETECTION:
            return None
        try:
            hwnd = user32.GetForegroundWindow()
            if hwnd == 0: return None
            thread_id = user32.GetWindowThreadProcessId(hwnd, None)
            layout_handle = user32.GetKeyboardLayout(thread_id)
            lang_id = layout_handle & 0xFFFF

            # ОПТИМІЗАЦІЯ: Використання констант
            if lang_id == LANG_ID_UKRAINIAN:
                return 'uk'
            elif lang_id in [LANG_ID_ENGLISH_US, LANG_ID_ENGLISH_UK]:
                return 'en'
            return None
        except Exception:
            return None

    def _setup_dependencies(self) -> bool:
        if 'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ:
            print(f"{Fore.RED}{'='*50}")
            print("!!! ПОМИЛКА: Не знайдено ключ доступу до Google Cloud. !!!")
            print("Будь ласка, встановіть змінну середовища GOOGLE_APPLICATION_CREDENTIALS.")
            print(f"{'='*50}")
            return False
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        if not os.path.exists(TESSERACT_PATH):
            print(f"{Fore.RED}ПОПЕРЕДЖЕННЯ: Tesseract OCR не знайдено: {TESSERACT_PATH}")
        try:
            self.translate_client = translate.Client()
        except Exception as e:
            print(f"{Fore.RED}Не вдалося ініціалізувати клієнт Google Translate: {e}")
            return False
        return True

    def _setup_logging(self):
        os.makedirs(LOG_DIR, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file_path = os.path.join(LOG_DIR, f"{timestamp}.txt")
        print(f"{self.NEUTRAL_COLOR}Лог-файл сесії: {self.log_file_path}")

    def _log_event(self, text: str):
        if not self.log_file_path: return
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {text}\n")
        except IOError as e:
            print(f"{Fore.RED}Не вдалося записати до лог-файлу: {e}")

    def _translate_text(self, text: str, target_language: str) -> Optional[str]:
        if not self.translate_client:
            print(f"{Fore.RED}Клієнт для перекладу не ініціалізовано.")
            return None
        try:
            self._log_event(f"TRANSLATE ({target_language}): {text}")
            result = self.translate_client.translate(text, target_language=target_language)
            translated = result['translatedText']
            self._log_event(f"RESULT ({target_language}): {translated}")
            return translated
        except Exception as e:
            print(f"\n{Fore.RED}--- Помилка API ---: {e}")
            return None

    @staticmethod
    def _speak_text(text: str, lang: str):
        temp_audio_file = os.path.join(SCRIPT_DIR, "temp_audio.mp3")
        try:
            tts = gTTS(text=text, lang=lang)
            tts.save(temp_audio_file)
            with open(os.devnull, "w") as devnull, contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
                pygame.mixer.init()
            pygame.mixer.music.load(temp_audio_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            print(f"\n{Fore.RED}--- Помилка озвучення ---: {e}")
        finally:
            if pygame.mixer.get_init():
                pygame.mixer.music.unload()
                pygame.mixer.quit()
            if os.path.exists(temp_audio_file):
                os.remove(temp_audio_file)

    def _select_monitor_interactive(self):
        with mss.mss() as sct:
            monitors = sct.monitors[1:]
            if not monitors:
                print(f"{Fore.RED}Не знайдено доступних моніторів.")
                return

            # ОПТИМІЗАЦІЯ: Логіка визначення назви монітора через словник
            def sign(x):
                return 0 if x == 0 else -1 if x < 0 else 1

            monitor_positions = {
                (0, 0): "основний", (0, -1): "зверху", (-1, -1): "зверху та зліва",
                (-1, 0): "зліва", (1, 0): "зправа", (1, -1): "зверху та зправа",
                (0, 1): "знизу", (-1, 1): "знизу та зліва", (1, 1): "знизу та зправа",
            }
            def monitor_name(mon):
                pos_key = (sign(mon['left']), sign(mon['top']))
                return monitor_positions.get(pos_key, f"({mon['left']},{mon['top']})")

            print(f"{self.NEUTRAL_COLOR}Доступні монітори:")
            for i, mon in enumerate(monitors, 1):
                coords = {k: mon[k] for k in ('left', 'top')}
                name = monitor_name(mon)
                print(f"{self.NEUTRAL_COLOR}{i}: {coords} [{name}]")
            try:
                default_idx = 2 if len(monitors) >= 3 else 0
                choice = input(f"{self.NEUTRAL_COLOR}Виберіть номер монітора (1-{len(monitors)}), Enter для {default_idx+1}: ")
                mon_idx = int(choice or str(default_idx + 1)) - 1
                if not 0 <= mon_idx < len(monitors): raise ValueError
                
                # ОПТИМІЗАЦІЯ: Зберігаємо і монітор, і його індекс
                self.selected_monitor = monitors[mon_idx]
                self.selected_monitor_idx = mon_idx + 1
            except (ValueError, IndexError):
                print(f"{Fore.RED}Невірний вибір, використовується монітор {default_idx+1}.")
                self.selected_monitor = monitors[default_idx]
                self.selected_monitor_idx = default_idx + 1

        coords = {k: self.selected_monitor[k] for k in ('left', 'top')}
        name = monitor_name(self.selected_monitor)
        print(f"{self.NEUTRAL_COLOR}Обрано монітор: {self.selected_monitor_idx} {coords} [{name}]")
        self._log_event(f"SET_MONITOR: {self.selected_monitor}")


    def _grab_and_ocr(self) -> Optional[str]:
        if not self.selected_monitor:
            print(f"{Fore.YELLOW}Монітор не вибрано. Спочатку виберіть його.")
            self._select_monitor_interactive()
            if not self.selected_monitor: return None
        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes('-alpha', 0.3)
        root.geometry(f"{self.selected_monitor['width']}x{self.selected_monitor['height']}+{self.selected_monitor['left']}+{self.selected_monitor['top']}")
        root.attributes('-topmost', True)
        canvas = tk.Canvas(root, cursor="cross", bg="grey")
        canvas.pack(fill=tk.BOTH, expand=True)
        coords = {"start_x": 0, "start_y": 0, "end_x": 0, "end_y": 0}
        rect = None
        def on_mouse_down(event): nonlocal rect; coords["start_x"], coords["start_y"] = event.x, event.y; rect = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline='red', width=2)
        def on_mouse_move(event):
            if rect: canvas.coords(rect, coords["start_x"], coords["start_y"], event.x, event.y)
        def on_mouse_up(event): coords["end_x"], coords["end_y"] = event.x, event.y; root.quit()
        canvas.bind("<ButtonPress-1>", on_mouse_down)
        canvas.bind("<B1-Motion>", on_mouse_move)
        canvas.bind("<ButtonRelease-1>", on_mouse_up)
        print("Виділіть область екрану для розпізнавання...")
        root.mainloop()
        root.destroy()
        x1, y1 = min(coords["start_x"], coords["end_x"]), min(coords["start_y"], coords["end_y"])
        x2, y2 = max(coords["start_x"], coords["end_x"]), max(coords["start_y"], coords["end_y"])
        if x2 - x1 < 10 or y2 - y1 < 10: print("Область не виділена або занадто мала."); return None
        bbox = {"left": self.selected_monitor['left'] + x1, "top": self.selected_monitor['top'] + y1, "width": x2 - x1, "height": y2 - y1}
        try:
            with mss.mss() as sct:
                sct_img = sct.grab(bbox)
                img = Image.frombytes('RGB', sct_img.size, sct_img.rgb)
            text = pytesseract.image_to_string(img, lang='eng+ukr').strip()
            print(f"{Fore.CYAN}{text}")
            self._log_event(f"OCR RESULT: {text}")
            return text
        except Exception as e: print(f"{Fore.RED}Помилка під час OCR: {e}"); return None

    def _show_help(self):
        print(f"{Fore.GREEN}\n--- Простий термінальний перекладач (UA ↔ EN) ---")
        print(f"{self.NEUTRAL_COLOR}Напрямок перекладу визначається АВТОМАТИЧНО за розкладкою клавіатури.")
        print(f"{self.NEUTRAL_COLOR}Розкладка УКР → переклад на англійську. Розкладка ENG → на українську.")
        print(f"{self.NEUTRAL_COLOR}Щоб примусово задати напрямок для одного запиту, використовуйте 'UA#: ...' або 'EN#: ...'")
        print(f"{Fore.CYAN}SOUND# {Style.RESET_ALL}- озвучити останній англійський переклад.")
        print(f"{Fore.CYAN}SCR# {Style.RESET_ALL}- захопити область екрану, розпізнати та перекласти текст.")
        print(f"{Fore.MAGENTA}SET_MONITOR# {Style.RESET_ALL}- вибрати інший монітор для OCR.")
        print(f"{Fore.MAGENTA}SET_SOUND# {Style.RESET_ALL}- увімкнути/вимкнути озвучення.")
        print(f"{self.NEUTRAL_COLOR}Для виходу введіть 'EXIT#'.\n")
        self._log_event("COMMAND: HELP#")

    def _speak_last_text(self):
        if self.last_english_text:
            print(f"{Fore.CYAN}Озвучуємо: '{self.last_english_text}'...")
            self._speak_text(self.last_english_text, 'en')
            self._log_event("COMMAND: SOUND#")
        else:
            print(f"{Fore.RED}Немає англійського тексту для озвучення.")

    def _handle_ocr_and_translate(self):
        self._log_event("COMMAND: SCR#")
        ocr_text = self._grab_and_ocr()
        if ocr_text: self._process_translation(ocr_text)

    def _toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        status = "УВІМКНЕНО" if self.sound_enabled else "ВИМКНЕНО"
        print(f"{self.NEUTRAL_COLOR}Режим озвучення: {status}")
        self._log_event(f"COMMAND: SET_SOUND# -> {status}")

    def _set_translation_direction(self, target_lang: str):
        self.last_target_lang = target_lang

    def _get_prompt(self) -> str:
        # ОПТИМІЗАЦІЯ: Миттєве отримання індексу монітора
        mon_idx_str = f"D{self.selected_monitor_idx}" if self.selected_monitor_idx else "D?"
        sound_str = "S" if self.sound_enabled else "M"
        if self.last_target_lang == 'en':
            dir_str, prompt_color = "УКР", Fore.YELLOW
        elif self.last_target_lang == 'uk':
            dir_str, prompt_color = "ENG", Fore.CYAN
        else:
            return f"{self.NEUTRAL_COLOR}Встановіть розкладку клавіатури (UA/EN): "
        return f"{prompt_color}[{mon_idx_str}:{sound_str}] {dir_str}#> {Style.RESET_ALL}"

    def _exit(self):
        print(f"\n{Fore.GREEN}До побачення!")
        sys.exit(0)

    def _process_translation(self, text: str):
        if not self.last_target_lang:
            print(f"{Fore.RED}Не вдалося визначити напрямок. Встановіть розкладку клавіатури на UA або EN.")
            return
        translated_text = self._translate_text(text, self.last_target_lang)
        if translated_text:
            print(f"{Fore.GREEN}-> {translated_text}{Style.RESET_ALL}", end="\n")
            if self.last_target_lang == 'en':
                self.last_english_text = translated_text
                if self.sound_enabled: self._speak_text(translated_text, 'en')
            else:
                self.last_english_text = text
                if self.sound_enabled: self._speak_text(text, 'en')

    def run(self):
        if not self._setup_dependencies(): return
        self._setup_logging()
        self._select_monitor_interactive()
        
        handler = None
        prev_b1_state = None
        try:
            handler = JoystickHandler()
            handler.start()
            joystick = handler
        except Exception as e:
            print(f"{Fore.YELLOW}JoystickHandler не ініціалізовано: {e}")
            joystick = None

        # --- ДОДАНО: неблокуючий цикл для джойстика і вводу ---
        import msvcrt
        import time

        buffer = ''
        last_prompt = None  # ДОДАНО: для контролю дублювання prompt
        while True:
            try:
                # --- Джойстик SOUND# ---
                if joystick is not None and hasattr(joystick, "state"):
                    state = joystick.state
                    if state:
                        b1 = state.get('B1')
                        if prev_b1_state == 'B1D' and b1 == 'B1U':
                            print(f"{Fore.LIGHTBLUE_EX}[Джойстик] SOUND#")
                            self._speak_last_text()
                        prev_b1_state = b1

                detected_lang = self._get_keyboard_language()
                if detected_lang == 'uk': self._set_translation_direction('en')
                elif detected_lang == 'en': self._set_translation_direction('uk')

                prompt = self._get_prompt()
                # --- Не друкувати prompt якщо не визначено напрямок ---
                if "Встановіть розкладку клавіатури" in prompt:
                    if buffer == '' and last_prompt != prompt:
                        print(prompt, end='', flush=True)
                        last_prompt = prompt
                    time.sleep(0.1)
                    continue

                # --- ДОДАНО: не друкувати prompt якщо не змінився ---
                if buffer == '' and last_prompt != prompt:
                    print(prompt, end='', flush=True)
                    last_prompt = prompt

                user_input = ''
                start = time.time()
                while time.time() - start < 0.1:
                    if msvcrt.kbhit():
                        char = msvcrt.getwche()
                        if char in ('\r', '\n'):
                            user_input = buffer
                            buffer = ''
                            print()
                            break
                        elif char == '\003':
                            raise KeyboardInterrupt
                        elif char == '\b':
                            buffer = buffer[:-1]
                            print('\b \b', end='', flush=True)
                        else:
                            buffer += char
                    else:
                        time.sleep(0.01)

                if not user_input:
                    continue

                # Пріоритет 1: Примусовий напрямок через префікс
                if user_input.upper().startswith("UA#:") or user_input.upper().startswith("EN#:"):
                    prefix, payload = user_input.split(":", 1)
                    target_lang = 'en' if prefix.upper() == "UA#" else 'uk'
                    self._set_translation_direction(target_lang)
                    self._process_translation(payload.strip())
                    continue

                # Пріоритет 2: Перевірка на стандартні команди (тільки якщо повний збіг)
                if user_input.upper() in self.commands:
                    self.commands[user_input.upper()]()
                    continue

                # Пріоритет 3: Якщо це схоже на команду (одне слово + #), але не зарезервовано — помилка
                stripped = user_input.strip()
                cmd_part = stripped.split('#', 1)[0]
                if (
                    len(stripped) > 1 and
                    '#' in stripped and
                    stripped.upper().endswith('#') and
                    cmd_part.replace('_', '').isalnum() and
                    stripped.upper() not in self.commands
                ):
                    print(f"{Fore.RED}Невідома команда: {cmd_part}#")
                    continue

                # Пріоритет 4: Якщо це не команда - перекладаємо
                self._process_translation(user_input)

            except (KeyboardInterrupt, EOFError):
                self._exit()
            except Exception as e:
                print(f"{Fore.RED}Сталася неочікувана помилка: {e}")
                self._log_event(f"UNEXPECTED ERROR: {e}")
                # --- Виправлено: не викликати self._process_translation(user_input) якщо user_input не визначено ---

if __name__ == "__main__":
    translator = TerminalTranslator()
    translator.run()
