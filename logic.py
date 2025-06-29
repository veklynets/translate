import joustick as joustick 
import pyautogui
import time
from controle_audio_system import *
    
JoystickButton = {
    "LED_Microphone": 'BG',
    'copy_to_AI_translation': 'B4q',
    'copy_to_AI_questions': 'B6q',
    'play/pause_media': 'B9q',
    'air': '-Axis 1q',
    'colleagues': '-Axis 0q'
    }

class logic_stage():
    """
    """
    def __init__(self, DEBUG = False, REAC_SYS = 0.1, DOUBLE_PUSH = 400, screen_position = None):
        print("Ініціалізація головної програми...")
        self.joystick_handler = joustick.JoystickHandler(DEBUG=DEBUG)
        self.is_running_joystick_handler = True

        self.DEBUG = DEBUG
        self.REAC_SYS = REAC_SYS
        self.DOUBLE_PUSH = DOUBLE_PUSH
        self.screen_position = screen_position
        self.start_time = time.time() * 1000
        self.last_key = None
        self.app = LogicAudioController()
        

    def run_logic(self):
        X = 0
        Y = 1

        self.joystick_handler.start()
        swich_LED_Microphone_dynamic = True
        swich_LED_Microphone_static_mode_ON = False  # True - статичний режим (default unmute), False - динамічний (default mute)
        swich_LED_Microphone_static = False

        while self.is_running_joystick_handler:
            time.sleep(0.1)
            if self.screen_position is None:
                print("❌ screen_position not set! only for debug")
                return  
        
            # default U (or Z) -> D (or U/D or L/R)
            if JoystickButton['LED_Microphone']+'R' == self.joystick_handler.state.get(JoystickButton['LED_Microphone']):
                swich_LED_Microphone_static = True
            if JoystickButton['LED_Microphone']+'Z' == self.joystick_handler.state.get(JoystickButton['LED_Microphone']) and swich_LED_Microphone_static:
                swich_LED_Microphone_static_mode_ON = not swich_LED_Microphone_static_mode_ON
                swich_LED_Microphone_static = False

            if swich_LED_Microphone_static_mode_ON :
                if self.app.send_LogicAudioController('Microphone status') == "Muted":
                    self.app.send_LogicAudioController('Microphone unmute')
            else:
                mic_webex_state = self.joystick_handler.state.get(JoystickButton['LED_Microphone'])
                if mic_webex_state == JoystickButton['LED_Microphone'] + 'L' and swich_LED_Microphone_dynamic:
                    swich_LED_Microphone_dynamic = False
                    self.app.send_LogicAudioController('Microphone unmute')
                elif mic_webex_state == JoystickButton['LED_Microphone'] + 'Z':
                    swich_LED_Microphone_dynamic = True
                    if self.app.send_LogicAudioController('Microphone status') == "Voice":
                        self.app.send_LogicAudioController('Microphone mute')

            if JoystickButton['copy_to_AI_translation']+'D' == self.joystick_handler.state.get(JoystickButton['copy_to_AI_translation']):
                from pynput.keyboard import Key, Controller   # import keyboard - lite analog of pynput
                print('pressed key: ' + 'copy_to_AI_translation')

                keyboard = Controller()
                time.sleep(1)

                pyautogui.click(self.screen_position['field_translate'][X], self.screen_position['field_translate'][Y], interval=0.05)
                time.sleep(self.REAC_SYS)

                keyboard.press(Key.ctrl)
                keyboard.press('a')
                keyboard.release('a')
                keyboard.release(Key.ctrl)
                time.sleep(self.REAC_SYS)

                keyboard.press(Key.ctrl)
                keyboard.press('c')
                keyboard.release('c')
                keyboard.release(Key.ctrl)
                time.sleep(self.REAC_SYS)

                pyautogui.click(self.screen_position['field_GM_translation'][X], self.screen_position['field_GM_translation'][Y], interval=0.05)
                time.sleep(self.REAC_SYS)
                pyautogui.click(self.screen_position['field_IA'][X], self.screen_position['field_IA'][Y], interval=0.05)
                time.sleep(self.REAC_SYS)

                keyboard.press(Key.ctrl)
                keyboard.press('v')
                keyboard.release('v')
                keyboard.release(Key.ctrl)
                time.sleep(self.REAC_SYS)

                pyautogui.click(self.screen_position['send_AI'][X], self.screen_position['send_AI'][Y], interval=0.05)
                time.sleep(self.REAC_SYS)

            if JoystickButton['copy_to_AI_questions']+'D' == self.joystick_handler.state.get(JoystickButton['copy_to_AI_questions']):
                from pynput.keyboard import Key, Controller
                print('pressed key: ' + 'copy_to_AI_questions')

                keyboard = Controller()
                time.sleep(1)

                pyautogui.click(self.screen_position['field_translate'][X], self.screen_position['field_translate'][Y], interval=0.05)
                time.sleep(self.REAC_SYS)

                keyboard.press(Key.ctrl)
                keyboard.press('a')
                keyboard.release('a')
                keyboard.release(Key.ctrl)
                time.sleep(self.REAC_SYS)

                keyboard.press(Key.ctrl)
                keyboard.press('c')
                keyboard.release('c')
                keyboard.release(Key.ctrl)
                time.sleep(self.REAC_SYS)

                pyautogui.click(self.screen_position['field_GM_questions'][X], self.screen_position['field_GM_questions'][Y], interval=0.05)
                time.sleep(self.REAC_SYS)
                pyautogui.click(self.screen_position['field_IA'][X], self.screen_position['field_IA'][Y], interval=0.05)
                time.sleep(self.REAC_SYS)

                keyboard.press(Key.ctrl)
                keyboard.press('v')
                keyboard.release('v')
                keyboard.release(Key.ctrl)
                time.sleep(self.REAC_SYS)

                pyautogui.click(self.screen_position['send_AI'][X], self.screen_position['send_AI'][Y], interval=0.05)
                time.sleep(self.REAC_SYS)

            if JoystickButton['play/pause_media']+'D' == self.joystick_handler.state.get(JoystickButton['play/pause_media']):
                import keyboard
                print('pressed key: ' + 'play/pause_media')

                keyboard.send('play/pause_media')
                time.sleep(self.REAC_SYS)

    def shutdown_logic(self):
        """Метод для чистого завершення роботи."""
        print("Початок процедури виходу...")
        self.is_running_joystick_handler = False # Сигнал для зупинки основного циклу
        self.joystick_handler.stop() # Команда для зупинки фонового потоку

if __name__ == "__main__":
    api = logic_stage()
    api.run_logic()



