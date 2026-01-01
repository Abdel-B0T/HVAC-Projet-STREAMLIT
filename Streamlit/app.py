import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# Configuration générale de la page
st.set_page_config(
    page_title="HVAC - Dashboard A_02 (Salle Technique)",
    layout="wide"
)

# Style CSS pour le bandeau du haut
st.markdown("""
    <style>
        .header {
            background-color: #1F1F1F;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .header h1 {
            color: white;
            text-align: center;
            font-size: 26px;
            margin: 0;
        }
    </style>
""", unsafe_allow_html=True)

# Bandeau en haut
st.markdown(
    "<div class='header'><h1>Supervision HVAC – Salle Technique</h1></div>",
    unsafe_allow_html=True
)

# Petite carte visuelle pour afficher une valeur
def card(title, value, color):
    st.markdown(
        f"""
        <div style='background-color:{color}; padding: 15px; border-radius: 10px; text-align:center; margin-bottom:10px;'>
            <h4 style='color:white; margin-bottom:5px;'>{title}</h4>
            <h2 style='color:white; margin:0;'>{value}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

# Gauge Plotly (gaz + vitesse moteur)
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
        title={"text": title},
        number={"suffix": f" {suffix}"},
        gauge={
            "axis": {"range": [vmin, vmax]},
            "steps": steps
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

# Menu à gauche
page = st.sidebar.selectbox(
    "Choisir une page",
    ["Vue générale", "Commandes", "Historique"]
)

# Secrets Streamlit Cloud
API_LATEST = st.secrets.get("API_LATEST", "").strip()
API_HISTORY = st.secrets.get("API_HISTORY", "").strip()  # optionnel mais recommandé

if not API_LATEST:
    st.error("Secret manquant: API_LATEST. Va dans Streamlit Cloud > Settings > Secrets.")
    st.stop()

@st.cache_data(ttl=2)
def get_latest():
    r = requests.get(API_LATEST, timeout=5)
    r.raise_for_status()
    return r.json()

@st.cache_data(ttl=5)
def get_history():
    if not API_HISTORY:
        return pd.DataFrame()
    r = requests.get(API_HISTORY, timeout=8)
    r.raise_for_status()
    data = r.json()
    return pd.DataFrame(data)

# Actualisation
st.sidebar.write("Actualisation")
refresh = st.sidebar.button("Rafraîchir les données")
if refresh:
    st.cache_data.clear()
    st.rerun()

# Page 1 : Vue générale
if page == "Vue générale":
    st.subheader("Vue générale - Salle technique")

    try:
        last = get_latest()
    except Exception as e:
        st.error(f"Erreur API (latest) : {e}")
        st.stop()

    if not last:
        st.error("Aucune donnée reçue depuis l'API.")
        st.stop()

    temperature_lt = last.get("temperature_lt", "—")
    humidite_lt    = last.get("humidite_lt", "—")
    gaz_value      = last.get("gaz", "—")
    motor_speed    = last.get("motor_speed", "—")
    alarme         = last.get("alarme", "—")
    date_mesure    = last.get("date", "—")

    st.caption(f"Dernière mesure : {date_mesure}")

    # Cartes rapides en haut
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        card("Température (°C)", f"{temperature_lt}", "#2E86C1")

    with col2:
        card("Humidité (%)", f"{humidite_lt}", "#239B56")

    with col3:
        try:
            alarme_int = int(float(alarme))
        except Exception:
            alarme_int = 0
        alarme_txt = "ACTIF" if alarme_int == 1 else "INACTIF"
        couleur_alarme = "#C0392B" if alarme_txt == "ACTIF" else "#5D6D7E"
        card("Alarme", alarme_txt, couleur_alarme)

    with col4:
        card("Date", f"{date_mesure}", "#5D6D7E")

    st.markdown("### Graphes (Température / Humidité)")

    df = get_history()
    if not df.empty and "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        g1, g2 = st.columns(2)
        with g1:
            if "temperature_lt" in df.columns:
                fig_t = px.line(df, x="date", y="temperature_lt", title="Température")
                st.plotly_chart(fig_t, use_container_width=True)
            else:
                st.info("Pas de colonne temperature_lt dans l'historique.")

        with g2:
            if "humidite_lt" in df.columns:
                fig_h = px.line(df, x="date", y="humidite_lt", title="Humidité")
                st.plotly_chart(fig_h, use_container_width=True)
            else:
                st.info("Pas de colonne humidite_lt dans l'historique.")
    else:
        st.info("Pour les graphes, configure API_HISTORY (voir Secrets Streamlit).")

    st.markdown("### Gauges (Gaz / Vitesse moteur)")
    c1, c2 = st.columns(2)

    with c1:
        # Gaz MQ2 typiquement 0..4095 (ADC)
        gauge("Gaz (MQ2)", gaz_value, 0, 4095, suffix="ADC", seuil_rouge=3000)

    with c2:
        # Vitesse moteur 0..255
        gauge("Vitesse moteur", motor_speed, 0, 255, suffix="/255", seuil_rouge=200)

# Page 2 : Commandes (UI seulement)
elif page == "Commandes":
    st.subheader("Commandes - Salle technique")

    st.info("Interface prête. Étape suivante : envoyer les commandes à Node-RED (POST) puis MQTT vers l'ESP32.")

    vitesse = st.slider("Vitesse du moteur (0 à 255)", 0, 255, 120)
    mute = st.checkbox("Mute alarme", value=False)

    st.write("Valeurs choisies :")
    st.write({"target_speed": vitesse, "mute": 1 if mute else 0})

# Page 3 : Historique
elif page == "Historique":
    st.subheader("Historique - mesures_hvac")

    df = get_history()
    if df.empty:
        st.error("Aucun historique (API_HISTORY pas configurée ou pas de données).")
    else:
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        st.dataframe(df, use_container_width=True)

        if "date" in df.columns and "gaz" in df.columns:
            fig_gaz = px.line(df, x="date", y="gaz", title="Évolution Gaz MQ2")
            st.plotly_chart(fig_gaz, use_container_width=True)

        if "date" in df.columns and "motor_speed" in df.columns:
            fig_motor = px.line(df, x="date", y="motor_speed", title="Évolution vitesse moteur")
            st.plotly_chart(fig_motor, use_container_width=True)

        # Fix: pas de px.step sur certaines versions -> line + line_shape="hv"
        if "date" in df.columns and "alarme" in df.columns:
            fig_al = px.line(df, x="date", y="alarme", title="Historique alarme (0/1)")
            fig_al.update_traces(line_shape="hv")
            st.plotly_chart(fig_al, use_container_width=True)

# Pied de page
st.markdown(
    "<hr><p style='text-align:center; font-size:12px; color:#888;'>© 2025 - Binôme A_02 : LFRAH Abdelrahman [HE304830] – IQBAL Adil [HE305031]</p>",
    unsafe_allow_html=True
)
