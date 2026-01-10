# Code app.py pour géré streamlit LFRAH & IQBAL

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from streamlit_autorefresh import st_autorefresh

# On configure la page (titre + layout large)
st.set_page_config(page_title="HVAC - Salle Technique", layout="wide")

# On met toute la DA en CSS (couleurs, cards, boutons, selectbox, etc.)
st.markdown("""
<style>
:root{
  --bg:#0b1220;
  --panel:#0f1b33;
  --card:#15253e;
  --line:#22324c;
  --text:#e8eefc;
  --muted:#b7c6e6;
  --accent:#60a5fa;
  --danger:#ef4444;
}

html, body, [data-testid="stAppViewContainer"]{
  background: var(--bg);
  color: var(--text);
}

[data-testid="stSidebar"]{
  background: #081327;
  border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] *{
  color: var(--text) !important;
}

.header{
  background: linear-gradient(135deg, #0f1b33, #0b1220);
  border: 1px solid var(--line);
  padding: 18px;
  border-radius: 16px;
  margin-bottom: 14px;
  text-align: center;
}
.header h1{
  margin: 0;
  font-size: 26px;
  font-weight: 800;
  color: var(--text);
}

.note{
  color: var(--muted);
  font-size: 13px;
  margin-top: -4px;
  margin-bottom: 12px;
}

.section-title{
  color: var(--text);
  font-size: 18px;
  font-weight: 800;
  margin: 12px 0 8px 0;
}

.kpi-card{
  background: rgba(21,37,62,0.92);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 16px;
  min-height: 120px;
  display:flex;
  flex-direction:column;
  justify-content:center;
  align-items:center;
  text-align:center;
}
.kpi-title{
  color: var(--muted);
  font-size: 13px;
  font-weight: 600;
  margin: 0 0 8px 0;
}
.kpi-value{
  color: var(--text);
  font-size: 34px;
  font-weight: 900;
  margin: 0;
}

[data-baseweb="select"] > div{
  background: rgba(21,37,62,0.85) !important;
  border: 1px solid var(--line) !important;
  border-radius: 12px !important;
}
[data-baseweb="select"] span,
[data-baseweb="select"] input{
  color: rgba(232,238,252,0.95) !important;
}
[data-baseweb="select"] svg{
  fill: rgba(232,238,252,0.95) !important;
}
[data-baseweb="select"] *::selection{
  background: rgba(96,165,250,0.25) !important;
  color: rgba(232,238,252,0.95) !important;
}
[data-baseweb="select"] > div:focus-within{
  border: 1px solid rgba(96,165,250,0.65) !important;
  box-shadow: 0 0 0 2px rgba(96,165,250,0.15) !important;
}

/* Fix: texte du menu déroulant (options) en blanc */
[data-baseweb="select"] *{
  color: rgba(232,238,252,0.95) !important;
}
[data-baseweb="menu"] *{
  color: rgba(232,238,252,0.95) !important;
}
[data-baseweb="menu"] div[role="option"]:hover{
  background-color: rgba(96,165,250,0.25) !important;
}
[data-baseweb="menu"] div[aria-selected="true"]{
  background-color: rgba(96,165,250,0.35) !important;
  color: white !important;
}

label, [data-testid="stWidgetLabel"]{
  color: rgba(232,238,252,0.95) !important;
}

[data-testid="stButton"] button{
  border-radius: 12px;
  border: 1px solid var(--line) !important;
  background: rgba(21,37,62,0.9) !important;
  color: var(--text) !important;
  font-weight: 700 !important;
  height: 46px;
}
[data-testid="stButton"] button:hover{
  background: rgba(96,165,250,0.25) !important;
  border: 1px solid rgba(96,165,250,0.65) !important;
}

.payload{
  background: rgba(7,18,34,0.9);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 12px 14px;
  color: rgba(232,238,252,0.95);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 14px;
  white-space: pre;
  overflow-x: auto;
}

[data-testid="stDataFrame"]{
  background: rgba(21,37,62,0.55);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 8px;
}

.js-plotly-plot .plotly, .js-plotly-plot .plotly div{
  background: rgba(0,0,0,0) !important;
}

hr{
  border: none;
  border-top: 1px solid rgba(34,50,76,0.7);
  margin: 14px 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='header'><h1>Supervision HVAC – Salle Technique</h1></div>", unsafe_allow_html=True)

def safe_int(x, default=0):
    try:
        return int(float(x))
    except Exception:
        return default

def safe_float(x, default=None):
    try:
        if x is None:
            return default
        s = str(x).strip()
        if s == "" or s == "—" or s.lower() == "nan":
            return default
        return float(s)
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

def payload_box(d: dict):
    txt = "{\n"
    for k, v in d.items():
        if isinstance(v, str):
            txt += f'  "{k}": "{v}"\n'
        else:
            txt += f'  "{k}": {v}\n'
    txt += "}"
    st.markdown(f"<div class='payload'>{txt}</div>", unsafe_allow_html=True)

def style_plot(fig, x_title: str, y_title: str, y_range=None):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="rgba(232,238,252,0.95)"),
        title_font=dict(color="rgba(232,238,252,0.95)"),
        xaxis=dict(
            title=x_title,
            color="rgba(232,238,252,0.95)",
            gridcolor="rgba(34,50,76,0.6)",
            zerolinecolor="rgba(34,50,76,0.6)"
        ),
        yaxis=dict(
            title=y_title,
            color="rgba(232,238,252,0.95)",
            gridcolor="rgba(34,50,76,0.6)",
            zerolinecolor="rgba(34,50,76,0.6)",
            range=y_range
        ),
        margin=dict(l=50, r=20, t=55, b=40),
        showlegend=False
    )
    fig.update_traces(line_width=2)

def gauge(title, value, vmin, vmax, unit="", seuil_rouge=None, bar_color="rgba(96,165,250,0.85)"):
    val = safe_float(value, default=None)
    display_val = 0.0 if val is None else float(val)

    steps = None
    if seuil_rouge is not None:
        steps = [
            {"range": [vmin, seuil_rouge], "color": "rgba(255,255,255,0.18)"},
            {"range": [seuil_rouge, vmax], "color": "rgba(239,68,68,0.9)"},
        ]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=display_val,
        title={"text": title, "font": {"size": 16, "color": "rgba(232,238,252,0.95)"}},
        number={
            "suffix": f" {unit}" if unit else "",
            "font": {"size": 44, "color": "rgba(232,238,252,0.95)"},
            "valueformat": ".0f" if val is not None else ""
        },
        gauge={
            "axis": {"range": [vmin, vmax], "tickcolor": "rgba(183,198,230,0.9)"},
            "bar": {"color": bar_color},
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

    if val is None:
        fig.update_traces(number={"prefix": "—", "suffix": ""})

    st.plotly_chart(fig, use_container_width=True)

# On choisit la page dans la sidebar
page = st.sidebar.selectbox("Choisir une page", ["Vue générale", "Commandes Salle technique", "Commandes Salle", "Historique"])

# On règle le refresh automatique
refresh_seconds = st.sidebar.slider("Temps de rafraîchissement (secondes)", 2, 15, 5, 1)

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

# On récupère les liens API depuis les secrets Streamlit
API_LATEST = st.secrets.get("API_LATEST", "").strip()
API_HISTORY = st.secrets.get("API_HISTORY", "").strip()
API_CMD = st.secrets.get("API_CMD", "").strip()
API_SALLE_CMD = st.secrets.get("API_SALLE_CMD", "").strip()

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

# On récupère la dernière mesure et l'historique si dispo
try:
    last = get_latest()
except Exception as e:
    st.error(f"Erreur API (latest) : {e}")
    st.stop()

df = get_history()

# On nettoie les dates de l'historique pour avoir la bonne timezone
if not df.empty and "date" in df.columns:
    df["date_local"] = pd.to_datetime(df["date"], errors="coerce")
    if df["date_local"].dt.tz is None:
        df["date_local"] = df["date_local"].dt.tz_localize("Europe/Brussels", ambiguous="infer", nonexistent="shift_forward")
    else:
        df["date_local"] = df["date_local"].dt.tz_convert("Europe/Brussels")

# On lit les dernières valeurs
temperature_lt = last.get("temperature_lt", "—")
humidite_lt = last.get("humidite_lt", "—")
gaz_value = last.get("gaz", "—")
motor_speed = last.get("motor_speed", "—")
alarme_value = last.get("alarme", "—")
date_value = last.get("date", None)

alarme_int = safe_int(alarme_value, 0)
alarme_txt = "ACTIF" if alarme_int == 1 else "INACTIF"

# On calcule le mode affiché (mode texte ou mode_confort)
mode_txt = "—"
if "mode" in last and str(last.get("mode", "")).strip() != "":
    mode_txt = str(last.get("mode")).upper()
elif "mode_confort" in last:
    mode_txt = "CONFORT" if safe_int(last.get("mode_confort", 0), 0) == 1 else "ECO"

st.markdown(f"<div class='note'>Dernière mesure : <b>{fmt_date(date_value)}</b></div>", unsafe_allow_html=True)

if page == "Vue générale":
    st.markdown("<div class='section-title'>Vue générale</div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Température", f"{temperature_lt} °C")
    with c2:
        kpi_card("Humidité", f"{humidite_lt} %")
    with c3:
        kpi_card("Mode", f"{mode_txt}")
    with c4:
        kpi_card("Alarme", f"{alarme_txt}")

    st.markdown("<div class='section-title'>Jauges</div>", unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    with g1:
        gauge("Gaz MQ-2", gaz_value, 0, 4095, unit="ADC", seuil_rouge=3000, bar_color="rgba(245,158,11,0.80)")
    with g2:
        gauge("Vitesse moteur", motor_speed, 0, 255, unit="PWM", seuil_rouge=200, bar_color="rgba(34,197,94,0.75)")

    st.markdown("<div class='section-title'>Graphes (température / humidité)</div>", unsafe_allow_html=True)

    if df.empty or "date_local" not in df.columns:
        st.info("Pour les graphes, configure API_HISTORY (Secrets Streamlit).")
    else:
        p1, p2 = st.columns(2)
        with p1:
            if "temperature_lt" in df.columns:
                fig = px.line(df, x="date_local", y="temperature_lt", title="Température")
                style_plot(fig, "Date / heure", "Température (°C)", y_range=[0, 40])
                st.plotly_chart(fig, use_container_width=True)

        with p2:
            if "humidite_lt" in df.columns:
                fig = px.line(df, x="date_local", y="humidite_lt", title="Humidité")
                style_plot(fig, "Date / heure", "Humidité (%)", y_range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)

elif page == "Commandes":
    st.markdown("<div class='section-title'>Commandes</div>", unsafe_allow_html=True)

    if not API_CMD:
        st.error("Secret manquant: API_CMD (POST commande vers Node-RED).")
        st.stop()

    # On gère le moteur et le mute alarme
    vitesse = st.slider("Vitesse moteur (0 à 255)", 0, 255, 120)
    mute = st.checkbox("Couper le buzzer (mute alarme)", value=False)

    payload_send = {"target_speed": int(vitesse), "mute": 1 if mute else 0}
    payload_stop = {"target_speed": 0, "mute": 1 if mute else 0}

    st.markdown("<div class='section-title'>Payload envoyé</div>", unsafe_allow_html=True)
    payload_box(payload_send)

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Envoyer la commande", use_container_width=True):
            try:
                r = requests.post(API_CMD, json=payload_send, timeout=10)
                r.raise_for_status()
                st.success("Commande envoyée !")
            except Exception as e:
                st.error(f"Erreur envoi commande : {e}")

    with b2:
        if st.button("Arrêter le moteur", use_container_width=True):
            try:
                r = requests.post(API_CMD, json=payload_stop, timeout=10)
                r.raise_for_status()
                st.warning("Moteur arrêté !")
            except Exception as e:
                st.error(f"Erreur arrêt moteur : {e}")

    st.markdown("<div class='section-title'>Aperçu état actuel</div>", unsafe_allow_html=True)
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        kpi_card("Température", f"{temperature_lt} °C")
    with a2:
        kpi_card("Humidité", f"{humidite_lt} %")
    with a3:
        kpi_card("Gaz", f"{gaz_value} ADC")
    with a4:
        kpi_card("Vitesse", f"{motor_speed} /255")

elif page == "Historique":
    st.markdown("<div class='section-title'>Historique - mesures_hvac</div>", unsafe_allow_html=True)

    if df.empty:
        st.error("Aucun historique (API_HISTORY pas configurée ou pas de données).")
    else:
        st.markdown("<div class='section-title'>Graphes</div>", unsafe_allow_html=True)

        if "date_local" in df.columns:
            if "temperature_lt" in df.columns:
                fig = px.line(df, x="date_local", y="temperature_lt", title="Température dans le temps")
                style_plot(fig, "Date / heure", "Température (°C)", y_range=[0, 40])
                st.plotly_chart(fig, use_container_width=True)

            if "humidite_lt" in df.columns:
                fig = px.line(df, x="date_local", y="humidite_lt", title="Humidité dans le temps")
                style_plot(fig, "Date / heure", "Humidité (%)", y_range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)

            if "gaz" in df.columns:
                fig = px.line(df, x="date_local", y="gaz", title="Gaz MQ-2 dans le temps")
                style_plot(fig, "Date / heure", "Gaz (ADC)", y_range=[0, 4095])
                st.plotly_chart(fig, use_container_width=True)

            if "motor_speed" in df.columns:
                fig = px.line(df, x="date_local", y="motor_speed", title="Vitesse moteur dans le temps")
                style_plot(fig, "Date / heure", "Vitesse (0–255)", y_range=[0, 255])
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("<div class='section-title'>Tableau</div>", unsafe_allow_html=True)

        df_show = df.copy()
        if "mode" in df_show.columns:
            df_show["mode"] = df_show["mode"].str.upper()

        if "date_local" in df_show.columns:
            ascending = True if ordre_tableau == "Plus ancien → plus récent" else False
            df_show = df_show.sort_values(by="date_local", ascending=ascending)
            df_show["date_local"] = df_show["date_local"].dt.strftime("%d/%m/%Y %H:%M:%S")

        cols = ["id", "date_local", "mode", "temperature_lt", "humidite_lt", "gaz", "motor_speed", "alarme"]
        cols = [c for c in cols if c in df_show.columns]
        st.dataframe(df_show[cols], use_container_width=True)

elif page == "Gestion Salle":
    st.markdown("<div class='section-title'>Gestion de commande de la Salle</div>", unsafe_allow_html=True)

    if not API_SALLE_CMD:
        st.error("Secret manquant: API_SALLE_CMD (POST commande Salle vers Node-RED).")
        st.stop()

    # Petite fonction pour récupérer une valeur actuelle ou mettre un défaut
    def get_val(d, key, default):
        try:
            v = d.get(key, default)
            if v in ["", "—", None]:
                return default
            return v
        except Exception:
            return default

    lamp_mode_current = str(get_val(last, "lampMode", "auto")).lower()
    brightness_current = safe_int(get_val(last, "brightness", 30), 30)

    tempT1_cur = float(get_val(last, "tempT1", 18.0))
    tempT2_cur = float(get_val(last, "tempT2", 24.0))
    tempT3_cur = float(get_val(last, "tempT3", 28.0))

    humH1_cur = float(get_val(last, "humH1", 40.0))
    humH2_cur = float(get_val(last, "humH2", 70.0))

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='section-title'>Lampe et luminosité</div>", unsafe_allow_html=True)

        lamp_choice = st.selectbox(
            "Mode lampe",
            ["Auto", "ON", "OFF"],
            index=0 if lamp_mode_current == "auto" else 1 if lamp_mode_current == "on" else 2
        )

        brightness = st.slider("Luminosité des bandeaux (%)", 0, 100, brightness_current, 1)

        # Preview simple: cercle blanc avec intensité selon le slider
        alpha = max(0.10, brightness / 100)
        size = 110
        glow = 6 + int(brightness * 0.4)

        st.markdown(
            f"""
            <div class="kpi-card" style="min-height:180px;">
                <div class="kpi-title">Aperçu luminosité</div>
                <div style="
                    width:{size}px;
                    height:{size}px;
                    border-radius:50%;
                    background: rgba(255,255,255,{alpha});
                    box-shadow: 0 0 {glow}px rgba(255,255,255,{alpha});
                    border: 1px solid rgba(34,50,76,0.8);
                "></div>
                <div style="margin-top:10px;font-weight:700;">
                    {brightness} %
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("<div class='section-title'>Seuils de fonctionnement</div>", unsafe_allow_html=True)

        st.markdown("<div class='note'>Température (T1 &lt; T2 &lt; T3)</div>", unsafe_allow_html=True)
        t1 = st.number_input("T1 (°C)", 0.0, 60.0, tempT1_cur, 0.5)
        t2 = st.number_input("T2 (°C)", 0.0, 60.0, tempT2_cur, 0.5)
        t3 = st.number_input("T3 (°C)", 0.0, 60.0, tempT3_cur, 0.5)

        st.markdown("<div class='note'>Humidité (H1 &lt; H2)</div>", unsafe_allow_html=True)
        h1 = st.number_input("H1 (%)", 0.0, 100.0, humH1_cur, 1.0)
        h2 = st.number_input("H2 (%)", 0.0, 100.0, humH2_cur, 1.0)

    lamp_mode_send = "auto"
    if lamp_choice == "ON":
        lamp_mode_send = "on"
    elif lamp_choice == "OFF":
        lamp_mode_send = "off"

    payload_salle = {
        "lampMode": lamp_mode_send,
        "brightness": int(brightness),
        "tempT1": float(t1),
        "tempT2": float(t2),
        "tempT3": float(t3),
        "humH1": float(h1),
        "humH2": float(h2)
    }

    st.markdown("<div class='section-title'>Payload envoyé</div>", unsafe_allow_html=True)
    payload_box(payload_salle)

    erreur = False
    if not (t1 < t2 < t3):
        st.error("Les seuils température doivent respecter T1 < T2 < T3")
        erreur = True
    if not (h1 < h2):
        st.error("Les seuils humidité doivent respecter H1 < H2")
        erreur = True

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Envoyer vers la Salle", use_container_width=True, disabled=erreur):
            try:
                r = requests.post(API_SALLE_CMD, json=payload_salle, timeout=10)
                r.raise_for_status()
                st.success("Commande envoyée à la Salle")
            except Exception as e:
                st.error(f"Erreur d’envoi : {e}")

    with b2:
        if st.button("Réglages par défaut", use_container_width=True):
            payload_default = {
                "lampMode": "auto",
                "brightness": 30,
                "tempT1": 18.0,
                "tempT2": 24.0,
                "tempT3": 28.0,
                "humH1": 40.0,
                "humH2": 70.0
            }
            try:
                r = requests.post(API_SALLE_CMD, json=payload_default, timeout=10)
                r.raise_for_status()
                st.warning("Valeurs par défaut envoyées")
            except Exception as e:
                st.error(f"Erreur reset : {e}")

st.markdown(
    "<hr><p style='text-align:center; font-size:12px; color:rgba(183,198,230,0.9);'>© 2025 - Binôme A_02 : LFRAH Abdelrahman [HE304830] – IQBAL Adil [HE305031]</p>",
    unsafe_allow_html=True
)
