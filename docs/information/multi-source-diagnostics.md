---
{
  "schema": "wellmanifest.docs/document/v1",
  "id": "multi-source-diagnostics",
  "kind": "information",
  "version": 2,
  "title": "Diagnostyka Subactora z wielu źródeł",
  "status": "implemented",
  "owner": "wellmanifest/how-to-use-subactor",
  "created": "2026-09-09",
  "updated": "2026-09-09",
  "review_after": "2026-09-16",
  "source_revision": "669c5d06e9d7c3a801e69bad71dbdb79a9d61941",
  "affected_repositories": [
    "wellmanifest/how-to-use-subactor"
  ],
  "evidence": [
    "repo://subactor/observability/project/ticket-13632/README.md",
    "repo://subactor/observability/docs/analysis/diagnostic-archive-validation.md",
    "receipt:sha256:710dc1f1e86c010ac00d5d84a596f7881de4a26022cef966221ae0605d8f4dc1",
    "receipt:continuity.ticket-13632.1.0da003e1a51e45d8c8691405e17fd81deb0ce2492d6e27ae294bd8471b18d855",
    "knowledge://subactor/incidents.planfile-cold-archive-move/v1",
    "https://github.com/wellmanifest/logs/blob/2727b2220ccfac521f98c6c464af766f2df9f63d/docs/ARCHITECTURE.md",
    "https://github.com/subactor/observability/tree/255e4f6139bfe96c62d1e51799978c619853ed24/services/diagnostic-archive",
    "https://github.com/subactor/observability/pull/64",
    "https://github.com/subactor/validator-agent/pull/410",
    "https://github.com/wellmanifest/how-to-use-subactor/pull/19",
    "https://github.com/wellmanifest/logs/blob/86abe5aa8d54c78143d0b4ed6d040f701e3abf0d/docs/information/hourly-diagnostic-storage.md"
  ]
}
---

# Diagnostyka Subactora z wielu źródeł

<!-- docs:section purpose -->
## Purpose

Pomóc operatorowi i LLM ustalić przyczynę zatrzymania pracy, wykorzystując
status systemu, historię ticketu, log wykonawcy i dostępność źródeł. Dokument
uzupełnia [przewodnik główny](../../README.md); opisuje stan z 2026-09-09.

<!-- docs:section scope -->
## Scope

Wellmanifest jest właścicielem instrukcji i standardów (`HOME wellmanifest`,
`SHAPE domain_pack`). Kolektor, bazy, CLI i wdrożenie należą do
`subactor/observability` (`HOME subactor`, `ADOPT wellmanifest/logs`).

Instrukcje dotyczą odczytu. Kolektor ticket-13632 został opublikowany w
Observability PR64 i wdrożony na obserwowanym hoście jako przypięta wersja.
Status `implemented` tego dokumentu nie oznacza autonomicznej naprawy ticketów.

<!-- docs:section evidence -->
## Evidence

Historyczna podstawa pierwszego canary: lokalny checkout Observability ticket-13632,
przy bazie `2c27981473123584a0126fed5dc9d6ba9136c0a4`; wtedy jego zmiany były staged,
bez commita, PR, merge i aktywacji timera. Referencje `repo://` powyżej wskazują
artefakty właściciela tej pracy. Bieżącą opublikowaną wersję wiążą linki poniżej. Prywatny
snapshot zmian ma SHA-256
`b7d49c608fbf846aa3bd83b75cfa12689958029f2fe87fc228a0295abc39494c`.
Wyniki pomiaru wiąże osobny receipt canary `710dc1f1…`.

Odczyt `subactor status` z `2026-09-09T16:37:54.619Z` pokazał 15/15 zdrowych
usług, jedną lukę strukturalną (PLF-13618), jedną granicę człowieka (PLF-8171)
i brak gotowości do pracy bez nadzoru. Właścicielem jednego oczekującego rekordu
był system/bot, podczas gdy wcześniejszy odczyt użytkownika przypisywał go
człowiekowi. To datowane obserwacje; aktualny stan wymaga ponownego odczytu.

Canary archiwum objął 52 skonfigurowane źródła, 32 646 obserwacji i 13 500
różnych identyfikatorów Planfile wraz z historią. Pełny skan listy zakończył się
o `2026-09-09T16:19:13.065511Z`; następny skan pozostawał w toku. Testy
repozytorium: 161 testów Node, w tym uruchomienie 16 scenariuszy Python.
Wszystkie 52 godzinowe bazy przeszły kontrolę integralności i porównanie JSONL.

