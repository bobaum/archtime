# Project Context: ArchTIME (Application Portfolio Rationalization Engine)

## 1. Projektziel & Anforderungen (MVP)
- **Vision:** Enterprise-Architecture- und PMO-Tool zur Bewertung und Konsolidierung von Unternehmens-Applikationslandschaften nach dem Gartner TIME-Framework (Tolerate, Invest, Migrate, Eliminate).
- **Kernfunktionen:**
  - Multi-Portfolio-Verwaltung in Supabase (PostgreSQL).
  - 1-Klick-Demo-Datensatz ("NordWest Maschinenbau GmbH") + CSV-Import/Export + manuelles CRUD.
  - Dynamische Pandas-Scoring-Engine mit einstellbaren Kriterien-Gewichtungen und Quadranten-Schwellenwerten.
  - Interaktive 4-Quadranten TIME-Matrix (Plotly Bubble Chart: X = Technical Fit, Y = Business Value, Größe = Jahreskosten €).
  - C-Level Rationalization & ROI-Rechner inkl. KI-Executive-Briefing (Gemini API) und optionalem Jira REST API Connector (Basic Auth).

## 2. Tech-Stack & FinOps-Architektur
- **Frontend & Charts:** Python, Streamlit, Plotly.
- **Datenverarbeitung:** Pandas.
- **Datenbank & Security:** Supabase (Shared PostgreSQL Instance mit Tabellenpräfix `archtime_`, Row Level Security aktiviert, Zugriff via `service_role` Key).
- **Schnittstellen:** Jira REST API v3 (Basic Auth), Google GenAI SDK (`gemini-2.5-flash`).
- **FinOps:** **0,00 € / Monat** (Nutzung der bestehenden Supabase Free-Tier-Instanz zur Einhaltung des 2-Projekte-Limits).

## 3. Master-Roadmap Status
- [x] Arbeitspaket 1: Infrastruktur, Datenbank (RLS) & Projekt-Setup
- [ ] Arbeitspaket 2: Datenmodell, 1-Klick-Demo-Generator & CSV/Manual-CRUD
- [ ] Arbeitspaket 3: Scoring-Engine & Interaktive Plotly TIME-Matrix
- [ ] Arbeitspaket 4: Jira REST API Connector & KI-Executive-Briefing
- [ ] Arbeitspaket 5: GitHub-Repo (`bobaum/archtime`), Cloud-Deployment & Portfolio-README