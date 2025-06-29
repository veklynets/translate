from google_translate.version_python import check_python_version
import time
from pynput import mouse
import pyautogui

class button_of_mouse_my:
        
    def __init__(self):
        " create lisener "
        with mouse.Listener(on_click=self.func_for_callback_click) as listener:
            listener.join()

    def func_for_callback_click(self, x, y, button, pressed):
        if pressed:
            print(f"# !!!!wrong positions!!! Click {button} on location: ({x}, {y})")

class mouse_position_my:

    def position_mouse(self):
        while True:
            x, y = pyautogui.position()
            print(str(x) + ', ' + str(y))
            time.sleep(3)

if __name__ == "__main__":

    check_python_version(3, 12)  # work on Python 3.12.1
    #button_of_mouse_my()
    exp = mouse_position_my()
    exp.position_mouse()
