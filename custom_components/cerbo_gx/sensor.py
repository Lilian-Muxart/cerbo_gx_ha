import logging
import json
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.components.sensor import SensorDeviceClass
from .mqtt_client import CerboMQTTClient  # Client MQTT importé (à définir dans mqtt_client.py)
from homeassistant.core import HomeAssistant
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistantType, entry, async_add_entities) -> None:
    """Configurer les capteurs et les commutateurs pour une entrée donnée."""
    device_name = entry.data["device_name"]
    id_site = entry.data["cerbo_id"]

    # Récupérer le client MQTT initialisé dans __init__.py
    mqtt_client = hass.data[DOMAIN][entry.entry_id]["mqtt_client"]

    # Vérifier que le client est disponible
    if not mqtt_client:
        _LOGGER.error("Le client MQTT n'est pas disponible pour %s", device_name)
        return

    _LOGGER.info(
        "Initialisation des capteurs et commutateurs pour le dispositif %s avec l'ID de site %s", device_name, id_site
    )

    # Liste des entités à ajouter
    entities = [
        CerboBatterySensor(device_name, id_site, mqtt_client),
        CerboVoltageSensor(device_name, id_site, mqtt_client),
        CerboTemperatureSensor(device_name, id_site, mqtt_client),
        CerboRelaySwitch(device_name, id_site, mqtt_client, relay_index=0),
        CerboRelaySwitch(device_name, id_site, mqtt_client, relay_index=1),
    ]

    # Ajouter les entités à Home Assistant
    async_add_entities(entities, update_before_add=True)

    _LOGGER.info("Entités ajoutées pour %s", device_name)


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
        if "value" in payload:
            if isinstance(payload["value"], list) and len(payload["value"]) > 0:
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


class CerboRelaySwitch(SwitchEntity):
    """Interrupteur pour contrôler un relais du Cerbo GX."""

    def __init__(self, device_name: str, id_site: str, mqtt_client: CerboMQTTClient, relay_index: int):
        self._device_name = device_name
        self._id_site = id_site
        self._mqtt_client = mqtt_client
        self._relay_index = relay_index
        self._state = False

        self._state_topic = f"N/{id_site}/system/0/Relay/{relay_index}/State"
        self._command_topic = f"W/{id_site}/system/0/Relay/{relay_index}/State"

        self._attr_name = f"{device_name} Relay Switch {relay_index}"
        self._attr_unique_id = f"{id_site}_relay_switch_{relay_index}"

    async def async_added_to_hass(self):
        """Abonnez-vous aux messages MQTT lorsque l'entité est ajoutée."""
        _LOGGER.info("Abonnement au topic MQTT pour %s", self._attr_name)
        self._mqtt_client.add_subscription(self._state_topic, self.on_mqtt_message)

    async def async_will_remove_from_hass(self):
        """Désabonnez-vous des messages MQTT lorsque l'entité est retirée."""
        _LOGGER.info("Désabonnement du topic MQTT pour %s", self._attr_name)
        self._mqtt_client.remove_subscription(self._state_topic, self.on_mqtt_message)

    def on_mqtt_message(self, client, userdata, msg):
        """Met à jour l'état local en fonction du message MQTT reçu."""
        try:
            if not msg.payload:
                _LOGGER.warning("Message vide reçu sur le topic %s", msg.topic)
                return

            payload = json.loads(msg.payload)
            self._state = payload.get("value", False)
            _LOGGER.info("Mise à jour de l'état du relais %d: %s", self._relay_index, self._state)
            self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)

        except json.JSONDecodeError as e:
            _LOGGER.error(f"Erreur de décodage du message JSON sur le topic {msg.topic}: {e}")
        except Exception as e:
            _LOGGER.error("Erreur lors du traitement du message : %s", e)

    @property
    def is_on(self):
        """Retourne l'état actuel du relais."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Allume le relais via MQTT."""
        _LOGGER.info("Activation du relais %d", self._relay_index)
        payload = json.dumps({"value": True})
        self._mqtt_client.publish(self._command_topic, payload)
        self._state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Éteint le relais via MQTT."""
        _LOGGER.info("Désactivation du relais %d", self._relay_index)
        payload = json.dumps({"value": False})
        self._mqtt_client.publish(self._command_topic, payload)
        self._state = False
        self.async_write_ha_state()



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
        state_topic = f"N/{id_site}/system/0/Dc/Battery/Voltage"
        value_key = ""  # Nous voulons extraire la tension
        super().__init__(device_name, id_site, mqtt_client, state_topic, value_key)
        self._attr_name = f"{device_name} Voltage"
        self._attr_unique_id = f"{id_site}_voltage"
        self._attr_device_class = SensorDeviceClass.VOLTAGE
        self._attr_native_unit_of_measurement = "V"


class CerboTemperatureSensor(CerboBaseSensor):
    """Capteur pour la température du Cerbo GX."""

    def __init__(self, device_name: str, id_site: str, mqtt_client: CerboMQTTClient):
        state_topic = f"N/{id_site}/system/0/Dc/Battery/Temperature"
        value_key = ""  # Nous voulons extraire la température
        super().__init__(device_name, id_site, mqtt_client, state_topic, value_key)
        self._attr_name = f"{device_name} Temperature"
        self._attr_unique_id = f"{id_site}_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = "°C"
