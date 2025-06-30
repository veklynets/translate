#https://qna.habr.com/q/1259764
#https://stackoverflow.com/questions/71814027/how-to-press-enter-using-pyautogui
# graphic python https://dafarry.github.io/tkinterbook/

import pygame
import threading
import asyncio
from joustick import JoystickHandler
from translate import TerminalTranslator, Config
from controle_audio_system import LogicAudioController

    
joystick_buttons = {
    "sound": 'B1',
    "LED_Microphone": 'BG',
    'copy_to_AI_translation': 'B4q',
    'copy_to_AI_questions': 'B6q',
    'play/pause_media': 'B9q',
    'air': '-Axis 1q',
    'colleagues': '-Axis 0q'
    }

state_buttons = {
    "UP": "U",
    "DOWN": "D",
    "LEFT": "L",
    "RIGHT": "R",  
    "ZERO": "Z"
}

class Haupt:
    """
    """
    def __init__(self, DEBUG = False, REAC_SYS = 0.1, DOUBLE_PUSH = 400, screen_position = None):
        print("Ініціалізація головної програми...")
        self.sound_flag = threading.Event()
        self.translator = TerminalTranslator(config=Config())
        self.translator.sound_flag = self.sound_flag
        self.audio_controller = LogicAudioController()            
        self.handler = JoystickHandler(DEBUG=DEBUG)
        self.handler.start()

    async def joystick_sound_flag_loop_async(self):
        """
        Async версія моніторингу стану джойстика для sound_flag.
        """
        prev_b1_state = None
        while True:
            await asyncio.sleep(0.1)            
            b1 = self.handler.state.get(joystick_buttons['sound'])
            if prev_b1_state == joystick_buttons['sound'] + state_buttons['DOWN'] \
            and b1 == joystick_buttons['sound'] + state_buttons['UP']:
                self.sound_flag.set()
            prev_b1_state = b1

    async def microphone_control_loop_async(self):
        """
        Async цикл для керування мікрофоном через джойстик.
        """
        swich_LED_Microphone_dynamic = True
        swich_LED_Microphone_static_mode_ON = False  # True - статичний режим (default unmute), False - динамічний (default mute)
        swich_LED_Microphone_static = False

        while True:
            await asyncio.sleep(0.1)
            # --- Перемикання статичного режиму мікрофона ---
            if joystick_buttons['LED_Microphone'] + state_buttons['RIGHT'] == self.handler.state.get(joystick_buttons['LED_Microphone']):
                swich_LED_Microphone_static = True
            if joystick_buttons['LED_Microphone'] + state_buttons['ZERO'] == self.handler.state.get(joystick_buttons['LED_Microphone']) and swich_LED_Microphone_static:
                swich_LED_Microphone_static_mode_ON = not swich_LED_Microphone_static_mode_ON
                swich_LED_Microphone_static = False

            # --- Статичний режим: мікрофон завжди unmute ---
            if swich_LED_Microphone_static_mode_ON:
                if self.audio_controller.send_LogicAudioController('Microphone status') == "Muted":
                    self.audio_controller.send_LogicAudioController('Microphone unmute')
            else:
                # --- Динамічний режим: mute/unmute залежно від стану кнопки ---
                mic_webex_state = self.handler.state.get(joystick_buttons['LED_Microphone'])
                if mic_webex_state == joystick_buttons['LED_Microphone'] + state_buttons['LEFT'] and swich_LED_Microphone_dynamic:
                    swich_LED_Microphone_dynamic = False
                    self.audio_controller.send_LogicAudioController('Microphone unmute')
                elif mic_webex_state == joystick_buttons['LED_Microphone'] + state_buttons['ZERO']:
                    swich_LED_Microphone_dynamic = True
                    if self.audio_controller.send_LogicAudioController('Microphone status') == "Voice":
                        self.audio_controller.send_LogicAudioController('Microphone mute')

    async def run_async(self):
        """
        Асинхронний запуск усіх компонентів: джойстик, мікрофон, перекладач.
        """
        # Запуск асинхронних тасків для джойстика та мікрофона
        joystick_task = asyncio.create_task(self.joystick_sound_flag_loop_async())
        mic_task = asyncio.create_task(self.microphone_control_loop_async())

        # Запуск перекладача у окремому потоці, бо він блокує цикл
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.translator.run)

        # Очікування завершення тасків (фактично вони нескінченні)
        await asyncio.gather(joystick_task, mic_task)

    def run(self):
        asyncio.run(self.run_async())
        
    def shutdown(self):
        pass

if __name__ == "__main__":
    api = Haupt()
    api.run()