# JarvisHealth Designsystem — „Tagesbriefing"

Version 2.0 · Juli 2026 · gilt für `frontend/`

JarvisHealth ist ein **tägliches Morgen-Briefing für einen Athleten**: Die eine
Aufgabe des Dashboards ist, in unter 10 Sekunden zu beantworten —
*„Wie erholt bin ich, und was trainiere ich heute?"* — und jede Antwort
wissenschaftlich nachvollziehbar zu machen. Alles in diesem Dokument leitet
sich aus dieser Aufgabe ab. Ästhetische Anker sind Bevel (ruhiger,
einspaltiger Feed, redaktioneller Ton) und WHOOP (Erholung/Belastung/Schlaf-
Trias, Coaching, Zielbänder) — bewusst als eigene Identität interpretiert,
nicht als Kopie.

---

## 1. Leitidee & Signatur

**Das Verdikt kommt vor der Zahl.** Klassische Tracker führen mit einer
großen Zahl; Menschen handeln aber auf Sprache, nicht auf Scores
(Klartext-Guidance schlägt Rohwerte; NN/g zu *plain language* und
Interpretationslast). JarvisHealth öffnet deshalb wie ein Briefing-Dokument:

1. **Datumszeile** als Eyebrow („Samstag · 5. Juli · Tagesbriefing"),
2. **Verdikt-Satz** in einer Serif als Held der Seite,
3. darunter die **Instrumenten-Trias** (Erholung · Belastung · Schlaf) als Belege.

Zweites wiederkehrendes Motiv: das **Zielband**. Die wissenschaftliche
Substanz der App ist überall „Ist-Wert gegen dein persönliches Band"
(Baseline ± SWC, Ziel-Range, Zonen-Soll). Die UI macht genau das zur
visuellen Sprache: Bullet-Graph-Meter (Ist-Balken + hinterlegtes Zielband +
Marker) für Strain-Budget, Schlafphasen-Ziele und Trainingssysteme
(Bullet Graph: Few, *Information Dashboard Design* — entwickelt als
präzisere, platzsparende Alternative zu Rundinstrumenten).

## 2. Informationsarchitektur

Reihenfolge = Entscheidungshierarchie (wichtigstes zuerst, F-Muster-Scanning;
Few: „the most important information on top", NN/g Eyetracking):

| # | Block | Frage, die er beantwortet |
|---|---|---|
| 1 | **Tagesbriefing** (Verdikt + Trias + Anomalie-Flags) | Wie geht es mir? |
| 2 | **Coach — Heute** (genau *eine* Empfehlung + Belastungs-Budget) | Was tue ich? |
| 3 | **Schlaf** (letzte Nacht, Hypnogramm, Phasen-Ziele) | Warum ist das so? |
| 4 | **Belastung** (Tagesakkumulation vs. Zielband) | Wo stehe ich heute? |
| 5 | **Training — Woche** (Systeme vs. Zielband, Lasttrend) | Bin ich auf Kurs? |
| 6 | **Trends** (VO₂max, Ruhepuls, HFV, Schritte, kcal, AZM) | Wohin entwickle ich mich? |

- **Genau eine Handlungsempfehlung** pro Tag im Coach-Block (Hick's Law:
  weniger Optionen → schnellere, bessere Entscheidungen; WHOOPs
  Strain-Coach-Prinzip).
- **6 Top-Level-Blöcke** — an der Kapazitätsgrenze des Arbeitsgedächtnisses
  ausgerichtet (4 ± 1 Chunks; Cowan 2001, historisch Miller 1956); die Trias
  ist *ein* Chunk, die Trends sind *ein* Chunk.
- **Progressive Disclosure** (NN/g): Feed zeigt Verdikt + Kernwerte; jede
  Karte öffnet eine Detailansicht mit Methodik, Komponenten und Verläufen.
- **Einspaltiger, zentrierter Feed (max. 720 px)**: eine Leserichtung, keine
  konkurrierenden Spalten (Bevel-Prinzip); Zeilenlängen bleiben in lesbaren
  45–75 Zeichen.

## 3. Farbe

Alle Paletten wurden **rechnerisch validiert** (Skript: OKLCH-Lightness-Band,
Chroma-Floor, Farbfehlsichtigkeits-Separation nach Machado et al. 2009,
Kontrast nach WCAG) — nicht nach Augenmaß. Ergebnisse unten.

### Flächen & Text (Dark-only)

Dunkles UI ist für den Anwendungsfall (Check morgens/abends, OLED) gesetzt.
Kein reines Schwarz: Auf #000 verstärkt sich Halation/Überstrahlen heller
Schrift, besonders bei Astigmatismus; Empfehlung dunkles Grau statt Schwarz
(Material Design Dark Theme Guidance).

| Token | Wert | Rolle | Kontrast |
|---|---|---|---|
| `--bg` Nachtblau | `#0C0E12` | Seite | — |
| `--surface` Graphit | `#161A21` | Karten | — |
| `--surface-2` | `#1D232C` | Eingaben, Nester | — |
| `--text-1` | `#EEF2F6` | Primärtext | 15,5:1 ✓ |
| `--text-2` | `#9AA5B5` | Sekundärtext | 7,0:1 ✓ (≥ 4,5:1) |
| `--text-3` | `#66707F` | Nur Achsen/Microlabels | 3,5:1 ✓ (≥ 3:1, groß) |

### Status (Erholung / Zustände) — desaturiert statt Neon

Vorher `#16EC06`-Neongrün: maximal gesättigte Farben „vibrieren" auf dunklen
Flächen und übersteuern die Hierarchie (Material-Empfehlung: desaturierte
Akzente auf Dark Surfaces). Neu, alle ≥ 3:1 auf Graphit:

| Token | Wert | Bedeutung |
|---|---|---|
| Jade `--good` | `#31B879` (6,9:1) | erholt / im Ziel |
| Bernstein `--warn` | `#E3A008` (7,7:1) | moderat / Grenzbereich |
| Koralle `--bad` | `#E5484D` (4,5:1) | belastet / Flag |
| Signal `--accent` | `#4CB8E8` (7,8:1) | Interaktion/Marke — nie Datenbedeutung |

Status wird **nie durch Farbe allein** codiert: immer Icon/Pfeil + Wort
(WCAG 1.4.1 *Use of Color*; ~8 % der Männer mit Rot-Grün-Schwäche).

### Kategoriale Paletten (validiert, Flags: alle Checks PASS)

**Schlafphasen** (adjazent in Stack & Hypnogramm; Machado-CVD worst pair
ΔE 12,1 ≥ 12, alle ≥ 3:1):

| Phase | Wert |
|---|---|
| Tiefschlaf | `#5560DE` |
| REM | `#A379EC` |
| Leichtschlaf | `#2F8CC7` |
| Wach | `#BD7F3F` (warm = „nicht Schlaf", bricht bewusst die kühle Familie) |

**Trainingssysteme** (semantische Hitze leicht→hart, immer mit Label;
worst pair ΔE 32,1):

| System | Wert |
|---|---|
| Basis (Z1–2) | `#26A69A` |
| Grauzone (Z3) | `#B98727` |
| Intensiv (Z4–5) | `#E0636F` |

Bewusst **andere Stufen als die Status-Farben**, damit eine Zonenfarbe nie
einen Zustand imitiert (Status-/Serien-Trennung).

**Sparklines in Stat-Tiles** tragen *eine* zurückhaltende Farbe
(De-Emphasis-Blaugrau) statt Regenbogen — Identität steckt im Label, die
Delta-Färbung trägt die Richtung (Stat-Tile-Kontrakt; Tufte: Sparklines als
„intense, word-sized graphics" leben von Zurückhaltung).

## 4. Typografie

| Rolle | Schrift | Einsatz |
|---|---|---|
| Verdikt & View-Titel | **Fraunces** (Serif, optical sizing) | genau ein Serif-Moment pro Screen — das redaktionelle Briefing-Signal |
| UI, Daten, alles andere | **Inter** | Zahlen *immer* Inter |

- Zahlen: große Einzelwerte proportional; `tabular-nums` **nur** in
  Tabellen/Achsen (gleichbreite Ziffern lassen große Zahlen sonst „locker"
  wirken).
- Skala (px): 11 · 12 · 13 · 14 · 16 · 18 · 22 · 28 · 40 · 56; Zeilenhöhen
  1,45 für Fließtext, 1,1 für Displays.
- Große Werte mit negativem Tracking (−0,02 em), Eyebrows mit +0,12 em
  Versalabstand.

## 5. Diagramm-Chrome (einheitlich, `chart.jsx`)

Vorher: vier verschiedene Grid-Farben, per Chart kopierte Tooltip-Styles.
Neu ein Satz Regeln (Cleveland & McGill 1984: Position/Länge sind die
präzisesten visuellen Kanäle → Linien/Balken/Bänder für Vergleiche; Winkel
und Fläche nur für Auf-einen-Blick-Status):

- Gridlines: Haarlinie 1 px, `#232933`, **durchgezogen**, nur horizontal;
  gestrichelt ist ausschließlich für Ziel-/Schwellen-Referenzlinien
  reserviert (dort bedeutet die Strichelung etwas).
- Linien 2 px, runde Joins; Flächenfüllung ≈ 10 % Deckkraft als Verlauf.
- Achsentext `--text-3`, 11 px, keine Achsen-/Tick-Striche.
- Ein gemeinsamer Tooltip (Wert fett zuerst, Serienname sekundär,
  Serien-Key als kurzer Farbstrich).
- Ringe/Meter: Track als **hellere Stufe derselben Rampe** (nicht grau),
  Strichstärke 8–10 px, kein Glow (Data-Ink-Ratio, Tufte).
- Der halbrunde Strain-Tacho wurde durch ein **lineares Budget-Meter mit
  Zielband** ersetzt: Position statt Winkel (Cleveland & McGill), halbe Höhe,
  und das Band zeigt die Ziel-Range explizit (Few: Bullet statt Gauge).
- Legende ab 2 Serien immer; einzelne Serien ohne Legendenkasten (Titel
  benennt sie). Werte nie auf jedem Punkt — selektiv (Endpunkt/Extrem).

## 6. Interaktion & Zugänglichkeit

- **Ein Filterband** (Zeitraum) oben pro View, scoped alles darunter —
  nie Filter in einzelnen Karten.
- Karten sind echte Buttons: fokussierbar, Enter/Leertaste, sichtbarer
  `:focus-visible`-Ring in Signal (WCAG 2.4.7).
- Trefferflächen ≥ 44 px Höhe für Primäraktionen (Fitts's Law; Apple HIG
  44 pt; WCAG 2.5.8 min. 24 px).
- `prefers-reduced-motion` deaktiviert alle Transitions/Animationen
  (WCAG 2.3.3; vestibuläre Störungen).
- Beim Neuladen bleibt der letzte Render gedimmt stehen (kein
  Skeleton-Flackern, kein Layout-Sprung).
- Motion: 160–240 ms, `ease-out`, nur für Zustandswechsel (Eintritt von
  Werten, Hover) — keine Dauer-Animationen.

## 7. Belege (Auswahl)

- Cleveland, W. & McGill, R. (1984). *Graphical Perception.* JASA 79(387) —
  Rangfolge visueller Kanäle.
- Few, S. (2006/2013). *Information Dashboard Design* — Bullet Graph,
  Ein-Bildschirm-Prinzip, Kritik an Rundinstrumenten.
- Tufte, E. (1983/2006). *The Visual Display of Quantitative Information*;
  *Beautiful Evidence* — Data-Ink-Ratio, Sparklines.
- Nielsen Norman Group — F-Pattern (Eyetracking), Progressive Disclosure,
  Plain Language, Recognition over Recall.
- Cowan, N. (2001). *The magical number 4 in short-term memory.* BBS 24 —
  Chunk-Grenze (statt Miller 1956er „7±2").
- Hick, W. E. (1952) / Hyman, R. (1953) — Reaktionszeit wächst mit
  Optionszahl.
- Fitts, P. M. (1954) — Zielgröße/Distanz und Zugriffszeit.
- WCAG 2.2 — 1.4.3 Kontrast, 1.4.1 Use of Color, 2.4.7 Focus Visible,
  2.5.8 Target Size, 2.3.3 Animation from Interactions.
- Machado, G. M. et al. (2009). *A Physiologically-based Model for Simulation
  of Color Vision Deficiency.* IEEE TVCG — Grundlage der CVD-Validierung.
- Material Design, *Dark theme* — kein reines Schwarz, desaturierte Akzente;
  Halation bei hellem Text auf #000 (Astigmatismus-Fallbeispiel).
- Kurosu, M. & Kashimura, K. (1995) — Aesthetic-Usability-Effekt.
- Driver & Taylor (2000), Shapiro (1981) — SWS-Rebound nach Trainingslast
  (Grundlage der lastadaptiven Tiefschlaf-Ziele, s. `sleep.py`).

## 8. Anti-Pattern-Checkliste (vor jedem Merge prüfen)

- ❌ Zwei Y-Achsen in einem Chart → zwei Charts oder indexieren.
- ❌ Neonfarben / gesättigte Großflächen auf Dark Surface.
- ❌ Wert an jedem Datenpunkt; gestricheltes Grid.
- ❌ Status-Farbe als Serienfarbe (und umgekehrt).
- ❌ Farbe als einziger Bedeutungsträger.
- ❌ `tabular-nums` auf Display-Zahlen.
- ❌ Neue Farbtöne „nach Gefühl" — jede Palettenänderung erneut validieren.
