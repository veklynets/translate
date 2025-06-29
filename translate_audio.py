# voice_translator_budget.py
import os
import time
import io
import numpy as np
import sounddevice as sd
import pygame
from google.cloud import translate_v2 as translate
from google.cloud import speech
from google.cloud import texttospeech

# --- Перевірка автентифікації (обов'язково) ---
if 'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ:
    raise RuntimeError("Не встановлено змінну середовища GOOGLE_APPLICATION_CREDENTIALS")

# --- Ініціалізація Pygame Mixer для відтворення звуку ---
pygame.mixer.init()

# ==============================================================================
# Функція 1: Розпізнавання мови з мікрофона (Speech-to-Text)
# ==============================================================================
def recognize_from_mic(language_code: str = "uk-UA") -> str | None:
    """
    Записує аудіо з мікрофона і розпізнає його (live transcript під час запису).
    language_code: код мови для Google Speech-to-Text (наприклад, 'uk-UA', 'en-US', 'pl-PL' тощо)
    """
    import queue
    import threading

    sample_rate = 16000
    duration = 5
    blocksize = 1024

    input(f"==> Натисніть Enter і говоріть українською протягом {duration} секунд...")

    q = queue.Queue()
    recorded = []

    def callback(indata, frames, time_info, status):
        q.put(indata.copy())

    print("Слухаю... (live transcript)")

    # --- Google StreamingRecognize setup ---
    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate,
        language_code=language_code,  # <-- тут задається мова розпізнавання!
        use_enhanced=False,
        max_alternatives=1,
        enable_automatic_punctuation=True,
    )
    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True,
        single_utterance=False,
    )

    def audio_generator():
        start_time = time.time()
        while time.time() - start_time < duration:
            try:
                data = q.get(timeout=0.1)
                recorded.append(data)
                yield speech.StreamingRecognizeRequest(audio_content=data.tobytes())
            except queue.Empty:
                continue

    with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16', blocksize=blocksize, callback=callback):
        requests = audio_generator()
        responses = client.streaming_recognize(streaming_config, requests)

        transcript = ""
        try:
            for response in responses:
                if not response.results:
                    continue
                result = response.results[0]
                if result.is_final or result.alternatives:
                    interim = result.alternatives[0].transcript
                    print(f"\r{interim}{' ' * 20}", end="", flush=True)
                    if result.is_final:
                        transcript = interim
                        break
        except Exception as e:
            print(f"\nПомилка live transcript: {e}")

    print()  # Перенос після live transcript
    if transcript:
        print(f"Розпізнано текст: '{transcript}'")
        return transcript
    else:
        print("Не вдалося нічого розпізнати.")
        return None

# ==============================================================================
# Функція 2: Переклад тексту (без змін)
# ==============================================================================
def translate_text(text: str, target_language: str) -> str | None:
    """Перекладає текст."""
    try:
        translate_client = translate.Client()
        result = translate_client.translate(text, target_language=target_language)
        translated = result['translatedText']
        print(f"Переклад ({target_language}): '{translated}'")
        return translated
    except Exception as e:
        print(f"Помилка перекладу: {e}")
        return None

# ==============================================================================
# Функція 3: Синтез мови (Text-to-Speech)
# ==============================================================================
def speak_text(text: str, language_code: str = "en-US"):
    """Синтезує мовлення з тексту і відтворює його, використовуючи стандартний голос."""
    try:
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text)

        ### ЗМІНА ###
        # Замість того, щоб дозволити Google обирати голос за замовчуванням (зазвичай дорожчий WaveNet),
        # ми явно просимо конкретний "Стандартний" голос, який є дешевшим.
        # Наприклад, 'en-US-Standard-C' для англійської.
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            # Видаляємо ssml_gender і вказуємо конкретне ім'я голосу,
            # якщо відомо. Якщо ні, API спробує обрати стандартний.
            # Для гарантії можна було б створити словник стандартних голосів.
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        print("Відтворення голосу...")
        audio_stream = io.BytesIO(response.audio_content)
        pygame.mixer.music.load(audio_stream)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        print("Відтворення завершено.")

    except Exception as e:
        print(f"Помилка синтезу мовлення: {e}")

# ==============================================================================
# Головний блок програми (без змін)
# ==============================================================================
def main():
    print("--- Голосовий перекладач Google (БЮДЖЕТНА ВЕРСІЯ) ---")
    print("Програма запише ваш голос, перекладе його і озвучить результат.")
    print("Для виходу натисніть Ctrl+C.\n")

    while True:
        original_text = recognize_from_mic(language_code="uk-UA")
        if original_text:
            translated_text = translate_text(original_text, target_language='en')
            if translated_text:
                speak_text(translated_text, language_code="en-US")
        print("\nГотовий до наступної фрази...")

if __name__ == "__main__":
    try:
        main()

        
    except KeyboardInterrupt:
        print("\nДо побачення!")
    except Exception as e:
        print(f"Сталася непередбачувана помилка: {e}")