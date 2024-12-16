import logging
import json
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.components.sensor import SensorDeviceClass
from . import DOMAIN
from .mqtt_client import CerboMQTTClient  # Importer le client MQTT

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistantType, entry, async_add_entities) -> None:
    """Configurer les capteurs pour une entrée donnée."""
    device_name = entry.data["device_name"]
    id_site = entry.data["cerbo_id"]
    username = entry.data["username"]
    password = entry.data["password"]

    _LOGGER.info(
        "Initialisation des capteurs pour le dispositif %s avec l'ID de site %s", device_name, id_site
    )

    # Créer le client MQTT
    mqtt_client = CerboMQTTClient(device_name, id_site, username, password, hass)

    # Liste des capteurs à ajouter
    sensors = [
        CerboBatterySensor(device_name, id_site, mqtt_client),
        CerboVoltageSensor(device_name, id_site, mqtt_client),
        CerboTemperatureSensor(device_name, id_site, mqtt_client),
    ]

    # Ajouter les capteurs à Home Assistant
    async_add_entities(sensors, update_before_add=True)

    _LOGGER.info("Capteurs ajoutés pour %s", device_name)


class CerboBaseSensor(SensorEntity):
    """Classe de base pour les capteurs du Cerbo GX."""

    def __init__(self, device_name: str, id_site: str, mqtt_client: CerboMQTTClient, state_topic: str, value_key: str):
        """Initialiser le capteur."""
        self._device_name = device_name
        self._id_site = id_site
        self._state = None
        self._mqtt_client = mqtt_client  # Utiliser le client MQTT pour gérer les messages
        self._state_topic = state_topic
        self._value_key = value_key  # Clé spécifique pour extraire la valeur du message
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
        await self._mqtt_client.connect()
        self._mqtt_client.add_subscriber(self)  # Inscrire le capteur comme abonné
        self._mqtt_client.client.subscribe(self._state_topic)

    def on_mqtt_message(self, client, userdata, msg):
        """Gérer les messages MQTT reçus."""
        try:
            payload = json.loads(msg.payload)
            value = self._extract_value(payload)
            if value is not None:
                self._state = value
                self.async_write_ha_state()  # Mettre à jour l'état de l'entité
        except Exception as e:
            _LOGGER.error("Erreur de traitement du message MQTT: %s", e)

    def _extract_value(self, payload: dict):
        """Extraire la valeur en fonction de la clé spécifique."""
        # Vérifiez si "value" existe et contient des éléments
        if "value" in payload and isinstance(payload["value"], list) and len(payload["value"]) > 0:
            # Extraire la première entrée de la liste (la batterie)
            sensor_data = payload["value"][0]
            # Extraire la valeur en fonction de la clé spécifique
            if self._value_key in sensor_data:
                return sensor_data[self._value_key]  # Retourner la valeur sous la clé spécifiée
        return None

    @property
    def state(self):
        return self._state


class CerboBatterySensor(CerboBaseSensor):
    """Capteur pour la batterie du Cerbo GX."""

    def __init__(self, device_name: str, id_site: str, mqtt_client: CerboMQTTClient):
        state_topic = f"N/{id_site}/system/0/Batteries"
        value_key = "soc"  # Nous voulons extraire la charge de la batterie
        super().__init__(device_name, id_site, mqtt_client, state_topic, value_key)
        self._attr_name = f"{device_name} Battery"
        self._attr_unique_id = f"{id_site}_battery_percent"
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
