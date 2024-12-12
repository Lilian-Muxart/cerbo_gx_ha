import aiohttp
import asyncio
from paho.mqtt import client as mqtt

async def fetch_mqtt_server(cerbo_id, username, password):
    """Fetch the MQTT server address from the VRM API based on cerbo_id."""
    async with aiohttp.ClientSession() as session:
        # Authentification via l'API VRM pour obtenir un token
        async with session.post(
            "https://vrmapi.victronenergy.com/v2/auth/login", 
            json={"username": username, "password": password}
        ) as response:
            if response.status != 200:
                raise Exception("Failed to authenticate")
            auth_data = await response.json()

        token = auth_data["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Récupérer les installations associées au compte de l'utilisateur
        async with session.get(
            f"https://vrmapi.victronenergy.com/v2/installations", 
            headers=headers
        ) as response:
            if response.status != 200:
                raise Exception("Failed to fetch installations")
            installations = await response.json()

        # Chercher l'installation correspondant à cerbo_id
        for installation in installations["records"]:
            if installation["idSite"] == int(cerbo_id):
                for attribute in installation.get("extended", []):
                    # Recherche de l'adresse du serveur MQTT dans les attributs étendus
                    if attribute["description"] == "MQTT Server":
                        mqtt_server = attribute["formattedValue"]
                        return {"server": mqtt_server}

        raise Exception("Installation not found or invalid cerbo_id")

class CerboMQTTClient:
    def __init__(self, config, session):
        """Initialisation du client MQTT avec les informations fournies par l'utilisateur."""
        self.server = config["mqtt_server"]  # Serveur récupéré via l'API VRM
        self.user = config["mqtt_user"]  # Identifiants MQTT fournis par l'utilisateur
        self.password = config["mqtt_password"]  # Identifiants MQTT fournis par l'utilisateur
        self.client = mqtt.Client()

    async def connect(self):
        """Se connecter au serveur MQTT et démarrer la boucle de gestion des messages."""
        # Configurer l'utilisateur et le mot de passe MQTT
        self.client.username_pw_set(self.user, self.password)
        # Définir les certificats pour la connexion sécurisée (TLS)
        self.client.tls_set("custom_components/cerbo_gx/venus-ca.crt")
        
        # Connexion au serveur MQTT
        self.client.connect(self.server)
        self.client.loop_start()

        while True:
            # Exemple de topic MQTT à publier, ajustez-le si nécessaire
            topic = f"R/{self.server}/system/0/Serial"
            self.client.publish(topic, "")
            await asyncio.sleep(30)
