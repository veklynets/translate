import threading
import pygame
from joustick import JoystickHandler
from translate import TerminalTranslator, Config

def joystick_sound_flag_loop(sound_flag: threading.Event):
    """
    Окремий потік для моніторингу стану джойстика.
    Встановлює sound_flag, якщо відбулося натискання B1D -> B1U.
    """
    handler = None
    try:
        handler = JoystickHandler()
        handler.start()
        prev_b1_state = None
        while True:
            state = handler.state
            b1 = state.get('B1')
            if prev_b1_state == 'B1D' and b1 == 'B1U':
                sound_flag.set()
            prev_b1_state = b1
            pygame.time.wait(20)
    except Exception as e:
        print(f"JoystickHandler не ініціалізовано: {e}")

def run_translator_with_joystick():
    """
    Запускає TerminalTranslator та окремий потік для джойстика.
    """
    sound_flag = threading.Event()
    joystick_thread = threading.Thread(target=joystick_sound_flag_loop, args=(sound_flag,), daemon=True)
    joystick_thread.start()

    translator = TerminalTranslator(config=Config())
    translator.sound_flag = sound_flag
    translator.run()

if __name__ == "__main__":
    run_translator_with_joystick()