import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.components.sensor import SensorDeviceClass
from .mqtt_client import CerboMQTTClient  # Client MQTT importé (à définir dans mqtt_client.py)
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistantType, entry, async_add_entities):
    """Configurer les capteurs pour une entrée donnée."""
    device_name = entry.data["device_name"]
    id_site = entry.data["cerbo_id"]

    # Récupérer le client MQTT initialisé dans __init__.py
    mqtt_client = hass.data[DOMAIN][entry.entry_id]["mqtt_client"]

    if not mqtt_client:
        _LOGGER.error("Le client MQTT n'est pas disponible pour %s", device_name)
        return

    _LOGGER.info(
        "Initialisation des capteurs pour le dispositif %s avec l'ID de site %s", device_name, id_site
    )

    sensors = [
        CerboBatterySensor(device_name, id_site, mqtt_client),
        CerboVoltageSensor(device_name, id_site, mqtt_client),
        CerboTemperatureSensor(device_name, id_site, mqtt_client),
    ]

    async_add_entities(sensors, update_before_add=True)
    _LOGGER.info("Capteurs ajoutés pour %s", device_name)


class CerboBaseSensor(SensorEntity):
    """Classe de base pour les capteurs du Cerbo GX."""

    def __init__(self, device_name, id_site, mqtt_client, state_topic, value_key):
        self._device_name = device_name
        self._id_site = id_site
        self._mqtt_client = mqtt_client
        self._state_topic = state_topic
        self._value_key = value_key
        self._state = None

        self._attr_device_info = {
            "identifiers": {(DOMAIN, id_site)},
            "name": device_name,
            "manufacturer": "Victron Energy",
            "model": "Cerbo GX",
        }

    async def async_added_to_hass(self):
        """Abonnez-vous aux messages MQTT lorsque l'entité est ajoutée."""
        self._mqtt_client.add_subscriber(self._state_topic, self)

    def handle_message(self, payload):
        """Traiter les messages MQTT pour extraire et mettre à jour l'état."""
        try:
            if "value" in payload and isinstance(payload["value"], list) and len(payload["value"]) > 0:
                sensor_data = payload["value"][0]
                if self._value_key in sensor_data:
                    self._state = sensor_data[self._value_key]
                    self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error("Erreur de traitement du message pour %s: %s", self.name, e)

    @property
    def state(self):
        return self._state


class CerboBatterySensor(CerboBaseSensor):
    """Capteur pour la charge de la batterie."""

    def __init__(self, device_name, id_site, mqtt_client):
        super().__init__(device_name, id_site, mqtt_client, f"N/{id_site}/system/0/Batteries", "soc")
        self._attr_name = f"{device_name} Battery"
        self._attr_unique_id = f"{id_site}_battery"
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_native_unit_of_measurement = "%"


class CerboVoltageSensor(CerboBaseSensor):
    """Capteur pour la tension de la batterie."""

    def __init__(self, device_name, id_site, mqtt_client):
        super().__init__(device_name, id_site, mqtt_client, f"N/{id_site}/system/0/Batteries", "voltage")
        self._attr_name = f"{device_name} Voltage"
        self._attr_unique_id = f"{id_site}_voltage"
        self._attr_device_class = SensorDeviceClass.VOLTAGE
        self._attr_native_unit_of_measurement = "V"


class CerboTemperatureSensor(CerboBaseSensor):
    """Capteur pour la température de la batterie."""

    def __init__(self, device_name, id_site, mqtt_client):
        super().__init__(device_name, id_site, mqtt_client, f"N/{id_site}/system/0/Batteries", "temperature")
        self._attr_name = f"{device_name} Temperature"
        self._attr_unique_id = f"{id_site}_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = "°C"
