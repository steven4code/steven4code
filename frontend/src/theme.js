// JarvisHealth Designsystem — Token für JS/Recharts.
// Quelle & Begründung: docs/DESIGN.md. Farben sind rechnerisch validiert
// (OKLCH-Band, Chroma-Floor, CVD nach Machado 2009, WCAG-Kontrast) —
// Änderungen hier nur mit erneuter Validierung.

export const SURFACE = {
  page: "#0C0E12", // Nachtblau
  card: "#161A21", // Graphit
  card2: "#1D232C",
  border: "rgba(255,255,255,0.07)",
};

export const INK = {
  1: "#EEF2F6", // Primärtext (15,5:1)
  2: "#9AA5B5", // Sekundärtext (7,0:1)
  3: "#66707F", // Achsen/Microlabels (3,5:1 — nur groß/sekundär)
};

// Status: desaturierte Trias, nie durch Farbe allein (immer Icon/Wort dazu).
export const STATUS = {
  good: "#31B879", // Jade
  warn: "#E3A008", // Bernstein
  bad: "#E5484D", //  Koralle
  neutral: INK[3],
};

// Interaktion/Marke — trägt nie Datenbedeutung.
export const ACCENT = "#4CB8E8"; // Signal

// Schlafphasen (kategorial, validiert: worst pair ΔE 12,1; alle ≥3:1).
export const STAGE = {
  deep: "#5560DE",
  rem: "#A379EC",
  light: "#2F8CC7",
  awake: "#BD7F3F",
};

// Trainingssysteme (semantische Hitze leicht→hart; worst pair ΔE 32,1).
// Bewusst andere Stufen als STATUS, damit Zone nie Zustand imitiert.
export const SYSTEM = {
  basis: "#26A69A",
  grauzone: "#B98727",
  intensiv: "#E0636F",
};

// Stat-Tile-Sparklines: EINE De-Emphasis-Farbe statt Regenbogen —
// Identität steckt im Label, Richtung im Delta.
export const SPARK = "#54627A";

// Chart-Chrome.
export const CHART = {
  grid: "#232933",
  axis: INK[3],
  refline: "rgba(238,242,246,0.35)",
};

// Score → Statusfarbe (Erholung/Schlaf, 0–100).
export const scoreColor = (s) =>
  s == null ? INK[3] : s >= 66 ? STATUS.good : s >= 40 ? STATUS.warn : STATUS.bad;

// Score → Ton-Klasse für Chips/Text.
export const scoreTone = (s) =>
  s == null ? "neutral" : s >= 66 ? "good" : s >= 40 ? "warn" : "bad";

// Strain-Status → Farbe/Ton (under = Raum, optimal = im Band, over = drüber).
export const strainColor = (status) =>
  status === "over" ? STATUS.warn : status === "optimal" ? STATUS.good : ACCENT;
export const strainTone = (status) =>
  status === "over" ? "warn" : status === "optimal" ? "good" : "accent";
