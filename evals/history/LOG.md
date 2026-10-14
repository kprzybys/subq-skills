# Dziennik przypadków: plugin `subq` z i bez

Cel: zbierać przebiegi `claude plugin eval` (i inne obserwacje), żeby później ocenić, co plugin realnie daje
i co trzeba w nim poprawiać. Każdy wpis: data, komenda, wynik liczbowy, co zawiodło bez pluginu, zastrzeżenia.
Surowe dane obok: `<data>-runN.json` (pełny wynik) i `<data>-runN-report.html` (raport z odpowiedziami i głosami sędziego).

## 2026-10-14, run1 — pierwszy przebieg po zbudowaniu pluginu

Komenda: `claude plugin eval . --trust-plugin --allow-tools Write WebFetch --no-publish -j 3` (1 przebieg na ramię,
sędzia domyślny = haiku, 3 głosy). Czas 163 s, koszt $1.21. Claude Code 2.1.299, plugin 0.1.0.

| przypadek | z pluginem | bez pluginu | co zawiodło bez pluginu |
|---|---|---|---|
| triage-tickets | 1.0 | 1.0 | nic: prompt wymienia `api.subq.ai`, agent z WebFetch sam doczytał Decisions API |
| jev-to-snap | 1.0 | 0.6 | Snap opisany poprawnie z docs; po stronie Jev „nie znalazłem ceny ani limitu” (są w docs.typesafe.ai/models.md: $0.042, 64k/32k); retry 429/503 nazwane „moim domysłem”, choć docs SubQ mówią to wprost |
| question-design | 1.0 | 0.0 | agent nie użył WebFetch, przyznał, że nie zna SubQ, wymyślił własny format (`binary`, `single_choice`, `rating`, `prompt`, `options`); uznał 40 opcji za „pewnie ponad limit” (limit 255) i rozbił na shortlistę do 8 albo turniej w 6 żądaniach |

Średnia różnica (Δ) +0.47. Wskaźnik „skill wywołany” w ramieniu z pluginem: 3/3.

Baseline sprzed evali (agent Sonnet, bez sieci, bez skilla, ten sam prompt co triage-tickets): endpoint `/v1/snap`,
model `snap`, format `input/question/choices`, 3 żądania na zgłoszenie zamiast 1, brak typów noul/choice/score.

Wnioski:
- Plugin daje (1) pewność, że agent sięgnie do docs SubQ zamiast zgadywać, (2) fakty, których agent sam nie składa:
  porównanie z Jev, limity decydujące o projekcie pytań (16 pytań, 255 opcji), reguły retry.
- Gdy prompt wskazuje adres API i agent ma sieć, różnica znika (triage-tickets).

Zastrzeżenia: jeden przebieg na ramię; sędzia haiku raz zagłosował FAIL także z pluginem (jev-to-snap: PASS PASS FAIL);
prompty i skill pisała ta sama osoba (ryzyko uczenia pod test). Do cytowania potrzebne `--runs 3` (ok. $3.5).

Żywy test tego dnia: `skills/subq/examples/snap_client.py` przez wrapper z kluczem → HTTP 200, 246 tokenów, 629 ms.

## 2026-10-14, run2 — po review kodu (plugin 0.1.1)

Zmiany przed przebiegiem (z review: własny przegląd + `/code-review` high): klient nie podąża za przekierowaniami
(urllib przekazywał `Authorization` na inny host; sprawdzone lokalnie przed i po), retry obejmuje zerwane połączenia
(`OSError`, `http.client.HTTPException`), `attempts<1` → `ValueError`, 12 testów jednostkowych (`test_snap_client.py`),
ruff czysty; w SKILL.md usunięte twierdzenie „pytania nie widzą swoich odpowiedzi” (brak w docs SubQ), 87% → 87.5%;
grader `no-literal-key` łapie każdy dosłowny token po `Bearer`, nie tylko `sk-`.

Komenda jak w README (`--trust-plugin --allow-tools Write WebFetch --no-publish -j 3`), 1 przebieg na ramię. Czas 192 s, koszt $1.30.

| przypadek | z pluginem | bez pluginu | uwagi |
|---|---|---|---|
| triage-tickets | 1.0 | 1.0 | jak w run1 |
| jev-to-snap | 1.0 | 1.0 | **inaczej niż w run1 (0.6)**: tym razem agent bez pluginu znalazł cenę i limit Jev w docs TypeSafe |
| question-design | 1.0 | 0.0 | jak w run1: bez pluginu agent nie czyta docs i wymyśla format |

Średnia Δ +0.33 (run1: +0.47). Wniosek: różnica w jev-to-snap bez pluginu to kwestia losu (czy agent trafi na
stronę Models w docs TypeSafe); question-design jest stabilnym przypadkiem przewagi pluginu. Pojedyncze przebiegi
nie wystarczą do liczb; do analizy zbierać kolejne przebiegi w tym pliku.
Surowe: `2026-10-14-run2.json`, `2026-10-14-run2-report.html`. Streszczenie: `python3 evals/history/summarize.py <plik.json>`.
