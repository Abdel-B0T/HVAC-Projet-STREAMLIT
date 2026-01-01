import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="HVAC - Salle Technique", layout="wide")

# -----------------------------
# CSS
# -----------------------------
st.markdown("""
<style>
.header {
    background-color: #1F1F1F;
    padding: 16px;
    border-radius: 14px;
    margin-bottom: 18px;
}
.header h1 {
    color: white;
    text-align: center;
    font-size: 26px;
    margin: 0;
}
.small-note {
    color: #666;
    font-size: 13px;
    margin-top: -6px;
    margin-bottom: 10px;
}
.kpi-card {
    padding: 14px;
    border-radius: 14px;
    text-align: center;
    margin-bottom: 10px;
}
.kpi-card h4 {
    color: white;
    margin: 0 0 6px 0;
    font-weight: 600;
}
.kpi-card h2 {
    color: white;
    margin: 0;
    font-size: 36px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='header'><h1>Supervision HVAC – Salle Technique</h1></div>", unsafe_allow_html=True)

def kpi(title: str, value: str, color: str):
    st.markdown(
        f"""
        <div class="kpi-card" style="background-color:{color};">
            <h4>{title}</h4>
            <h2>{value}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

# Gauge Plotly (titre non coupé)
def gauge(title, value, vmin, vmax, suffix="", seuil_rouge=None):
    try:
        val = float(value)
    except Exception:
        val = 0.0

    steps = None
    if seuil_rouge is not None:
        steps = [
            {"range": [vmin, seuil_rouge], "color": "lightgray"},
            {"range": [seuil_rouge, vmax], "color": "red"},
        ]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        title={"text": title, "font": {"size": 18}},
        number={"suffix": f" {suffix}", "font": {"size": 48}},
        gauge={"axis": {"range": [vmin, vmax]}, "steps": steps}
    ))

    fig.update_layout(
        margin=dict(l=20, r=20, t=80, b=20),
        height=320
    )
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Sidebar
# -----------------------------
page = st.sidebar.selectbox("Choisir une page", ["Vue générale", "Commandes", "Historique"])

# Slider de contrôle du refresh (en secondes)
refresh_seconds = st.sidebar.slider(
    "Temps de rafraîchissement (secondes)",
    min_value=2,
    max_value=10,
    value=4,
    step=1
)

# Auto-refresh UNIQUEMENT sur Vue générale
if page == "Vue générale":
    st_autorefresh(interval=refresh_seconds * 1000, key="auto_refresh_vue_generale")

st.sidebar.write("Actualisation")
if st.sidebar.button("Rafraîchir maintenant"):
    st.cache_data.clear()
    st.rerun()

# Choix ordre tableau (uniquement pour Historique)
ordre_tableau = "Plus récent → plus ancien"
if page == "Historique":
    ordre_tableau = st.sidebar.radio(
        "Ordre du tableau",
        ["Plus récent → plus ancien", "Plus ancien → plus récent"],
        index=0
    )

# -----------------------------
# API Secrets
# -----------------------------
API_LATEST = st.secrets.get("API_LATEST", "").strip()
API_HISTORY = st.secrets.get("API_HISTORY", "").strip()

if not API_LATEST:
    st.error("Secret manquant: API_LATEST. Va dans Streamlit Cloud > Settings > Secrets.")
    st.stop()

@st.cache_data(ttl=2)
def get_latest():
    r = requests.get(API_LATEST, timeout=6)
    r.raise_for_status()
    return r.json()

@st.cache_data(ttl=8)
def get_history():
    if not API_HISTORY:
        return pd.DataFrame()
    r = requests.get(API_HISTORY, timeout=10)
    r.raise_for_status()
    return pd.DataFrame(r.json())

def fmt_date(dt_value):
    if dt_value is None:
        return "—"
    ts = pd.to_datetime(dt_value, utc=True, errors="coerce")
    if pd.isna(ts):
        return str(dt_value)
    return ts.tz_convert("Europe/Brussels").strftime("%d/%m/%Y %H:%M:%S")

def safe_int(x, default=0):
    try:
        return int(float(x))
    except Exception:
        return default

# -----------------------------
# Data
# -----------------------------
try:
    last = get_latest()
except Exception as e:
    st.error(f"Erreur API (latest) : {e}")
    st.stop()

df = get_history()
if not df.empty and "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    df["date_local"] = df["date"].dt.tz_convert("Europe/Brussels")

# Valeurs last
temperature_lt = last.get("temperature_lt", "—")
humidite_lt    = last.get("humidite_lt", "—")
gaz_value      = last.get("gaz", "—")
motor_speed    = last.get("motor_speed", "—")
alarme_value   = last.get("alarme", "—")
date_value     = last.get("date", None)

alarme_int = safe_int(alarme_value, 0)
alarme_txt = "ACTIF" if alarme_int == 1 else "INACTIF"

