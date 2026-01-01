import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="HVAC - Salle Technique", layout="wide")

# CSS
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
    fig.update_layout(margin=dict(l=20, r=20, t=90, b=20), height=320)
    st.plotly_chart(fig, use_container_width=True)

def safe_int(x, default=0):
    try:
        return int(float(x))
    except Exception:
        return default

def fmt_date(dt_value):
    if dt_value is None:
        return "—"

    ts = pd.to_datetime(dt_value, errors="coerce")
    if pd.isna(ts):
        return str(dt_value)

    # Si pas de timezone -> on suppose que c'est déjà Europe/Brussels
    if ts.tzinfo is None:
        ts = ts.tz_localize("Europe/Brussels", ambiguous="infer", nonexistent="shift_forward")
    else:
        ts = ts.tz_convert("Europe/Brussels")

    return ts.strftime("%d/%m/%Y %H:%M:%S")

# Sidebar
page = st.sidebar.selectbox("Choisir une page", ["Vue générale", "Commandes", "Historique"])

refresh_seconds = st.sidebar.slider(
    "Temps de rafraîchissement (secondes)",
    min_value=2, max_value=15, value=5, step=1
)

# Auto-refresh uniquement sur Vue générale
if page == "Vue générale":
    st_autorefresh(interval=refresh_seconds * 1000, key="auto_refresh_vg")

if st.sidebar.button("Rafraîchir maintenant"):
    st.cache_data.clear()
    st.rerun()

ordre_tableau = "Plus récent → plus ancien"
if page == "Historique":
    ordre_tableau = st.sidebar.radio(
        "Ordre du tableau",
        ["Plus récent → plus ancien", "Plus ancien → plus récent"],
        index=0
    )

# Secrets
API_LATEST = st.secrets.get("API_LATEST", "").strip()
API_HISTORY = st.secrets.get("API_HISTORY", "").strip()
API_CMD = st.secrets.get("API_CMD", "").strip()

if not API_LATEST:
    st.error("Secret manquant: API_LATEST (GET dernière mesure).")
    st.stop()

@st.cache_data(ttl=2)
def get_latest():
    r = requests.get(API_LATEST, timeout=8)
    r.raise_for_status()
    return r.json()

@st.cache_data(ttl=8)
def get_history():
    if not API_HISTORY:
        return pd.DataFrame()
    r = requests.get(API_HISTORY, timeout=12)
    r.raise_for_status()
    return pd.DataFrame(r.json())

# Data
try:
    last = get_latest()
except Exception as e:
    st.error(f"Erreur API (latest) : {e}")
    st.stop()

df = get_history()

# Conversion dates historique (sans forcer utc=True)
if not df.empty and "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Si naive -> on suppose déjà Brussels
    if df["date"].dt.tz is None:
        df["date_local"] = df["date"].dt.tz_localize("Europe/Brussels", ambiguous="infer", nonexistent="shift_forward")
    else:
        df["date_local"] = df["date"].dt.tz_convert("Europe/Brussels")

temperature_lt = last.get("temperature_lt", "—")
humidite_lt    = last.get("humidite_lt", "—")
gaz_value      = last.get("gaz", "—")
motor_speed    = last.get("motor_speed", "—")
alarme_value   = last.get("alarme", "—")
date_value     = last.get("date", None)

alarme_int = safe_int(alarme_value, 0)
alarme_txt = "ACTIF" if alarme_int == 1 else "INACTIF"

# Page: Vue générale
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

    st.markdown("### Gauges (dernière mesure)")
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
                st.plotly_chart(px.line(df, x="date_local", y="temperature_lt", title="Température"), use_container_width=True)
        with p2:
            if "humidite_lt" in df.columns:
                st.plotly_chart(px.line(df, x="date_local", y="humidite_lt", title="Humidité"), use_container_width=True)

# Page: Commandes
elif page == "Commandes":
    st.subheader("Commandes - Salle technique")
    st.info("Streamlit → POST Node-RED → MQTT → ESP32")

    if not API_CMD:
        st.error("Secret manquant: API_CMD (POST commande vers Node-RED).")
        st.stop()

    vitesse = st.slider("Vitesse du moteur (0 à 255)", 0, 255, 120)
    mute = st.checkbox("Mute alarme", value=False)

    payload_send = {"target_speed": int(vitesse), "mute": 1 if mute else 0}
    payload_stop = {"target_speed": 0, "mute": 1 if mute else 0}

    st.json(payload_send)

    b1, b2 = st.columns(2)

    with b1:
        if st.button("Envoyer la commande", use_container_width=True):
            try:
                r = requests.post(API_CMD, json=payload_send, timeout=10)
                r.raise_for_status()
                st.success("Commande envoyée !")
                try:
                    st.json(r.json())
                except Exception:
                    st.write(r.text)
            except Exception as e:
                st.error(f"Erreur envoi commande : {e}")

    with b2:
        if st.button("Arrêter le moteur", use_container_width=True):
            try:
                r = requests.post(API_CMD, json=payload_stop, timeout=10)
                r.raise_for_status()
                st.warning("Moteur arrêté !")
                try:
                    st.json(r.json())
                except Exception:
                    st.write(r.text)
            except Exception as e:
                st.error(f"Erreur arrêt moteur : {e}")

# Page: Historique
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

        st.markdown("### Gauges (dernière mesure)")
        gg1, gg2 = st.columns(2)
        with gg1:
            gauge("Gaz (MQ2)", gaz_value, 0, 4095, suffix="ADC", seuil_rouge=3000)
        with gg2:
            gauge("Vitesse moteur", motor_speed, 0, 255, suffix="/255", seuil_rouge=200)

        st.markdown("### Graphes")
        if "date_local" in df.columns:
            if "gaz" in df.columns:
                st.plotly_chart(px.line(df, x="date_local", y="gaz", title="Évolution Gaz MQ2"), use_container_width=True)
            if "motor_speed" in df.columns:
                st.plotly_chart(px.line(df, x="date_local", y="motor_speed", title="Évolution vitesse moteur"), use_container_width=True)
            if "alarme" in df.columns:
                fig_al = px.line(df, x="date_local", y="alarme", title="Historique alarme (0/1)")
                fig_al.update_traces(line_shape="hv")
                st.plotly_chart(fig_al, use_container_width=True)

        st.markdown("### Tableau")
        df_show = df.copy()

        if "date_local" in df_show.columns:
            ascending = True if ordre_tableau == "Plus ancien → plus récent" else False
            df_show = df_show.sort_values(by="date_local", ascending=ascending)
            df_show["date_local"] = df_show["date_local"].dt.strftime("%d/%m/%Y %H:%M:%S")

        cols = ["id", "date_local", "temperature_lt", "humidite_lt", "gaz", "motor_speed", "alarme"]
        cols = [c for c in cols if c in df_show.columns]
        st.dataframe(df_show[cols], use_container_width=True)

# Footer
st.markdown(
    "<hr><p style='text-align:center; font-size:12px; color:#888;'>© 2025 - Binôme A_02 : LFRAH Abdelrahman [HE304830] – IQBAL Adil [HE305031]</p>",
    unsafe_allow_html=True
)
