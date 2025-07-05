# DictAItor - Twoje Osobiste Centrum Transkrypcji



**DictAItor** to nowoczesna, intuicyjna aplikacja desktopowa, która przekształca mowę na tekst. Nagrywaj notatki głosowe, spotkania czy wykłady i otrzymuj precyzyjne transkrypcje lub tłumaczenia za pomocą jednego kliknięcia. Dzięki wsparciu dla lokalnych modeli AI (Whisper) oraz potężnego API OpenAI, masz pełną kontrolę nad swoimi danymi i jakością wyników.

---

## Kluczowe Funkcje

✨ **Nowoczesny Interfejs**
- Czysty i przejrzysty design stworzony z użyciem CustomTkinter.
- Dwa motywy do wyboru: **jasny** i **ciemny**.
- Wygodny system zakładek oddzielający główne funkcje od ustawień.
- Pełna responsywność i skalowanie okna.

🎙️ **Elastyczne Źródła Dźwięku**
- **Nagrywanie na żywo:** Użyj wbudowanego rejestratora, aby natychmiast przechwycić swoje myśli.
- **Import plików:** Przeciągnij lub wybierz dowolny plik audio (`.wav`, `.mp3`, `.flac`, `.ogg`) do transkrypcji.

🧠 **Dwa Tryby Transkrypcji**
- **💻 Lokalna (Whisper):** Działa w 100% offline na Twoim komputerze. Idealne do prywatnych notatek i szybkiej pracy bez udostępniania danych.
- **☁️ Online (OpenAI API):** Wykorzystaj moc najnowszego modelu `whisper-1` od OpenAI dla najwyższej możliwej dokładności.

🌐 **Zaawansowane Tłumaczenia**
- Nie tylko transkrypcja! Aplikacja potrafi **tłumaczyć mowę z dowolnego języka** na:
  - Angielski (dedykowany tryb `translate`)
  - Polski, Niemiecki, Francuski, Hiszpański, Włoski i Rosyjski.

⚙️ **Inteligentne Udogodnienia**
- **Automatyczne kopiowanie do schowka:** Gotowy tekst jest od razu dostępny do wklejenia.
- **Wizualne wskaźniki:** Animowany pasek postępu i pulsujący wskaźnik nagrywania informują Cię o stanie aplikacji.
- **Zapisywanie ustawień:** Aplikacja pamięta Twój preferowany tryb, model i wygląd.

---

## Instalacja Krok po Kroku

Aby uruchomić DictAItor, potrzebujesz Pythona oraz zewnętrznego narzędzia FFmpeg.

### Krok 1: Instalacja Pythona (jeśli go nie masz)

1.  Pobierz instalator Pythona (zalecana wersja 3.9+) ze strony [python.org](https://www.python.org/downloads/).
2.  Uruchom instalator.
3.  **To najważniejszy krok:** Na pierwszym ekranie instalatora **koniecznie zaznacz opcję "Add Python to PATH"**.
    
4.  Dokończ instalację, klikając "Install Now".

### Krok 2: Instalacja FFmpeg (wymagane)

FFmpeg to kluczowe narzędzie, którego model Whisper używa do przetwarzania plików audio.

1.  Otwórz menu Start i wpisz **"PowerShell"**.
2.  Kliknij prawym przyciskiem myszy na "Windows PowerShell" i wybierz **"Uruchom jako administrator"**.
3.  W niebieskim oknie konsoli, które się pojawi, wklej poniższe polecenie i naciśnij Enter:
    ```powershell
    winget install "FFmpeg (Gyan)"
    ```
4.  Poczekaj, aż instalacja się zakończy. Może pojawić się prośba o zaakceptowanie warunków – zatwierdź ją.

### Krok 3: Instalacja Aplikacji DictAItor

1.  Na górze tej strony na GitHubie kliknij zielony przycisk **`< > Code`**, a następnie wybierz **"Download ZIP"**.
2.  Rozpakuj pobrany plik `.zip` do wybranego folderu na swoim komputerze (np. na Pulpit).
3.  Wejdź do rozpakowanego folderu. Znajdziesz tam plik `setup.bat`.
4.  Kliknij dwukrotnie na **`setup.bat`**, aby zainstalować wszystkie potrzebne biblioteki. Poczekaj cierpliwie, aż proces dobiegnie końca.

---

## Uruchamianie i Użytkowanie

Po zakończeniu instalacji, po prostu kliknij dwukrotnie na plik **`run_dictaitor.bat`** w folderze aplikacji.

### Jak to działa?

1.  **Wybierz Tryb:** Zdecyduj, czy chcesz użyć transkrypcji lokalnej (offline), czy online (OpenAI).
2.  **Wybierz Opcje:**
    - **Język wejściowy:** Daj modelowi wskazówkę, w jakim języku jest nagranie (lub zostaw "Automatycznie").
    - **Format wyjściowy:** Wybierz, czy chcesz otrzymać tekst w oryginalnym języku, czy przetłumaczony na inny.
3.  **Nagraj lub Wybierz Plik:**
    - Kliknij **"Rejestruj Mowę"**, aby zacząć nagrywanie.
    - Lub kliknij **"Wybierz Plik Audio"**, aby załadować istniejący plik.
4.  **Transkrybuj:** Kliknij przycisk **"Transkrybuj"**. Gotowy tekst pojawi się w polu poniżej i zostanie skopiowany do schowka.
5.  **Dostosuj Ustawienia:** W zakładce **"Ustawienia"** możesz:
    - Wprowadzić swój klucz API OpenAI.
    - Zmienić motyw aplikacji z ciemnego na jasny.

---

## Autor

Aplikacja stworzona i rozwijana przez:
*   **Maciej Walczuk**
*   **Kontakt:** [LinkedIn](https://www.linkedin.com/in/walczuk-maciej/)

---

## Licencja

Ten projekt jest udostępniany na zasadach licencji MIT. Możesz go dowolnie używać, modyfikować i rozpowszechniać.