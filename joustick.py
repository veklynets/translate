import pyjoystick
from pyjoystick.sdl2 import run_event_loop
import time

class JoystickHandler:
    def __init__(self, DEBUG=False):
        self.DEBUG = DEBUG
        self.dictionary = {
            "Button 0 = 1": 'B1D',
            "Button 0 = 0": 'B1U',
            "Button 1 = 1": 'B2D',
            "Button 1 = 0": 'B2U',
            "Button 2 = 1": 'B3D',
            "Button 2 = 0": 'B3U',
            "Button 3 = 1": 'B4D',
            "Button 3 = 0": 'B4U',
            "Button 5 = 1": 'R1D',
            "Button 5 = 0": 'R1U',
            "Button 7 = 1": 'R2D',
            "Button 7 = 0": 'R2U',
            "Button 4 = 1": 'L1D',
            "Button 4 = 0": 'L1U',
            "Button 6 = 1": 'L2D',
            "Button 6 = 0": 'L2U',
            "-Axis 1 = -1.0": 'BVU',
            "Axis 1 = 1.0": 'BVD',
            "Axis 1 = 0.0": 'BVZ',
            "-Axis 0 = -1.0": 'BGL',
            "Axis 0 = 1.0": 'BGR',
            "Axis 0 = 0.0": 'BGZ',
            "Button 8 = 1": 'MSD',
            "Button 8 = 0": 'MSU',
            "Button 9 = 1": 'MRD',
            "Button 9 = 0": 'MRU',
            "Button 10 = 1": 'JLD',
            "Button 10 = 0": 'JLU',
            "Button 11 = 1": 'JRD',
            "Button 11 = 0": 'JRU'
        }

        self.state = {
            'B1': 'B1U', 'B2': 'B2U', 'B3': 'B3U', 'B4': 'B4U',
            'R1': 'R1U', 'R2': 'R2U', 'L1': 'L1U', 'L2': 'L2U',
            'BV': 'BVZ', 'BG': 'BGZ', 'MS': 'MSU', 'MR': 'MRU',
            'JL': 'JLU', 'JR': 'JRU',
        }

        self.repeater = pyjoystick.HatRepeater(first_repeat_timeout=0.5, repeat_timeout=0.03, check_timeout=0.01)
        self.mngr = pyjoystick.ThreadEventManager(
            event_loop=run_event_loop,
            handle_key_event=self.handle_key_event,
            button_repeater=self.repeater
        )
        print("--- JoustickController - OK ---")


    def handle_key_event(self, key):
        self.DEBUG == True and print('{} = {}'.format(key, key.value))
        lookup_key = '{} = {}'.format(key, key.value)
        event_code = self.dictionary.get(lookup_key)
        self.DEBUG == True and print(event_code)
        if event_code:
            prefix = event_code[:2]
            if prefix in self.state:
                self.state[prefix] = event_code
                self.DEBUG == True and print(self.state)

    def start(self):
        self.mngr.start()

    def stop(self):
        self.mngr.stop()
    

if __name__ == "__main__":
    handler = JoystickHandler(DEBUG=True)
    handler.start()
    while True:
        time.sleep(1)