import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="HVAC - Salle Technique", layout="wide")

# Style sombre (lisible dans la sidebar aussi)
st.markdown("""
<style>
:root{
  --bg:#0b1220;
  --panel:#0f1b33;
  --card:#15253e;
  --text:#e8eefc;
  --muted:#b7c6e6;
  --line:#22324c;
  --blue:#60a5fa;
  --green:#22c55e;
  --red:#ef4444;
  --orange:#f59e0b;
}

html, body, [data-testid="stAppViewContainer"]{
  background: var(--bg);
  color: var(--text);
}

[data-testid="stSidebar"]{
  background: #081327;
  border-right: 1px solid var(--line);
}

.header{
  background: linear-gradient(90deg, #0f1b33, #0b1220);
  border: 1px solid var(--line);
  padding: 18px;
  border-radius: 14px;
  margin-bottom: 14px;
}

.header h1{
  color: var(--text);
  text-align: center;
  font-size: 26px;
  margin: 0;
  font-weight: 800;
}

.subhead{
  color: var(--muted);
  font-size: 13px;
  margin-top: -6px;
  margin-bottom: 10px;
}

.section-title{
  color: var(--text);
  font-size: 18px;
  font-weight: 800;
  margin-top: 10px;
}

.block{
  background: rgba(21,37,62,0.55);
  border: 1px solid var(--line);
  padding: 14px;
  border-radius: 14px;
}

.small{
  color: var(--muted);
  font-size: 13px;
}

.kpi-card{
  background: var(--card);
  border: 1px solid var(--line);
  padding: 14px;
  border-radius: 14px;
}

.kpi-title{
  color: var(--muted);
  font-size: 13px;
  margin: 0 0 6px 0;
  font-weight: 600;
}

.kpi-value{
  color: var(--text);
  margin: 0;
  font-size: 32px;
  font-weight: 900;
}

.badge{
  display:inline-block;
  padding: 6px 10px;
  border-radius: 999px;
  font-weight: 800;
  font-size: 12px;
  border: 1px solid var(--line);
  margin-left: 6px;
}
.badge-confort{ background: rgba(34,197,94,.15); color: #86efac; }
.badge-eco{ background: rgba(96,165,250,.12); color: #93c5fd; }
.badge-alarm{ background: rgba(239,68,68,.15); color: #fca5a5; }
.badge-off{ background: rgba(183,198,230,.12); color: rgba(232,238,252,.9); }

hr{
  border: none;
  border-top: 1px solid var(--line);
  margin: 16px 0;
}

/* Sidebar : force les couleurs du texte et des labels */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div{
  color: var(--text) !important;
}

/* Inputs sidebar */
[data-testid="stSidebar"] .stSelectbox,
[data-testid="stSidebar"] .stSlider,
[data-testid="stSidebar"] .stRadio,
[data-testid="stSidebar"] .stButton{
  color: var(--text) !important;
}

/* Fond des widgets (selectbox) */
[data-testid="stSidebar"] [data-baseweb="select"] > div{
  background: rgba(21,37,62,0.85) !important;
  border: 1px solid var(--line) !important;
}

/* Fond des inputs */
[data-baseweb="input"] > div{
  background: rgba(21,37,62,0.85) !important;
  border: 1px solid var(--line) !important;
}

/* Radio */
[data-testid="stSidebar"] [role="radiogroup"]{
  background: rgba(21,37,62,0.35);
  border: 1px solid var(--line);
  padding: 10px;
  border-radius: 12px;
}

/* Boutons */
[data-testid="stButton"] button{
  border-radius: 12px;
  border: 1px solid var(--line);
}

/* Plotly transparent */
.js-plotly-plot .plotly, .js-plotly-plot .plotly div{
  background: rgba(0,0,0,0) !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='header'><h1>Supervision HVAC – Salle Technique</h1></div>", unsafe_allow_html=True)

def safe_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default

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
    return ts.strftime("%d/%m/%Y %H:%M:%S")

def kpi_card(title: str, value: str):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def badge_mode(mode_txt: str):
    if mode_txt == "CONFORT":
        st.markdown("<span class='badge badge-confort'>MODE : CONFORT</span>", unsafe_allow_html=True)
    elif mode_txt == "ECO":
        st.markdown("<span class='badge badge-eco'>MODE : ECO</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='badge badge-off'>MODE : —</span>", unsafe_allow_html=True)

def badge_alarm(is_alarm: bool):
    if is_alarm:
        st.markdown("<span class='badge badge-alarm'>ALARME : ACTIVE</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='badge badge-off'>ALARME : INACTIVE</span>", unsafe_allow_html=True)

def gauge(title, value, vmin, vmax, unit="", seuil_rouge=None):
    val = safe_float(value, 0.0)

    steps = None
    if seuil_rouge is not None:
        steps = [
            {"range": [vmin, seuil_rouge], "color": "rgba(255,255,255,0.18)"},
            {"range": [seuil_rouge, vmax], "color": "rgba(239,68,68,0.9)"},
        ]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        title={"text": title, "font": {"size": 16, "color": "rgba(232,238,252,0.95)"}},
        number={"suffix": f" {unit}" if unit else "", "font": {"size": 44, "color": "rgba(232,238,252,0.95)"}},
        gauge={
            "axis": {"range": [vmin, vmax], "tickcolor": "rgba(183,198,230,0.9)"},
            "bar": {"color": "rgba(96,165,250,0.85)"},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": steps
        }
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=70, b=10),
        height=300
    )
    st.plotly_chart(fig, use_container_width=True)

def style_plot(fig, x_title: str, y_title: str):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="rgba(232,238,252,0.95)"),
        xaxis=dict(title=x_title, gridcolor="rgba(34,50,76,0.6)", zerolinecolor="rgba(34,50,76,0.6)"),
        yaxis=dict(title=y_title, gridcolor="rgba(34,50,76,0.6)", zerolinecolor="rgba(34,50,76,0.6)"),
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)")
    )
    fig.update_traces(line_width=2)

# Sidebar
page = st.sidebar.selectbox("Choisir une page", ["Vue générale", "Commandes", "Historique"])

refresh_seconds = st.sidebar.slider(
    "Temps de rafraîchissement (secondes)",
    min_value=2, max_value=15, value=5, step=1
)

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

# Conversion dates historique (fix .dt)
if not df.empty and "date" in df.columns:
    df["date_local"] = pd.to_datetime(df["date"], errors="coerce")
    if df["date_local"].dt.tz is None:
        df["date_local"] = df["date_local"].dt.tz_localize(
            "Europe/Brussels",
            ambiguous="infer",
            nonexistent="shift_forward"
        )
    else:
        df["date_local"] = df["date_local"].dt.tz_convert("Europe/Brussels")

temperature_lt = last.get("temperature_lt", "—")
humidite_lt    = last.get("humidite_lt", "—")
gaz_value      = last.get("gaz", "—")
motor_speed    = last.get("motor_speed", "—")
alarme_value   = last.get("alarme", "—")
date_value     = last.get("date", None)

mode_confort = last.get("mode_confort", None)
mode_txt = "—"
if mode_confort is not None:
    mode_txt = "CONFORT" if safe_int(mode_confort, 0) == 1 else "ECO"

alarme_int = safe_int(alarme_value, 0)
alarme_txt = "ACTIF" if alarme_int == 1 else "INACTIF"

# Ligne d'infos en haut
top_left, top_right = st.columns([2, 1])
with top_left:
    st.markdown(f"<div class='subhead'>Dernière mesure : <b>{fmt_date(date_value)}</b></div>", unsafe_allow_html=True)
with top_right:
    b1, b2 = st.columns(2)
    with b1:
        badge_mode(mode_txt)
    with b2:
        badge_alarm(alarme_int == 1)

# Page Vue générale
if page == "Vue générale":
    st.markdown("<div class='section-title'>Vue générale</div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Température", f"{temperature_lt} °C")
    with c2:
        kpi_card("Humidité", f"{humidite_lt} %")
    with c3:
        kpi_card("État alarme", alarme_txt)
    with c4:
        kpi_card("Vitesse moteur", f"{motor_speed} /255")

    st.markdown("<div class='section-title'>Jauges</div>", unsafe_allow_html=True)
    g1, g2 = st.columns(2)
    with g1:
        gauge("Gaz MQ-2", gaz_value, 0, 4095, unit="ADC", seuil_rouge=3000)
    with g2:
        gauge("Vitesse moteur", motor_speed, 0, 255, unit="PWM", seuil_rouge=200)

    st.markdown("<div class='section-title'>Évolution récente</div>", unsafe_allow_html=True)
    if df.empty or "date_local" not in df.columns:
        st.info("Pour les graphes, configure API_HISTORY (Secrets Streamlit).")
    else:
        p1, p2 = st.columns(2)
        with p1:
            if "temperature_lt" in df.columns:
                fig = px.line(df, x="date_local", y="temperature_lt", title="Température dans le temps")
                style_plot(fig, "Date / heure", "Température (°C)")
                st.plotly_chart(fig, use_container_width=True)
        with p2:
            if "humidite_lt" in df.columns:
                fig = px.line(df, x="date_local", y="humidite_lt", title="Humidité dans le temps")
                style_plot(fig, "Date / heure", "Humidité (%)")
                st.plotly_chart(fig, use_container_width=True)

# Page Commandes
elif page == "Commandes":
    st.markdown("<div class='section-title'>Commandes</div>", unsafe_allow_html=True)

    if not API_CMD:
        st.error("Secret manquant: API_CMD (POST commande vers Node-RED).")
        st.stop()

    st.markdown("<div class='block'>", unsafe_allow_html=True)
    st.markdown("<div class='small'>Streamlit envoie une commande à Node-RED, puis Node-RED publie via MQTT vers l'ESP32.</div>", unsafe_allow_html=True)

    col_form, col_payload = st.columns([2, 1])
    with col_form:
        vitesse = st.slider("Vitesse moteur (0 à 255)", 0, 255, 120)
        mute = st.checkbox("Couper le buzzer (mute alarme)", value=False)

    payload_send = {"target_speed": int(vitesse), "mute": 1 if mute else 0}
    payload_stop = {"target_speed": 0, "mute": 1 if mute else 0}

    with col_payload:
        st.markdown("<div class='small'>Payload envoyé</div>", unsafe_allow_html=True)
        st.json(payload_send)

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Envoyer la commande", type="primary", use_container_width=True):
            try:
                r = requests.post(API_CMD, json=payload_send, timeout=10)
                r.raise_for_status()
                st.success("Commande envoyée.")
            except Exception as e:
                st.error(f"Erreur envoi commande : {e}")

    with b2:
        if st.button("Arrêter le moteur", use_container_width=True):
            try:
                r = requests.post(API_CMD, json=payload_stop, timeout=10)
                r.raise_for_status()
                st.warning("Commande stop envoyée.")
            except Exception as e:
                st.error(f"Erreur arrêt moteur : {e}")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Aperçu état actuel</div>", unsafe_allow_html=True)
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        kpi_card("Température", f"{temperature_lt} °C")
    with s2:
        kpi_card("Humidité", f"{humidite_lt} %")
    with s3:
        kpi_card("Gaz", f"{gaz_value} ADC")
    with s4:
        kpi_card("Vitesse", f"{motor_speed} /255")

# Page Historique
elif page == "Historique":
    st.markdown("<div class='section-title'>Historique</div>", unsafe_allow_html=True)

    if df.empty:
        st.error("Aucun historique (API_HISTORY pas configurée ou pas de données).")
    else:
        st.markdown("<div class='block'>", unsafe_allow_html=True)
        st.markdown("<div class='small'>Ici je regarde les tendances sur une période plus longue et je peux trier le tableau.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        top1, top2, top3, top4 = st.columns(4)
        with top1:
            kpi_card("Température", f"{temperature_lt} °C")
        with top2:
            kpi_card("Humidité", f"{humidite_lt} %")
        with top3:
            kpi_card("État alarme", alarme_txt)
        with top4:
            kpi_card("Vitesse moteur", f"{motor_speed} /255")

        st.markdown("<div class='section-title'>Courbes</div>", unsafe_allow_html=True)

        if "date_local" in df.columns:
            tcol, hcol = st.columns(2)

            with tcol:
                if "temperature_lt" in df.columns:
                    fig = px.line(df, x="date_local", y="temperature_lt", title="Historique température")
                    style_plot(fig, "Date / heure", "Température (°C)")
                    st.plotly_chart(fig, use_container_width=True)

            with hcol:
                if "humidite_lt" in df.columns:
                    fig = px.line(df, x="date_local", y="humidite_lt", title="Historique humidité")
                    style_plot(fig, "Date / heure", "Humidité (%)")
                    st.plotly_chart(fig, use_container_width=True)

            g1, g2 = st.columns(2)
            with g1:
                if "gaz" in df.columns:
                    fig = px.line(df, x="date_local", y="gaz", title="Historique gaz MQ-2")
                    style_plot(fig, "Date / heure", "Gaz (ADC)")
                    st.plotly_chart(fig, use_container_width=True)

            with g2:
                if "motor_speed" in df.columns:
                    fig = px.line(df, x="date_local", y="motor_speed", title="Historique vitesse moteur")
                    style_plot(fig, "Date / heure", "Vitesse (0–255)")
                    st.plotly_chart(fig, use_container_width=True)

            if "alarme" in df.columns:
                fig_al = px.line(df, x="date_local", y="alarme", title="Historique alarme")
                fig_al.update_traces(line_shape="hv")
                style_plot(fig_al, "Date / heure", "Alarme (0 = off, 1 = on)")
                st.plotly_chart(fig_al, use_container_width=True)

        st.markdown("<div class='section-title'>Tableau</div>", unsafe_allow_html=True)
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
    "<hr><p style='text-align:center; font-size:12px; color:rgba(183,198,230,0.9);'>© 2025 - Binôme A_02 : LFRAH Abdelrahman [HE304830] – IQBAL Adil [HE305031]</p>",
    unsafe_allow_html=True
)
