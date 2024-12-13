import logging
import os
import ssl
import paho.mqtt.client as mqtt
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import Entity
import asyncio

_LOGGER = logging.getLogger(__name__)

class VictronMqttSensor(SensorEntity):
    """Représente un capteur MQTT pour l'intégration Victron."""

    def __init__(self, device_name, broker_url, id_site):
        """Initialiser le capteur."""
        self.device_name = device_name
        self.broker_url = broker_url
        self.id_site = id_site
        self._state = None
        self.is_connected = False

        # Charger le certificat CA à partir du même dossier que l'intégration
        self._load_ca_certificate()

        # Initialiser le client MQTT
        self._client = mqtt.Client()

        # Configurer les callbacks MQTT
        self._client.on_connect = self.on_connect
        self._client.on_disconnect = self.on_disconnect
        self._client.on_message = self.on_message

        # Configurer la connexion SSL avec le certificat
        self._client.tls_set(ca_certs=self.ca_cert, tls_version=ssl.PROTOCOL_TLSv1_2)

        # Connexion au broker MQTT
        self._client.connect(self.broker_url)

    def _load_ca_certificate(self):
        """Charge le certificat CA venus-ca.crt depuis le dossier de l'intégration."""
        integration_folder = os.path.dirname(__file__)  # Récupère le dossier actuel de l'intégration
        self.ca_cert = os.path.join(integration_folder, "venus-ca.crt")  # Chemin complet vers le certificat

        if not os.path.exists(self.ca_cert):
            _LOGGER.error(f"Le certificat CA venus-ca.crt n'a pas été trouvé à {self.ca_cert}")
            raise FileNotFoundError(f"Le certificat CA venus-ca.crt n'a pas été trouvé à {self.ca_cert}")
        
        _LOGGER.info(f"Certificat CA trouvé à : {self.ca_cert}")

    async def disconnect(self):
        """Déconnexion propre du serveur MQTT."""
        if self.is_connected:
            _LOGGER.info("Déconnexion propre du serveur MQTT.")
            loop = asyncio.get_event_loop()
            await asyncio.to_thread(self._client.disconnect)

    def on_connect(self, client, userdata, flags, rc):
        """Gérer la connexion réussie."""
        if rc == 0:
            _LOGGER.info("Connecté au serveur MQTT avec succès.")
            self.is_connected = True
            # Abonnement à tous les topics nécessaires
            self._client.subscribe(f"N/{self.id_site}/system/0/#")
        else:
            _LOGGER.error("Erreur de connexion MQTT avec code de retour %d", rc)
            self.is_connected = False

    def on_disconnect(self, client, userdata, rc):
        """Gérer la déconnexion."""
        self.is_connected = False
        if rc != 0:
            _LOGGER.warning("Déconnexion imprévue du serveur MQTT, code %d", rc)

    def on_message(self, client, userdata, msg):
        """Gérer la réception de messages MQTT."""
        _LOGGER.debug("Message reçu sur le topic %s: %s", msg.topic, msg.payload.decode())
        self._state = msg.payload.decode()  # Mettre à jour l'état avec la charge utile du message
        self.async_write_ha_state()  # Mettre à jour l'état de l'entité dans Home Assistant

    @property
    def name(self):
        """Retourner le nom du capteur."""
        return f"Victron Sensor {self.device_name}"

    @property
    def state(self):
        """Retourner l'état du capteur."""
        return self._state

    async def async_update(self):
        """Mettre à jour l'état du capteur."""
        self._client.loop()  # Assurez-vous que le client MQTT est en train de recevoir des messages
