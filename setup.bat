@echo off
chcp 65001 > nul
setlocal

echo ==============================================================
echo.
echo     Instalator zaleznosci dla aplikacji DictAItor
echo.
echo ==============================================================
echo.
echo Witaj! Ten skrypt przygotuje Twoj komputer do uruchomienia
echo aplikacji DictAItor.
echo.
echo Kroki, ktore wykonamy:
echo   1. Sprawdzimy, czy Python jest poprawnie zainstalowany.
echo   2. Zainstalujemy wszystkie niezbedne biblioteki Pythona.
echo   3. Pobioremy podstawowy model AI (Whisper 'base').
echo.
echo Upewnij sie, ze masz polaczenie z internetem.
echo.
echo Nacisnij dowolny klawisz, aby rozpoczac...
pause > nul
echo.

REM --- Krok 1: Sprawdzanie Pythona ---
echo --- Krok 1/3: Sprawdzanie srodowiska Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  [BLAD]
    echo  Nie znaleziono Pythona w Twoim systemie lub nie jest on
    echo  dodany do sciezki systemowej (PATH).
    echo.
    echo  Rozwiazanie:
    echo  a) Pobierz i zainstaluj Pythona ze strony: https://www.python.org/
    echo  b) Podczas instalacji KONIECZNIE zaznacz opcje "Add Python to PATH".
    echo.
    pause
    exit /b 1
)
echo  [OK] Znaleziono Pythona.
echo.

REM --- Krok 2: Instalacja bibliotek ---
echo --- Krok 2/3: Instalacja bibliotek z pliku requirements.txt...
echo  To moze potrwac kilka minut. Prosze o cierpliwosc.
echo.

python -m pip install --upgrade pip > nul
python -m pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  [BLAD]
    echo  Wystapil problem podczas instalacji bibliotek.
    echo.
    echo  Mozliwe przyczyny:
    echo  - Brak polaczenia z internetem.
    echo  - Problemy z uprawnieniami (sprobuj uruchomic ten plik jako administrator).
    echo  - Konflikty w srodowisku Python.
    echo.
    pause
    exit /b 1
)
echo  [OK] Wszystkie biblioteki zostaly pomyslnie zainstalowane.
echo.

REM --- Krok 3: Pobieranie modelu AI ---
echo --- Krok 3/3: Pobieranie startowego modelu AI (Whisper 'base')...
echo  Model zostanie pobrany tylko za pierwszym razem.
echo  Rozmiar: ~140 MB. Moze to chwile potrwac.
echo.

python -c "import whisper; print('Pobieranie modelu...'); whisper.load_model('base'); print('Model pobrany.')"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  [OSTRZEZENIE]
    echo  Nie udalo sie automatycznie pobrac modelu AI.
    echo  Aplikacja sprobuje pobrac go przy pierwszym uruchomieniu transkrypcji lokalnej.
    echo.
) else (
    echo  [OK] Podstawowy model AI jest gotowy do uzycia.
)
echo.

echo ==============================================================
echo.
echo  Instalacja zakonczona sukcesem!
echo.
echo ==============================================================
echo.
echo WAZNE: Aplikacja do pelnego dzialania wymaga narzedzia FFmpeg.
echo Szczegolowe instrukcje instalacji znajdziesz w pliku README.md.
echo.
echo Mozesz teraz uruchomic aplikacje, klikajac dwukrotnie
echo na plik: run_dictaitor.bat
echo.
pause
exit /b 0