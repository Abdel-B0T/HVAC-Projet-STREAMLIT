import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px

import json
import time
import paho.mqtt.client as mqtt

# Configuration générale de la page Streamlit
st.set_page_config(
    page_title="HVAC - Dashboard A_02",
    layout="wide"
)

# Style du bandeau en haut
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

# Affichage du bandeau
st.markdown(
    "<div class='header'><h1>Supervision HVAC – Projet Final</h1></div>",
    unsafe_allow_html=True
)

# Fonction pour afficher une carte d'information
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

# Configuration MQTT (même broker que l’ESP32)
MQTT_BROKER = "20.251.206.33"
MQTT_PORT = 1883

TOPIC_LT_DATA = "hvac/a02/localtech/data"
TOPIC_LT_CMD  = "hvac/a02/localtech/cmd"
TOPIC_SALLE_DATA = "hvac/salle/data"

# Variables pour stocker la dernière donnée reçue
latest_lt = {}
latest_salle = {}

# Callback appelé à chaque message MQTT reçu
def on_message(client, userdata, msg):
    global latest_lt, latest_salle
    try:
        data = json.loads(msg.payload.decode("utf-8"))

        if msg.topic == TOPIC_LT_DATA:
            latest_lt = data
        elif msg.topic == TOPIC_SALLE_DATA:
            latest_salle = data
    except:
        pass

# Démarrage du client MQTT (une seule fois)
@st.cache_resource
def start_mqtt():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    client.subscribe(TOPIC_LT_DATA)
    client.subscribe(TOPIC_SALLE_DATA)

    client.loop_start()
    return client

mqtt_client = start_mqtt()

# Envoi d’une commande vers l’ESP32
def send_cmd_localtech(target_speed, mute):
    cmd = {
        "target_speed": int(target_speed),
        "mute": 1 if mute else 0
    }
    mqtt_client.publish(TOPIC_LT_CMD, json.dumps(cmd))

# Lecture des données historiques dans MariaDB
def get_mariadb_data(limit=200):
    try:
        conn = mysql.connector.connect(
            host="20.19.176.195",
            user="ec",
            password="ec",
            database="IOT_DB",
            port=3306
        )

        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM mesures_hvac ORDER BY id DESC LIMIT {limit}")
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return pd.DataFrame(rows)

    except Exception as e:
        st.sidebar.error(f"Erreur MariaDB : {e}")
        return None

# Menu latéral
page = st.sidebar.selectbox(
    "Choisir une page",
    ["Vue générale", "Commandes", "Historique"]
)

# Page Vue générale
if page == "Vue générale":
    st.subheader("Vue générale (données en direct ESP32)")

    temperature_lt = latest_lt.get("temp", "--")
    humidite_lt = latest_lt.get("hum", "--")
    gaz_value = latest_lt.get("gas_a", "--")
    motor_speed = latest_lt.get("motor_speed", "--")

    alarme_val = latest_lt.get("alarm", 0)
    alarme = "ACTIF" if str(alarme_val) == "1" else "INACTIF"

    mode_val = latest_lt.get("mode_confort", 0)
    mode_confort = "Actif" if str(mode_val) == "1" else "Inactif"

    temp_salle = latest_salle.get("temp", "--")
    hum_salle = latest_salle.get("hum", "--")
    mode_salle = latest_salle.get("mode", "--")

    col1, col2, col3 = st.columns(3)

    with col1:
        card("Température Local Technique", f"{temperature_lt} °C", "#2E86C1")
        card("Humidité Local Technique", f"{humidite_lt} %", "#239B56")

    with col2:
        try:
            gv = float(gaz_value)
        except:
            gv = 0

        couleur_gaz = "#C0392B" if gv > 800 else "#D68910"
        card("Gaz MQ2", gaz_value, couleur_gaz)
        card("Alarme", alarme, "#C0392B" if alarme == "ACTIF" else "#5D6D7E")

    with col3:
        card("Vitesse moteur", motor_speed, "#5D6D7E")
        card("Mode confort", mode_confort, "#34495E")

    st.markdown("### Données Salle")

    col4, col5, col6 = st.columns(3)
    with col4:
        card("Température Salle", f"{temp_salle} °C", "#1F618D")
    with col5:
        card("Humidité Salle", f"{hum_salle} %", "#1E8449")
    with col6:
        card("Mode Salle", mode_salle, "#566573")

    time.sleep(2)
    st.rerun()

# Page Commandes
elif page == "Commandes":
    st.subheader("Commandes vers l’ESP32 – Salle technique")

    vitesse = st.slider("Vitesse du moteur (0 à 255)", 0, 255, 120)
    mute = st.checkbox("Mute alarme")

    if st.button("Envoyer la commande"):
        send_cmd_localtech(vitesse, mute)
        st.success("Commande envoyée en MQTT")

# Page Historique
elif page == "Historique":
    st.subheader("Historique des mesures (MariaDB)")

    df = get_mariadb_data()

    if df is None or df.empty:
        st.error("Aucune donnée trouvée")
    else:
        st.dataframe(df)

        if "temperature_lt" in df.columns and "date" in df.columns:
            fig = px.line(df, x="date", y="temperature_lt", title="Température Local Technique")
            st.plotly_chart(fig, use_container_width=True)

        if "gaz" in df.columns and "date" in df.columns:
            fig = px.line(df, x="date", y="gaz", title="Gaz MQ2")
            st.plotly_chart(fig, use_container_width=True)

        if "alarme" in df.columns and "date" in df.columns:
            df["alarme_num"] = df["alarme"].apply(lambda x: 1 if str(x) == "1" else 0)
            fig = px.step(df, x="date", y="alarme_num", title="Alarme")
            st.plotly_chart(fig, use_container_width=True)

# Pied de page
st.markdown(
    "<hr><p style='text-align:center; font-size:12px; color:#888;'>© 2025 - Binôme A_02 : LFRAH Abdelrahman [HE304830] – IQBAL Adil [HE305031]</p>",
    unsafe_allow_html=True
)
