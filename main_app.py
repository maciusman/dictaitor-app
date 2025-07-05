# X:\Aplikacje\dictaitor\main_app.py
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
import logging
import webbrowser
from functools import partial
from typing import Optional, List, Dict, Any, Callable

# Importy z naszych modułów
from modules.config_manager import save_config, load_config
from modules.audio_recorder import AudioRecorder

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("DictAItorApp")

# Sprawdzenie dostępności bibliotek
try:
    import whisper
    WHISPER_AVAILABLE = True
    try:
        from modules.local_stt import transcribe_audio_local, AVAILABLE_WHISPER_MODELS, get_available_models
        LOCAL_STT_MODULE_AVAILABLE = True
        actual_models = get_available_models()
        if actual_models:
            AVAILABLE_WHISPER_MODELS = actual_models
    except ImportError:
        LOCAL_STT_MODULE_AVAILABLE = False
        AVAILABLE_WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]
except ImportError:
    WHISPER_AVAILABLE = False
    LOCAL_STT_MODULE_AVAILABLE = False
    AVAILABLE_WHISPER_MODELS = ["tiny", "base", "small", "medium", "large", "turbo"]

try:
    from modules.openai_whisper_client import OpenAIWhisperClient
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from PIL import Image

# Globalne ustawienia wyglądu
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Stałe aplikacji
APP_NAME = "DictAItor"
APP_VERSION = "1.0.2" # Wersja z poprawką logiki UI
WINDOW_WIDTH = 700
WINDOW_HEIGHT = 750

# Ścieżki
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(CURRENT_DIR, "assets")
RECORDINGS_DIR = os.path.join(CURRENT_DIR, "recordings")
LOGO_FILE_DARK = os.path.join(ASSETS_DIR, "logo.png")
LOGO_FILE_LIGHT = os.path.join(ASSETS_DIR, "logo-dark.png")
ICON_FILE = os.path.join(ASSETS_DIR, "icon.ico")

# Klucze konfiguracji
OPENAI_KEY_CONFIG = 'openai_api_key'
PREFERRED_MODE_CONFIG = 'preferred_mode'
PREFERRED_MODEL_CONFIG = 'preferred_model'
PREFERRED_LANGUAGE_HINT_CONFIG = 'preferred_language_hint'
PREFERRED_OUTPUT_FORMAT_CONFIG = 'preferred_output_format'
APPEARANCE_MODE_CONFIG = 'appearance_mode'

for directory in [ASSETS_DIR, RECORDINGS_DIR]:
    os.makedirs(directory, exist_ok=True)


