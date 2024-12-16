import logging
import json
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.components.sensor import SensorDeviceClass
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistantType, entry, async_add_entities) -> None:
    """Configurer les capteurs pour une entrée donnée."""
    device_name = entry.data["device_name"]
    id_site = entry.data["cerbo_id"]

    _LOGGER.info(
        "Initialisation des capteurs pour le dispositif %s avec l'ID de site %s", device_name, id_site
    )

    # Liste des capteurs à ajouter
    sensors = [
        CerboBatterySensor(device_name, id_site),
        CerboVoltageSensor(device_name, id_site),
        CerboTemperatureSensor(device_name, id_site),
    ]

    # Ajouter les capteurs à Home Assistant
    async_add_entities(sensors, update_before_add=True)

    _LOGGER.info("Capteurs ajoutés pour %s", device_name)


class CerboBaseSensor(SensorEntity):
    """Classe de base pour les capteurs du Cerbo GX."""

    def __init__(self, device_name: str, id_site: str):
        """Initialiser le capteur."""
        self._device_name = device_name
        self._id_site = id_site
        self._state = None
        self._attr_device_info = {
            "identifiers": {(DOMAIN, id_site)},
            "name": device_name,
            "manufacturer": "Victron Energy",
            "model": "Cerbo GX",
        }

    async def async_added_to_hass(self):
        """Abonnez-vous aux messages MQTT lorsque l'entité est ajoutée."""
        _LOGGER.info("Abonnement au topic MQTT pour %s", self._attr_name)
        # Abonnement au topic MQTT pour recevoir les données
        await self._subscribe_to_mqtt()

    async def _subscribe_to_mqtt(self):
        """S'abonner aux messages MQTT et traiter les mises à jour."""
        # Exemple de gestion de l'abonnement
        async def mqtt_message_received(msg):
            """Gérer les messages MQTT reçus."""
            payload = json.loads(msg.payload)
            if "value" in payload:
                self._state = payload["value"]
                self.async_write_ha_state()  # Mettre à jour l'état de l'entité

        # Exemple d'abonnement, à adapter en fonction de la structure de ton MQTT
        topic = self._state_topic  # Utilise le topic spécifique pour chaque capteur
        await self.hass.components.mqtt.async_subscribe(topic, mqtt_message_received)


class CerboBatterySensor(CerboBaseSensor):
    """Capteur pour la batterie du Cerbo GX."""

    def __init__(self, device_name: str, id_site: str):
        super().__init__(device_name, id_site)
        self._attr_name = f"{device_name} Battery"
        self._attr_unique_id = f"{id_site}_battery_percent"
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_native_unit_of_measurement = "%"
        self._state_topic = f"N/{id_site}/system/0/Battery"

    @property
    def state(self):
        return self._state


class CerboVoltageSensor(CerboBaseSensor):
    """Capteur pour la tension du Cerbo GX."""

    def __init__(self, device_name: str, id_site: str):
        super().__init__(device_name, id_site)
        self._attr_name = f"{device_name} Voltage"
        self._attr_unique_id = f"{id_site}_voltage"
        self._attr_device_class = SensorDeviceClass.VOLTAGE
        self._attr_native_unit_of_measurement = "V"
        self._state_topic = f"N/{id_site}/system/0/Voltage"

    @property
    def state(self):
        return self._state


class CerboTemperatureSensor(CerboBaseSensor):
    """Capteur pour la température du Cerbo GX."""

    def __init__(self, device_name: str, id_site: str):
        super().__init__(device_name, id_site)
        self._attr_name = f"{device_name} Temperature"
        self._attr_unique_id = f"{id_site}_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = "°C"
        self._state_topic = f"N/{id_site}/system/0/Temperature"

    @property
    def state(self):
        return self._state
