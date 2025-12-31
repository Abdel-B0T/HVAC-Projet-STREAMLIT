import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
from datetime import datetime

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

# Paramètres MariaDB (mets les tiens)
DB_HOST = "127.0.0.1"
DB_USER = "ec"
DB_PASS = "ec"
DB_NAME = "IOT_DB"

# Je me connecte à MariaDB et je lis la table
def get_mariadb_data(limit=200):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        cursor = conn.cursor(dictionary=True)

        cursor.execute(f"SELECT * FROM mesures_hvac ORDER BY id DESC LIMIT {int(limit)}")
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)

        # Je remets l'ordre chronologique pour les graphes
        df = df.sort_values("id")

        return df

    except Exception as e:
        st.sidebar.error(f"Erreur MariaDB : {e}")
        return pd.DataFrame()

# Je récupère les données une fois
df = get_mariadb_data(limit=300)

# Option pour rafraîchir (simple)
st.sidebar.write("Actualisation")
refresh = st.sidebar.button("Rafraîchir les données")

if refresh:
    st.rerun()

# Page 1 : Vue générale
if page == "Vue générale":
    st.subheader("Vue générale - Salle technique")

    if df.empty:
        st.error("Aucune donnée dans mesures_hvac. Vérifie que Node-RED insère bien dans la table.")
    else:
        # Je prends la dernière ligne (la plus récente)
        last = df.iloc[-1]

        temperature_lt = last.get("temperature_lt", None)
        humidite_lt    = last.get("humidite_lt", None)
        gaz_value      = last.get("gaz", None)
        motor_speed    = last.get("motor_speed", None)
        alarme         = last.get("alarme", None)
        date_mesure    = last.get("date", None)

        # Affichage date si elle existe
        if date_mesure is not None:
            st.caption(f"Dernière mesure : {date_mesure}")

        # Cartes
        col1, col2, col3 = st.columns(3)

        with col1:
            card("Température (°C)", f"{temperature_lt}", "#2E86C1")
            card("Humidité (%)", f"{humidite_lt}", "#239B56")

        with col2:
            # Couleur gaz
            couleur_gaz = "#C0392B" if (gaz_value is not None and int(gaz_value) >= 3000) else "#D68910"
            card("Gaz MQ2 (analog)", f"{gaz_value}", couleur_gaz)

            # Alarme
            alarme_txt = "ACTIF" if (alarme is not None and int(alarme) == 1) else "INACTIF"
            couleur_alarme = "#C0392B" if alarme_txt == "ACTIF" else "#5D6D7E"
            card("Alarme", alarme_txt, couleur_alarme)

        with col3:
            card("Vitesse moteur (0-255)", f"{motor_speed}", "#5D6D7E")

        # Petit graphique rapide température/hum
        if "date" in df.columns:
            g1, g2 = st.columns(2)

            with g1:
                if "temperature_lt" in df.columns:
                    fig_t = px.line(df, x="date", y="temperature_lt", title="Température")
                    st.plotly_chart(fig_t, use_container_width=True)

            with g2:
                if "humidite_lt" in df.columns:
                    fig_h = px.line(df, x="date", y="humidite_lt", title="Humidité")
                    st.plotly_chart(fig_h, use_container_width=True)

# Page 2 : Commandes (on ne fait pas MQTT ici, juste une page UI)
elif page == "Commandes":
    st.subheader("Commandes - Salle technique")

    st.info("Ici tu peux mettre des commandes plus tard. Pour l’instant on affiche juste l’interface.")

    vitesse = st.slider("Vitesse du moteur (0 à 255)", 0, 255, 120)
    mute = st.checkbox("Mute alarme", value=False)

    st.write("Valeurs choisies :")
    st.write({"target_speed": vitesse, "mute": 1 if mute else 0})

    st.warning("Si tu veux que Streamlit commande l’ESP32, je te donne le code MQTT direct dans Streamlit.")

# Page 3 : Historique
elif page == "Historique":
    st.subheader("Historique - mesures_hvac")

    if df.empty:
        st.error("Aucune donnée trouvée.")
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
