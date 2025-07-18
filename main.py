from mouse import mouse_position_my, button_of_mouse_my
from logic_base import Haupt
from version_python import date
import gc

DEBUG = False
DOUBLE_PUSH = 400 # ms
REAC_SYS = 0.1  # seconds


class start_my(Haupt):  # or class start_my() ->  logic = logic_stage(DEBUG, REAC_SYS, DOUBLE_PUSH)

    screen_position_multi = {
        'big': { # 3 monitors
            'G_microphone': [1065, 1471],
            'G_clear': [1619, 1362],
            'G_speeker_in': [1105, 1471],
            'G_speeker_out': [1683, 1471],
            'G_change': [1655, 1313],
            'field_translate': [-1449, -1198],
            'field_GM_translation': [-1289, -1593],
            'field_GM_questions': [-884, -1591],
            'field_IA': [-732, -156],
            'send_AI': [-126, -90]
        },
        'big_full': {

        },
        'small': { # 1 monitor
            'G_microphone': [942, 1471],  # 1065 - 942 = 123
            'G_clear': [1499, 1362],
            'G_speeker_in': [990, 1471],
            'G_speeker_out': [1564, 1471],
            'G_change': [1532, 1313],
            'field_translate': [-1449, -1198],
            'field_GM_translation': [-1289, -1593],
            'field_GM_questions': [-884, -1591],
            'field_IA': [-732, -156],
            'send_AI': [-126, -90]
        }
    }
    
    def __init__(self):
        date()

        location_button = input("see location true buttons: write  yes or skip ---> ")
        if 'yes' == location_button: 
            exp = mouse_position_my()
            exp.position_mouse()

        location_button = input("see location buttons: write  yes or skip ---> ")
        if 'yes' == location_button: button_of_mouse_my()
        
        size_screen = input("enter size screen: " + str(list(self.screen_position_multi.keys())))
        if size_screen in list(self.screen_position_multi.keys()):
            self.screen_position = self.screen_position_multi[size_screen]
            print(f"selected mode: ", size_screen) 
        else:
            self.screen_position = self.screen_position_multi['small']
            print(f"selected mode: small") 
        
        Haupt.__init__(self, DEBUG=DEBUG, DOUBLE_PUSH=DOUBLE_PUSH,
                              REAC_SYS=REAC_SYS, screen_position=self.screen_position)   # super().__init__(DEBUG=DEBUG, DOUBLE_PUSH=DOUBLE_PUSH, REAC_SYS=REAC_SYS):

        
    def start(self):
        print("Start method called")
        self.run()
        print("Run method finished")

    def stop(self):
        print("Stop method called")
        self.shutdown()
        print("Shutdown finished")


if __name__ == "__main__":
    app = start_my()
    try:
        app.start()
        print("App start finished")
    finally:
        app.stop()
        gc.collect()
        print("App stopped and GC collected")


