import logging
import json
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.components.sensor import SensorDeviceClass
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistantType, entry, async_add_entities) -> None:
    """Configurer les capteurs pour une entrée donnée."""
    device_name = entry.data["device_name"]
    id_site = entry.data["cerbo_id"]

    _LOGGER.info("Initialisation des capteurs pour le dispositif %s avec l'ID de site %s", device_name, id_site)

    # Liste des capteurs à ajouter
    sensors = [
        CerboBatterySensor(device_name, id_site),
        CerboVoltageSensor(device_name, id_site),
        CerboTemperatureSensor(device_name, id_site),
    ]

    # Ajouter les capteurs
    async_add_entities(sensors, update_before_add=True)

    _LOGGER.info("Capteurs ajoutés pour %s", device_name)


class CerboBatterySensor(SensorEntity):
    """Capteur pour la batterie du Cerbo GX."""

    def __init__(self, device_name: str, id_site: str):
        """Initialiser le capteur."""
        self._name = f"{device_name} Battery Percent"
        self._unique_id = f"{device_name}_battery_percent"
        self._state = None
        self._device_class = SensorDeviceClass.BATTERY
        self._unit_of_measurement = "%"
        self._state_topic = f"N/{id_site}/system/0/Batteries"
        _LOGGER.debug("Capteur de batterie initialisé pour %s avec topic %s", device_name, self._state_topic)

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
        _LOGGER.debug("Demande de mise à jour du capteur de batterie %s", self._name)
        pass

    def on_message(self, client, userdata, msg):
        """Gérer la réception de messages MQTT pour la batterie."""
        _LOGGER.debug("Message reçu sur le topic %s", msg.topic)
        
        if msg.topic == self._state_topic:
            try:
                payload = json.loads(msg.payload.decode())
                _LOGGER.debug("Payload reçu pour la batterie : %s", payload)

                # Extraire la valeur 'soc' (state of charge) de la batterie
                self._state = payload.get("soc", None)
                if self._state is not None:
                    _LOGGER.info("État de la batterie mis à jour : %s%%", self._state)
                else:
                    _LOGGER.warning("Clé 'soc' manquante dans le payload de batterie.")
                
                # Mettre à jour l'état dans Home Assistant
                self.schedule_update_ha_state()
            except json.JSONDecodeError:
                _LOGGER.error("Erreur de décodage JSON pour le message de batterie : %s", msg.payload)
            except KeyError as e:
                _LOGGER.error("Clé manquante dans les données de batterie : %s", e)


class CerboVoltageSensor(SensorEntity):
    """Capteur pour la tension du Cerbo GX."""

    def __init__(self, device_name: str, id_site: str):
        """Initialiser le capteur."""
        self._name = f"{device_name} Voltage"
        self._unique_id = f"{device_name}_voltage"
        self._state = None
        self._device_class = SensorDeviceClass.VOLTAGE
        self._unit_of_measurement = "V"
        self._state_topic = f"N/{id_site}/system/0/Voltage"
        _LOGGER.debug("Capteur de tension initialisé pour %s avec topic %s", device_name, self._state_topic)

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
        _LOGGER.debug("Demande de mise à jour du capteur de tension %s", self._name)
        pass

    def on_message(self, client, userdata, msg):
        """Gérer la réception de messages MQTT pour la tension."""
        _LOGGER.debug("Message reçu sur le topic %s", msg.topic)

        if msg.topic == self._state_topic:
            try:
                payload = json.loads(msg.payload.decode())
                _LOGGER.debug("Payload reçu pour la tension : %s", payload)

                # Extraire la valeur 'voltage' (tension)
                self._state = payload.get("voltage", None)
                if self._state is not None:
                    _LOGGER.info("Tension mise à jour : %s V", self._state)
                else:
                    _LOGGER.warning("Clé 'voltage' manquante dans le payload de tension.")

                # Mettre à jour l'état dans Home Assistant
                self.schedule_update_ha_state()
            except json.JSONDecodeError:
                _LOGGER.error("Erreur de décodage JSON pour le message de tension : %s", msg.payload)
            except KeyError as e:
                _LOGGER.error("Clé manquante dans les données de tension : %s", e)


class CerboTemperatureSensor(SensorEntity):
    """Capteur pour la température du Cerbo GX."""

    def __init__(self, device_name: str, id_site: str):
        """Initialiser le capteur."""
        self._name = f"{device_name} Temperature"
        self._unique_id = f"{device_name}_temperature"
        self._state = None
        self._device_class = SensorDeviceClass.TEMPERATURE
        self._unit_of_measurement = "°C"
        self._state_topic = f"N/{id_site}/system/0/Temperature"
        _LOGGER.debug("Capteur de température initialisé pour %s avec topic %s", device_name, self._state_topic)

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
        _LOGGER.debug("Demande de mise à jour du capteur de température %s", self._name)
        pass

    def on_message(self, client, userdata, msg):
        """Gérer la réception de messages MQTT pour la température."""
        _LOGGER.debug("Message reçu sur le topic %s", msg.topic)

        if msg.topic == self._state_topic:
            try:
                payload = json.loads(msg.payload.decode())
                _LOGGER.debug("Payload reçu pour la température : %s", payload)

                # Extraire la valeur 'temperature' (température)
                self._state = payload.get("temperature", None)
                if self._state is not None:
                    _LOGGER.info("Température mise à jour : %s °C", self._state)
                else:
                    _LOGGER.warning("Clé 'temperature' manquante dans le payload de température.")

                # Mettre à jour l'état dans Home Assistant
                self.schedule_update_ha_state()
            except json.JSONDecodeError:
                _LOGGER.error("Erreur de décodage JSON pour le message de température : %s", msg.payload)
            except KeyError as e:
                _LOGGER.error("Clé manquante dans les données de température : %s", e)
