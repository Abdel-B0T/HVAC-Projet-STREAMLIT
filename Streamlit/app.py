import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from streamlit_autorefresh import st_autorefresh

# Configuration générale
st.set_page_config(
    page_title="HVAC – Salle Technique",
    layout="wide"
)

# Style global sombre (inspiration dashboard Node-RED)
st.markdown("""
<style>
body {
    background-color: #0B1220;
    color: #E8EEFC;
}

/* Header */
.header {
    background: linear-gradient(135deg, #0E1A2F, #0B1220);
    padding: 18px;
    border-radius: 16px;
    margin-bottom: 20px;
    text-align: center;
    font-size: 26px;
    font-weight: 600;
}

/* Cartes KPI */
.kpi {
    background: #12223A;
    border-radius: 16px;
    padding: 18px;
    text-align: center;
}
.kpi h4 {
    margin: 0;
    font-size: 15px;
    color: #9FB4D8;
}
.kpi h2 {
    margin: 8px 0 0 0;
    font-size: 34px;
    color: #E8EEFC;
}

/* Texte secondaire */
.note {
    color: #9FB4D8;
    font-size: 13px;
}

/* Selectbox sidebar */
[data-baseweb="select"] * {
    color: #E8EEFC !important;
}
[data-baseweb="select"] *::selection {
    background: rgba(96,165,250,0.25) !important;
    color: #E8EEFC !important;
}
[data-baseweb="select"] > div {
    background-color: #12223A !important;
    border-radius: 12px !important;
}

/* Boutons */
.stButton > button {
    border-radius: 12px;
    height: 48px;
    font-weight: 600;
}

/* Slider */
.stSlider > div {
    color: #E8EEFC;
}

/* JSON payload */
pre {
    background-color: #0E1A2F !important;
    color: #E8EEFC !important;
    border-radius: 12px;
    padding: 14px;
}

/* Graphes Plotly */
.js-plotly-plot .plotly {
    background: transparent !important;
}
</style>
""", unsafe_allow_html=True)

# Titre principal
st.markdown("<div class='header'>Supervision HVAC – Salle Technique</div>", unsafe_allow_html=True)

# Sidebar
page = st.sidebar.selectbox(
    "Choisir une page",
    ["Vue générale", "Commandes", "Historique"]
)

refresh = st.sidebar.slider(
    "Temps de rafraîchissement (secondes)",
    2, 15, 5
)

if page == "Vue générale":
    st_autorefresh(interval=refresh * 1000, key="refresh_vg")

# Secrets API
API_LATEST = st.secrets.get("API_LATEST", "")
API_HISTORY = st.secrets.get("API_HISTORY", "")
API_CMD = st.secrets.get("API_CMD", "")

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

# Récupération des données
last = get_latest()
df = get_history()

# Extraction valeurs
temp = last.get("temperature_lt", 0)
hum = last.get("humidite_lt", 0)
gaz = last.get("gaz", 0)
motor = last.get("motor_speed", 0)
alarme = "ACTIF" if int(last.get("alarme", 0)) == 1 else "INACTIF"
mode = last.get("mode", "—")
date = last.get("date", "—")

# ------------------------
# Vue générale
# ------------------------
if page == "Vue générale":
    st.markdown(f"<div class='note'>Dernière mesure : {date}</div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<div class='kpi'><h4>Température</h4><h2>{temp} °C</h2></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='kpi'><h4>Humidité</h4><h2>{hum} %</h2></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='kpi'><h4>Mode</h4><h2>{mode}</h2></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='kpi'><h4>Alarme</h4><h2>{alarme}</h2></div>", unsafe_allow_html=True)

    st.markdown("### Jauges")

    g1, g2 = st.columns(2)

    with g1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=gaz,
            number={"suffix": " ADC"},
            title={"text": "Gaz MQ-2"},
            gauge={
                "axis": {"range": [0, 4095]},
                "steps": [
                    {"range": [0, 3000], "color": "#2A3F5F"},
                    {"range": [3000, 4095], "color": "#C0392B"}
                ]
            }
        ))
        fig.update_layout(height=320, margin=dict(t=60, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with g2:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=motor,
            number={"suffix": " /255"},
            title={"text": "Vitesse moteur"},
            gauge={
                "axis": {"range": [0, 255]},
                "steps": [
                    {"range": [0, 180], "color": "#2A3F5F"},
                    {"range": [180, 255], "color": "#F39C12"}
                ]
            }
        ))
        fig.update_layout(height=320, margin=dict(t=60, b=20))
        st.plotly_chart(fig, use_container_width=True)

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        st.markdown("### Évolution récente")

        l1, l2 = st.columns(2)
        with l1:
            fig = px.line(
                df, x="date", y="temperature_lt",
                labels={"temperature_lt": "Température (°C)", "date": "Date / heure"},
                range_y=[0, 40]
            )
            st.plotly_chart(fig, use_container_width=True)

        with l2:
            fig = px.line(
                df, x="date", y="humidite_lt",
                labels={"humidite_lt": "Humidité (%)", "date": "Date / heure"},
                range_y=[0, 100]
            )
            st.plotly_chart(fig, use_container_width=True)

# ------------------------
# Commandes
# ------------------------
elif page == "Commandes":
    st.markdown("### Commandes moteur et alarme")

    vitesse = st.slider("Vitesse moteur (0 à 255)", 0, 255, 120)
    mute = st.checkbox("Couper le buzzer (mute alarme)")

    payload = {
        "target_speed": int(vitesse),
        "mute": 1 if mute else 0
    }

    st.markdown("Payload envoyé")
    st.json(payload)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Envoyer la commande", use_container_width=True):
            requests.post(API_CMD, json=payload, timeout=10)
            st.success("Commande envoyée")

    with c2:
        if st.button("Arrêter le moteur", use_container_width=True):
            requests.post(API_CMD, json={"target_speed": 0, "mute": 1}, timeout=10)
            st.warning("Moteur arrêté")

# ------------------------
# Historique
# ------------------------
elif page == "Historique":
    st.markdown("### Historique des mesures")

    if df.empty:
        st.info("Aucune donnée historique")
    else:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        fig1 = px.line(
            df, x="date", y="temperature_lt",
            labels={"temperature_lt": "Température (°C)", "date": "Date / heure"},
            range_y=[0, 40]
        )
        st.plotly_chart(fig1, use_container_width=True)

        fig2 = px.line(
            df, x="date", y="humidite_lt",
            labels={"humidite_lt": "Humidité (%)", "date": "Date / heure"},
            range_y=[0, 100]
        )
        st.plotly_chart(fig2, use_container_width=True)

        fig3 = px.line(
            df, x="date", y="motor_speed",
            labels={"motor_speed": "Vitesse moteur (0–255)", "date": "Date / heure"},
            range_y=[0, 255]
        )
        st.plotly_chart(fig3, use_container_width=True)

# Footer
st.markdown(
    "<p style='text-align:center; font-size:12px; color:#6B84B5;'>© 2025 – Binôme A_02 : LFRAH Abdelrahman – IQBAL Adil</p>",
    unsafe_allow_html=True
)
