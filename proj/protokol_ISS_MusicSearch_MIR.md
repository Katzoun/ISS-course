# Protokol — ISS Music search (řešení)

**Autor:** *doplnit jméno*  
**Login:** *doplnit login*  
**Datum:**  2025-11-05

## Zadání
Vyhledávání krátkých dotazových audio-klipů ve větší databázi známých nahrávek (mono, 16 kHz). Metriky: 1-best a 5-best přesnost na validační sadě. Odevzdání obsahuje protokol a predikce pro evaluační sadu (login).

## Průzkum vhodných přístupů
- Fingerprinty (Shazam-like): robustní k hluku a posunu v čase, rychlé vyhledávání přes hashe peak‑pairů.
- MFCC embeddingy + kNN: globální timbre podobnost, jednoduchá implementace a ladění, menší paměť.
- Rozšíření (neimplementováno): log-mel CNN embeddingy, případně chroma/tempo popisy.

## Implementace
- Metoda A (Shazam): log-spektrum -> detekce vrcholů (max-filter), tvorba párů (fan-out), hash a hlasování pro (song_id, offset).
- Metoda B (MFCC): MFCC z log-melu (DCT-II), agregace [mean | std | delta-mean | delta-std], PCA (volitelně), kNN (kosinová).

## Výsledky na validační sadě
Po spuštění části *Vyhodnocení na validační sadě* se doplní do `results/valid_results.json` z notebooku.

## Diskuse a ladění
- Shazam: prahy (dB), neighborhood, fan-out, rozsahy Δt a Δf, n_fft/hop.
- MFCC: n_mels, n_ceps, liftering, Δ/ΔΔ, PCA dimenze, volba metriky.

## Závěr
Metody se doplňují: fingerprinty obvykle dávají vyšší 1-best přesnost; MFCC mohou být užitečné jako záloha.
