python -m uvicorn main:app --reload


# AI Call Center Agent – Propozycja Architektury Systemu

## 1. Analiza problemu

System obsługi rozmów głosowych znacząco różni się od klasycznego chatbota tekstowego.

W rozmowie telefonicznej należy uwzględnić:
- naturalny, nieliniowy sposób wypowiedzi klienta,
- możliwość przerywania,
- błędy rozpoznawania mowy (STT),
- niejednoznaczne odpowiedzi,
- emocje klienta (np. frustracja przy awarii),
- możliwość rozłączenia w trakcie rozmowy.

Dlatego kluczowe elementy systemu to:
- utrzymywanie stanu rozmowy (conversation state),
- walidacja i potwierdzanie danych,
- obsługa niskiej pewności rozpoznania,
- odporność na błędy i timeouty.

System powinien minimalizować ryzyko zapisania niekompletnych lub błędnych zgłoszeń.

## 2. Podział na moduły

System zaprojektowałbym jako modułowy, asynchroniczny backend oparty o FastAPI, pełniący rolę orkiestratora.

### Architektura wysokiego poziomu

```
Telefon
↓
Twilio (Telephony Adapter)
↓
FastAPI Backend
↓
Whisper (STT)
↓
OpenAI GPT (Dialog Manager)
↓
Business Logic
↓
PostgreSQL (Persistence Layer)
↓
Google Cloud TTS
↓
Telefon
```

## 3. Warstwa telefonii – Twilio

Twilio odpowiada za:
- odbieranie połączeń,
- przekazywanie strumienia audio do backendu,
- odtwarzanie wygenerowanych odpowiedzi.

Zaletą jest brak konieczności budowy własnej infrastruktury VoIP oraz wbudowana skalowalność.

## 4. Speech Processing

### STT – OpenAI Whisper API

Odpowiada za konwersję: `audio → tekst`

Wykorzystanie zewnętrznego API:
- eliminuje konieczność utrzymywania GPU,
- zmniejsza złożoność infrastruktury,
- wspiera niskie opóźnienia.

### TTS – Google Cloud Text-to-Speech

Odpowiada za konwersję: `tekst → audio`

Zalety:
- naturalna jakość głosu,
- szybka synteza,
- stabilne API.

## 5. Dialog Manager (AI)

Model językowy (OpenAI GPT) odpowiada za:
- rozpoznanie intencji (awaria, reklamacja itd.),
- ekstrakcję danych (adres, urządzenie),
- prowadzenie kontekstowego dialogu,
- generowanie odpowiedzi tekstowej.

Stan rozmowy przechowywany jest w Redis, co umożliwia:
- obsługę wielu równoległych rozmów,
- skalowanie poziome backendu,
- zachowanie kontekstu przy wielu instancjach aplikacji.

## 6. Business Logic

Backend odpowiada za:
- walidację danych,
- kontrolę kompletności zgłoszenia,
- potwierdzenie danych przed zapisem,
- generowanie numeru zgłoszenia.

Zapis do bazy następuje dopiero po potwierdzeniu danych przez klienta, co minimalizuje ryzyko błędnych rekordów.

## 7. Persistence Layer – PostgreSQL

PostgreSQL przechowuje trwałe dane biznesowe:
- numer telefonu,
- opis problemu,
- adres,
- urządzenie,
- numer sprawy,
- status zgłoszenia,
- timestamp.

Redis przechowuje wyłącznie tymczasowy stan rozmowy.

## Spełnienie wymagań niefunkcjonalnych

**✔ Obsługa min. 50 równoległych rozmów**
- asynchroniczny backend (FastAPI async),
- stan rozmowy w Redis,
- możliwość skalowania poziomego.

**✔ Opóźnienie odpowiedzi < 2s**
- brak operacji blokujących,
- wykorzystanie zoptymalizowanych API,
- możliwość przetwarzania strumieniowego.

**✔ Łatwa zmiana dostawcy STT/TTS**

Zastosowanie warstwy abstrakcji (adapter), co pozwala zmienić dostawcę bez ingerencji w logikę systemu.

**✔ Logowanie i monitoring**

System powinien rejestrować:
- czas odpowiedzi,
- błędy API,
- długość rozmowy,
- status zgłoszenia.

## Wartość operacyjna

Moje doświadczenie w pracy w call center pozwala mi spojrzeć na projekt również z perspektywy operacyjnej.

Kluczowe aspekty:
- naturalność dialogu,
- potwierdzanie danych przed zapisem,
- minimalizacja frustracji klienta,
- poprawność zgłoszeń trafiających do CRM.
