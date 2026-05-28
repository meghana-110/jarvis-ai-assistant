import os
import openai
import speech_recognition as sr
import webbrowser
import datetime
import pyttsx3
import threading
import cv2
import pyautogui
import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import shutil
import time
import mediapipe as mp
import pywhatkit

# Configuration - Perfectly safe placeholder text for GitHub tracking
apikey = os.getenv('OPENAI_API_KEY') or 'your-api-key-here'

# Initialize text-to-speech engine
engine = pyttsx3.init()
chatStr = ""
gesture_thread = None
gesture_active = False
listening_active = True  # Control variable for listening loop

# Initialize Mediapipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils


def say(text):
    engine.say(text)
    engine.runAndWait()


def chat(query):
    global chatStr
    openai.api_key = apikey
    chatStr += f"You: {query}\nJarvis: "
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a helpful AI assistant."},
                      {"role": "user", "content": query}]
        )
        response_text = response["choices"][0]["message"]["content"].strip()
        chatStr += response_text + "\n"
        say(response_text)
        return response_text
    except Exception as e:
        print(f"OpenAI Error: {e}")
        say("sorry I am having some trouble can i help you in other way")
        return "I'm having trouble connecting to OpenAI."


def processCommand(query):
    global gesture_thread, gesture_active, listening_active

    query = query.lower()

    if "open" in query:
        words = query.split()
        if "website" in words:
            site = words[words.index("website") - 1]
            webbrowser.open(f"https://www.{site}.com")
            return f"Opening {site}..."
        elif "air" in query:
            if not gesture_active:
                gesture_active = True
                gesture_thread = threading.Thread(target=detect_gestures, daemon=True)
                gesture_thread.start()
                say("Air gesture control activated.")
                return "Air gesture control activated."
            else:
                say("Gesture control is already active.")
                return "Gesture control is already active."
        else:
            app_name = query.replace("open", "").strip()
            possible_apps = {
                "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "notepad": "notepad.exe",
                "calculator": "calc.exe",
                "word": "C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE",
                "excel": "C:\\Program Files\\Microsoft Office\\root\\Office16\\EXCEL.EXE",
                "vs code": "C:\\Users\\YourUsername\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
                "whatsapp": "C:\\Program Files\\WindowsApps\\WhatsAppDesktop_2.2140.7.0_x64__8ptj331gd3njg\\WhatsApp.exe"
            }

            if app_name in possible_apps:
                subprocess.Popen(possible_apps[app_name])
                say(f"Opening {app_name}...")
                return f"Opening {app_name}..."
            else:
                executable_path = shutil.which(app_name)
                if executable_path:
                    subprocess.Popen(executable_path)
                    say(f"Opening {app_name}...")
                    return f"Opening {app_name}..."
                else:

                    say(f"Could not find {app_name}. Please check the application name.")
                    return f"Could not find {app_name}. Please check the application name."

    elif "stop gesture" in query and gesture_active:
        gesture_active = False
        say("Air gesture control stopped.")
        return "Air gesture control stopped."

    elif "scroll up" in query:
        pyautogui.scroll(500)
        return "Scrolling up..."

    elif "scroll down" in query:
        pyautogui.scroll(-500)
        return "Scrolling down..."

    elif "time" in query:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        say("The time is" + current_time)
        return f"The time is {current_time}."

    elif "exit" in query or "quit" in query:
        listening_active = False
        say("Goodbye!")
        root.quit()

    elif "song" in query:
        say("Which song would you like to listen to?")
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                audio = recognizer.listen(source, timeout=5)
                song = recognizer.recognize_google(audio).lower()
                title = song
                pywhatkit.playonyt(title)
                return f"Playing {song} on YouTube..."
            except (sr.UnknownValueError, sr.WaitTimeoutError):
                return "Sorry, I didn't catch that."

    elif "search" in query:
        search_query = query[7:].strip()
        webbrowser.open(f"https://www.bing.com/search?q={search_query}")
        return f"Searching for {search_query}..."

    elif "about" in query:
        say("I am Jarvis, a system assistant developed by Batch 13 of CSEC.")
        return "I am Jarvis, a system assistant developed by Batch 13 of CSEC."

    elif "repeat after me" in query:
        say("What should I repeat?")
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                audio = recognizer.listen(source, timeout=5)
                rep = recognizer.recognize_google(audio)
                say(rep)
                return f"I said: {rep}"
            except (sr.UnknownValueError, sr.WaitTimeoutError):
                return "Sorry, I didn't catch that."

    elif "can you do" in query:
        say("I can perform many operations like opening applications, searching the web, playing music, controlling your computer with gestures, and more.")
        return "I can perform many operations like opening applications, searching the web, playing music, controlling your computer with gestures, and more."

    elif "sleep" in query:
        say("thank you")
        return "Thank you"
    elif "back" in query:
        pyautogui.hotkey('alt', 'tab')
        pyautogui.hotkey('enter')


    else:
        return chat(query)


