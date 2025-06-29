"""
pycaw — це вузькоспеціалізована бібліотека, створена для однієї конкретної задачі: керування аудіопристроями Windows.
pywin32 (яка включає модулі win32api, win32gui та інші) — це всеохоплююча бібліотека, що надає прямий доступ до більшості функцій Windows API.

"""
from version_python import check_python_version
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


class AudioController:
    def __init__(self):
        """
        Ініціалізує контролер, отримуючи доступ до головного аудіопристрою (колонок).
        """
        try:
            self.devices = AudioUtilities.GetSpeakers()
            self.interface = self.devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume = cast(self.interface, POINTER(IAudioEndpointVolume))
            self.volume_range = self.volume.GetVolumeRange() # (-65.25, 0.0, 0.03125)
            self.min_db = self.volume_range[0]
            self.max_db = self.volume_range[1]
        except Exception as e:
            print(f"❌ Помилка ініціалізації: не знайдено аудіопристрій. {e}")
            exit(1)

    def speakers_volume_set(self, level_percent):
        """
        Встановлює гучність системи у відсотках (0-100).
        """
        if not 0 <= level_percent <= 100:
            print("Помилка: Гучність має бути в діапазоні від 0 до 100.")
            return

        # Конвертуємо відсотки в децибели
        # Формула для лінійного масштабування
        db_level = self.min_db + (self.max_db - self.min_db) * (level_percent / 100.0)
        
        self.volume.SetMasterVolumeLevel(db_level, None)
        print(f"✅ Гучність встановлено на {level_percent}%.")

    def speakers_current_volume(self):
        """
        Повертає поточну гучність системи у відсотках (0-100).
        """
        # Отримуємо поточний рівень в децибелах
        current_db = self.volume.GetMasterVolumeLevel()
        
        # Конвертуємо децибели у відсотки
        # Зворотня формула
        if current_db <= self.min_db:
            return 0
        
        percentage = ((current_db - self.min_db) / (self.max_db - self.min_db)) * 100
        return int(round(percentage))

    def speakers_is_muted(self):
        """
        Повертає True, якщо звук вимкнено (Mute), інакше False.
        """
        return bool(self.volume.GetMute())

    def get_microphone_status(self):
        """
        """
        try:
            devices = AudioUtilities.GetMicrophone()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))

            if volume.GetMute() == 0:
                return "Voice"
            else:
                return "Muted"
        except Exception as e:
            return f"Не вдалося отримати статус мікрофона. Помилка: {e}"

    def set_microphone_mute(self, state):
        """
        Встановлює стан Mute для мікрофона за замовчуванням.
        :param state: bool, де True -> Mute, False - увімкнути.
        """
        try:
            devices = AudioUtilities.GetMicrophone()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            
            # Встановити Mute (1 - вимкнути, 0 - увімкнути)
            mute_value = 1 if state else 0
            volume.SetMute(mute_value, None)
            
            if state:
                print("🎤🚫 Мікрофон виключено.")
            else:
                print("🎤✅ Мікрофон увімкнено.")
                
        except Exception as e:
            # Обробка помилки, якщо мікрофон не знайдено (наприклад, не підключений)
            if "HRESULT: 0x80070490" in str(e):
                print("❌ Помилка: Мікрофон не знайдено. Перевірте, чи підключено пристрій запису.")
            else:
                print(f"❌ Сталася помилка: {e}")


class LogicAudioController:
    """
    Логіка контролера аудіо для керування гучністю та станом мікрофона.
    Використовує AudioController для взаємодії з аудіопристроями.
    """
    def __init__(self):
        try:
            self.Sound = AudioController()
        except SystemExit:
            # Не продовжуємо, якщо контролер не зміг запуститись
            pass
        else:
            print("--- AudioController - OK ---")

    def send_LogicAudioController(self, command: str):
        """
        """ 
        if command.startswith("Volume set"):
            parts = command.split()
            if len(parts) == 3:
                try:
                    print("Volume set...", parts[2])
                    self.Sound.speakers_volume_set(int(parts[2]))
                except ValueError:
                    print("\n--- AudioController A - FAIL ---")
            return

        if command.startswith("Volume get"):
            try:
                print(f"Volume get... {self.Sound.speakers_current_volume()}%")
            except ValueError:
                print("\n--- AudioController B - FAIL ---")
            return

        if command.startswith("Volume status"):
            try:
                print(f"Volume mute {'Yes' if self.Sound.speakers_is_muted() else 'No'}")
            except ValueError:
                print("\n--- AudioController C - FAIL ---")
            return

        if command.startswith("Microphone mute"):
            try:
                self.Sound.set_microphone_mute(True)
            except ValueError:
                print("\n--- AudioController D - FAIL ---")
            return

        if command.startswith("Microphone unmute"):
            try:
                self.Sound.set_microphone_mute(False)
            except ValueError:
                print("\n--- AudioController E - FAIL ---")
            return

        if command.startswith("Microphone status"):
            return self.Sound.get_microphone_status()

        print(f"❌ Команда не знайдена: {command}")

if __name__ == "__main__":

    check_python_version(3, 12)  # work on Python 3.12.1
    app = LogicAudioController()
    app.send_LogicAudioController("Volume set 50")
    app.send_LogicAudioController("Volume get")
    app.send_LogicAudioController("Volume status")
    app.send_LogicAudioController("Microphone mute")
    app.send_LogicAudioController("Microphone unmute")
    app.send_LogicAudioController("Microphone status")
    app.send_LogicAudioController("Microphone wrong command")  # Test for unknown command
    app.send_LogicAudioController("Volume wrong command")  # Test for unknown command
