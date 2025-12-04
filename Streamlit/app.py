import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px

# Ici je mets le titre et le mode d'affichage
st.set_page_config(
    page_title="HVAC - Dashboard A_02",
    layout="wide"
)

# Style CSS pour faire un bandeau propre en haut de la page
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

# J'affiche le bandeau en haut du dashboard
st.markdown(
    "<div class='header'><h1>Supervision HVAC – Projet Final</h1></div>",
    unsafe_allow_html=True
)

# Petite fonction qui crée une carte visuelle (comme une tuile d'information)
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

# Menu sur la gauche pour naviguer entre les différentes pages du dashboard
page = st.sidebar.selectbox(
    "Choisir une page",
    ["Vue générale", "Commandes", "Historique"]
)

# Fonction qui va lire la base MariaDB
# Je fais la connexion, j'exécute une requête et je renvoie un DataFrame
def get_mariadb_data():
    """
    Je récupère les dernières mesures dans MariaDB.
    Si la connexion ne marche pas, je renvoie None.
    """
    try:
        conn = mysql.connector.connect(
            host="20.19.176.195",
            user="ec",
            password="ec",
            database="IOT_DB"
        )
        cursor = conn.cursor(dictionary=True)

        # Je prends les 50 dernières mesures
        cursor.execute("SELECT * FROM mesures_hvac ORDER BY id DESC LIMIT 50")
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        # Je transforme les résultats en DataFrame
        return pd.DataFrame(rows)

    except Exception as e:
        # En cas de problème, je l'affiche dans la barre de gauche
        st.sidebar.error(f"Erreur MariaDB : {e}")
        return None

# Page 1 du dashboard : vue générale
if page == "Vue générale":
    st.subheader("Vue générale de la salle technique")

    # Pour l'instant je mets des valeurs simulées
    # Plus tard elles seront remplacées par des vraies valeurs venant de MariaDB ou MQTT
    temperature_lt = 26.0
    humidite_lt = 40
    gaz_value = 740
    motor_speed = 180
    mode_confort = "Actif"
    alarme = "INACTIF"

    # Je crée 3 colonnes pour organiser les cartes
    col1, col2, col3 = st.columns(3)

    # Colonne 1
    with col1:
        card("Température salle technique", f"{temperature_lt} °C", "#2E86C1")
        card("Humidité salle technique", f"{humidite_lt} %", "#239B56")

    # Colonne 2
    with col2:
        couleur_gaz = "#C0392B" if gaz_value > 800 else "#D68910"
        card("Niveau Gaz MQ2", gaz_value, couleur_gaz)

        couleur_alarme = "#C0392B" if alarme == "ACTIF" else "#5D6D7E"
        card("Alarme", alarme, couleur_alarme)

    # Colonne 3
    with col3:
        card("Vitesse moteur", motor_speed, "#5D6D7E")
        card("Mode confort", mode_confort, "#34495E")

    st.caption("Remarque : valeurs simulées pour le moment. Les données réelles seront ajoutées plus tard.")

# Page 2 : commandes vers l’ESP32
elif page == "Commandes":
    st.subheader("Commandes vers l'ESP32 - Salle technique")

    st.markdown("Cette page servira à envoyer les commandes MQTT vers la salle technique.")

    # Slider pour choisir la vitesse du moteur
    vitesse = st.slider("Vitesse du moteur (0 à 255)", 0, 255, 120)

    # Boutons de commande
    bouton_confort = st.button("Activer le mode confort")
    bouton_reset = st.button("Acquitter l'alarme")

    # Pour l’instant ce sont juste des simulations
    if bouton_confort:
        st.success("Commande simulée : mode confort activé.")

    if bouton_reset:
        st.warning("Commande simulée : reset alarme envoyé.")

    st.caption("Les commandes MQTT seront ajoutées plus tard.")

# Page 3 : historique des valeurs venant de MariaDB
elif page == "Historique":
    st.subheader("Historique des mesures salle technique (MariaDB)")

    # Je demande les données MariaDB
    df = get_mariadb_data()

    if df is None or df.empty:
        st.error("Aucune donnée trouvée. Vérifier la connexion MariaDB et la table mesures_hvac.")
    else:
        # J'affiche les données sous forme de tableau
        st.dataframe(df)

        # Graphique température si la colonne existe
        if "temperature_lt" in df.columns and "date" in df.columns:
            fig_temp = px.line(
                df,
                x="date",
                y="temperature_lt",
                title="Évolution de la température"
            )
            st.plotly_chart(fig_temp, use_container_width=True)

        # Graphique gaz si la colonne existe
        if "gaz" in df.columns and "date" in df.columns:
            fig_gaz = px.line(
                df,
                x="date",
                y="gaz",
                title="Évolution du niveau de gaz MQ2"
            )
            st.plotly_chart(fig_gaz, use_container_width=True)

        # Graphique de l'état de l'alarme
        if "alarme" in df.columns and "date" in df.columns:
            df_alarme = df.copy()
            df_alarme["alarme_num"] = df_alarme["alarme"].apply(
                lambda x: 1 if str(x).upper() == "ACTIF" else 0
            )
            fig_alarme = px.step(
                df_alarme,
                x="date",
                y="alarme_num",
                title="Historique de l'alarme (0 = INACTIF, 1 = ACTIF)"
            )
            st.plotly_chart(fig_alarme, use_container_width=True)

# Pied de page
st.markdown(
    "<hr><p style='text-align:center; font-size:12px; color:#888;'>© 2025 - Binôme A_02 : LFRAH Abdelrahman [HE304830] – IQBAL Adil [HE305031]</p>",
    unsafe_allow_html=True
)
