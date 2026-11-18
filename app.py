from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from supabase import create_client, Client
from engine import (
    JIRA_SIMULATED_ISSUES,
    fetch_portfolios,
    create_portfolio,
    delete_portfolio,
    fetch_applications,
    insert_application,
    delete_application,
    seed_demo_portfolio,
    calculate_time_scores,
    fetch_jira_cmdb_issues,
    generate_executive_briefing,
)

# --- 1. KONFIGURATION & STYLING ---
st.set_page_config(
    page_title="ArchTIME | Enterprise Application Portfolio Analyzer",
    page_icon="🏛️",
    layout="wide",
)

QUADRANT_COLORS = {
    "Invest": "#10B981",     # Smaragdgrün
    "Migrate": "#F59E0B",    # Bernstein / Orange
    "Tolerate": "#3B82F6",   # Stahlblau
    "Eliminate": "#EF4444",  # Signalrot
}

@st.cache_resource
def init_supabase() -> Client:
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception as e:
        st.error(f"Supabase-Verbindung fehlgeschlagen. Bitte `.streamlit/secrets.toml` prüfen: {e}")
        st.stop()

supabase = init_supabase()
gemini_key = st.secrets.get("GEMINI_API_KEY", "")

# --- 2. SIDEBAR: PORTFOLIO-AUSWAHL & SCORING-GEWICHTUNG ---
with st.sidebar:
    st.title("🏛️ ArchTIME")
    st.caption("TOGAF & Gartner TIME Rationalization Engine")

    portfolios = fetch_portfolios(supabase)

    if not portfolios:
        st.info("Noch kein Portfolio in der Datenbank.")
        if st.button("🚀 Demo-Portfolio laden (16 Apps)", type="primary", use_container_width=True):
            with st.spinner("Erstelle NordWest Maschinenbau GmbH..."):
                seed_demo_portfolio(supabase)
            st.rerun()
        selected_portfolio = None
    else:
        portfolio_map = {p["name"]: p for p in portfolios}
        selected_name = st.selectbox("Aktives Portfolio:", list(portfolio_map.keys()))
        selected_portfolio = portfolio_map[selected_name]

        with st.expander("➕ Neues Portfolio / Verwaltung"):
            new_p_name = st.text_input("Portfolio-Name", placeholder="z.B. Post-Merger IT 2026")
            new_p_desc = st.text_input("Beschreibung", placeholder="Optional")
            if st.button("Leeres Portfolio anlegen", use_container_width=True):
                if new_p_name.strip():
                    create_portfolio(supabase, new_p_name, new_p_desc)
                    st.rerun()
            st.divider()
            if st.button("🚀 Weiteres Demo-Portfolio generieren", use_container_width=True):
                seed_demo_portfolio(supabase)
                st.rerun()
            if st.button("🗑️ Aktuelles Portfolio löschen", use_container_width=True):
                delete_portfolio(supabase, selected_portfolio["id"])
                st.rerun()

    st.divider()
    st.subheader("⚖️ Kriterien-Gewichtung")
    st.caption("Verschiebe die Gewichte, um die TIME-Matrix live neu zu berechnen.")

    with st.expander("Business Value Gewichte", expanded=True):
        w_bv_strat = st.slider("Strategischer Fit", 0.0, 2.0, 1.0, 0.1)
        w_bv_crit = st.slider("Prozess-Kritikalität", 0.0, 2.0, 1.0, 0.1)
        w_bv_usage = st.slider("Nutzer-Abdeckung", 0.0, 2.0, 1.0, 0.1)

    with st.expander("Technical Fit Gewichte", expanded=True):
        w_tf_maint = st.slider("Wartbarkeit & Architektur", 0.0, 2.0, 1.0, 0.1)
        w_tf_sec = st.slider("Security & Compliance", 0.0, 2.0, 1.0, 0.1)
        w_tf_int = st.slider("Integrationsfähigkeit", 0.0, 2.0, 1.0, 0.1)

    with st.expander("Quadranten-Schwellenwerte"):
        bv_thresh = st.slider("Business Value Schwelle (Y)", 1.5, 4.5, 3.0, 0.1)
        tf_thresh = st.slider("Technical Fit Schwelle (X)", 1.5, 4.5, 3.0, 0.1)

# --- 3. HAUPTBEREICH ---
if not selected_portfolio:
    st.header("Willkommen bei ArchTIME")
    st.write(
        "Klicke links in der Sidebar auf **🚀 Demo-Portfolio laden (16 Apps)**, um sofort mit dem "
        "realistischen Beispiel-Portfolio der *NordWest Maschinenbau GmbH* zu starten."
    )
    st.stop()

