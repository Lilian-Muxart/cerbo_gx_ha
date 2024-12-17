import json
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import TEMP_CELSIUS, PERCENTAGE, VOLT
from mqtt_client import CerboMQTTClient

_LOGGER = logging.getLogger(__name__)

class CerboBaseSensor(SensorEntity):
    """Classe de base pour les capteurs Cerbo GX."""
    
    def __init__(self, device_name: str, id_site: str, mqtt_client: CerboMQTTClient, state_topic: str, value_key: str):
        """Initialisation du capteur."""
        self.device_name = device_name
        self.id_site = id_site
        self.mqtt_client = mqtt_client
        self.state_topic = state_topic
        self.value_key = value_key
        self._state = None

        # Abonnement au topic et configuration du callback pour le message MQTT
        self.mqtt_client.client.message_callback_add(self.state_topic, self.on_message)
        self.mqtt_client.client.subscribe(self.state_topic)

    def on_message(self, client, userdata, msg):
        """Callback pour traiter les messages MQTT."""
        try:
            payload = json.loads(msg.payload.decode())
            if self.value_key in payload:
                self._state = payload[self.value_key]
                _LOGGER.debug(f"{self.device_name} - {self.value_key}: {self._state}")
        except Exception as e:
            _LOGGER.error(f"Erreur lors du traitement du message MQTT: {e}")

    @property
    def state(self):
        """Retourne l'état actuel du capteur."""
        return self._state

class CerboBatterySensor(CerboBaseSensor):
    """Capteur pour la batterie du Cerbo GX."""
    
    def __init__(self, device_name: str, id_site: str, mqtt_client: CerboMQTTClient):
        """Initialisation du capteur de batterie."""
        state_topic = f"N/{id_site}/system/0/Batteries"
        value_key = "soc"  # Valeur de la charge de la batterie
        super().__init__(device_name, id_site, mqtt_client, state_topic, value_key)
        self._attr_name = f"{device_name} Battery"
        self._attr_unique_id = f"{id_site}_battery_percent"
        self._attr_device_class = "battery"
        self._attr_native_unit_of_measurement = PERCENTAGE

class CerboVoltageSensor(CerboBaseSensor):
    """Capteur pour la tension du Cerbo GX."""
    
    def __init__(self, device_name: str, id_site: str, mqtt_client: CerboMQTTClient):
        """Initialisation du capteur de tension."""
        state_topic = f"N/{id_site}/system/0/Batteries"
        value_key = "voltage"  # Valeur de la tension
        super().__init__(device_name, id_site, mqtt_client, state_topic, value_key)
        self._attr_name = f"{device_name} Voltage"
        self._attr_unique_id = f"{id_site}_voltage"
        self._attr_device_class = "voltage"
        self._attr_native_unit_of_measurement = VOLT

class CerboTemperatureSensor(CerboBaseSensor):
    """Capteur pour la température du Cerbo GX."""
    
    def __init__(self, device_name: str, id_site: str, mqtt_client: CerboMQTTClient):
        """Initialisation du capteur de température."""
        state_topic = f"N/{id_site}/system/0/Batteries"
        value_key = "temperature"  # Valeur de la température
        super().__init__(device_name, id_site, mqtt_client, state_topic, value_key)
        self._attr_name = f"{device_name} Temperature"
        self._attr_unique_id = f"{id_site}_temperature"
        self._attr_device_class = "temperature"
        self._attr_native_unit_of_measurement = TEMP_CELSIUS
