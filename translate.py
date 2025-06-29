# translator.py
# -*- coding: utf-8 -*-
# Для роботи програми потрібно встановити додаткові бібліотеки:
# pip install google-cloud-translate gTTS pygame pytesseract pillow mss colorama pyjoystick

import os
import sys
import contextlib
import datetime
import io
import shutil
import tkinter as tk
from typing import Dict, Optional, Tuple

import mss
import pygame
import pytesseract
from PIL import Image
from colorama import Fore, Style, init as colorama_init
from gtts import gTTS
from google.cloud import translate_v2 as translate

# Імпортуємо ваш клас з файлу joustick.py
from joustick import JoystickHandler

# --- ЛОГІКА ВИЗНАЧЕННЯ РОЗКЛАДКИ (тільки для Windows) ---
IS_WINDOWS = os.name == 'nt'
WINDOWS_API_AVAILABLE = False
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
        import msvcrt
        WINDOWS_API_AVAILABLE = True
    except (ImportError, OSError):
        print(f"{Fore.YELLOW}Попередження: Не вдалося завантажити Windows API.")
else:
    print(f"{Fore.YELLOW}Попередження: Авто-визначення розкладки та джойстик працюють тільки на Windows.")


class Config:
    """Клас для зберігання конфігурації та констант."""
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
    TESSERACT_PATH = shutil.which('tesseract') or r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    LANG_ID_UKRAINIAN = 0x0422
    LANG_ID_ENGLISH_US = 0x0409
    LANG_ID_ENGLISH_UK = 0x0809
    CMD_HELP = "HELP#"
    CMD_SOUND = "SOUND#"
    CMD_OCR = "SCR#"
    CMD_SET_MONITOR = "SET_MONITOR#"
    CMD_SET_SOUND = "SET_SOUND#"
    CMD_EXIT = "EXIT#"
    COLOR_NEUTRAL = Fore.LIGHTBLUE_EX
    COLOR_PROMPT_UA = Fore.YELLOW
    COLOR_PROMPT_EN = Fore.CYAN
    COLOR_RESULT = Fore.GREEN
    COLOR_ERROR = Fore.RED
    COLOR_WARNING = Fore.YELLOW
    COLOR_INFO = Fore.CYAN


class ScreenAreaSelector:
    """Інкапсулює логіку вибору області екрану за допомогою Tkinter."""
    def __init__(self, monitor: Dict):
        self._monitor = monitor
        self._root = tk.Tk()
        self._coords = {"start_x": 0, "start_y": 0, "end_x": 0, "end_y": 0}
        self._rect = None
        self._setup_widget()

    def _setup_widget(self):
        self._root.overrideredirect(True)
        self._root.attributes('-alpha', 0.3)
        self._root.geometry(f"{self._monitor['width']}x{self._monitor['height']}+{self._monitor['left']}+{self._monitor['top']}")
        self._root.attributes('-topmost', True)
        canvas = tk.Canvas(self._root, cursor="cross", bg="grey")
        canvas.pack(fill=tk.BOTH, expand=True)
        canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        canvas.bind("<B1-Motion>", self._on_mouse_move)
        canvas.bind("<ButtonRelease-1>", self._on_mouse_up)

    def _on_mouse_down(self, event):
        self._coords["start_x"] = event.x
        self._coords["start_y"] = event.y
        self._rect = event.widget.create_rectangle(event.x, event.y, event.x, event.y, outline='red', width=2)

    def _on_mouse_move(self, event):
        if self._rect:
            event.widget.coords(self._rect, self._coords["start_x"], self._coords["start_y"], event.x, event.y)

    def _on_mouse_up(self, event):
        self._coords["end_x"] = event.x
        self._coords["end_y"] = event.y
        self._root.quit()

    def select_area(self) -> Optional[Tuple[int, int, int, int]]:
        print("Виділіть область екрану...")
        self._root.mainloop()
        self._root.destroy()
        x1 = min(self._coords["start_x"], self._coords["end_x"])
        y1 = min(self._coords["start_y"], self._coords["end_y"])
        x2 = max(self._coords["start_x"], self._coords["end_x"])
        y2 = max(self._coords["start_y"], self._coords["end_y"])
        if (x2 - x1) < 10 or (y2 - y1) < 10:
            print(f"{Config.COLOR_WARNING}Область не виділена або занадто мала.")
            return None
        return x1, y1, x2, y2


