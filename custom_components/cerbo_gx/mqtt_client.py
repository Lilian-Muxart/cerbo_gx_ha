import paho.mqtt.client as mqtt
import logging

_LOGGER = logging.getLogger(__name__)

class CerboMQTTClient:
    def __init__(self, device_name, id_site, username, password, session):
        self.device_name = device_name
        self.id_site = id_site
        self.username = username
        self.password = password
        self.session = session
        self.client = mqtt.Client()

    async def connect(self):
        """Connecter le client MQTT."""
        try:
            # Connexion au serveur MQTT
            self.client.username_pw_set(self.username, self.password)
            self.client.connect(f"mqtt{self.id_site}.victronenergy.com")
            self.client.loop_start()  # Démarre la boucle de gestion des messages MQTT
            _LOGGER.info("Connexion au serveur MQTT réussie pour %s", self.device_name)
        except Exception as e:
            _LOGGER.error("Erreur lors de la connexion au serveur MQTT: %s", str(e))
            raise

    async def disconnect(self):
        """Déconnecter le client MQTT."""
        self.client.loop_stop()
        self.client.disconnect()