# -----------------------------
# Page: Vue générale
# -----------------------------
if page == "Vue générale":
    st.subheader("Vue générale - Salle technique")
    st.markdown(f"<div class='small-note'>Dernière mesure : <b>{fmt_date(date_value)}</b></div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi("Température (°C)", f"{temperature_lt}", "#2E86C1")
    with c2:
        kpi("Humidité (%)", f"{humidite_lt}", "#239B56")
    with c3:
        kpi("Alarme", alarme_txt, "#C0392B" if alarme_txt == "ACTIF" else "#5D6D7E")
    with c4:
        kpi("Vitesse (0-255)", f"{motor_speed}", "#5D6D7E")

    st.markdown("### Gauges")
    g1, g2 = st.columns(2)
    with g1:
        gauge("Gaz (MQ2)", gaz_value, 0, 4095, suffix="ADC", seuil_rouge=3000)
    with g2:
        gauge("Vitesse moteur", motor_speed, 0, 255, suffix="/255", seuil_rouge=200)

    st.markdown("### Graphes (Température / Humidité)")
    if df.empty or "date_local" not in df.columns:
        st.info("Pour les graphes, configure API_HISTORY (Secrets Streamlit).")
    else:
        p1, p2 = st.columns(2)
        with p1:
            if "temperature_lt" in df.columns:
                fig_t = px.line(df, x="date_local", y="temperature_lt", title="Température")
                st.plotly_chart(fig_t, use_container_width=True)
            else:
                st.info("Colonne temperature_lt manquante.")
        with p2:
            if "humidite_lt" in df.columns:
                fig_h = px.line(df, x="date_local", y="humidite_lt", title="Humidité")
                st.plotly_chart(fig_h, use_container_width=True)
            else:
                st.info("Colonne humidite_lt manquante.")

# -----------------------------
# Page: Commandes (UI)
# -----------------------------
elif page == "Commandes":
    st.subheader("Commandes - Salle technique")
    st.info("Étape suivante : on envoie les commandes à Node-RED (POST) → MQTT → ESP32.")

    vitesse = st.slider("Vitesse du moteur (0 à 255)", 0, 255, 120)
    mute = st.checkbox("Mute alarme", value=False)
    st.write({"target_speed": vitesse, "mute": 1 if mute else 0})

# -----------------------------
# Page: Historique
# -----------------------------
elif page == "Historique":
    st.subheader("Historique - mesures_hvac")

    if df.empty:
        st.error("Aucun historique (API_HISTORY pas configurée ou pas de données).")
    else:
        st.markdown(f"<div class='small-note'>Dernière mesure : <b>{fmt_date(date_value)}</b></div>", unsafe_allow_html=True)

        top1, top2, top3, top4 = st.columns(4)
        with top1:
            kpi("Température (°C)", f"{temperature_lt}", "#2E86C1")
        with top2:
            kpi("Humidité (%)", f"{humidite_lt}", "#239B56")
        with top3:
            kpi("Alarme", alarme_txt, "#C0392B" if alarme_txt == "ACTIF" else "#5D6D7E")
        with top4:
            kpi("Vitesse (0-255)", f"{motor_speed}", "#5D6D7E")

        st.markdown("### Gauges")
        gg1, gg2 = st.columns(2)
        with gg1:
            gauge("Gaz (MQ2)", gaz_value, 0, 4095, suffix="ADC", seuil_rouge=3000)
        with gg2:
            gauge("Vitesse moteur", motor_speed, 0, 255, suffix="/255", seuil_rouge=200)

        st.markdown("### Graphes")
        if "date_local" in df.columns and "gaz" in df.columns:
            fig_gaz = px.line(df, x="date_local", y="gaz", title="Évolution Gaz MQ2")
            st.plotly_chart(fig_gaz, use_container_width=True)

        if "date_local" in df.columns and "motor_speed" in df.columns:
            fig_motor = px.line(df, x="date_local", y="motor_speed", title="Évolution vitesse moteur")
            st.plotly_chart(fig_motor, use_container_width=True)

        if "date_local" in df.columns and "alarme" in df.columns:
            fig_al = px.line(df, x="date_local", y="alarme", title="Historique alarme (0/1)")
            fig_al.update_traces(line_shape="hv")
            st.plotly_chart(fig_al, use_container_width=True)

        st.markdown("### Tableau")
        df_show = df.copy()

        # Tri selon le choix utilisateur
        if "date_local" in df_show.columns:
            ascending = True if ordre_tableau == "Plus ancien → plus récent" else False
            df_show = df_show.sort_values(by="date_local", ascending=ascending)

            # Format lisible après tri
            df_show["date_local"] = df_show["date_local"].dt.strftime("%d/%m/%Y %H:%M:%S")

        cols = ["id", "date_local", "temperature_lt", "humidite_lt", "gaz", "motor_speed", "alarme"]
        cols = [c for c in cols if c in df_show.columns]
        st.dataframe(df_show[cols], use_container_width=True)

# Pied de page
st.markdown(
    "<hr><p style='text-align:center; font-size:12px; color:#888;'>© 2025 - Binôme A_02 : LFRAH Abdelrahman [HE304830] – IQBAL Adil [HE304830]</p>",
    unsafe_allow_html=True
)
