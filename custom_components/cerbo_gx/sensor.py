import logging
import json
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
        # Nous n'utilisons plus cette méthode pour récupérer les données
        pass

    def on_message(self, client, userdata, msg):
        """Gérer la réception de messages MQTT pour la batterie."""
        if msg.topic == self._state_topic:
            try:
                payload = json.loads(msg.payload.decode())
                self._state = payload.get("soc", None)  # Valeur spécifique de la batterie
                self.schedule_update_ha_state()
            except json.JSONDecodeError:
                _LOGGER.error("Erreur de décodage JSON pour le message de batterie.")
            except KeyError:
                _LOGGER.error("Clé 'soc' manquante dans les données de batterie.")


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
        # Nous n'utilisons plus cette méthode pour récupérer les données
        pass

    def on_message(self, client, userdata, msg):
        """Gérer la réception de messages MQTT pour la tension."""
        if msg.topic == self._state_topic:
            try:
                payload = json.loads(msg.payload.decode())
                self._state = payload.get("voltage", None)  # Valeur spécifique de la tension
                self.schedule_update_ha_state()
            except json.JSONDecodeError:
                _LOGGER.error("Erreur de décodage JSON pour le message de tension.")
            except KeyError:
                _LOGGER.error("Clé 'voltage' manquante dans les données de tension.")


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
        # Nous n'utilisons plus cette méthode pour récupérer les données
        pass

    def on_message(self, client, userdata, msg):
        """Gérer la réception de messages MQTT pour la température."""
        if msg.topic == self._state_topic:
            try:
                payload = json.loads(msg.payload.decode())
                self._state = payload.get("temperature", None)  # Valeur spécifique de la température
                self.schedule_update_ha_state()
            except json.JSONDecodeError:
                _LOGGER.error("Erreur de décodage JSON pour le message de température.")
            except KeyError:
                _LOGGER.error("Clé 'temperature' manquante dans les données de température.")
