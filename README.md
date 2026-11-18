# ArchTIME: Application Portfolio Analyzer

Hi, ich bin Bo und studiere Wirtschaftsinformatik an der Hochschule Osnabrück.

Ich habe ArchTIME gebaut, weil in vielen Unternehmen über die Jahre unzählige Programme und Server parallel wachsen, ohne dass jemand einen klaren Überblick über das Verhältnis aus Kosten, Nutzen und technischem Risiko hat. Aus meiner praktischen Arbeit in der IT weiß ich, wie schwer es oft ist, alte Systeme abzuschalten oder Budgets für wichtige Modernisierungen durchzusetzen, wenn greifbare Zahlen fehlen.

Mit diesem Projekt wollte ich ein greifbares Werkzeug für das IT Management und Enterprise Architecture Management entwickeln. Statt trockener Tabellen kombiniert die Anwendung das bekannte Gartner TIME Modell mit einer interaktiven Kostensimulation und einer KI Schnittstelle, die auf Knopfdruck fertige Entscheidungsvorlagen für das Management formuliert.

## Was das Tool besonders macht

* **Interaktive Gartner TIME Matrix:** Alle Applikationen werden anhand von Business Value und Technical Fit automatisch in die vier Sektoren Tolerate, Invest, Migrate und Eliminate eingeordnet. Die Größe der Kreise im Diagramm zeigt direkt die jährlichen Lizenzkosten und Betriebskosten.
* **Echtzeit Gewichtung und Simulation:** Über Regler in der Seitenleiste lassen sich Kriterien wie IT Sicherheit, Wartbarkeit oder strategischer Nutzen live unterschiedlich gewichten. So sieht man sofort im Meeting, wie sich Prioritätsverschiebungen auf das gesamte Portfolio und das Einsparpotenzial auswirken.
* **Ausfallsicherer KI Advisor für Business Cases:** Für jedes System generiert das Tool über die Google Gemini API eine strukturierte Entscheidungsvorlage inklusive Kosten pro Nutzer, Risikoanalyse und einem konkreten Maßnahmenplan für die nächsten 90 Tage. Falls die KI Server einmal ausgelastet sind, springt automatisch eine mehrstufige Fallback Logik samt lokaler Regel Engine ein, sodass die App niemals abstürzt.
* **Schnittstellen und Demo Modus:** Neben einem direkten 1 Klick Demo Portfolio (am Beispiel eines mittelständischen Maschinenbauers mit 16 Systemen) unterstützt die App den Import per CSV sowie eine Anbindung an die Jira Cloud REST API über HTTP Basic Authentication.
* **Saubere Cloud und FinOps Architektur:** Die Datenbank nutzt eine bestehende Supabase PostgreSQL Instanz über isolierte Tabellen mit aktivierter Row Level Security (RLS), wodurch das gesamte System bei vollem Datenschutz dauerhaft mit 0,00 Euro laufenden Betriebskosten in der Cloud läuft.

## Mein Tech Stack

**Frontend und Visualisierung:** Python, Streamlit, Plotly (interaktiver 4 Quadranten Bubble Chart)  
**Datenverarbeitung und Scoring:** Pandas  
**Datenbank und Sicherheit:** Supabase (PostgreSQL mit Row Level Security)  
**Schnittstellen und KI:** Jira Cloud REST API v3 (Basic Auth), Google GenAI SDK (Gemini Flash Kaskade mit lokalem TOGAF Fallback)

## Die Module

1. **TIME Matrix und KPIs**  
   Das zentrale Dashboard berechnet auf einen Blick die gesamten jährlichen IT Run Kosten, das direkte Einsparpotenzial durch Abschaltungen im Bereich Eliminate sowie das Budgetvolumen kritischer Altsysteme im Bereich Migrate. Darunter liegen die interaktive Matrix und eine filterbare Detailtabelle.

2. **C Level Rationalization und KI Advisor**  
   Hier werden die dringendsten Streichkandidaten und Modernisierungsfälle nach ihrem finanziellen Hebel sortiert. Rechts daneben lässt sich für jede Applikation ein fertiges Management Briefing erzeugen und direkt als Markdown Dokument exportieren.

3. **Portfolio Daten, CSV und Jira API**  
   Ein Verwaltungsbereich zum Erfassen neuer Applikationen, zum Hochladen ganzer Systemlisten per CSV Vorlage sowie zum Synchronisieren von IT Assets aus Jira.