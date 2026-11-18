from __future__ import annotations
import base64
import pandas as pd
import requests
from supabase import Client

# Synthetisches Mittelstands-Portfolio ("NordWest Maschinenbau GmbH")
DEMO_PORTFOLIO_NAME = "NordWest Maschinenbau GmbH (Ist-Analyse)"
DEMO_PORTFOLIO_DESC = "Konsolidierungs-Assessment von 16 Fachbereichs- und Kern-Applikationen (340 Mitarbeitende)."

DEMO_APPLICATIONS = [
    # --- INVEST (Hoher Business Value, Hoher Technical Fit) ---
    {
        "app_name": "SAP S/4HANA Cloud",
        "vendor": "SAP",
        "department": "Finanzen & Produktion",
        "annual_cost_eur": 145000,
        "active_users": 210,
        "bv_strategic": 4.9, "bv_criticality": 5.0, "bv_usage": 4.6,
        "tf_maintainability": 4.4, "tf_security": 4.8, "tf_integration": 4.5,
        "notes": "Zentrales ERP-Rückgrat, vor 18 Monaten erfolgreich auf Cloud-Edition migriert."
    },
    {
        "app_name": "Salesforce Sales Cloud",
        "vendor": "Salesforce",
        "department": "Vertrieb",
        "annual_cost_eur": 68000,
        "active_users": 65,
        "bv_strategic": 4.6, "bv_criticality": 4.4, "bv_usage": 4.2,
        "tf_maintainability": 4.5, "tf_security": 4.7, "tf_integration": 4.3,
        "notes": "Hohe Vertriebsakzeptanz, saubere REST-API-Anbindung an ERP."
    },
    {
        "app_name": "Microsoft 365 E3",
        "vendor": "Microsoft",
        "department": "Unternehmensweit",
        "annual_cost_eur": 89000,
        "active_users": 340,
        "bv_strategic": 4.5, "bv_criticality": 4.9, "bv_usage": 5.0,
        "tf_maintainability": 4.7, "tf_security": 4.6, "tf_integration": 4.8,
        "notes": "Standard-Kollaborationsplattform inkl. Entra ID SSO."
    },
    {
        "app_name": "Jira & Confluence Cloud",
        "vendor": "Atlassian",
        "department": "IT & Engineering",
        "annual_cost_eur": 24000,
        "active_users": 85,
        "bv_strategic": 4.2, "bv_criticality": 4.0, "bv_usage": 4.3,
        "tf_maintainability": 4.6, "tf_security": 4.5, "tf_integration": 4.4,
        "notes": "Führendes Ticket- und Dokumentationssystem der IT."
    },

    # --- MIGRATE (Hoher Business Value, Niedriger Technical Fit -> Modernisieren/Ablösen) ---
    {
        "app_name": "Legacy Lagerverwaltung (LVS 2011)",
        "vendor": "Eigenentwicklung / Alt-Vendor",
        "department": "Logistik",
        "annual_cost_eur": 78000,
        "active_users": 95,
        "bv_strategic": 4.1, "bv_criticality": 4.9, "bv_usage": 4.5,
        "tf_maintainability": 1.6, "tf_security": 1.8, "tf_integration": 1.5,
        "notes": "Läuft auf veraltetem Windows Server 2012 R2, kein Vendor-Support mehr, hohe Ausfallgefahr."
    },
    {
        "app_name": "Angebotskonfigurator (MS Access)",
        "vendor": "Intern (Fachbereich)",
        "department": "Vertrieb & Konstruktion",
        "annual_cost_eur": 32000,
        "active_users": 42,
        "bv_strategic": 4.4, "bv_criticality": 4.6, "bv_usage": 4.0,
        "tf_maintainability": 1.4, "tf_security": 2.0, "tf_integration": 1.3,
        "notes": "Kritisch für Sondermaschinen-Kalkulation, aber monolithische Access-DB ohne Versionierung."
    },
    {
        "app_name": "On-Premise HR & Zeiterfassung",
        "vendor": "LokalSoft",
        "department": "Personal (HR)",
        "annual_cost_eur": 41000,
        "active_users": 340,
        "bv_strategic": 3.8, "bv_criticality": 4.5, "bv_usage": 4.7,
        "tf_maintainability": 2.2, "tf_security": 2.4, "tf_integration": 1.9,
        "notes": "Fehlende Self-Service-App für Mitarbeitende, manuelle CSV-Exporte zur Lohnbuchhaltung."
    },
    {
        "app_name": "CAD-PDM Tresor Server",
        "vendor": "AutoDesk (Alt-Lizenz)",
        "department": "Konstruktion",
        "annual_cost_eur": 64000,
        "active_users": 48,
        "bv_strategic": 4.5, "bv_criticality": 4.8, "bv_usage": 4.4,
        "tf_maintainability": 2.3, "tf_security": 2.5, "tf_integration": 2.1,
        "notes": "Hohe Wartungskosten für lokale Storage-Server, Migration in Cloud-PLM sinnvoll."
    },

    # --- TOLERATE (Niedriger Business Value, Hoher Technical Fit -> Weiterlaufen lassen) ---
    {
        "app_name": "DATEV Unternehmen Online",
        "vendor": "DATEV",
        "department": "Buchhaltung",
        "annual_cost_eur": 18500,
        "active_users": 12,
        "bv_strategic": 2.4, "bv_criticality": 3.8, "bv_usage": 2.6,
        "tf_maintainability": 4.2, "tf_security": 4.6, "tf_integration": 3.6,
        "notes": "Reines Steuerberater-Austauschportal, läuft stabil und wartungsfrei."
    },
    {
        "app_name": "Kantine & Zutrittskontrolle",
        "vendor": "Dormakaba",
        "department": "Facility Management",
        "annual_cost_eur": 11000,
        "active_users": 340,
        "bv_strategic": 1.8, "bv_criticality": 2.9, "bv_usage": 3.5,
        "tf_maintainability": 4.0, "tf_security": 4.1, "tf_integration": 3.2,
        "notes": "Standard-Infrastruktur ohne strategischen Differenzierungshebel."
    },
    {
        "app_name": "DeepL Pro Team",
        "vendor": "DeepL",
        "department": "Marketing & Export",
        "annual_cost_eur": 6500,
        "active_users": 35,
        "bv_strategic": 2.6, "bv_criticality": 2.2, "bv_usage": 3.1,
        "tf_maintainability": 4.8, "tf_security": 4.5, "tf_integration": 4.0,
        "notes": "Günstiges SaaS-Utility mit hohem Nutzerkomfort, kein Handlungsbedarf."
    },
    {
        "app_name": "Fuhrpark-Verwaltung SaaS",
        "vendor": "FleetControl",
        "department": "Einkauf & Fuhrpark",
        "annual_cost_eur": 7200,
        "active_users": 8,
        "bv_strategic": 2.0, "bv_criticality": 2.3, "bv_usage": 2.1,
        "tf_maintainability": 4.1, "tf_security": 4.0, "tf_integration": 3.5,
        "notes": "Erfüllt Zweck für 28 Dienstwagen zuverlässig."
    },

    # --- ELIMINATE (Niedriger Business Value, Niedriger Technical Fit -> Abschalten & Sparen) ---
    {
        "app_name": "Asana Business (Shadow IT)",
        "vendor": "Asana",
        "department": "Marketing",
        "annual_cost_eur": 29500,
        "active_users": 24,
        "bv_strategic": 2.1, "bv_criticality": 1.9, "bv_usage": 2.2,
        "tf_maintainability": 2.8, "tf_security": 2.1, "tf_integration": 1.8,
        "notes": "Redundant zu Jira & MS Planner; über Kreditkarte ohne IT-Freigabe beschafft."
    },
    {
        "app_name": "Altes Intranet-Wiki (MediaWiki)",
        "vendor": "Open Source (Self-Hosted)",
        "department": "Unternehmensweit",
        "annual_cost_eur": 19000,
        "active_users": 18,
        "bv_strategic": 1.5, "bv_criticality": 1.6, "bv_usage": 1.4,
        "tf_maintainability": 1.7, "tf_security": 1.5, "tf_integration": 1.4,
        "notes": "Veraltete PHP-Version mit offenen CVEs; Inhalte bereits in Confluence vorhanden."
    },
    {
        "app_name": "QlikView Legacy BI-Server",
        "vendor": "Qlik",
        "department": "Controlling",
        "annual_cost_eur": 52000,
        "active_users": 14,
        "bv_strategic": 2.3, "bv_criticality": 2.5, "bv_usage": 1.9,
        "tf_maintainability": 2.0, "tf_security": 2.3, "tf_integration": 1.9,
        "notes": "Teure Alt-Lizenzen; 90% der Reports laufen bereits über Power BI (in M365 enthalten)."
    },
    {
        "app_name": "On-Premise Fax- & Scan-Server",
        "vendor": "FaxWare",
        "department": "Verwaltung",
        "annual_cost_eur": 14800,
        "active_users": 9,
        "bv_strategic": 1.2, "bv_criticality": 1.8, "bv_usage": 1.3,
        "tf_maintainability": 1.5, "tf_security": 1.9, "tf_integration": 1.2,
        "notes": "Wird kaum noch genutzt, lässt sich sofort durch Cloud-Mail-Gateway ersetzen."
    },
]