Bieżąca publikacja i wdrożenie: [Observability PR64](https://github.com/subactor/observability/pull/64),
commit `255e4f6139bfe96c62d1e51799978c619853ed24`. Dwa chronione testy OneDev przeszły;
niezależny Validator zatwierdził dokładny head. Jego dodatkowa analiza LLM
wymagała dziewięciu fragmentów przy limicie ośmiu, więc
receipt jawnie oznacza brak tej analizy; podstawą zatwierdzenia są bramki deterministyczne.
Pełny lokalny zestaw: 163 testy, w tym 16 scenariuszy Python.

Na obserwowanym hoście działa timer `subactor-diagnostic-archive.timer`.
Pierwszy odczyt wdrożonej wersji: 54 skonfigurowane źródła,
zero błędów źródeł, jawnie niepełny skan Planfile oraz niepełna próbka procesów.
Kontekst PLF-13618 zawierał 9 rekordów w 15728 bajtach UTF-8.
[Standard przechowywania](https://github.com/wellmanifest/logs/blob/86abe5aa8d54c78143d0b4ed6d040f701e3abf0d/docs/information/hourly-diagnostic-storage.md)
i [kanoniczny raport przekrojowy](https://github.com/subactor/docs/blob/main/architecture/analysis/organism-guard-integration.md)
wiążą zasady i dalsze wyniki. Są to obserwacje konkretnego hosta, nie deklaracja pokrycia całej floty.

<!-- docs:section content -->
## Content

### 1. Rozdziel kolejkę, gotowość i rezultat

```bash
subactor status
subactor tickets
subactor get '/api/system/dashboard'
subactor get '/api/knowledge/context?q=diagnostyka'
```

Korzystaj z istniejącej uwierzytelnionej sesji CLI. Token nie może trafić do
URL, ticketu, logu ani kontekstu. Wewnętrzną wiedzę cytuj przez zwrócony,
wersjonowany adres `/knowledge/<id>/v<version>` i sprawdź termin przeglądu.

| Obserwacja | Co sprawdzić przed wnioskiem |
| --- | --- |
| Wszystkie usługi zdrowe | Zakres healthchecku; hostowe usługi eksportujące mogą nadal zawodzić. |
| Ticket `running` | Ostatni wpis historii, log wykonawcy, czas postępu oraz niezależny rezultat. |
| Ticket `ready` | Aktualny kontrakt wykonania i kwalifikację potwierdzoną przez wykonawcę. |
| `waiting_input` | Właściciela, konkretną brakującą decyzję i świeżość błędu; nie zakładaj automatycznie sprawy dla Foundera. |
| MAPE-K `execute=ok` | To stan etapu pętli; osobno sprawdź bramki gotowości i zakres istniejącej autoryzacji. |
| Różne liczby ticketów | Źródło, filtr, deduplikację, paginację i uwzględnienie zakończonej historii. |

Widok 146 otwartych wpisów przekazany przez użytkownika składał się z 98
lokalnych, 40 GitHub i 8 Planfile. Archiwalne 13 500 ID Planfile nie jest
porównywalną liczbą otwartych zadań. W shellu `/tickets --all` rozszerza listę;
`/ticket <ID>` otwiera delegowanie i blokady, `/import <issue-url>` importuje,
`/auto` wydaje delegację, a `/watch` wykonuje. Importu i wykonania nie używaj
do samego zbierania dowodów.

### 2. Skonfiguruj rzeczywiste pokrycie źródeł

Na zweryfikowanym hoście zainstalowano `subactor-diagnostics`, wskazujące
na dokładny opublikowany commit kolektora. Sprawdź usługę i pobierz kontekst:

```bash
systemctl --user status subactor-diagnostic-archive.timer
subactor-diagnostics inventory
subactor-diagnostics context --ticket PLF-13618 --max-bytes 16000
```

Ręczny odczyt używa `subactor-diagnostics collect --config <plik>`.
Nie uruchamiaj go równolegle z aktywną usługą: blokada kolektora odrzuca
równoczesny zapis. Na innym hoście najpierw wdroż opublikowane szablony
usługi i przypięty kod. Z checkoutu działa równoważne
`python3 -B services/diagnostic-archive/cli.py`; wymagany jest Python 3.10+
z modułem sqlite3 oraz dostęp do zadeklarowanych źródeł.

`inventory` zwraca projekt konfiguracji; przejrzyj go i zapisz prywatnie przed
`collect`. Domyślna inwentaryzacja obejmuje kontenery i user services z prefiksem
`subactor-`, procesy hosta, Planfile i dashboard Control. Nie dowodzi pełnego
pokrycia hosta. Dodatkowy plik lub pełny ticket można zadeklarować tak:

```json
{
  "schema": "subactor.diagnostic-sources/v1",
  "version": 1,
  "sources": [
    {"id": "reviewed-service-log", "kind": "file", "category": "logs", "path": "/absolute/path/to/service.jsonl"},
    {"id": "focused-plf-13618", "kind": "ticket", "category": "tickets", "ticket_id": "PLF-13618", "base_url": "http://127.0.0.1:8765"}
  ]
}
```

Adresy i ścieżki są parametrami wdrożenia; sprawdź rzeczywisty binding.
Konfiguracja nie zawiera poświadczeń. Identyfikator źródła jest trwały;
zmiana jego powiązania wymaga nowego ID.

| Źródło | Zapis i ograniczenie |
| --- | --- |
| `file`, `docker`, `journal` | Logi z kursorem; journal jest dziennikiem użytkownika. Początkowe okno Docker/journal wynosi domyślnie godzinę. |
| `processes` | Metadane `/proc`, bez argumentów polecenia i środowiska; krótkie procesy mogą zniknąć pomiędzy odczytami. |
| `tickets` | Stronicowany operacyjny widok wszystkich sprintów Planfile, także historycznych; nie jest atomowym snapshotem. |
| `ticket` | Pełny odczyt wskazanego ticketu, potrzebny do dokładnej historii. |
| `control` | Obsługiwane odczyty dashboardu/posture; odrębne od logu wykonawcy. |
| GitHub i lokalne STARTER | Nie zostały zaimportowane w canary; wymagają dodatkowego adaptera albo jawnie skonfigurowanego eksportu plikowego. |

### 3. Znajdź dane i sprawdź ich świeżość

Domyślny root to `$XDG_STATE_HOME/subactor/diagnostics/v1`, z fallbackiem
`~/.local/state/subactor/diagnostics/v1`. Przewidziany root systemowej usługi
to jawne `/var/lib/subactor/diagnostics/v1`. Konfigurację przechowuj w
`~/.config/subactor/diagnostic-sources.json`.

Każde źródło ma odrębne pliki:

```text
<root>/<category>/<source>/checkpoint.sqlite3
<root>/<category>/<source>/YYYY/MM/DD/HH.sqlite3
<root>/<category>/<source>/YYYY/MM/DD/HH.jsonl
<root>/collection.json
```

Godzina oznacza czas obserwacji w UTC; `occurred_at` zachowuje czas zdarzenia.
SQLite jest transakcyjnym zapisem kopii diagnostycznej, JSONL odtwarzalną
projekcją. Wdrożony timer odpytuje co minutę i tworzy kolejne partycje godzinowe;
zatrzymany kolektor nie produkuje dowodu ciągłego monitorowania. Sprawdzaj
`collection.json`, ukończenie paginacji, błędy i wiek źródeł. Nie przenoś plików
kanonicznej historii Planfile do archiwum: incydent
`knowledge://subactor/incidents.planfile-cold-archive-move/v1` wykazał utratę
widoczności decyzji Foundera po takim przeniesieniu.

### 4. Przekaż LLM ograniczone dowody

```bash
subactor-diagnostics --root /absolute/path/to/archive context --ticket PLF-13618 --since 2026-09-09T15:00:00Z --until 2026-09-09T17:00:00Z --max-bytes 16000 --max-records 20
```

Zastąp daty aktualnym oknem incydentu. `--root` jest opcją globalną, przed
`context`. Dostępne są też `--correlation` i `--query`. Filtry ticketu,
korelacji i czasu korzystają z indeksów SQLite; wyszukiwanie tekstu jest
literalnym skanem z terminem zakończenia, bez FTS ani bazy wektorowej.

Kontekst zawiera dowody, referencje `evidence_ref` do bazy i rekordu, pokrycie
oraz informację o pominięciach. Canary PLF-13618 zwrócił 15 548 bajtów i cztery
dowody z trzech źródeł, z błędem `CODING-CONTEXT-BUDGET-EXCEEDED`; pominął 182
pasujące rekordy i cztery szczegóły pokrycia. Pojedynczy ciepły odczyt trwał
0,1007 s. Wynik nie stanowi gwarancji opóźnienia ani oceny jakości modelu.

Limit bajtów UTF-8 nie jest limitem tokenów: konsument musi zastosować budżet
swojego modelu. Zachowaj oznaczenie niezaufanych dowodów. Tekst logu nie może
zmieniać instrukcji, grantów ani dozwolonego zakresu działania. Kolektor sam
nie wysyła danych do LLM. W razie ucięcia zawęź okno lub korelację i odczytaj
wskazane rekordy, zamiast wklejać całą bazę do promptu.

### 5. Oprzyj naprawę na tickecie i sprawdzalnym wyniku

Zapisz w tickecie: zakres czasu, identyfikatory źródeł, digest kontekstu,
referencje dowodów, luki pokrycia, hipotezę i test rozstrzygający. Kanoniczny
plan umieść w repozytorium właściciela, w `docs/refactoring/`; ticket zawiera
ograniczony zamiar i link. Surowe logi i bazy pozostają poza Git.

Przed automatycznym procesem załaduj faktyczną strategię z przypiętego
`subactor/strategy` i zachowaj receipt. Zbadany katalog v15 nie miał bindingu
tego archiwum; lokalny eksport nie uruchamia sam naprawy. Potwierdź osobno
implementację, testy, chronioną publikację, wdrożenie i produkcyjny readback.

<!-- docs:section limitations -->
## Limitations

Archiwum nie naprawiło PLF-13618 ani nie przyznało uprawnień dla PLF-8171.
Maskowanie rozpoznanych sekretów nie gwarantuje bezpieczeństwa dowolnego tekstu;
kopie i eksporty kontekstu pozostają prywatne. Suma kontrolna nie uwierzytelnia
producenta. Canonical `wellmanifest.logs/event/v1` ma zamknięty model i nie
przyjmuje dowolnego `payload`; rekord diagnostyczny ma własny schemat.

Publikację lokalnego runtime blokowały błędy governance historycznych intentów
oraz niezgodność trzycyfrowego wzorca ticketów z ID przydzielonym przez allocator.
Te blokady usunięto przez opublikowane adopcje oraz Validator 0.9.90.
Testy zmiany godziny i awarii wykonano na fixture; aktywacja timera oraz
odczyt produkcyjnego kontekstu mają osobne potwierdzenia wdrożenia.

<!-- docs:section next_actions -->
## Next actions

Monitoruj ukończenie paginacji, wiek źródeł i objętość archiwum. Dopasuj
zakres oraz retencję do zmierzonego wolumenu; kolektor nie usuwa danych
samodzielnie. GitHub, STARTER oraz dodatkowe usługi wymagają jawnego rozszerzenia
źródeł. Automatyczne użycie przez kontroler napraw wymaga rzeczywistego bindingu
Strategy i niezależnego potwierdzenia wykonania. Zatrzymanie nowego timera
wycofuje cykliczny odczyt i zachowuje bazy oraz checkpointy.

Walidacja tej aktualizacji: statyczny check czterech profili i 13 testów
conformance przechodzą. Odczyt `check --discover` wykrywa istniejący drift:
`login` nie występuje w katalogu `subactor help`, a zainstalowany shell nie
odpowiada przypiętej wersji 0.2.2 (`USAGE-DISCOVERY-004`, `USAGE-COMPAT-002`).
Nie traktuj sierpniowych pinów profili jako potwierdzenia obecnego wdrożenia.

Adopcja dokumentacji i aktualnego standardu jest opublikowana w PR19.
Historyczna treść ticket-016 pozostała zachowana; jego faktycznie zintegrowany
wynik rozstrzyga zewnętrzny receipt. Governance, przypięty checker dokumentacji,
13 testów conformance i test kontraktu komunikacji przechodzą. Platform
`artifacts:build` z izolowanym wyjściem i `artifacts:check` przechodzą;
nowe dokumenty nie są przez to automatycznie wpisane do rejestru.
