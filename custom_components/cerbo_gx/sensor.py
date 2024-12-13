import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import Entity
import paho.mqtt.client as mqtt
from . import _get_vrm_broker_url

_LOGGER = logging.getLogger(__name__)

class VictronMqttSensor(SensorEntity):
    """Représente un capteur MQTT pour l'intégration Victron."""

    def __init__(self, device_name, broker_url):
        """Initialiser le capteur."""
        self.device_name = device_name
        self.broker_url = broker_url
        self._state = None
        self._client = mqtt.Client()
        self._client.on_connect = self.on_connect
        self._client.on_message = self.on_message
        self._client.connect(self.broker_url)

    def on_connect(self, client, userdata, flags, rc):
        """Callback lorsque la connexion est établie."""
        _LOGGER.info(f"Connected to MQTT broker: {self.broker_url}")
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
