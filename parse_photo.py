    import pyautogui
    import cv2
    import numpy as np
    import os

class Calibration:
    # Отримати абсолютний шлях до папки скрипта
    script_dir = os.path.dirname(__file__)  # Директорія, де знаходиться main.py
    template_path = os.path.join(script_dir, 'images', 'microphone_button.png')
    template_path2 = os.path.join(script_dir, 'images', 'screenshot.png')

    # Зробити скріншот екрану
    screenshot = pyautogui.screenshot()

    # Зберегти скріншот
    screenshot.save(template_path2)

    # Конвертувати скріншот у формат OpenCV
    screen = np.array(screenshot)
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)

    # Перетворити скріншот у чорно-білий формат
    gray_screen = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

    # Завантажити зображення кнопки мікрофона
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)

    # Перевірка на успішність завантаження шаблону
    if template is None:
        print("Не вдалося завантажити зображення шаблону. Перевірте шлях до файлу.")
    else:
        # Перетворити шаблон у чорно-білий формат
        gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

        # Шукати місце на екрані, де знаходиться кнопка
        result = cv2.matchTemplate(gray_screen, gray_template, cv2.TM_CCOEFF_NORMED)

        # Знайти координати найбільшої відповідності
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # Якщо знайдено відповідність
        if max_val > 0.9:  # 80% точності
            print(max_loc)
            #pyautogui.click(max_loc)  # Натиснути на місце, де знаходиться кнопка
        else:
            print("---")

def Vr():
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.options import Options
    import time
    # Налаштування опцій для Chrome
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Приховує автоматизацію
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    #chrome_options.add_argument("--headless")  # Режим headless (без інтерфейсу)
    chrome_options.add_argument("--disable-gpu")  # Вимкнути GPU
    chrome_options.add_argument("--no-sandbox")   # Вимкнути пісочницю
    chrome_options.add_argument("--disable-dev-shm-usage")  # Вимкнути спільну пам'ять


    # Створення браузера з цими налаштуваннями
    driver = webdriver.Chrome(options=chrome_options)

    # Відкриваємо сторінку
    driver.get("https://translate.google.com/")


    # Знаходимо поле для введення тексту
    input_box = driver.find_element(By.CSS_SELECTOR, "textarea[aria-label='Source text']")

    # Вводимо текст для перекладу
    input_box.send_keys("Hello, how are you?")

    # Очікуємо, щоб переклад завершився
    time.sleep(20)

    # 1. Натискання кнопки "Динамік" для відтворення перекладу
    speaker_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Listen to translation']")
    speaker_button.click()

    time.sleep(20)
    # 2. Натискання кнопки "Мікрофон" для голосового введення
    mic_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Turn on voice input']")
    mic_button.click()

    # Закриваємо браузер після завершення
    time.sleep(50)
    driver.quit()

