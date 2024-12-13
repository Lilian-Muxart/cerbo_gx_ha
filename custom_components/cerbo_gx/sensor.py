import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.const import DEVICE_CLASS_BATTERY, DEVICE_CLASS_VOLTAGE, DEVICE_CLASS_TEMPERATURE
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistantType, entry, async_add_entities) -> None:
    """Configurer les capteurs pour une entrée donnée."""
    device_name = entry.data["device_name"]
    id_site = entry.data["cerbo_id"]

    # Liste des capteurs à ajouter
    sensors = [
        CerboBatterySensor(device_name, id_site),
        CerboVoltageSensor(device_name, id_site),
        CerboTemperatureSensor(device_name, id_site),
    ]

    # Ajouter les capteurs
    async_add_entities(sensors, update_before_add=True)


class CerboBatterySensor(SensorEntity):
    """Capteur pour la batterie du Cerbo GX."""

    def __init__(self, device_name: str, id_site: str):
        """Initialiser le capteur."""
        self._name = f"{device_name} Battery Percent"
        self._unique_id = f"{device_name}_battery_percent"
        self._state = None
        self._device_class = DEVICE_CLASS_BATTERY
        self._unit_of_measurement = "%"
        self._state_topic = f"N/{id_site}/system/0/Batteries"

    @property
    def name(self):
        """Retourner le nom du capteur."""
        return self._name

    @property
    def unique_id(self):
        """Retourner l'ID unique du capteur."""
        return self._unique_id

    @property
    def device_class(self):
        """Retourner la classe du dispositif."""
        return self._device_class

    @property
    def state(self):
        """Retourner l'état actuel du capteur."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Retourner l'unité de mesure."""
        return self._unit_of_measurement

    async def async_update(self):
        """Mettre à jour l'état du capteur avec les données MQTT."""
        # Récupérer la donnée MQTT du topic
        mqtt_client = self.hass.data[DOMAIN].get("mqtt_client")
        if mqtt_client:
            payload = mqtt_client.client.subscribe(self._state_topic)
            self._state = payload["value"][0]["soc"]  # Valeur spécifique de la batterie


class CerboVoltageSensor(SensorEntity):
    """Capteur pour la tension du Cerbo GX."""

    def __init__(self, device_name: str, id_site: str):
        """Initialiser le capteur."""
        self._name = f"{device_name} Voltage"
        self._unique_id = f"{device_name}_voltage"
        self._state = None
        self._device_class = DEVICE_CLASS_VOLTAGE
        self._unit_of_measurement = "V"
        self._state_topic = f"N/{id_site}/system/0/Voltage"

    @property
    def name(self):
        """Retourner le nom du capteur."""
        return self._name

    @property
    def unique_id(self):
        """Retourner l'ID unique du capteur."""
        return self._unique_id

    @property
    def device_class(self):
        """Retourner la classe du dispositif."""
        return self._device_class

    @property
    def state(self):
        """Retourner l'état actuel du capteur."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Retourner l'unité de mesure."""
        return self._unit_of_measurement

    async def async_update(self):
        """Mettre à jour l'état du capteur avec les données MQTT."""
        # Récupérer la donnée MQTT du topic
        mqtt_client = self.hass.data[DOMAIN].get("mqtt_client")
        if mqtt_client:
            payload = mqtt_client.client.subscribe(self._state_topic)
            self._state = payload["value"][0]["voltage"]  # Valeur spécifique de la tension


class CerboTemperatureSensor(SensorEntity):
    """Capteur pour la température du Cerbo GX."""

    def __init__(self, device_name: str, id_site: str):
        """Initialiser le capteur."""
        self._name = f"{device_name} Temperature"
        self._unique_id = f"{device_name}_temperature"
        self._state = None
        self._device_class = DEVICE_CLASS_TEMPERATURE
        self._unit_of_measurement = "°C"
        self._state_topic = f"N/{id_site}/system/0/Temperature"

    @property
    def name(self):
        """Retourner le nom du capteur."""
        return self._name

    @property
    def unique_id(self):
        """Retourner l'ID unique du capteur."""
        return self._unique_id

    @property
    def device_class(self):
        """Retourner la classe du dispositif."""
        return self._device_class

    @property
    def state(self):
        """Retourner l'état actuel du capteur."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Retourner l'unité de mesure."""
        return self._unit_of_measurement

    async def async_update(self):
        """Mettre à jour l'état du capteur avec les données MQTT."""
        # Récupérer la donnée MQTT du topic
        mqtt_client = self.hass.data[DOMAIN].get("mqtt_client")
        if mqtt_client:
            payload = mqtt_client.client.subscribe(self._state_topic)
            self._state = payload["value"][0]["temperature"]  # Valeur spécifique de la température