class TerminalTranslator:
    """Основний клас перекладача."""
    def __init__(self, config: Config):
        colorama_init(autoreset=True)
        self.cfg = config
        self.joystick_handler = None
        self.translate_client: Optional[translate.Client] = None
        self.sound_enabled: bool = False
        self.selected_monitor: Optional[Dict] = None
        self.selected_monitor_idx: Optional[int] = None
        self.last_target_lang: Optional[str] = None
        self.last_english_text: Optional[str] = None
        self.log_file_path: Optional[str] = None
        self.commands = {
            self.cfg.CMD_HELP.lower(): self._show_help,
            self.cfg.CMD_SOUND.lower(): self._speak_last_text,
            self.cfg.CMD_OCR.lower(): self._handle_ocr_and_translate,
            self.cfg.CMD_SET_MONITOR.lower(): self._select_monitor_interactive,
            self.cfg.CMD_SET_SOUND.lower(): self._toggle_sound,
            self.cfg.CMD_EXIT.lower(): self._exit,
        }

    @staticmethod
    def _get_keyboard_language() -> Optional[str]:
        if not WINDOWS_API_AVAILABLE: return None
        try:
            hwnd = user32.GetForegroundWindow()
            thread_id = user32.GetWindowThreadProcessId(hwnd, None)
            layout_handle = user32.GetKeyboardLayout(thread_id)
            lang_id = layout_handle & 0xFFFF
            if lang_id == Config.LANG_ID_UKRAINIAN: return 'uk'
            if lang_id in [Config.LANG_ID_ENGLISH_US, Config.LANG_ID_ENGLISH_UK]: return 'en'
            return None
        except Exception: return None

    def _setup_dependencies(self) -> bool:
        if 'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ:
            print(f"{self.cfg.COLOR_ERROR}ПОМИЛКА: Немає ключа GOOGLE_APPLICATION_CREDENTIALS.")
            return False
        pytesseract.pytesseract.tesseract_cmd = self.cfg.TESSERACT_PATH
        if not os.path.exists(self.cfg.TESSERACT_PATH):
            print(f"{self.cfg.COLOR_WARNING}ПОПЕРЕДЖЕННЯ: Tesseract не знайдено: {self.cfg.TESSERACT_PATH}")
        try: self.translate_client = translate.Client()
        except Exception as e:
            print(f"{self.cfg.COLOR_ERROR}Не вдалося ініціалізувати Google Translate: {e}")
            return False
        pygame.init()
        return True

    def _setup_logging(self):
        os.makedirs(self.cfg.LOG_DIR, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file_path = os.path.join(self.cfg.LOG_DIR, f"session_{timestamp}.txt")
        print(f"{self.cfg.COLOR_NEUTRAL}Лог-файл: {self.log_file_path}")

    def _log_event(self, text: str):
        if self.log_file_path:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {text}\n")

    def _translate_text(self, text: str, target_language: str) -> Optional[str]:
        if not self.translate_client:
            print(f"{self.cfg.COLOR_ERROR}Перекладач не ініціалізовано.")
            return None
        try:
            self._log_event(f"TRANSLATE (to: {target_language}): {text}")
            result = self.translate_client.translate(text, target_language=target_language)
            translated = result['translatedText']
            self._log_event(f"RESULT: {translated}")
            return translated
        except Exception as e:
            print(f"\n{self.cfg.COLOR_ERROR}--- Помилка API ---: {e}")
            return None

    @staticmethod
    def _speak_text(text: str, lang: str):
        try:
            with io.BytesIO() as audio_fp:
                tts = gTTS(text=text, lang=lang)
                tts.write_to_fp(audio_fp)
                audio_fp.seek(0)
                pygame.mixer.music.load(audio_fp)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
        except Exception as e:
            print(f"\n{self.cfg.COLOR_ERROR}--- Помилка озвучення ---: {e}")

    def _select_monitor_interactive(self):
        with mss.mss() as sct:
            monitors = sct.monitors[1:]
            print(f"\n{self.cfg.COLOR_NEUTRAL}Доступні монітори:")
            for i, mon in enumerate(monitors, 1):
                print(f"{self.cfg.COLOR_NEUTRAL}{i}: {mon['width']}x{mon['height']} @ ({mon['left']},{mon['top']})")
            try:
                choice = input(f"{self.cfg.COLOR_NEUTRAL}Виберіть монітор (Enter для 1): ")
                mon_idx = int(choice or '1') - 1
                self.selected_monitor = monitors[mon_idx]
                self.selected_monitor_idx = mon_idx + 1
            except (ValueError, IndexError):
                print(f"{self.cfg.COLOR_WARNING}Невірний вибір, використано монітор 1.")
                self.selected_monitor = monitors[0]
                self.selected_monitor_idx = 1
        print(f"{self.cfg.COLOR_NEUTRAL}Обрано монітор: {self.selected_monitor_idx}")
        self._log_event(f"SET_MONITOR: {self.selected_monitor}")

    def _grab_and_ocr(self) -> Optional[str]:
        if not self.selected_monitor: self._select_monitor_interactive()
        if not self.selected_monitor: return None
        area = ScreenAreaSelector(self.selected_monitor).select_area()
        if not area: return None
        x1, y1, x2, y2 = area
        bbox = {"left": self.selected_monitor['left'] + x1, "top": self.selected_monitor['top'] + y1, "width": x2 - x1, "height": y2 - y1}
        with mss.mss() as sct:
            sct_img = sct.grab(bbox)
            img = Image.frombytes('RGB', sct_img.size, sct_img.rgb)
        text = pytesseract.image_to_string(img, lang='eng+ukr').strip()
        print(f"{self.cfg.COLOR_INFO} {text}")
        self._log_event(f"OCR RESULT: {text}")
        return text

    def _show_help(self):
        print(f"\n{self.cfg.COLOR_RESULT}--- Перекладач (UA ↔ EN) ---")
        print(f"{self.cfg.COLOR_NEUTRAL}Напрямок перекладу визначається автоматично за розкладкою клавіатури.")
        commands_desc = {
            self.cfg.CMD_SOUND: "озвучити останній англійський текст.",
            self.cfg.CMD_OCR: "розпізнати текст з екрану.",
            self.cfg.CMD_SET_MONITOR: "вибрати монітор для OCR.",
            self.cfg.CMD_SET_SOUND: "увімкнути/вимкнути авто-озвучення."
        }
        for cmd, desc in commands_desc.items():
            print(f"{self.cfg.COLOR_INFO}{cmd:<15}{Style.RESET_ALL}- {desc}")
        print(f"{self.cfg.COLOR_NEUTRAL}Для виходу введіть '{self.cfg.CMD_EXIT}'.\n")

    def _speak_last_text(self):
        if self.last_english_text:
            print(f"{self.cfg.COLOR_INFO}Озвучуємо...")
            self._speak_text(self.last_english_text, 'en')
        else:
            print(f"{self.cfg.COLOR_WARNING}Немає тексту для озвучення.")

    def _handle_ocr_and_translate(self):
        self._log_event("COMMAND: SCR#")
        ocr_text = self._grab_and_ocr()
        if ocr_text: self._process_translation(ocr_text)

    def _toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        status = "УВІМКНЕНО" if self.sound_enabled else "ВИМКНЕНО"
        print(f"{self.cfg.COLOR_NEUTRAL}Авто-озвучення: {status}")

    def _get_prompt(self) -> str:
        mon_str = f"D{self.selected_monitor_idx}" if self.selected_monitor_idx else "D?"
        sound_str = "S" if self.sound_enabled else "M"
        if self.last_target_lang == 'en':
            dir_str, color = "УКР", self.cfg.COLOR_PROMPT_UA
        elif self.last_target_lang == 'uk':
            dir_str, color = "ENG", self.cfg.COLOR_PROMPT_EN
        else:
            return f"{self.cfg.COLOR_WARNING}Встановіть розкладку (UA/EN): "
        return f"{color}[{mon_str}:{sound_str}] {dir_str}#> {Style.RESET_ALL}"

    def _exit(self):
        if self.joystick_handler: self.joystick_handler.stop()
        print(f"\n{self.cfg.COLOR_RESULT}До побачення!")
        sys.exit(0)

    def _process_translation(self, text: str, forced_target_lang: Optional[str] = None):
        target_lang = forced_target_lang or self.last_target_lang
        if not target_lang:
            print(f"{self.cfg.COLOR_WARNING}Не визначено напрямок перекладу.")
            return
        translated_text = self._translate_text(text, target_lang)
        if translated_text:
            print(f"{self.cfg.COLOR_RESULT}-> {translated_text}{Style.RESET_ALL}")
            is_to_english = target_lang == 'en'
            self.last_english_text = translated_text if is_to_english else text
            if self.sound_enabled: self._speak_text(self.last_english_text, 'en')

    def run(self):
        if not self._setup_dependencies(): return
        self._setup_logging()
        self._select_monitor_interactive()
        self._show_help()
        if not WINDOWS_API_AVAILABLE:
            print(f"{self.cfg.COLOR_ERROR}Робота неможлива без Windows API.")
            return

        try:
            self.joystick_handler = JoystickHandler()
            self.joystick_handler.start()
        except Exception as e:
            print(f"{self.cfg.COLOR_WARNING}JoystickHandler не ініціалізовано: {e}")

        buffer = ''; last_prompt = ''; prev_b1_state = None
        
        while True:
            try:
                if self.joystick_handler:
                    state = self.joystick_handler.state
                    b1 = state.get('B1')
                    if prev_b1_state == 'B1D' and b1 == 'B1U':
                        sys.stdout.write(f'\r{" " * (len(last_prompt) + len(buffer))}\r')
                        print(f"{self.cfg.COLOR_NEUTRAL}[Джойстик] -> {self.cfg.CMD_SOUND}")
                        self._speak_last_text()
                        last_prompt = ''
                    prev_b1_state = b1
                
                detected_lang = self._get_keyboard_language()
                if detected_lang == 'uk': self.last_target_lang = 'en'
                elif detected_lang == 'en': self.last_target_lang = 'uk'

                prompt = self._get_prompt()
                if prompt != last_prompt:
                    sys.stdout.write(f'\r{" " * len(last_prompt)}\r{prompt}{buffer}')
                    sys.stdout.flush()
                    last_prompt = prompt

                if msvcrt.kbhit():
                    char = msvcrt.getwch()

                    # --- ДОДАНО: ігнорувати спец. символи (наприклад, стрілки) ---
                    if char in ('\x00', '\xe0'):
                        # Зчитати наступний символ (коди спец. клавіш, наприклад, стрілки)
                        msvcrt.getwch()
                        continue

                    if char in ('\r', '\n'):
                        sys.stdout.write('\n')
                        user_input = buffer.strip()
                        buffer = ''
                        last_prompt = ''
                        if user_input:
                            # --- Команди не залежать від регістру ---
                            cmd = user_input.lower()
                            if cmd in self.commands:
                                self.commands[cmd]()
                            else:
                                self._process_translation(user_input)
                    
                    elif char == '\x08':
                        if buffer:
                            buffer = buffer[:-1]
                            sys.stdout.write('\b \b')
                            sys.stdout.flush()
                    
                    elif char == '\x03':
                        raise KeyboardInterrupt
                    
                    else:
                        buffer += char
                        sys.stdout.write(char)
                        sys.stdout.flush()
                
                pygame.time.wait(20)

            except (KeyboardInterrupt, EOFError): self._exit()
            except Exception as e:
                print(f"\n{self.cfg.COLOR_ERROR}Критична помилка: {e}")
                self._log_event(f"ERROR: {e}")
                buffer = ''

if __name__ == "__main__":
    translator = TerminalTranslator(config=Config())
    translator.run()