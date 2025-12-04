# Dashboard Streamlit – Projet HVAC Industrie 4.0

## Informations
- Cours : A304 (Systèmes Embarqués II) & A311 (Industrie 4.0)
- Année académique : 2025-2026
- Binôme A_02 :
  - LFRAH Abdelrahman [HE304830]
  - IQBAL Adil [HE305031]

---

## Description
Ce dossier contient le tableau de bord Streamlit utilisé pour superviser le système HVAC.  
Les données provenant des deux ESP32 (Salle et Local Technique) transitent via MQTT, sont traitées par Node-RED et enregistrées dans MariaDB (VM Azure).  
Le dashboard affiche : température, humidité, luminosité, gaz MQ2, présence, consigne moteur et états du système.

---

## Structure
HVAC_Streamlit/  
│── app.py  
│── requirements.txt  
│── assets/  
│── config/  
└── README.md  

---

## Installation
pip install -r requirements.txt

---

## Lancement
streamlit run app.py  
Accès : http://localhost:8501

---

## Technologies
Streamlit, Python, Plotly, MariaDB, MQTT, Node-RED.

---

Projet réalisé dans le cadre des cours A304/A311 – EPHEC TECH (2025-2026).
