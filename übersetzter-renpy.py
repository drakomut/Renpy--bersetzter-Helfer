import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel
from deep_translator import GoogleTranslator as DeepGoogleTranslator
import re
import time
import traceback
from datetime import datetime

class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RPY-Datei Übersetzer")

        # Frame für die Sprachenauswahl
        self.frame = tk.Frame(root)
        self.frame.pack(pady=20)

        # Canvas und Scrollbar für Sprachenauswahl
        self.canvas = tk.Canvas(self.frame)
        self.scrollbar = tk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Frame innerhalb des Canvas für die Sprachenauswahl
        self.lang_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.lang_frame, anchor="nw")

        # Sprachenauswahl
        self.languages = {
            'English': 'en',
            'German': 'de',
            'French': 'fr',
            'Spanish': 'es',
            'Italian': 'it',
            # Weitere Sprachen hier hinzufügen
        }

        # Ausgangssprache
        self.src_lang_label = tk.Label(self.lang_frame, text="Ausgangssprache:")
        self.src_lang_label.pack()
        self.src_lang = tk.StringVar(value='English')  # Standard auf Englisch
        self.src_lang_menu = tk.OptionMenu(self.lang_frame, self.src_lang, *self.languages.keys())
        self.src_lang_menu.pack(fill="x")

        # Zielsprache
        self.dest_lang_label = tk.Label(self.lang_frame, text="Zielsprache:")
        self.dest_lang_label.pack()
        self.dest_lang = tk.StringVar(value='German')  # Standard auf Deutsch
        self.dest_lang_menu = tk.OptionMenu(self.lang_frame, self.dest_lang, *self.languages.keys())
        self.dest_lang_menu.pack(fill="x")

        # Übersetzungsdienst auswählen
        self.service_label = tk.Label(self.lang_frame, text="Übersetzungsdienst:")
        self.service_label.pack()
        self.services = ['Deep Translator']
        self.selected_service = tk.StringVar(value=self.services[0])
        self.service_menu = tk.OptionMenu(self.lang_frame, self.selected_service, *self.services)
        self.service_menu.pack(fill="x")

        # Datei auswählen Button
        self.select_button = tk.Button(root, text="RPY-Datei auswählen", command=self.select_file)
        self.select_button.pack(pady=20)

        # Übersetzen Button
        self.translate_button = tk.Button(root, text="Übersetzen", command=self.translate_file, state=tk.DISABLED)
        self.translate_button.pack(pady=20)

        self.file_path = None
        self.translator = None

        # Update Canvas Größe nach Layout Änderungen
        self.lang_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def select_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("RPY-Dateien", "*.rpy")])
        if self.file_path:
            self.translate_button.config(state=tk.NORMAL)

    def translate_file(self):
        if not self.file_path:
            messagebox.showwarning("Keine Datei ausgewählt", "Bitte wählen Sie zuerst eine RPY-Datei aus.")
            return

        start_time = time.time()
        log_file_path = self.file_path.replace('.rpy', '_errors.log')
        errors = []

        try:
            # Übersetzungsdienst auswählen
            if self.selected_service.get() == 'Deep Translator':
                self.translator = DeepGoogleTranslator(source=self.languages[self.src_lang.get()],
                                                       target=self.languages[self.dest_lang.get()])
                translate_func = self.translate_deep
            else:
                raise ValueError("Unbekannter Übersetzungsdienst ausgewählt.")

            with open(self.file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            if not content.strip():  # Überprüfe, ob die Datei leer ist
                raise ValueError("Die Datei ist leer oder konnte nicht gelesen werden.")

            # Fortschrittsfenster erstellen
            progress_window = Toplevel(self.root)
            progress_window.title("Übersetzung Fortschritt")
            progress_label = tk.Label(progress_window, text="Starte Übersetzung...")
            progress_label.pack(pady=20)

            translated_lines = []
            lines = content.splitlines()
            total_lines = len(lines)
            last_comment_line = None

            # Regex für Kommentarzeilen, Textzeilen innerhalb von Anführungszeichen und Funktionsaufrufe
            regex_comment = r'^\s*#\s*(.*?)(?:"([^"]*)")?$'
            regex_text = r'^\s*(\w+)\s*"([^"]+)"'
            regex_function = r'^\s*(\w+\([^)]*\))\s*"([^"]+)"'

            for i, line in enumerate(lines):
                progress_label.config(text=f"Übersetze Zeile {i + 1} von {total_lines}...")
                progress_window.update_idletasks()

                match_comment = re.match(regex_comment, line)
                match_text = re.match(regex_text, line)
                match_function = re.match(regex_function, line)

                if match_comment:
                    last_comment_line = line
                elif match_text:
                    speaker = match_text.group(1)
                    original_text = match_text.group(2)
                    if speaker == "old":  # Zeilen mit "old" nicht übersetzen
                        translated_lines.append(line)
                    else:
                        try:
                            translated_text = translate_func(original_text)
                        except Exception as e:
                            errors.append(f"Fehler bei der Übersetzung von '{original_text}': {str(e)}")
                            translated_text = original_text  # Verwende den Originaltext bei einem Fehler

                        if last_comment_line:
                            translated_lines.append(last_comment_line)
                            last_comment_line = None  # Zurücksetzen
                        translated_lines.append(f'    {speaker} "{translated_text}"')
                elif match_function:
                    function_call = match_function.group(1)
                    original_text = match_function.group(2)
                    try:
                        translated_text = translate_func(original_text)
                    except Exception as e:
                        errors.append(f"Fehler bei der Übersetzung von '{original_text}': {str(e)}")
                        translated_text = original_text  # Verwende den Originaltext bei einem Fehler

                    if last_comment_line:
                        translated_lines.append(last_comment_line)
                        last_comment_line = None  # Zurücksetzen
                    translated_lines.append(f'    {function_call} "{translated_text}"')
                else:
                    translated_lines.append(line)

            # Entferne doppelte Kommentarzeilen und falsche Einrückungen
            cleaned_lines = []
            previous_line = None

            for line in translated_lines:
                # Entferne doppelte Zeilen und zusätzliche Einrückungen
                if line.startswith("#") and previous_line and line == previous_line:
                    continue  # Überspringe doppelte Kommentarzeilen
                if previous_line and previous_line.strip() and previous_line.strip().startswith("#") and not line.strip().startswith("#"):
                    cleaned_lines.append("\n")  # Leerzeile hinzufügen zwischen Kommentar und Übersetzung
                cleaned_lines.append(line)
                previous_line = line

            # Header mit Zeitstempel hinzufügen
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            header = f"# TODO: Translation updated at {timestamp}\n\n"
            translated_content = header + "\n".join(cleaned_lines)

            # Speichere den übersetzten Inhalt
            translated_file_path = self.file_path.replace('.rpy', '_translated.rpy')
            with open(translated_file_path, 'w', encoding='utf-8') as file:
                file.write(translated_content)

            # Speichere das Fehlerprotokoll
            if errors:
                with open(log_file_path, 'w', encoding='utf-8') as log_file:
                    for error in errors:
                        log_file.write(f"{error}\n")

            end_time = time.time()
            duration = end_time - start_time
            progress_label.config(
                text=f"Übersetzung abgeschlossen. Dauer: {duration:.2f} Sekunden.\nÜbersetzte Datei: {translated_file_path}\nFehlerprotokoll: {log_file_path}")

        except Exception as e:
            with open(log_file_path, 'w', encoding='utf-8') as log_file:
                log_file.write(traceback.format_exc())
            messagebox.showerror("Fehler", f"Ein Fehler ist aufgetreten: {str(e)}")

    def translate_deep(self, text):
        if self.translator is None:
            raise ValueError("Deep Translator ist nicht initialisiert.")
        try:
            return self.translator.translate(text)
        except Exception as e:
            raise RuntimeError(f"Fehler bei der Deep Translator-Übersetzung: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = TranslatorApp(root)
    root.mainloop()

