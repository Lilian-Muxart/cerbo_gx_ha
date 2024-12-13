import paho.mqtt.client as mqtt
import asyncio
import logging
import ssl
import os

_LOGGER = logging.getLogger(__name__)

class CerboMQTTClient:
    def __init__(self, device_name, id_site, username, password, session):
        self.device_name = device_name
        self.id_site = id_site
        self.username = username
        self.password = password
        self.session = session
        self.client = mqtt.Client(client_id=f"cerbo_{id_site}")
        self.client.username_pw_set(username, password)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

    def _get_vrm_broker_url(self):
        """Calculer l'URL du serveur MQTT basé sur l'ID du site."""
        sum = 0
        for character in self.id_site.lower().strip():
            sum += ord(character)
        broker_index = sum % 128
        return f"mqtt{broker_index}.victronenergy.com"

    async def connect(self):
        """Se connecter au serveur MQTT avec l'URL dynamique et activer TLS sur le port 8883."""
        broker_url = self._get_vrm_broker_url()
        _LOGGER.info("Tentative de connexion sécurisée au serveur MQTT: %s", broker_url)

        # Spécifier le fichier de certificat CA
        ca_cert_path = os.path.join(os.path.dirname(__file__), "venus-ca.crt")

        # Configurer la connexion TLS
        self.client.tls_set(ca_certs=ca_cert_path, tls_version=ssl.PROTOCOL_TLSv1_2)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.client.connect, broker_url, 8883, 60)
        await loop.run_in_executor(None, self.client.loop_start)

    async def disconnect(self):
        """Déconnexion propre du serveur MQTT."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.client.disconnect)

    def on_connect(self, client, userdata, flags, rc):
        """Gérer la connexion réussie."""
        if rc == 0:
            _LOGGER.info("Connecté au serveur MQTT avec succès.")
            # Abonnement à tous les topics nécessaires
            self.client.subscribe(f"N/{self.id_site}/system/0/#")
        else:
            _LOGGER.error("Erreur de connexion MQTT avec code de retour %d", rc)

    def on_disconnect(self, client, userdata, rc):
        """Gérer la déconnexion."""
        if rc != 0:
            _LOGGER.warning("Déconnexion imprévue du serveur MQTT, code %d", rc)

    def on_message(self, client, userdata, msg):
        """Gérer la réception de messages MQTT."""
        _LOGGER.debug("Message reçu sur le topic %s: %s", msg.topic, msg.payload.decode())
