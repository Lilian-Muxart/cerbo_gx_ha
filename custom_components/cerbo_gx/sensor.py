import logging
import json
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.components.sensor import SensorDeviceClass
from .mqtt_client import CerboMQTTClient  # Client MQTT importé (à définir dans mqtt_client.py)
from homeassistant.core import HomeAssistant
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistantType, entry, async_add_entities) -> None:
    """Configurer les capteurs pour une entrée donnée."""
    device_name = entry.data["device_name"]
    id_site = entry.data["cerbo_id"]

    # Récupérer le client MQTT initialisé dans __init__.py
    mqtt_client = hass.data[DOMAIN][entry.entry_id]["mqtt_client"]

    # Vérifier que le client est disponible
    if not mqtt_client:
        _LOGGER.error("Le client MQTT n'est pas disponible pour %s", device_name)
        return

    _LOGGER.info(
        "Initialisation des capteurs pour le dispositif %s avec l'ID de site %s", device_name, id_site
    )

    # Liste des capteurs à ajouter
    sensors = [
        CerboBatterySensor(device_name, id_site, mqtt_client),
        CerboVoltageSensor(device_name, id_site, mqtt_client),
        CerboTemperatureSensor(device_name, id_site, mqtt_client),
        CerboRelaySensor(device_name, id_site, mqtt_client),
    ]

    # Ajouter les capteurs à Home Assistant
    async_add_entities(sensors, update_before_add=True)

    _LOGGER.info("Capteurs ajoutés pour %s", device_name)


class CerboBaseSensor(SensorEntity):
    def __init__(self, device_name: str, id_site: str, mqtt_client: CerboMQTTClient, state_topic: str, value_key: str):
        self._device_name = device_name
        self._id_site = id_site
        self._state = None
        self._mqtt_client = mqtt_client
        self._state_topic = state_topic
        self._value_key = value_key
        self._attr_device_info = {
            "identifiers": {(DOMAIN, id_site)},
            "name": device_name,
            "manufacturer": "Victron Energy",
            "model": "Cerbo GX",
        }

    async def async_added_to_hass(self):
        """Abonnez-vous aux messages MQTT lorsque l'entité est ajoutée."""
        _LOGGER.info("Abonnement au topic MQTT pour %s", self._attr_name)
        self._mqtt_client.add_subscription(self.get_state_topic(), self.on_mqtt_message)

    async def async_will_remove_from_hass(self):
        """Désabonnez-vous des messages MQTT lorsque l'entité est retirée."""
        _LOGGER.info("Désabonnement du topic MQTT pour %s", self._attr_name)
        self._mqtt_client.remove_subscription(self.get_state_topic(), self.on_mqtt_message)

    def on_mqtt_message(self, client, userdata, msg):
        try:
            if not msg.payload:
                _LOGGER.warning("Message vide reçu sur le topic %s", msg.topic)
                return
            
            payload = json.loads(msg.payload)
            value = self._extract_value(payload)
            
            if value is not None:
                self._state = value
                self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)
        
        except json.JSONDecodeError as e:
            _LOGGER.error(f"Erreur de décodage du message JSON sur le topic {msg.topic}: {e}")
        except Exception as e:
            _LOGGER.error("Erreur lors du traitement du message : %s", e)

    def _extract_value(self, payload: dict):
        # Vérifie si "value" est une liste avec des données
        if "value" in payload:
            if isinstance(payload["value"], list) and len(payload["value"]) > 0:
                sensor_data = payload["value"][0]
                if self._value_key in sensor_data:
                    return sensor_data[self._value_key]
            # Si "value" n'est pas une liste, mais une valeur directe
            elif isinstance(payload["value"], (int, float, str, bool)):
                return payload["value"]
        return None

    @property
    def state(self):
        return self._state

    def get_state_topic(self):
        return self._state_topic

class CerboBatterySensor(CerboBaseSensor):
    """Capteur pour la batterie du Cerbo GX."""

    def __init__(self, device_name: str, id_site: str, mqtt_client: CerboMQTTClient):
        state_topic = f"N/{id_site}/system/0/Batteries"
        value_key = "soc"  # Nous voulons extraire la charge de la batterie
        super().__init__(device_name, id_site, mqtt_client, state_topic, value_key)
        self._attr_name = f"{device_name} Battery"
        self._attr_unique_id = f"{id_site}_battery"
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_native_unit_of_measurement = "%"


class CerboVoltageSensor(CerboBaseSensor):
    """Capteur pour la tension du Cerbo GX."""

    def __init__(self, device_name: str, id_site: str, mqtt_client: CerboMQTTClient):
        state_topic = f"N/{id_site}/system/0/Batteries"
        value_key = "voltage"  # Nous voulons extraire la tension
        super().__init__(device_name, id_site, mqtt_client, state_topic, value_key)
        self._attr_name = f"{device_name} Voltage"
        self._attr_unique_id = f"{id_site}_voltage"
        self._attr_device_class = SensorDeviceClass.VOLTAGE
        self._attr_native_unit_of_measurement = "V"


class CerboTemperatureSensor(CerboBaseSensor):
    """Capteur pour la température du Cerbo GX."""

    def __init__(self, device_name: str, id_site: str, mqtt_client: CerboMQTTClient):
        state_topic = f"N/{id_site}/system/0/Batteries"
        value_key = "temperature"  # Nous voulons extraire la température
        super().__init__(device_name, id_site, mqtt_client, state_topic, value_key)
        self._attr_name = f"{device_name} Temperature"
        self._attr_unique_id = f"{id_site}_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = "°C"


class RelayDeviceClass:
    RELAY = "relay"


class CerboRelaySensor(CerboBaseSensor):
    """Capteur pour l'état des relais du Cerbo GX."""
    
    def __init__(self, device_name: str, id_site: str, mqtt_client: CerboMQTTClient):
        state_topic = f"N/{id_site}/system/0/Relay/1/State"
        value_key = ""  # Définir la clé de valeur pour l'état du relais
        
        super().__init__(device_name, id_site, mqtt_client, state_topic, value_key)
        
        self._attr_name = f"{device_name} Relay State"
        self._attr_unique_id = f"{id_site}_relay_state"
        self._attr_device_class = RelayDeviceClass.RELAY
        self._attr_native_unit_of_measurement = ""