# Beispiel-Tickets für den Jira-Simulationsmodus (falls kein echter Jira-Token vorliegt)
JIRA_SIMULATED_ISSUES = [
    {
        "app_name": " Trello Team-Boards (Jira Sync)",
        "vendor": "Atlassian",
        "department": "HR & Recruiting",
        "annual_cost_eur": 8400,
        "active_users": 16,
        "bv_strategic": 1.9, "bv_criticality": 2.0, "bv_usage": 2.3,
        "tf_maintainability": 2.9, "tf_security": 2.2, "tf_integration": 2.0,
        "notes": "[Jira-Import CMDB-104] Parallelbetrieb zu Jira Cloud, Konsolidierung empfohlen."
    },
    {
        "app_name": "Legacy SPS-Steuerungs-Monitor",
        "vendor": "Siemens / Eigenbau",
        "department": "Fertigung Halle 2",
        "annual_cost_eur": 46000,
        "active_users": 38,
        "bv_strategic": 4.6, "bv_criticality": 4.9, "bv_usage": 4.4,
        "tf_maintainability": 1.7, "tf_security": 1.6, "tf_integration": 1.8,
        "notes": "[Jira-Import CMDB-108] Hohes OT-Security-Risiko, ungepatchte Linux-Appliance."
    },
]


