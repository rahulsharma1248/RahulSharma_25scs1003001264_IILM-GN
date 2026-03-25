import speech_recognition as sr
import pyttsx3
import webbrowser
import os
import subprocess
from datetime import datetime
import threading
import re
from openai import OpenAI


class Athena:
    def __init__(self, openai_api_key=None):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.setup_voice()
        self.desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        self.running = True
        self.listening_active = True


        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            self.client = OpenAI(api_key=self.openai_api_key)
            self.chatgpt_enabled = True
            self.conversation_history = []
        else:
            self.chatgpt_enabled = False
            print("Warning: OpenAI API key not found. ChatGPT features will be disabled.")

    def setup_voice(self):
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        self.engine.setProperty('rate', 200)
        self.engine.setProperty('volume', 1.0)
        try:
            self.engine.setProperty('pitch', 1.5)
        except:
            pass

    def speak(self, text):
        print(f"Athena: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self):
        with sr.Microphone() as source:
            print("Listening...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                text = self.recognizer.recognize_google(audio)
                print(f"You said: {text}")
                self.speak("Got it")
                return text.lower()
            except sr.WaitTimeoutError:
                return ""
            except sr.UnknownValueError:
                self.speak("Sorry, I didn't catch that. Could you repeat please?")
                return ""
            except sr.RequestError:
                self.speak("Sorry, I'm having trouble connecting to the speech service")
                return ""

    def ask_chatgpt(self, question):

        if not self.chatgpt_enabled:
            return "ChatGPT is not available. Please set up your OpenAI API key and billing."

        try:

            self.conversation_history.append({
                "role": "user",
                "content": question
            })


            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system",
                     "content": "You are Athena, a helpful and friendly AI assistant. Keep your responses concise and conversational, as they will be spoken aloud."},
                    *self.conversation_history
                ],
                max_tokens=150,
                temperature=0.7
            )

            # Get the response text
            answer = response.choices[0].message.content.strip()

            # Add assistant response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": answer
            })

            # Keep conversation history manageable (last 10 messages)
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]

            return answer

        except Exception as e:
            error_msg = str(e)
            print(f"ChatGPT Error: {error_msg}")


            if "429" in error_msg or "quota" in error_msg.lower():
                return "You've exceeded your OpenAI creds"
            else:
                return "Sorry, I'm having trouble connecting to ChatGPT right now."

    def clear_conversation(self):

        self.conversation_history = []
        self.speak("Conversation history cleared! Let's start fresh~")

    def extract_query(self, command, keywords):
        query = command
        for keyword in keywords:
            query = query.replace(keyword, '')
        query = query.replace('for', '').replace('about', '').replace('the', '').strip()
        return query

    def google_search(self, query):
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        try:
            edge_path = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
            if os.path.exists(edge_path):
                subprocess.Popen([edge_path, search_url])
            else:
                webbrowser.open(search_url)
            self.speak(f"Searching Google for {query}! Here you go~")
        except Exception as e:
            self.speak("Oh no! I couldn't open the browser. Sorry~")

    def youtube_search(self, query):
        search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        try:
            webbrowser.open(search_url)
            self.speak(f"Searching YouTube for {query}! Enjoy~")
        except Exception as e:
            self.speak("Oh no! I couldn't open YouTube. Sorry~")

    def open_website(self, site):
        sites = {
            'youtube': 'https://www.youtube.com',
            'gmail': 'https://mail.google.com',
            'github': 'https://github.com',
            'reddit': 'https://www.reddit.com',
            'twitter': 'https://twitter.com',
            'facebook': 'https://www.facebook.com',
            'instagram': 'https://www.instagram.com',
            'linkedin': 'https://www.linkedin.com',
            'amazon': 'https://www.amazon.com',
            'netflix': 'https://www.netflix.com'
        }

        if site in sites:
            try:
                webbrowser.open(sites[site])
                self.speak(f"Opening {site} for you! Here we go~")
            except Exception as e:
                self.speak(f"Oh no! I couldn't open {site}. Sorry~")
        else:
            if not site.startswith('http'):
                site = 'https://' + site
            try:
                webbrowser.open(site)
                self.speak(f"Opening the website! Here we go~")
            except Exception as e:
                self.speak("Hmm, I couldn't open that website. Sorry~")

    def get_time(self):
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        self.speak(f"It's {time_str} right now!")

    def get_date(self):
        now = datetime.now()
        date_str = now.strftime("%B %d, %Y")
        self.speak(f"Today is {date_str}!")

    def create_text_file(self, filename):
        if not filename.endswith('.txt'):
            filename += '.txt'
        filepath = os.path.join(self.desktop_path, filename)
        try:
            with open(filepath, 'w') as f:
                f.write(f"File created by Athena on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.speak(f"Yay! Created {filename} on your desktop~")
        except Exception as e:
            self.speak(f"Oopsie! I couldn't create the file. Sorry~")

    def delete_text_file(self, filename):
        if not filename.endswith('.txt'):
            filename += '.txt'
        filepath = os.path.join(self.desktop_path, filename)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                self.speak(f"Done! Deleted {filename} from your desktop~")
            else:
                self.speak(f"Hmm, I couldn't find {filename} on your desktop. Are you sure it exists?")
        except Exception as e:
            self.speak(f"Oh no! I couldn't delete the file. Sorry~")

    def list_desktop_files(self):
        try:
            files = [f for f in os.listdir(self.desktop_path) if os.path.isfile(os.path.join(self.desktop_path, f))]
            if files:
                file_count = len(files)
                self.speak(f"You have {file_count} files on your desktop. Let me list them for you!")
                for i, file in enumerate(files[:10], 1):
                    print(f"{i}. {file}")
                if len(files) > 10:
                    self.speak(f"And {len(files) - 10} more files!")
            else:
                self.speak("Your desktop is empty! So clean~")
        except Exception as e:
            self.speak("Oh no! I couldn't read your desktop. Sorry~")

    def open_application(self, app_name):
        apps = {
            'paint': 'mspaint.exe',
            'calculator': 'calc.exe',
            'notepad': 'notepad.exe',
            'settings': 'ms-settings:',
            'file explorer': 'explorer.exe',
            'explorer': 'explorer.exe',
            'edge': 'msedge.exe',
            'microsoft edge': 'msedge.exe',
            'chrome': 'chrome.exe',
            'google chrome': 'chrome.exe',
            'word': 'winword.exe',
            'excel': 'excel.exe',
            'powerpoint': 'powerpnt.exe',
            'outlook': 'outlook.exe',
            'command prompt': 'cmd.exe',
            'terminal': 'cmd.exe',
            'task manager': 'taskmgr.exe'
        }

        if app_name in apps:
            try:
                if app_name == 'settings':
                    os.startfile(apps[app_name])
                else:
                    subprocess.Popen(apps[app_name], shell=True)
                self.speak(f"Opening {app_name} for you! Here we go~")
            except Exception as e:
                self.speak(f"Oh no! I couldn't open {app_name}. Sorry~")
        else:
            self.speak(f"Hmm, I don't know how to open {app_name} yet. Maybe teach me later?")

    def shutdown_computer(self):
        self.speak("Are you sure you want to shut down? Say yes to confirm or no to cancel.")
        confirmation = self.listen()
        if confirmation and 'yes' in confirmation:
            self.speak("Okay, shutting down the computer. Goodbye!")
            os.system("shutdown /s /t 1")
        else:
            self.speak("Shutdown cancelled! We can keep working together~")

    def restart_computer(self):
        self.speak("Are you sure you want to restart? Say yes to confirm or no to cancel.")
        confirmation = self.listen()
        if confirmation and 'yes' in confirmation:
            self.speak("Okay, restarting the computer. See you in a moment!")
            os.system("shutdown /r /t 1")
        else:
            self.speak("Restart cancelled! Let's continue~")

    def set_reminder(self, reminder_text):
        self.speak("How many minutes should I remind you in?")
        time_response = self.listen()

        if time_response:
            numbers = re.findall(r'\d+', time_response)
            if numbers:
                minutes = int(numbers[0])
                self.speak(f"Okay! I'll remind you in {minutes} minutes about: {reminder_text}")

                def remind():
                    import time
                    time.sleep(minutes * 60)
                    self.speak(f"Reminder! {reminder_text}")

                threading.Thread(target=remind, daemon=True).start()
            else:
                self.speak("I didn't catch the time. Let's try again later~")

    def process_command(self, command):
        if not command:
            return


        if any(word in command for word in ['exit', 'quit', 'goodbye', 'bye', 'stop']):
            self.speak("Aww, goodbye! Have an amazing day! See you soon~")
            self.running = False
            return


        elif 'clear conversation' in command or 'clear chat' in command or 'forget conversation' in command:
            self.clear_conversation()


        elif any(phrase in command for phrase in ['what time', 'current time', 'time is it']):
            self.get_time()


        elif any(phrase in command for phrase in ['what date', 'what day', 'today date', 'what is today']):
            self.get_date()


        elif 'youtube' in command:
            if 'open' in command and command.count(' ') <= 2:
                self.open_website('youtube')
            else:
                query = self.extract_query(command, ['youtube', 'search', 'on'])
                if query:
                    self.youtube_search(query)
                else:
                    self.open_website('youtube')


        elif any(word in command for word in ['search', 'google', 'look up', 'find']):
            query = self.extract_query(command, ['search', 'google', 'look up', 'find'])
            if query:
                self.google_search(query)
            else:
                self.speak("What would you like me to search for? I'm ready!")


        elif 'open' in command and any(word in command for word in ['website', 'site', '.com', 'www']):
            site = self.extract_query(command, ['open', 'website', 'site'])
            self.open_website(site)


        elif any(site in command for site in
                 ['gmail', 'github', 'reddit', 'twitter', 'facebook', 'instagram', 'linkedin', 'amazon', 'netflix']):
            for site in ['gmail', 'github', 'reddit', 'twitter', 'facebook', 'instagram', 'linkedin', 'amazon',
                         'netflix']:
                if site in command:
                    self.open_website(site)
                    break


        elif 'create' in command and 'file' in command:
            filename = self.extract_query(command, ['create', 'file', 'named', 'called'])
            if filename:
                self.create_text_file(filename)
            else:
                self.speak("Please tell me what to name the file~")

        elif 'delete' in command and 'file' in command:
            filename = self.extract_query(command, ['delete', 'file', 'named', 'called'])
            if filename:
                self.delete_text_file(filename)
            else:
                self.speak("Which file should I delete? Please tell me~")

        elif any(phrase in command for phrase in ['list files', 'show files', 'what files', 'files on desktop']):
            self.list_desktop_files()


        elif 'open' in command:
            app = self.extract_query(command, ['open', 'launch', 'start'])
            self.open_application(app)


        elif any(phrase in command for phrase in ['shut down', 'shutdown', 'turn off computer']):
            self.shutdown_computer()

        elif any(phrase in command for phrase in ['restart', 'reboot']):
            self.restart_computer()


        elif 'remind me' in command or 'set reminder' in command:
            reminder = self.extract_query(command, ['remind me', 'set reminder', 'to', 'about'])
            if reminder:
                self.set_reminder(reminder)
            else:
                self.speak("What should I remind you about?")


        elif 'help' in command or 'what can you do' in command or 'commands' in command:
            self.speak("""Yay! Let me tell you what I can do! I can search Google or YouTube, 
                open websites like Gmail, GitHub, Reddit, and more! I can tell you the time and date,
                create and delete text files, list files on your desktop,
                open Paint, Calculator, Notepad, Settings, File Explorer, and other apps! 
                I can even set reminders, shut down or restart your computer!
                Plus, I can answer any questions using ChatGPT! Just ask me anything!
                Say 'clear conversation' to start fresh with ChatGPT.
                Just talk to me naturally! I'm here to help you!""")


        else:
            if self.chatgpt_enabled:
                self.speak("Let me think about that...")
                answer = self.ask_chatgpt(command)
                self.speak(answer)
            else:
                self.speak("Hmm, I didn't quite understand that. Say help to hear what I can do for you~")

    def run(self):
        if self.chatgpt_enabled:
            self.speak(
                "Hiii! I'm Athena, your personal AI assistant , I'm so excited to help you today! What can I do for you?")
        else:
            self.speak(
                "Hiii! I'm Athena, your personal AI assistant! I'm so excited to help you today! What can I do for you?")

        while self.running:
            command = self.listen()
            if command:
                self.process_command(command)


if __name__ == "__main__":
    print("=" * 50)
    print("ATHENA - AI Adaptive Assistant with ChatGPT")
    print("=" * 50)
    print("\nInitializing Athena...")


    api_key = "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"

    print("\nCommands you can use:")
    print("- 'search [query]' or 'google [query]'")
    print("- 'youtube [query]' or 'search youtube [query]'")
    print("- 'open [website]' (gmail, github, reddit, etc.)")
    print("- 'what time is it' or 'what's the date'")
    print("- 'create file [filename]'")
    print("- 'delete file [filename]'")
    print("- 'list files' or 'show files on desktop'")
    print("- 'open [app name]' (paint, calculator, notepad, etc.)")
    print("- 'remind me to [task]'")
    print("- 'shut down' or 'restart'")
    print("- 'clear conversation' - Clear ChatGPT history")
    print("- 'help' for full assistance")
    print("- 'exit' or 'goodbye' to quit")
    print("- Or just ask me any question! I'll use ChatGPT to answer!")
    print("\n" + "=" * 50 + "\n")

    athena = Athena(openai_api_key=api_key)
    athena.run()