st.header(f"📊 {selected_portfolio['name']}")
if selected_portfolio.get("description"):
    st.caption(selected_portfolio["description"])

apps_raw = fetch_applications(supabase, selected_portfolio["id"])
df = calculate_time_scores(
    apps_raw,
    bv_weights=(w_bv_strat, w_bv_crit, w_bv_usage),
    tf_weights=(w_tf_maint, w_tf_sec, w_tf_int),
    bv_threshold=bv_thresh,
    tf_threshold=tf_thresh,
)

tab_matrix, tab_roadmap, tab_data = st.tabs([
    "🎯 TIME Matrix & KPIs",
    "🧠 C-Level Rationalization & KI-Advisor",
    "📥 Portfolio-Daten, CSV & Jira API",
])

# === TAB 1: INTERAKTIVE TIME MATRIX ===
with tab_matrix:
    if df.empty:
        st.warning("Dieses Portfolio enthält noch keine Applikationen. Wechsle zum Tab **📥 Portfolio-Daten, CSV & Jira API**.")
    else:
        total_cost = df["annual_cost_eur"].sum()
        elim_df = df[df["quadrant"] == "Eliminate"]
        migr_df = df[df["quadrant"] == "Migrate"]
        elim_savings = elim_df["annual_cost_eur"].sum()
        migr_budget = migr_df["annual_cost_eur"].sum()

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Applikationen gesamt", f"{len(df)} Apps")
        k2.metric("Jährliche IT-Run-Kosten", f"{total_cost:,.0f} €".replace(",", "."))
        k3.metric(
            "Direktes Einsparpotenzial (Eliminate)",
            f"{elim_savings:,.0f} € / J.".replace(",", "."),
            delta=f"-{(elim_savings / total_cost * 100):.1f}% Run-Cost" if total_cost > 0 else None,
            delta_color="normal",
        )
        k4.metric(
            "Migrations-Fokus (Migrate)",
            f"{migr_budget:,.0f} € / J.".replace(",", "."),
            delta=f"{len(migr_df)} kritische Legacy-Apps",
            delta_color="off",
        )

        st.divider()

        fig = go.Figure()

        # Farbliche Quadranten-Hintergründe (bis 5.45 erweitert, damit Blasen nicht am Label kleben)
        fig.add_shape(type="rect", x0=0.8, y0=bv_thresh, x1=tf_thresh, y1=5.45,
                      fillcolor="rgba(245, 158, 11, 0.07)", line_width=0, layer="below")
        fig.add_shape(type="rect", x0=tf_thresh, y0=bv_thresh, x1=5.45, y1=5.45,
                      fillcolor="rgba(16, 185, 129, 0.07)", line_width=0, layer="below")
        fig.add_shape(type="rect", x0=0.8, y0=0.8, x1=tf_thresh, y1=bv_thresh,
                      fillcolor="rgba(239, 68, 68, 0.07)", line_width=0, layer="below")
        fig.add_shape(type="rect", x0=tf_thresh, y0=0.8, x1=5.45, y1=bv_thresh,
                      fillcolor="rgba(59, 130, 246, 0.07)", line_width=0, layer="below")

        # Schwellenwert-Linien
        fig.add_vline(x=tf_thresh, line_dash="dash", line_color="rgba(150,150,150,0.55)")
        fig.add_hline(y=bv_thresh, line_dash="dash", line_color="rgba(150,150,150,0.55)")

        # Quadranten-Labels sauber in den äußeren Ecken platziert
        fig.add_annotation(x=0.95, y=5.32, text="<b>MIGRATE</b> (Modernisieren / Ablösen)", showarrow=False,
                           xanchor="left", font=dict(color="#F59E0B", size=12))
        fig.add_annotation(x=5.35, y=5.32, text="<b>INVEST</b> (Strategisch ausbauen)", showarrow=False,
                           xanchor="right", font=dict(color="#10B981", size=12))
        fig.add_annotation(x=0.95, y=0.95, text="<b>ELIMINATE</b> (Abschalten & Sparen)", showarrow=False,
                           xanchor="left", font=dict(color="#EF4444", size=12))
        fig.add_annotation(x=5.35, y=0.95, text="<b>TOLERATE</b> (Stabil halten)", showarrow=False,
                           xanchor="right", font=dict(color="#3B82F6", size=12))

        max_cost = df["annual_cost_eur"].max() or 1
        for quad in ["Invest", "Migrate", "Tolerate", "Eliminate"]:
            sub = df[df["quadrant"] == quad]
            if sub.empty:
                continue
            sizes = (sub["annual_cost_eur"] / max_cost * 36) + 14
            fig.add_trace(go.Scatter(
                x=sub["technical_fit"],
                y=sub["business_value"],
                mode="markers+text",
                name=f"{quad} ({len(sub)})",
                text=sub["app_name"],
                textposition="top center",
                textfont=dict(size=10),
                marker=dict(
                    size=sizes,
                    color=QUADRANT_COLORS[quad],
                    opacity=0.85,
                    line=dict(width=1.5, color="white"),
                ),
                customdata=sub[["department", "vendor", "annual_cost_eur", "active_users", "cost_per_user", "notes"]],
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Quadrant: " + quad + "<br>"
                    "Business Value: %{y:.2f} | Technical Fit: %{x:.2f}<br>"
                    "Jahreskosten: %{customdata[2]:,.0f} € (%{customdata[4]:,.0f} €/User)<br>"
                    "Fachbereich: %{customdata[0]} (%{customdata[3]} User)<br>"
                    "<i>%{customdata[5]}</i><extra></extra>"
                ),
            ))

        fig.update_layout(
            height=600,
            xaxis=dict(title="Technical Fit (Wartbarkeit, Security, Integration) →", range=[0.8, 5.45], dtick=0.5),
            yaxis=dict(title="Business Value (Strategie, Kritikalität, Nutzung) →", range=[0.8, 5.45], dtick=0.5),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 Bewertungsübersicht & Export")
        quad_filter = st.multiselect(
            "Nach TIME-Quadrant filtern:",
            options=["Eliminate", "Migrate", "Invest", "Tolerate"],
            default=["Eliminate", "Migrate", "Invest", "Tolerate"],
        )
        display_df = df[df["quadrant"].isin(quad_filter)][[
            "app_name", "quadrant", "department", "annual_cost_eur",
            "active_users", "cost_per_user", "business_value", "technical_fit", "notes"
        ]].rename(columns={
            "app_name": "Applikation",
            "quadrant": "TIME-Quadrant",
            "department": "Fachbereich",
            "annual_cost_eur": "Kosten (€/Jahr)",
            "active_users": "User",
            "cost_per_user": "€ / User",
            "business_value": "Business Value",
            "technical_fit": "Technical Fit",
            "notes": "Architektur-Notiz",
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)

# === TAB 2: C-LEVEL RATIONALIZATION & KI-ADVISOR ===
with tab_roadmap:
    if df.empty:
        st.info("Bitte zuerst Applikationen laden.")
    else:
        total_cost = df["annual_cost_eur"].sum()
        col_left, col_right = st.columns([1.05, 1.35])

        with col_left:
            st.subheader("💰 Top-Konsolidierungs-Kandidaten")
            st.caption("Priorisiert nach finanziellem Einsparhebel (*Eliminate*) und technischem Risiko (*Migrate*).")

            action_df = df[df["quadrant"].isin(["Eliminate", "Migrate"])].sort_values(
                by=["quadrant", "annual_cost_eur"], ascending=[True, False]
            )
            if action_df.empty:
                st.success("Keine Applikationen in Eliminate oder Migrate!")
            else:
                for _, row in action_df.iterrows():
                    badge = "🔴 ELIMINATE" if row["quadrant"] == "Eliminate" else "🟠 MIGRATE"
                    with st.container(border=True):
                        c1, c2 = st.columns([2.4, 1])
                        c1.markdown(f"**{row['app_name']}**  \n`{badge}` · *{row['department']}*")
                        c2.markdown(f"**{row['annual_cost_eur']:,.0f} € / J.**  \nBV: {row['business_value']} | TF: {row['technical_fit']}".replace(",", "."))
                        st.caption(row.get("notes", ""))

        with col_right:
            st.subheader("🧠 KI-Executive-Briefing (Vorstandsvorlage)")
            st.caption(
                "Generiert eine C-Level-Entscheidungsvorlage inkl. Business Case und 90-Tage-PMO-Plan. "
                "Mit integriertem Multi-Model- & TOGAF-Fallback bei Gemini-Überlastung (503)."
            )

            # Standardmäßig Eliminate- und Migrate-Kandidaten oben in der Auswahlliste zeigen
            priority_order = {"Eliminate": 0, "Migrate": 1, "Tolerate": 2, "Invest": 3}
            sorted_df = df.assign(_prio=df["quadrant"].map(priority_order)).sort_values(
                by=["_prio", "annual_cost_eur"], ascending=[True, False]
            )
            app_choices = {
                f"[{r['quadrant'].upper()}] {r['app_name']} ({r['annual_cost_eur']:,.0f} €)".replace(",", "."): r
                for _, r in sorted_df.iterrows()
            }

            selected_label = st.selectbox("Applikation für C-Level-Briefing wählen:", list(app_choices.keys()))
            target_row = app_choices[selected_label]

            if st.button("✨ Vorstandsvorlage & Maßnahmenplan generieren", type="primary", use_container_width=True):
                with st.spinner("Erstelle C-Level-Entscheidungsvorlage..."):
                    memo_md, engine_source = generate_executive_briefing(
                        target_row.to_dict(),
                        portfolio_total_cost=total_cost,
                        api_key=gemini_key,
                    )
                st.session_state["last_memo"] = memo_md
                st.session_state["last_source"] = engine_source
                st.session_state["last_app_name"] = target_row["app_name"]

            if "last_memo" in st.session_state:
                st.caption(f"Quelle: **{st.session_state['last_source']}**")
                with st.container(border=True):
                    st.markdown(st.session_state["last_memo"])
                st.download_button(
                    "📥 Entscheidungsvorlage als Markdown (.md) exportieren",
                    data=st.session_state["last_memo"].encode("utf-8"),
                    file_name=f"Executive_Briefing_{st.session_state['last_app_name'].replace(' ', '_')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

# === TAB 3: PORTFOLIO-DATEN, CSV & JIRA REST API CONNECTOR ===
with tab_data:
    col_add, col_integrations = st.columns([1.15, 1.15])

    with col_add:
        st.subheader("➕ Einzelne Applikation erfassen")
        with st.form("add_app_form", clear_on_submit=True):
            f1, f2 = st.columns(2)
            app_name = f1.text_input("Applikationsname *", placeholder="z.B. HubSpot CRM")
            vendor = f2.text_input("Hersteller / Vendor", placeholder="z.B. HubSpot Inc.")
            f3, f4, f5 = st.columns(3)
            department = f3.text_input("Fachbereich", value="IT")
            annual_cost = f4.number_input("Jahreskosten (€)", min_value=0, value=15000, step=1000)
            active_users = f5.number_input("Aktive User", min_value=0, value=25, step=5)

            st.markdown("**Business Value Kriterien (1 = niedrig, 5 = hoch)**")
            b1, b2, b3 = st.columns(3)
            bv_s = b1.slider("Strategischer Fit", 1.0, 5.0, 3.0, 0.5)
            bv_c = b2.slider("Kritikalität", 1.0, 5.0, 3.0, 0.5)
            bv_u = b3.slider("Nutzungsgrad", 1.0, 5.0, 3.0, 0.5)

            st.markdown("**Technical Fit Kriterien (1 = kritisch/alt, 5 = modern/stabil)**")
            t1, t2, t3 = st.columns(3)
            tf_m = t1.slider("Wartbarkeit", 1.0, 5.0, 3.0, 0.5)
            tf_s = t2.slider("Security", 1.0, 5.0, 3.0, 0.5)
            tf_i = t3.slider("Integration", 1.0, 5.0, 3.0, 0.5)

            notes = st.text_input("Kommentar / Architektur-Risiko", placeholder="z.B. Fehlende SSO-Anbindung")

            if st.form_submit_button("💾 Applikation speichern", type="primary", use_container_width=True):
                if not app_name.strip():
                    st.error("Bitte einen Applikationsnamen angeben.")
                else:
                    insert_application(supabase, selected_portfolio["id"], {
                        "app_name": app_name.strip(),
                        "vendor": vendor.strip(),
                        "department": department.strip(),
                        "annual_cost_eur": annual_cost,
                        "active_users": active_users,
                        "bv_strategic": bv_s,
                        "bv_criticality": bv_c,
                        "bv_usage": bv_u,
                        "tf_maintainability": tf_m,
                        "tf_security": tf_s,
                        "tf_integration": tf_i,
                        "notes": notes.strip(),
                    })
                    st.success(f"'{app_name}' gespeichert!")
                    st.rerun()

    with col_integrations:
        st.subheader("🔗 Jira Cloud REST API Connector (CMDB Sync)")
        st.caption(
            "Authentifiziert sich per **HTTP Basic Auth (Base64 `email:api_token`)** gegen `/rest/api/3/search` "
            "oder simuliert den CMDB-Import für Live-Demos ohne eigenen Jira-Tenant."
        )
        with st.expander("⚙️ Live Jira REST API Verbindung (Optional)", expanded=False):
            j_domain = st.text_input("Jira Cloud Domain", placeholder="dein-team.atlassian.net")
            j_email = st.text_input("Atlassian E-Mail", placeholder="bo@beispiel.de")
            j_token = st.text_input("Atlassian API-Token", type="password")
            j_jql = st.text_input("JQL-Filter", value="issuetype = Task ORDER BY created DESC")

            if st.button("🔄 Live aus Jira Cloud importieren", use_container_width=True):
                if not (j_domain and j_email and j_token):
                    st.warning("Bitte Domain, E-Mail und API-Token ausfüllen.")
                else:
                    try:
                        with st.spinner("Rufe Jira REST API v3 ab..."):
                            jira_apps = fetch_jira_cmdb_issues(j_domain, j_email, j_token, j_jql)
                        if not jira_apps:
                            st.info("Keine passenden Jira-Issues gefunden.")
                        else:
                            for ja in jira_apps:
                                insert_application(supabase, selected_portfolio["id"], ja)
                            st.success(f"✅ {len(jira_apps)} Assets aus Jira importiert!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Jira API Fehler: {e}")

        if st.button("⚡ Jira CMDB-Sync simulieren (2 IT-Assets importieren)", use_container_width=True):
            for sim_app in JIRA_SIMULATED_ISSUES:
                insert_application(supabase, selected_portfolio["id"], sim_app)
            st.success("✅ 2 CMDB-Tickets (Trello & SPS-Monitor) ins Portfolio synchronisiert!")
            st.rerun()

        st.divider()
        st.subheader("📤 CSV-Bulk-Import & Template")
        template_df = pd.DataFrame([{
            "app_name": "Miro Enterprise",
            "vendor": "Miro",
            "department": "Produktmanagement",
            "annual_cost_eur": 12000,
            "active_users": 40,
            "bv_strategic": 3.5, "bv_criticality": 2.5, "bv_usage": 4.0,
            "tf_maintainability": 4.5, "tf_security": 4.5, "tf_integration": 4.0,
            "notes": "Sauberes Cloud-Whiteboard",
        }])
        st.download_button(
            "📥 Beispiel-CSV herunterladen",
            data=template_df.to_csv(index=False).encode("utf-8"),
            file_name="archtime_template.csv",
            mime="text/csv",
            use_container_width=True,
        )

        uploaded_csv = st.file_uploader("CSV-Datei hochladen", type=["csv"])
        if uploaded_csv is not None:
            try:
                in_df = pd.read_csv(uploaded_csv)
                if st.button(f"✨ {len(in_df)} Zeilen importieren", type="primary", use_container_width=True):
                    for _, row in in_df.iterrows():
                        insert_application(supabase, selected_portfolio["id"], {
                            "app_name": str(row.get("app_name", "Unbenannt")),
                            "vendor": str(row.get("vendor", "")),
                            "department": str(row.get("department", "IT")),
                            "annual_cost_eur": float(row.get("annual_cost_eur", 0)),
                            "active_users": int(row.get("active_users", 0)),
                            "bv_strategic": float(row.get("bv_strategic", 3.0)),
                            "bv_criticality": float(row.get("bv_criticality", 3.0)),
                            "bv_usage": float(row.get("bv_usage", 3.0)),
                            "tf_maintainability": float(row.get("tf_maintainability", 3.0)),
                            "tf_security": float(row.get("tf_security", 3.0)),
                            "tf_integration": float(row.get("tf_integration", 3.0)),
                            "notes": str(row.get("notes", "")),
                        })
                    st.success("CSV-Import erfolgreich!")
                    st.rerun()
            except Exception as e:
                st.error(f"Fehler beim Lesen der CSV: {e}")

        if not df.empty:
            st.divider()
            st.subheader("🗑️ Applikation entfernen")
            app_options = {f"{r['app_name']} ({r['annual_cost_eur']:,.0f} €)": r["id"] for _, r in df.iterrows()}
            del_choice = st.selectbox("Applikation auswählen:", list(app_options.keys()))
            if st.button("Ausgewählte App löschen", use_container_width=True):
                delete_application(supabase, app_options[del_choice])
                st.rerun()