import logging
import os
import ssl
import paho.mqtt.client as mqtt
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

class VictronMqttSensor(SensorEntity):
    """Représente un capteur MQTT pour l'intégration Victron."""

    def __init__(self, device_name, broker_url):
        """Initialiser le capteur."""
        self.device_name = device_name
        self.broker_url = broker_url
        self._state = None
        self._client = mqtt.Client()
        
        # Charger le certificat CA à partir du même dossier que l'intégration
        self._load_ca_certificate()

        # Configurer les callbacks MQTT
        self._client.on_connect = self.on_connect
        self._client.on_message = self.on_message

        # Connexion au broker MQTT avec certificat SSL
        self._client.tls_set(ca_certs=self.ca_cert, tls_version=ssl.PROTOCOL_TLSv1_2)
        self._client.connect(self.broker_url)

    def _load_ca_certificate(self):
        """Charge le certificat CA venus-ca.crt depuis le dossier de l'intégration."""
        integration_folder = os.path.dirname(__file__)  # Récupère le dossier actuel de l'intégration
        self.ca_cert = os.path.join(integration_folder, "venus-ca.crt")  # Chemin complet vers le certificat

        if not os.path.exists(self.ca_cert):
            _LOGGER.error(f"Le certificat CA venus-ca.crt n'a pas été trouvé à {self.ca_cert}")
            raise FileNotFoundError(f"Le certificat CA venus-ca.crt n'a pas été trouvé à {self.ca_cert}")
        
        _LOGGER.info(f"Certificat CA trouvé à : {self.ca_cert}")

    def on_connect(self, client, userdata, flags, rc):
        """Callback lorsque la connexion est établie."""
        _LOGGER.info(f"Connecté au broker MQTT: {self.broker_url}")
        client.subscribe(f"homeassistant/{self.device_name}/#")

    def on_message(self, client, userdata, msg):
        """Callback pour les messages MQTT."""
        self._state = msg.payload.decode()
        self.async_write_ha_state()

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
        self._client.loop()
