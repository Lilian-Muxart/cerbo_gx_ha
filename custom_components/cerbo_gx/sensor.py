import logging
import json
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.core import HomeAssistant
from .mqtt_client import CerboMQTTClient  # Client MQTT importé (à définir dans mqtt_client.py)
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistantType, entry, async_add_entities) -> None:
    """Configurer les entités pour une entrée donnée."""
    device_name = entry.data["device_name"]
    id_site = entry.data["cerbo_id"]

    # Récupérer le client MQTT initialisé dans __init__.py
    mqtt_client: CerboMQTTClient = hass.data[DOMAIN][entry.entry_id]["mqtt_client"]

    if not mqtt_client:
        _LOGGER.error("Le client MQTT n'est pas disponible pour %s", device_name)
        return

    _LOGGER.info("Initialisation des entités pour le dispositif %s avec l'ID de site %s", device_name, id_site)

    entities = [
        CerboVoltageSensor(device_name, id_site, mqtt_client),
        CerboWattSensor(device_name, id_site, mqtt_client),
        CerboAmperageSensor(device_name, id_site, mqtt_client),
        CerboRelaySwitch(device_name, id_site, mqtt_client, 0),  # Relais 0
        CerboRelaySwitch(device_name, id_site, mqtt_client, 1),  # Relais 1
    ]

    async_add_entities(entities, update_before_add=True)
    _LOGGER.info("Entités ajoutées pour %s", device_name)


class CerboBaseSensor(SensorEntity):
    """Classe de base pour les capteurs de Cerbo GX."""

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
        """S'abonner aux messages MQTT lors de l'ajout de l'entité."""
        _LOGGER.info("Abonnement au topic MQTT pour %s", self._attr_name)
        self._mqtt_client.add_subscription(self.get_state_topic(), self.on_mqtt_message)

    async def async_will_remove_from_hass(self):
        """Se désabonner des messages MQTT lors du retrait de l'entité."""
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
            _LOGGER.error(f"Erreur de décodage du JSON sur le topic {msg.topic}: {e}")
        except Exception as e:
            _LOGGER.error("Erreur lors du traitement du message : %s", e)

    def _extract_value(self, payload: dict):
        if "value" in payload:
            if isinstance(payload["value"], list) and payload["value"]:
                sensor_data = payload["value"][0]
                if self._value_key in sensor_data:
                    return sensor_data[self._value_key]
            elif isinstance(payload["value"], (int, float, str, bool)):
                return payload["value"]
        return None

    @property
    def state(self):
        return self._state

    def get_state_topic(self):
        return self._state_topic


class CerboVoltageSensor(CerboBaseSensor):
    """Capteur pour la tension du Cerbo GX."""

    def __init__(self, device_name: str, id_site: str, mqtt_client: CerboMQTTClient):
        state_topic = f"N/{id_site}/system/0/Dc/Battery/Voltage"
        value_key = ""  # On récupère directement la valeur
        super().__init__(device_name, id_site, mqtt_client, state_topic, value_key)
        self._attr_name = f"{device_name} Voltage"
        self._attr_unique_id = f"{id_site}_voltage"
        self._attr_device_class = SensorDeviceClass.VOLTAGE
        self._attr_native_unit_of_measurement = "V"
        self._attr_suggested_display_precision = 2


class CerboWattSensor(CerboBaseSensor):
    """Capteur pour la puissance solaire du Cerbo GX."""

    def __init__(self, device_name: str, id_site: str, mqtt_client: CerboMQTTClient):
        state_topic = f"N/{id_site}/system/0/Dc/Pv/Power"
        value_key = ""
        super().__init__(device_name, id_site, mqtt_client, state_topic, value_key)
        self._attr_name = f"{device_name} Power solaire"
        self._attr_unique_id = f"{id_site}_solaire"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = "W"
        self._attr_suggested_display_precision = 2


class CerboAmperageSensor(CerboBaseSensor):
    """Capteur pour l'ampérage du Cerbo GX."""

    def __init__(self, device_name: str, id_site: str, mqtt_client: CerboMQTTClient):
        state_topic = f"N/{id_site}/system/0/Dc/Battery/Current"
        value_key = ""
        super().__init__(device_name, id_site, mqtt_client, state_topic, value_key)
        self._attr_name = f"{device_name} Amperage"
        self._attr_unique_id = f"{id_site}_amperage"
        self._attr_device_class = SensorDeviceClass.CURRENT
        self._attr_native_unit_of_measurement = "A"
        self._attr_suggested_display_precision = 2


class RelayDeviceClass:
    RELAY = "relay"


class CerboRelaySwitch(SwitchEntity):
    """Switch pour contrôler l'état des relais du Cerbo GX."""

    def __init__(self, device_name: str, id_site: str, mqtt_client: CerboMQTTClient, relay_number: int):
        self._device_name = device_name
        self._id_site = id_site
        self._relay_number = relay_number
        self._mqtt_client = mqtt_client
        self._state = False  # État par défaut : OFF
        self._state_topic = f"N/{id_site}/system/0/Relay/{relay_number}/State"
        self._command_topic = f"W/{id_site}/system/0/Relay/{relay_number}/State"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, id_site)},
            "name": device_name,
            "manufacturer": "Victron Energy",
            "model": "Cerbo GX",
        }
        self._attr_name = f"{device_name} Relay {relay_number} Switch"
        self._attr_unique_id = f"{id_site}_relay_switch_{relay_number}"
        self._attr_icon = "mdi:power"
        self._attr_is_on = False

    async def async_added_to_hass(self):
        _LOGGER.info("Abonnement au topic MQTT pour %s", self._attr_name)
        self._mqtt_client.add_subscription(self._state_topic, self.on_mqtt_message)

    async def async_will_remove_from_hass(self):
        _LOGGER.info("Désabonnement du topic MQTT pour %s", self._attr_name)
        self._mqtt_client.remove_subscription(self._state_topic, self.on_mqtt_message)

    def on_mqtt_message(self, client, userdata, msg):
        try:
            if not msg.payload:
                _LOGGER.warning("Message vide reçu sur le topic %s", msg.topic)
                return

            payload = json.loads(msg.payload)
            # On attend que le payload soit de la forme {"value": <int>}
            value = payload.get("value")
            if value is not None:
                self._state = (value == 1)
                self._attr_is_on = self._state
                self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)
        except json.JSONDecodeError as e:
            _LOGGER.error(f"Erreur de décodage JSON sur le topic {msg.topic}: {e}")
        except Exception as e:
            _LOGGER.error("Erreur lors du traitement du message : %s", e)

    @property
    def is_on(self) -> bool:
        return self._state

    async def async_turn_on(self, **kwargs):
        _LOGGER.info(f"Allumer le relais {self._relay_number}")
        payload = json.dumps({"value": 1})
        self._mqtt_client.publish(self._command_topic, payload)

    async def async_turn_off(self, **kwargs):
        _LOGGER.info(f"Éteindre le relais {self._relay_number}")
        payload = json.dumps({"value": 0})
        self._mqtt_client.publish(self._command_topic, payload)