# --- DATENBANK CRUD ---
def fetch_portfolios(supabase: Client) -> list[dict]:
    res = supabase.table("archtime_portfolios").select("*").order("created_at", desc=True).execute()
    return res.data or []


def create_portfolio(supabase: Client, name: str, description: str = "") -> dict:
    res = supabase.table("archtime_portfolios").insert({
        "name": name.strip(),
        "description": description.strip()
    }).execute()
    return res.data[0]


def delete_portfolio(supabase: Client, portfolio_id: str):
    supabase.table("archtime_portfolios").delete().eq("id", portfolio_id).execute()


def fetch_applications(supabase: Client, portfolio_id: str) -> list[dict]:
    res = (
        supabase.table("archtime_applications")
        .select("*")
        .eq("portfolio_id", portfolio_id)
        .order("annual_cost_eur", desc=True)
        .execute()
    )
    return res.data or []


def insert_application(supabase: Client, portfolio_id: str, app_data: dict):
    payload = {"portfolio_id": portfolio_id, **app_data}
    supabase.table("archtime_applications").insert(payload).execute()


def delete_application(supabase: Client, app_id: str):
    supabase.table("archtime_applications").delete().eq("id", app_id).execute()


def seed_demo_portfolio(supabase: Client) -> dict:
    portfolio = create_portfolio(supabase, DEMO_PORTFOLIO_NAME, DEMO_PORTFOLIO_DESC)
    rows = [{"portfolio_id": portfolio["id"], **app} for app in DEMO_APPLICATIONS]
    supabase.table("archtime_applications").insert(rows).execute()
    return portfolio


