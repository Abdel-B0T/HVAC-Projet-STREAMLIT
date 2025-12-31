import streamlit as st
import pandas as pd
import plotly.express as px
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
            border-radius: 5px;
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

# Menu à gauche
page = st.sidebar.selectbox(
    "Choisir une page",
    ["Vue générale", "Commandes", "Historique"]
)

# -----------------------------
# API Node-RED (obligatoire)
# -----------------------------
API_LATEST = st.secrets.get("API_LATEST", "").strip()
API_HISTORY = st.secrets.get("API_HISTORY", "").strip()  # optionnel

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

# Option pour rafraîchir (simple)
st.sidebar.write("Actualisation")
refresh = st.sidebar.button("Rafraîchir les données")
if refresh:
    st.cache_data.clear()
    st.rerun()

# -----------------------------
# Page 1 : Vue générale
# -----------------------------
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

    # Cartes
    col1, col2, col3 = st.columns(3)

    with col1:
        card("Température (°C)", f"{temperature_lt}", "#2E86C1")
        card("Humidité (%)", f"{humidite_lt}", "#239B56")

    with col2:
        # Couleur gaz (tu peux ajuster le seuil)
        try:
            gaz_int = int(float(gaz_value))
        except Exception:
            gaz_int = None

        couleur_gaz = "#C0392B" if (gaz_int is not None and gaz_int >= 3000) else "#D68910"
        card("Gaz MQ2 (analog)", f"{gaz_value}", couleur_gaz)

        # Alarme
        try:
            alarme_int = int(float(alarme))
        except Exception:
            alarme_int = 0

        alarme_txt = "ACTIF" if alarme_int == 1 else "INACTIF"
        couleur_alarme = "#C0392B" if alarme_txt == "ACTIF" else "#5D6D7E"
        card("Alarme", alarme_txt, couleur_alarme)

    with col3:
        card("Vitesse moteur (0-255)", f"{motor_speed}", "#5D6D7E")

    # Graphiques si API_HISTORY est fourni
    df = get_history()
    if not df.empty and "date" in df.columns:
        g1, g2 = st.columns(2)

        with g1:
            if "temperature_lt" in df.columns:
                fig_t = px.line(df, x="date", y="temperature_lt", title="Température")
                st.plotly_chart(fig_t, use_container_width=True)

        with g2:
            if "humidite_lt" in df.columns:
                fig_h = px.line(df, x="date", y="humidite_lt", title="Humidité")
                st.plotly_chart(fig_h, use_container_width=True)
    else:
        st.info("Pour afficher les graphes, ajoute une API d'historique (API_HISTORY) côté Node-RED.")

# -----------------------------
# Page 2 : Commandes (UI seulement pour l'instant)
# -----------------------------
elif page == "Commandes":
    st.subheader("Commandes - Salle technique")

    st.info("Ici tu peux mettre les commandes plus tard. Pour l’instant on affiche juste l’interface.")

    vitesse = st.slider("Vitesse du moteur (0 à 255)", 0, 255, 120)
    mute = st.checkbox("Mute alarme", value=False)

    st.write("Valeurs choisies :")
    st.write({"target_speed": vitesse, "mute": 1 if mute else 0})

    st.warning("Étape suivante : on enverra ces valeurs à Node-RED (POST) -> MQTT -> ESP32.")

# -----------------------------
# Page 3 : Historique
# -----------------------------
elif page == "Historique":
    st.subheader("Historique - mesures_hvac")

    df = get_history()
    if df.empty:
        st.error("Aucun historique (API_HISTORY pas configurée ou pas de données).")
    else:
        st.dataframe(df, use_container_width=True)

        if "date" in df.columns and "gaz" in df.columns:
            fig_gaz = px.line(df, x="date", y="gaz", title="Évolution Gaz MQ2")
            st.plotly_chart(fig_gaz, use_container_width=True)

        if "date" in df.columns and "motor_speed" in df.columns:
            fig_motor = px.line(df, x="date", y="motor_speed", title="Évolution vitesse moteur")
            st.plotly_chart(fig_motor, use_container_width=True)

        if "date" in df.columns and "alarme" in df.columns:
            fig_al = px.step(df, x="date", y="alarme", title="Historique alarme (0/1)")
            st.plotly_chart(fig_al, use_container_width=True)

# Pied de page
st.markdown(
    "<hr><p style='text-align:center; font-size:12px; color:#888;'>© 2025 - Binôme A_02 : LFRAH Abdelrahman [HE304830] – IQBAL Adil [HE305031]</p>",
    unsafe_allow_html=True
)