class DictAItorApp:
    def __init__(self, root: ctk.CTk) -> None:
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        try:
            if os.path.exists(ICON_FILE): self.root.iconbitmap(ICON_FILE)
            else: logger.warning(f"Plik ikony nie znaleziony: {ICON_FILE}")
        except Exception as e:
            logger.error(f"Nie można załadować ikony aplikacji: {e}")

        self.config = load_config()
        ctk.set_appearance_mode(self.config.get(APPEARANCE_MODE_CONFIG, "dark"))

        self.openai_key_value = self.config.get(OPENAI_KEY_CONFIG, '')
        self.recorder = AudioRecorder()
        
        if OPENAI_AVAILABLE:
            self.openai_client = OpenAIWhisperClient(api_key=self.openai_key_value)
            self.openai_client.debug_mode = True
        
        self.is_recording_app_state = False
        self.selected_whisper_model = ctk.StringVar()
        self.selected_language_hint = ctk.StringVar(value=self.config.get(PREFERRED_LANGUAGE_HINT_CONFIG, ''))
        self.selected_output_format = ctk.StringVar(value=self.config.get(PREFERRED_OUTPUT_FORMAT_CONFIG, "Oryginalny (Transkrypcja)"))
        
        preferred_model = self.config.get(PREFERRED_MODEL_CONFIG, '')
        if preferred_model and preferred_model in AVAILABLE_WHISPER_MODELS:
            self.selected_whisper_model.set(preferred_model)
        elif "turbo" in AVAILABLE_WHISPER_MODELS:
            self.selected_whisper_model.set("turbo")
        elif AVAILABLE_WHISPER_MODELS:
            self.selected_whisper_model.set(AVAILABLE_WHISPER_MODELS[1] if len(AVAILABLE_WHISPER_MODELS) > 1 else AVAILABLE_WHISPER_MODELS[0])

        preferred_mode = self.config.get(PREFERRED_MODE_CONFIG, '')
        if preferred_mode == 'local' and WHISPER_AVAILABLE:
            self.transcription_mode = ctk.StringVar(value="local")
        elif preferred_mode == 'openai' and OPENAI_AVAILABLE:
            self.transcription_mode = ctk.StringVar(value="openai")
        else:
            self.transcription_mode = ctk.StringVar(value="local" if WHISPER_AVAILABLE else "openai")
        
        self.last_recorded_file = None
        self.pulse_animation_id = None
        self.logo_image = None

        self._create_widgets()
        self._load_initial_config()
        
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # ### KLUCZOWA POPRAWKA: Wywołanie aktualizacji po stworzeniu widgetów ###
        self.root.after(50, self._update_transcription_mode)

    def _setup_output_formats(self):
        self.output_formats = {
            "Oryginalny (Transkrypcja)": {'task': 'transcribe', 'language': None},
            "Angielski (Tłumaczenie)": {'task': 'translate', 'language': None},
            "Polski (Tłumaczenie/Transkrypcja)": {'task': 'transcribe', 'language': 'pl'},
            "Niemiecki (Tłumaczenie/Transkrypcja)": {'task': 'transcribe', 'language': 'de'},
            "Francuski (Tłumaczenie/Transkrypcja)": {'task': 'transcribe', 'language': 'fr'},
            "Hiszpański (Tłumaczenie/Transkrypcja)": {'task': 'transcribe', 'language': 'es'},
            "Włoski (Tłumaczenie/Transkrypcja)": {'task': 'transcribe', 'language': 'it'},
            "Rosyjski (Tłumaczenie/Transkrypcja)": {'task': 'transcribe', 'language': 'ru'}
        }

    def _load_initial_config(self) -> None:
        if hasattr(self, 'openai_api_entry') and self.openai_key_value:
            self.openai_api_entry.insert(0, self.openai_key_value)

    def _create_widgets(self) -> None:
        self._setup_output_formats()

        tabview = ctk.CTkTabview(self.root, corner_radius=8)
        tabview.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        tab_transcription = tabview.add("Transkrypcja")
        tab_settings = tabview.add("Ustawienia")
        
        tab_transcription.grid_columnconfigure(0, weight=1)
        tab_transcription.grid_rowconfigure(5, weight=1)
        tab_settings.grid_columnconfigure(0, weight=1)
        tab_settings.grid_rowconfigure(2, weight=1)

        self._create_transcription_tab_widgets(tab_transcription)
        self._create_settings_tab_widgets(tab_settings)

    def _create_transcription_tab_widgets(self, parent_tab: ctk.CTkFrame):
        self._create_header(parent_tab, row=0)
        self._create_transcription_mode_section(parent_tab, row=1)
        self._create_model_section(parent_tab, row=2)
        self._create_action_section(parent_tab, row=3)
        self._create_file_selection_section(parent_tab, row=4)
        self._create_transcription_section(parent_tab, row=5)

    def _create_settings_tab_widgets(self, parent_tab: ctk.CTkFrame):
        self._create_api_section(parent_tab, row=0)
        self._create_appearance_section(parent_tab, row=1)
        self._create_footer_section(parent_tab, row=2)

    def _create_header(self, parent: ctk.CTkFrame, row: int):
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.grid(row=row, column=0, sticky="ew", pady=(0, 15))
        try:
            light_image = Image.open(LOGO_FILE_LIGHT) if os.path.exists(LOGO_FILE_LIGHT) else None
            dark_image = Image.open(LOGO_FILE_DARK) if os.path.exists(LOGO_FILE_DARK) else None

            if dark_image:
                original_width, original_height = dark_image.size
                aspect_ratio = original_width / original_height
                target_height = 84
                target_width = int(target_height * aspect_ratio)
                
                self.logo_image = ctk.CTkImage(light_image=light_image, dark_image=dark_image, size=(target_width, target_height))
                logo_label = ctk.CTkLabel(header_frame, image=self.logo_image, text="")
                logo_label.pack(pady=10)
            else:
                 logger.warning(f"Główne logo nie znalezione: {LOGO_FILE_DARK}")
        except Exception as e:
            logger.error(f"Błąd ładowania logo: {e}")

    def _create_model_section(self, parent: ctk.CTkFrame, row: int):
        model_frame_container = ctk.CTkFrame(parent)
        model_frame_container.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        model_frame_container.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(model_frame_container, text="Opcje Transkrypcji", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=(5,5), sticky="w")
        
        # ### KLUCZOWA POPRAWKA: Kontener modelu jest teraz tworzony i zarządzany przez grid ###
        self.whisper_models_container = ctk.CTkFrame(model_frame_container, fg_color="transparent")
        # Nie umieszczamy go jeszcze w siatce - zrobi to metoda _update_transcription_mode

        ctk.CTkLabel(self.whisper_models_container, text="Model Whisper:").pack(side="left")
        self.whisper_model_combobox = ctk.CTkComboBox(self.whisper_models_container, variable=self.selected_whisper_model, values=AVAILABLE_WHISPER_MODELS, state="readonly")
        self.whisper_model_combobox.pack(side="left", padx=10, fill="x", expand=True)

        ctk.CTkLabel(model_frame_container, text="Język wejściowy (wskazówka):").grid(row=2, column=0, padx=(15, 5), pady=5, sticky="w")
        self.language_hint_combobox = ctk.CTkComboBox(model_frame_container, state="readonly", command=self._on_language_hint_selected)
        self.language_hint_combobox.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        language_options = [("🌐 Automatycznie", ""), ("🇵🇱 Polski", "pl"), ("🇬🇧 Angielski", "en"), ("🇩🇪 Niemiecki", "de"), ("🇫🇷 Francuski", "fr"), ("🇪🇸 Hiszpański", "es"), ("🇮🇹 Włoski", "it"), ("🇷🇺 Rosyjski", "ru")]
        self.language_hints_display = [lang[0] for lang in language_options]
        self._language_hint_codes = {lang[0]: lang[1] for lang in language_options}
        self._language_code_to_display = {code: name for name, code in self._language_hint_codes.items()}
        self._language_code_to_display[""] = "🌐 Automatycznie"
        self.language_hint_combobox.configure(values=self.language_hints_display)
        self.language_hint_combobox.set(self._language_code_to_display.get(self.selected_language_hint.get(), "🌐 Automatycznie"))

        ctk.CTkLabel(model_frame_container, text="Format wyjściowy (cel):").grid(row=3, column=0, padx=(15, 5), pady=5, sticky="w")
        self.output_format_combobox = ctk.CTkComboBox(model_frame_container, variable=self.selected_output_format, values=list(self.output_formats.keys()), state="readonly", command=self._on_output_format_selected)
        self.output_format_combobox.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

    def _create_api_section(self, parent, row):
        api_frame_container = ctk.CTkFrame(parent)
        api_frame_container.grid(row=row, column=0, sticky="ew", pady=10, padx=10)
        api_frame_container.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(api_frame_container, text="Konfiguracja OpenAI API", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=3, padx=10, pady=(5,0), sticky="w")
        ctk.CTkLabel(api_frame_container, text="Klucz API:").grid(row=1, column=0, padx=(15, 5), pady=5, sticky="w")
        self.openai_api_entry = ctk.CTkEntry(api_frame_container, show="*")
        self.openai_api_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        save_key_button = ctk.CTkButton(api_frame_container, text="Zapisz Klucz", command=self.save_openai_key_action, corner_radius=100)
        save_key_button.grid(row=1, column=2, padx=(5, 15), pady=5)

    def _create_appearance_section(self, parent, row):
        appearance_frame = ctk.CTkFrame(parent)
        appearance_frame.grid(row=row, column=0, sticky="ew", pady=10, padx=10)
        ctk.CTkLabel(appearance_frame, text="Wygląd Aplikacji", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5,5))
        switch_frame = ctk.CTkFrame(appearance_frame, fg_color="transparent")
        switch_frame.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(switch_frame, text="Tryb Ciemny / Jasny").pack(side="left")
        self.theme_switch = ctk.CTkSwitch(switch_frame, text="", command=self._change_appearance_mode, onvalue="dark", offvalue="light")
        self.theme_switch.pack(side="left", padx=10)
        if ctk.get_appearance_mode().lower() == "dark": self.theme_switch.select()

    def _create_footer_section(self, parent, row):
        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.grid(row=row, column=0, sticky="sew", pady=(10, 5), padx=10)
        footer_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(footer_frame, text="Autor: Maciej Walczuk", font=ctk.CTkFont(size=11)).pack()
        link_label = ctk.CTkLabel(footer_frame, text="Kontakt: LinkedIn", font=ctk.CTkFont(size=11, underline=True), text_color=("#3B8ED0", "#4A9EE3"), cursor="hand2")
        link_label.pack()
        link_label.bind("<Button-1>", lambda e: self._open_linkedin())

    def _create_transcription_mode_section(self, parent, row):
        mode_frame_container = ctk.CTkFrame(parent)
        mode_frame_container.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(mode_frame_container, text="Tryb Transkrypcji", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5,0))
        mode_frame = ctk.CTkFrame(mode_frame_container, fg_color="transparent")
        mode_frame.pack(fill="x", padx=10, pady=(0,10))
        whisper_radio = ctk.CTkRadioButton(mode_frame, text="Lokalna (Whisper)", variable=self.transcription_mode, value="local", command=self._update_transcription_mode)
        whisper_radio.pack(side="left", padx=(0, 20))
        if not WHISPER_AVAILABLE: whisper_radio.configure(state="disabled")
        if OPENAI_AVAILABLE:
            openai_radio = ctk.CTkRadioButton(mode_frame, text="Online (OpenAI API)", variable=self.transcription_mode, value="openai", command=self._update_transcription_mode)
            openai_radio.pack(side="left", padx=(0, 10))
            if not OPENAI_AVAILABLE: openai_radio.configure(state="disabled")

    def _create_action_section(self, parent, row):
        action_frame_container = ctk.CTkFrame(parent)
        action_frame_container.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(action_frame_container, text="Akcje", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5,0))
        action_frame = ctk.CTkFrame(action_frame_container, fg_color="transparent")
        action_frame.pack(fill="x", padx=10, pady=(0,10))
        self.record_button = ctk.CTkButton(action_frame, text="Rejestruj Mowę", command=self.toggle_recording, fg_color="#2c8057", hover_color="#35996a", corner_radius=100)
        self.record_button.pack(side="left", padx=5, pady=5)
        self.transcribe_button = ctk.CTkButton(action_frame, text="Transkrybuj", command=self.transcribe_action, state="disabled", corner_radius=100)
        self.transcribe_button.pack(side="left", padx=5, pady=5)
        self.status_frame = ctk.CTkFrame(action_frame, fg_color="transparent", border_width=0)
        self.status_frame.pack(side="left", padx=10, pady=0, fill="x", expand=True)
        self.recording_indicator_label = ctk.CTkLabel(self.status_frame, text="", width=10)
        self.recording_indicator_label.pack(side="left", padx=(0,5))
        self.status_label = ctk.CTkLabel(self.status_frame, text="Status: Gotowy")
        self.status_label.pack(side="left", pady=5)
        self.progress_bar = ctk.CTkProgressBar(action_frame_container, orientation="horizontal", mode="indeterminate")

    def _create_file_selection_section(self, parent, row):
        file_frame_container = ctk.CTkFrame(parent)
        file_frame_container.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(file_frame_container, text="Wybór Pliku Audio (opcjonalnie)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5,0))
        file_frame = ctk.CTkFrame(file_frame_container, fg_color="transparent")
        file_frame.pack(fill="x", padx=10, pady=(0,10))
        file_frame.grid_columnconfigure(0, weight=1)
        self.file_path_label = ctk.CTkLabel(file_frame, text="Brak wybranego pliku", text_color="gray")
        self.file_path_label.pack(side="left", fill="x", expand=True, padx=(0, 10))
        browse_button = ctk.CTkButton(file_frame, text="Wybierz Plik Audio", command=self.browse_audio_file, width=150, corner_radius=100)
        browse_button.pack(side="right", padx=(5,0))
        folder_button = ctk.CTkButton(file_frame, text="Pokaż folder", command=self.open_recordings_folder, width=120, corner_radius=100)
        folder_button.pack(side="right", padx=5)

    def _create_transcription_section(self, parent, row):
        result_frame_container = ctk.CTkFrame(parent)
        result_frame_container.grid(row=row, column=0, sticky="nsew", pady=(0, 0))
        result_frame_container.grid_rowconfigure(1, weight=1)
        result_frame_container.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(result_frame_container, text="Transkrypcja", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=(5,0), sticky="w")
        self.transcription_text = ctk.CTkTextbox(result_frame_container, wrap="word", font=("Arial", 12), state="disabled")
        self.transcription_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))
        self.copy_confirm_label = ctk.CTkLabel(self.transcription_text, text="✓ Skopiowano do schowka", corner_radius=10, fg_color=("#DDDDDD", "#333333"))

    # ### Metody Logiki Biznesowej (Poprawione i Kompletne) ###

    def _on_language_hint_selected(self, choice: str):
        code = self._language_hint_codes.get(choice, "")
        self.selected_language_hint.set(code)
        self._save_settings({PREFERRED_LANGUAGE_HINT_CONFIG: code})
        
    def _on_output_format_selected(self, choice: str): 
        self._save_settings({PREFERRED_OUTPUT_FORMAT_CONFIG: choice})

    def _transcribe_local_thread(self):
        format_key = self.selected_output_format.get()
        format_logic = self.output_formats.get(format_key, {'task': 'transcribe', 'language': None})
        
        task = format_logic['task']
        language_target = format_logic['language']
        
        language_hint = self.selected_language_hint.get() if task == 'transcribe' and language_target is None else None

        transcript, error_msg = transcribe_audio_local(self.last_recorded_file, 
                                                       model_name=self.selected_whisper_model.get(), 
                                                       language=language_target or language_hint, 
                                                       task=task)
        self._update_gui(lambda: self._handle_transcription_result(transcript, error_msg))

    def _transcribe_openai_thread(self):
        format_key = self.selected_output_format.get()
        format_logic = self.output_formats.get(format_key, {'task': 'transcribe', 'language': None})
        
        language_hint = self.selected_language_hint.get() if format_logic['task'] == 'transcribe' and format_logic['language'] is None else None

        if format_logic['task'] == 'translate':
            transcript, error_msg = self.openai_client.translate_audio_to_english(self.last_recorded_file)
        else:
            language_target = format_logic['language']
            transcript, error_msg = self.openai_client.transcribe_audio(self.last_recorded_file, language=language_target or language_hint)
            
        self._update_gui(lambda: self._handle_transcription_result(transcript, error_msg))

    def _open_linkedin(self):
        webbrowser.open_new_tab("https://www.linkedin.com/in/walczuk-maciej/")

    def _change_appearance_mode(self):
        new_mode = self.theme_switch.get()
        ctk.set_appearance_mode(new_mode)
        self._save_settings({APPEARANCE_MODE_CONFIG: new_mode})

    def _pulse_recording_indicator(self, pulse_on=True):
        if self.is_recording_app_state:
            color_dark = "#ff4d4d" if pulse_on else "#a04040"
            color_light = "#d00000" if pulse_on else "#800000"
            self.recording_indicator_label.configure(text="●", text_color=(color_light, color_dark))
            self.pulse_animation_id = self.root.after(700, lambda: self._pulse_recording_indicator(not pulse_on))
        else:
            self.recording_indicator_label.configure(text="")
            if self.pulse_animation_id:
                self.root.after_cancel(self.pulse_animation_id)
                self.pulse_animation_id = None

    def _start_recording(self):
        if not self.recorder.start_recording():
            self._show_message("error", "Błąd Nagrywania", "Nie można rozpocząć nagrywania.")
            return
            
        self.is_recording_app_state = True
        self.record_button.configure(text="Zatrzymaj Nagrywanie")
        self._update_status("Nagrywanie...")
        self.status_frame.configure(border_width=2, border_color=("#d00000", "#ff4d4d"))
        
        self.transcribe_button.configure(state="disabled")
        self.transcription_text.configure(state="normal")
        self.transcription_text.delete("1.0", "end")
        self.transcription_text.configure(state="disabled")
        
        self.last_recorded_file = None
        self.file_path_label.configure(text="Brak wybranego pliku", text_color="gray")
        self._pulse_recording_indicator()

    def _stop_recording(self):
        self.is_recording_app_state = False
        self._pulse_recording_indicator()
        self.status_frame.configure(border_width=0)
        self._update_status("Zapisywanie nagrania...")
        self._run_in_thread(self._stop_recording_thread)
    
    def _stop_recording_thread(self):
        filepath = self.recorder.stop_recording()
        def finish_recording():
            self.record_button.configure(text="Rejestruj Mowę")
            if filepath:
                self.last_recorded_file = filepath
                self.file_path_label.configure(text=f"Nagranie: {os.path.basename(filepath)}", text_color=("black", "white"))
                self._update_status("Zapisano nagranie")
                self.transcribe_button.configure(state="normal")
            else:
                self._update_status("Błąd zapisu")
                self.file_path_label.configure(text="Błąd zapisu", text_color="red")
                self._show_message("error", "Błąd Zapisu", "Nie udało się zapisać nagrania.")
        self._update_gui(finish_recording)

    def toggle_recording(self):
        if not self.is_recording_app_state:
            self._start_recording()
        else:
            self._stop_recording()

    def transcribe_action(self):
        if not self.last_recorded_file:
            self._show_message("warning", "Brak Nagrania", "Najpierw nagraj lub wskaż plik audio.")
            return
            
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 10))
        self.progress_bar.start()
        self.record_button.configure(state="disabled")
        self.transcribe_button.configure(state="disabled")
        
        if self.transcription_mode.get() == "local":
            self._run_in_thread(self._transcribe_local_thread)
        else:
            self._run_in_thread(self._transcribe_openai_thread)

    def _handle_transcription_result(self, transcript: Optional[str], error_msg: Optional[str]):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.record_button.configure(state="normal")
        self.transcribe_button.configure(state="normal" if self.last_recorded_file else "disabled")

        if error_msg:
            self._update_status("❌ Błąd transkrypcji")
            self._show_message("error", "Błąd Transkrypcji", error_msg)
            self.transcription_text.configure(state="normal")
            self.transcription_text.delete("1.0", "end")
            self.transcription_text.insert("end", f"--- BŁĄD ---\n{error_msg}\n")
            self.transcription_text.configure(state="disabled")
        elif transcript is not None:
            self._update_status("Transkrypcja zakończona.")
            self.transcription_text.configure(state="normal")
            self.transcription_text.delete("1.0", "end")
            self.transcription_text.insert("end", transcript)
            self.transcription_text.configure(state="disabled")
            self.root.clipboard_clear()
            self.root.clipboard_append(transcript)
            self._show_copy_confirmation()
        else:
            self._handle_transcription_result(None, "Wystąpił nieznany błąd.")

    def _show_copy_confirmation(self):
        self.copy_confirm_label.place(relx=0.5, rely=0.5, anchor="center")
        self._update_status("Transkrypcja skopiowana do schowka ✓")
        self.root.after(2500, self.copy_confirm_label.place_forget)

    def browse_audio_file(self):
        file_path = filedialog.askopenfilename(title="Wybierz plik audio", filetypes=[("Pliki Audio", "*.wav *.mp3 *.ogg *.flac"), ("Wszystkie pliki", "*.*")], initialdir=RECORDINGS_DIR)
        if file_path:
            self.last_recorded_file = file_path
            self.file_path_label.configure(text=f"Wybrany plik: {os.path.basename(file_path)}", text_color=("black", "white"))
            self.transcribe_button.configure(state="normal")
            self._update_status("Wybrano plik")

    def open_recordings_folder(self):
        try:
            if os.path.exists(RECORDINGS_DIR):
                os.startfile(RECORDINGS_DIR)
            else:
                self._show_message("warning", "Folder Nie Istnieje", f"Folder {RECORDINGS_DIR} nie istnieje.")
        except Exception as e:
            self._show_message("error", "Błąd", f"Nie można otworzyć folderu: {e}")

    # ### KLUCZOWA POPRAWKA: Przebudowana metoda aktualizacji widoku ###
    def _update_transcription_mode(self, event=None):
        mode = self.transcription_mode.get()
        is_local_mode = (mode == "local" and WHISPER_AVAILABLE)
        
        # Spójne zarządzanie widocznością za pomocą grid/grid_forget
        if is_local_mode:
            # Pokaż kontener w określonym miejscu siatki
            self.whisper_models_container.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(15, 5), pady=0)
        else:
            # Bezpiecznie usuń kontener z siatki
            self.whisper_models_container.grid_forget()

        self._save_settings({PREFERRED_MODE_CONFIG: mode})
        
        # Aktualizacja tekstu przycisku (opcjonalne)
        if is_local_mode:
            self.transcribe_button.configure(text="Transkrybuj Lokalnie")
        elif mode == "openai" and OPENAI_AVAILABLE:
            self.transcribe_button.configure(text="Transkrybuj przez OpenAI")

    def _save_settings(self, settings: Dict[str, Any]):
        self.config.update(settings)
        try:
            save_config(self.config)
        except Exception as e:
            logger.error(f"Błąd zapisywania konfiguracji: {e}")

    def save_openai_key_action(self):
        key = self.openai_api_entry.get().strip()
        if not key:
            self._show_message("warning", "Pusty Klucz", "Klucz API nie może być pusty.")
            return
            
        self._save_settings({OPENAI_KEY_CONFIG: key})
        self.openai_key_value = key
        
        if OPENAI_AVAILABLE and hasattr(self, 'openai_client'):
            self.openai_client.update_api_key(key)
            
        self._show_message("info", "Sukces", "Klucz API OpenAI został zapisany.")

    def _update_status(self, message: str):
        self.status_label.configure(text=f"Status: {message}")
        self.root.update_idletasks()

    def _show_message(self, msg_type: str, title: str, message: str):
        if msg_type == "info": messagebox.showinfo(title, message)
        elif msg_type == "warning": messagebox.showwarning(title, message)
        elif msg_type == "error": messagebox.showerror(title, message)
        
    def _run_in_thread(self, func: Callable, daemon: bool = True):
        threading.Thread(target=func, daemon=daemon).start()
        
    def _update_gui(self, func: Callable):
        self.root.after(0, func)

if __name__ == "__main__":
    root = ctk.CTk()
    app = DictAItorApp(root)
    root.mainloop()