# --- SCORING ENGINE ---
def calculate_time_scores(
    apps: list[dict],
    bv_weights: tuple[float, float, float] = (1.0, 1.0, 1.0),
    tf_weights: tuple[float, float, float] = (1.0, 1.0, 1.0),
    bv_threshold: float = 3.0,
    tf_threshold: float = 3.0,
) -> pd.DataFrame:
    if not apps:
        return pd.DataFrame()

    df = pd.DataFrame(apps)
    numeric_cols = [
        "annual_cost_eur", "active_users",
        "bv_strategic", "bv_criticality", "bv_usage",
        "tf_maintainability", "tf_security", "tf_integration",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(3.0 if col.startswith(("bv_", "tf_")) else 0.0)

    w_bv_sum = sum(bv_weights) or 1.0
    df["business_value"] = (
        df["bv_strategic"] * bv_weights[0]
        + df["bv_criticality"] * bv_weights[1]
        + df["bv_usage"] * bv_weights[2]
    ) / w_bv_sum

    w_tf_sum = sum(tf_weights) or 1.0
    df["technical_fit"] = (
        df["tf_maintainability"] * tf_weights[0]
        + df["tf_security"] * tf_weights[1]
        + df["tf_integration"] * tf_weights[2]
    ) / w_tf_sum

    df["business_value"] = df["business_value"].round(2)
    df["technical_fit"] = df["technical_fit"].round(2)

    def classify(row) -> str:
        high_bv = row["business_value"] >= bv_threshold
        high_tf = row["technical_fit"] >= tf_threshold
        if high_bv and high_tf:
            return "Invest"
        if high_bv and not high_tf:
            return "Migrate"
        if not high_bv and high_tf:
            return "Tolerate"
        return "Eliminate"

    df["quadrant"] = df.apply(classify, axis=1)
    df["cost_per_user"] = df.apply(
        lambda r: round(r["annual_cost_eur"] / r["active_users"], 2) if r["active_users"] > 0 else r["annual_cost_eur"],
        axis=1,
    )
    return df


# --- JIRA REST API CONNECTOR (BASIC AUTH RFC 7617) ---
def fetch_jira_cmdb_issues(
    jira_domain: str,
    email: str,
    api_token: str,
    jql: str = "issuetype = Task ORDER BY created DESC",
    max_results: int = 10,
) -> list[dict]:
    """
    Ruft über die offizielle Jira Cloud REST API v3 Tickets per Basic Auth ab
    und transformiert sie in ArchTIME-Applikationsdatensätze.
    """
    clean_domain = jira_domain.strip().replace("https://", "").replace("http://", "").rstrip("/")
    url = f"https://{clean_domain}/rest/api/3/search"

    # Base64-Kodierung von 'email:api_token'
    raw_auth = f"{email.strip()}:{api_token.strip()}".encode("utf-8")
    b64_auth = base64.b64encode(raw_auth).decode("utf-8")

    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    params = {
        "jql": jql,
        "maxResults": max_results,
        "fields": "summary,status,priority,labels,assignee",
    }

    resp = requests.get(url, headers=headers, params=params, timeout=12)
    resp.raise_for_status()
    data = resp.json()

    priority_map = {"Highest": 4.8, "High": 4.2, "Medium": 3.2, "Low": 2.2, "Lowest": 1.5}
    imported_apps = []

    for issue in data.get("issues", []):
        fields = issue.get("fields", {})
        key = issue.get("key", "JIRA")
        summary = fields.get("summary", f"Jira Asset {key}")
        prio_name = (fields.get("priority") or {}).get("name", "Medium")
        status_name = (fields.get("status") or {}).get("name", "Open")
        labels = fields.get("labels") or []

        bv_score = priority_map.get(prio_name, 3.0)
        tf_score = 4.2 if status_name.lower() in ("done", "closed", "resolved") else 2.3

        imported_apps.append({
            "app_name": f"{summary[:45]} ({key})",
            "vendor": "Jira Asset / CMDB",
            "department": labels[0] if labels else "IT Operations",
            "annual_cost_eur": 18000,
            "active_users": 30,
            "bv_strategic": bv_score,
            "bv_criticality": bv_score,
            "bv_usage": 3.0,
            "tf_maintainability": tf_score,
            "tf_security": tf_score,
            "tf_integration": 3.0,
            "notes": f"[Jira API Import {key}] Status: {status_name}, Priorität: {prio_name}",
        })
    return imported_apps


# --- RESILIENTE C-LEVEL KI-BERATUNGS-ENGINE (MULTI-MODEL + LOKALER FALLBACK) ---
def _build_deterministic_memo(app_row: dict, portfolio_total_cost: float) -> str:
    """
    Deterministischer TOGAF-Fallback-Generator, falls alle Gemini-Modelle (503/429) überlastet sind.
    Garantiert 100 % Verfügbarkeit in Live-Demos und Vorstellungsgesprächen.
    """
    name = app_row["app_name"]
    quad = app_row["quadrant"]
    cost = float(app_row["annual_cost_eur"])
    users = int(app_row["active_users"])
    cpu = float(app_row["cost_per_user"])
    bv = float(app_row["business_value"])
    tf = float(app_row["technical_fit"])
    sec = float(app_row["tf_security"])
    maint = float(app_row["tf_maintainability"])
    dept = app_row.get("department", "Fachbereich")
    notes = app_row.get("notes", "Keine spezifischen Notizen hinterlegt.")
    share_pct = (cost / portfolio_total_cost * 100) if portfolio_total_cost > 0 else 0.0

    action_templates = {
        "Eliminate": (
            "Kurzfristige Abschaltung (Decommissioning) & Lizenzkündigung",
            f"Sofortige Einsparung von **{cost:,.0f} € / Jahr** ({share_pct:.1f}% des Gesamtbudgets) ohne kritischen Prozessverlust.",
            "1. Lizenzvertrag auf Kündigungsfrist prüfen und vorsorglich kündigen.\n"
            f"2. Die {users} aktiven Nutzer im Bereich *{dept}* auf bestehende Standard-Plattformen (z. B. M365 / Jira / Power BI) umleiten.\n"
            "3. Datenarchivierung (Read-Only-Export) durchführen und Server/Instanz binnen 60 Tagen abschalten.",
        ),
        "Migrate": (
            "Priorisierte Architektur-Modernisierung / Cloud-Ablösung (Replatforming)",
            f"Eliminierung eines kritischen Betriebs- und Sicherheitsrisikos (Technical Fit nur **{tf:.2f}/5.00**) für **{users} produktive Nutzer**.",
            "1. Fachliches Anforderungsprofil (Lastenheft) mit dem Bereich *" + dept + "* aufnehmen.\n"
            "2. Make-or-Buy-Analyse zugunsten einer modernen SaaS-/Cloud-Lösung mit nativer SSO- und API-Integration.\n"
            "3. Parallele Datenmigration und kontrollierter Cut-Over im nächsten Quartal.",
        ),
        "Invest": (
            "Strategischer Ausbau & Prozess-Standardisierung",
            f"Maximierung des ROI einer leistungsfähigen Kernplattform (Business Value **{bv:.2f}**, Technical Fit **{tf:.2f}**).",
            "1. Prüfung, ob redundante Tools aus dem *Eliminate*-Quadranten funktional in dieses System integriert werden können.\n"
            "2. Automatisierung weiterer Schnittstellen (API-First) zur Senkung manueller Prozesskosten.\n"
            "3. Langfristige Enterprise-Rahmenvereinbarung zur Optimierung der Lizenzkosten pro User (" + f"{cpu:,.0f} €" + ").",
        ),
        "Tolerate": (
            "Wartungsarmer Weiterbetrieb (Keep-the-Lights-On / Budget-Deckelung)",
            f"Stabile Unterstützung von *{dept}* bei kontrollierten Kosten (**{cost:,.0f} € / Jahr**), jedoch ohne strategischen Differenzierungshebel.",
            "1. Keine größeren Customizing- oder Beratungsbudgets für dieses System freigeben.\n"
            "2. Jährliches Sicherheits- und Lizenz-Review beibehalten.\n"
            "3. Mittelfristig prüfen, ob die Funktion im Rahmen regulärer ERP-/Cloud-Updates kostenneutral mitabgedeckt wird.",
        ),
    }

    headline, roi_lever, steps = action_templates.get(quad, action_templates["Tolerate"])
    risk_flag = (
        f"⚠️ **Erhöhtes Security-/Compliance-Risiko** (Score: {sec:.1f}/5.0) sowie hohe technische Schuld (Wartbarkeit: {maint:.1f}/5.0)."
        if tf < 2.8 else
        f"✅ Technisch stabiler Zustand (Technical Fit: {tf:.2f}/5.00, Security: {sec:.1f}/5.0)."
    )

    return f"""### 🎯 Management-Entscheidungsvorlage: {name}
**Gartner TIME-Klassifizierung:** `{quad.upper()}` — *{headline}*

#### 1. Ist-Diagnose & Architektur-Risiko
* **Kaufmännische Eckdaten:** {cost:,.0f} € Jahreskosten ({share_pct:.1f}% Anteil am Portfolio-Budget) bei {users} aktiven Nutzern (**{cpu:,.0f} € / User**).
* **Scoring-Bilanz:** Business Value **{bv:.2f} / 5.00** | Technical Fit **{tf:.2f} / 5.00**.
* **Technischer Befund:** {risk_flag}
* **Kontext aus dem Assessment:** *{notes}*

#### 2. Wirtschaftlicher Hebel (Business Case / ROI)
* {roi_lever}

#### 3. Konkreter 3-Stufen-Umsetzungsplan (PMO-Roadmap)
{steps}
""".replace(",", ".")


def generate_executive_briefing(
    app_row: dict,
    portfolio_total_cost: float,
    api_key: str | None = None,
) -> tuple[str, str]:
    """
    Versucht über eine 3-stufige Modell-Kaskade ein individuelles C-Level-Briefing via Gemini zu erstellen.
    Fällt bei Server-Überlastung (503/429) nahtlos auf die deterministische TOGAF-Engine zurück.
    Gibt (markdown_text, verwendete_quelle) zurück.
    """
    prompt = f"""Du bist Senior Enterprise Architect (TOGAF) und IT-Management-Consultant.
Erstelle eine präzise, vorstandstaugliche C-Level-Entscheidungsvorlage (auf Deutsch, mit klarer Markdown-Struktur, ohne lange Einleitung) für folgende Applikation:

- Applikation: {app_row['app_name']} (Hersteller: {app_row.get('vendor', 'k.A.')}, Bereich: {app_row.get('department', 'IT')})
- Gartner TIME-Quadrant: {app_row['quadrant']}
- Jährliche Kosten: {app_row['annual_cost_eur']:,.0f} EUR ({app_row['active_users']} aktive User -> {app_row['cost_per_user']:,.0f} EUR/User)
- Gesamtbudget des Portfolios: {portfolio_total_cost:,.0f} EUR
- Business Value Score: {app_row['business_value']}/5.00 (Strategie: {app_row['bv_strategic']}, Kritikalität: {app_row['bv_criticality']}, Nutzung: {app_row['bv_usage']})
- Technical Fit Score: {app_row['technical_fit']}/5.00 (Wartbarkeit: {app_row['tf_maintainability']}, Security: {app_row['tf_security']}, Integration: {app_row['tf_integration']})
- Architektur-Notiz: {app_row.get('notes', '')}

Gliedere exakt in:
1. Management Summary & TIME-Urteil (2 knackige Sätze)
2. Wirtschaftlicher Business Case & Risikobewertung (konkrete Zahlen & Security/Legacy-Risiken nennen)
3. Konkreter 3-Schritte-Maßnahmenplan für das PMO (nächste 90 Tage)
"""

    if api_key and api_key.strip():
        try:
            from google import genai
            client = genai.Client(api_key=api_key.strip())
            # Modell-Kaskade bei 503 Overload auf dem primären Modell
            for model_name in ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    if response and response.text:
                        return response.text, f"✨ Live KI-Analyse ({model_name})"
                except Exception:
                    continue
        except Exception:
            pass

    # Nahtloser Fallback bei API-Überlastung (503) oder fehlendem Key
    memo = _build_deterministic_memo(app_row, portfolio_total_cost)
    return memo, "🛡️ TOGAF Rule-Engine (Resilient Fallback aktiv – 0 ms Latenz)"