def detect_gestures():
    cap = cv2.VideoCapture(0)
    screen_width, screen_height = pyautogui.size()
    hold_start_time = None
    while gesture_active and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                landmarks = hand_landmarks.landmark

                # Get finger tip positions
                thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
                index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                middle_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
                ring_tip = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP]
                pinky_tip = landmarks[mp_hands.HandLandmark.PINKY_TIP]

                # Move cursor
                cursor_x = int(index_tip.x * screen_width)
                cursor_y = int(index_tip.y * screen_height)
                pyautogui.moveTo(cursor_x, cursor_y, duration=0.1)

                # Click detection
                if index_tip.y < middle_tip.y < ring_tip.y < pinky_tip.y:
                    if hold_start_time is None:
                        hold_start_time = time.time()
                    elif time.time() - hold_start_time > 1:
                        pyautogui.click()
                        hold_start_time = None
                else:
                    hold_start_time = None

                # Scroll control
                if index_tip.y < middle_tip.y:
                    pyautogui.scroll(50)
                elif index_tip.y > middle_tip.y:
                    pyautogui.scroll(-50)

                # Task view (Alt-Tab alternative)
                if (index_tip.y > middle_tip.y and
                        middle_tip.y > ring_tip.y and
                        ring_tip.y > pinky_tip.y):
                    pyautogui.hotkey('win', 'tab')
                    time.sleep(1)

        cv2.imshow("Hand Gesture Control", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


def listen_for_wake_word():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        while listening_active:
            try:
                print("Listening for wake word...")
                update_conversation("Listening for wake word...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
                query = recognizer.recognize_google(audio).lower()
                if "jarvis" in query:
                    say("Yes, how can I help?")
                    update_conversation("Jarvis: Yes, how can I help?")
                    listen_for_command()
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except Exception as e:
                print(f"Wake word error: {e}")
                update_conversation("Error in wake word detection")
                time.sleep(1)


def listen_for_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        try:
            print("Listening for command...")
            update_conversation("Listening for command...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            query = recognizer.recognize_google(audio).lower()
            update_conversation(f"You: {query}")

            response = processCommand(query)
            update_conversation(f"Jarvis: {response}")

            # Continue listening if not exit command
            if listening_active:
                listen_for_command()

        except sr.WaitTimeoutError:
            say("I didn't hear anything. Going back to sleep.")
            update_conversation("Jarvis: I didn't hear anything. Going back to sleep.")
        except sr.UnknownValueError:
            say("Sorry, I didn't catch that. Please try again.")
            update_conversation("Jarvis: Sorry, I didn't catch that. Please try again.")
            listen_for_command()
        except Exception as e:
            print(f"Command error: {e}")
            update_conversation("Error processing command")
            listen_for_command()


def update_conversation(text):
    conversation_display.config(state=tk.NORMAL)
    conversation_display.insert(tk.END, text + "\n")
    conversation_display.config(state=tk.DISABLED)
    conversation_display.see(tk.END)


def process_typed_command(event=None):
    command = text_input.get()
    if command:
        update_conversation(f"You: {command}")
        response = processCommand(command)
        update_conversation(f"Jarvis: {response}")
        text_input.delete(0, tk.END)


def toggle_air_gesture_mode():
    global gesture_active
    gesture_active = not gesture_active
    if gesture_active:
        status_label.config(text="Air Gesture Mode Active")
        threading.Thread(target=detect_gestures, daemon=True).start()
    else:
        status_label.config(text="Air Gesture Mode Inactive")
    update_conversation(f"Air gestures {'activated' if gesture_active else 'deactivated'}")


def start_listening():
    """Function to start listening for commands when button is clicked"""
    update_conversation("Listening button pressed. Speak now...")
    say("I'm listening, please speak now")

    # Start listening in a separate thread to prevent GUI freezing
    threading.Thread(target=listen_for_command, daemon=True).start()


# Initialize main GUI window
root = tk.Tk()
root.title("Jarvis AI Assistant")
root.geometry("700x700")
root.configure(bg="#0D1B2A")

# Style configuration
style = ttk.Style()
style.configure("TButton", font=("Arial", 12), padding=5)
style.configure("TEntry", font=("Arial", 12))

# Conversation display
conversation_display = scrolledtext.ScrolledText(
    root, height=15, width=65, bg="#1B263B", fg="white",
    font=("Arial", 12), state=tk.DISABLED
)
conversation_display.pack(pady=10)

# Status label
status_label = tk.Label(
    root, text="Say 'Jarvis' to activate or click Listen button",
    font=("Times New Roman", 14, "bold"),
    bg="#0D1B2A", fg="#FF4500"
)
status_label.pack(pady=5)

# Text input
text_input = ttk.Entry(root, width=50)
text_input.pack(pady=10)
text_input.bind("<Return>", process_typed_command)

# Buttons
button_frame = tk.Frame(root, bg="#0D1B2A")
button_frame.pack(pady=10)

submit_button = ttk.Button(button_frame, text="Submit", command=process_typed_command)
submit_button.grid(row=0, column=0, padx=5)

gesture_button = ttk.Button(button_frame, text="Toggle Gestures", command=toggle_air_gesture_mode)
gesture_button.grid(row=0, column=1, padx=5)

# New Listen button
listen_button = ttk.Button(button_frame, text="Listen", command=start_listening)
listen_button.grid(row=0, column=2, padx=5)

exit_button = ttk.Button(button_frame, text="Exit", command=root.quit)
exit_button.grid(row=0, column=3, padx=5)

# Start the wake word listener in a separate thread
threading.Thread(target=listen_for_wake_word, daemon=True).start()

# Start the GUI
root.mainloop()