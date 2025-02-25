import logging
import json
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.components.sensor import SensorDeviceClass
from .mqtt_client import CerboMQTTClient  # Client MQTT importé (à définir dans mqtt_client.py)
from homeassistant.core import HomeAssistant
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistantType, entry, async_add_entities) -> None:
    """Configurer les switchs pour une entrée donnée."""
    device_name = entry.data["device_name"]
    id_site = entry.data["cerbo_id"]

    # Récupérer le client MQTT initialisé dans __init__.py
    mqtt_client = hass.data[DOMAIN][entry.entry_id]["mqtt_client"]

    # Vérifier que le client est disponible
    if not mqtt_client:
        _LOGGER.error("Le client MQTT n'est pas disponible pour %s", device_name)
        return

    _LOGGER.info(
        "Initialisation des switchs pour le dispositif %s avec l'ID de site %s", device_name, id_site
    )

    # Liste des switchs à ajouter
    switches = [
        CerboRelaySwitch(device_name, id_site, mqtt_client, 0),
        CerboRelaySwitch(device_name, id_site, mqtt_client, 1),
    ]

    # Ajouter les switchs à Home Assistant
    async_add_entities(switches, update_before_add=True)

    _LOGGER.info("Switchs ajoutés pour %s", device_name)


class CerboBaseSensor:
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


class CerboRelaySwitch(CerboBaseSensor, SwitchEntity):
    """Switch pour contrôler les relais du Cerbo GX."""
    
    def __init__(self, device_name: str, id_site: str, mqtt_client: CerboMQTTClient, relay_id: int):
        # Définir les topics pour l'état du relais et la commande
        state_topic = f"N/{id_site}/system/0/Relay/{relay_id}/State"
        command_topic = f"W/{id_site}/system/0/Relay/{relay_id}/State"
        value_key = ""  # Pas de clé spécifique pour l'état du relais
        
        super().__init__(device_name, id_site, mqtt_client, state_topic, value_key)
        
        self._relay_id = relay_id
        self._command_topic = command_topic
        
        # Attributs pour la classe switch
        self._attr_name = f"{device_name} Relay {relay_id} Switch"
        self._attr_unique_id = f"{id_site}_relay_{relay_id}_switch"
        self._attr_device_class = "switch"  # Définir le type comme switch
        self._attr_native_unit_of_measurement = ""
        self._attr_is_read_only = False  # L'état peut être modifié
    
    def turn_on(self):
        """Action pour allumer le relais (mettre à 1)."""
        payload = json.dumps({"value": 1})
        self._mqtt_client.publish(self._command_topic, payload)
        _LOGGER.info(f"Commande envoyée au topic {self._command_topic}: {payload}")

    def turn_off(self):
        """Action pour éteindre le relais (mettre à 0)."""
        payload = json.dumps({"value": 0})
        self._mqtt_client.publish(self._command_topic, payload)
        _LOGGER.info(f"Commande envoyée au topic {self._command_topic}: {payload}")

    def update_state(self, message: str):
        """Mettre à jour l'état du switch en fonction du message reçu sur le topic d'état."""
        if message == "1":
            self._attr_native_value = True  # Le relais est activé
        elif message == "0":
            self._attr_native_value = False  # Le relais est désactivé
        _LOGGER.info(f"État mis à jour: {self._attr_native_value} pour {self._attr_name}")

    async def async_update(self):
        """Mettre à jour l'état du switch en fonction du message reçu."""
        if self._state is not None:
            self.update_state(str(self._state))


class CerboRelaySensor(CerboBaseSensor):
    """Capteur pour l'état des relais du Cerbo GX."""
    
    def __init__(self, device_name: str, id_site: str, mqtt_client: CerboMQTTClient):
        state_topic = f"N/{id_site}/system/0/Relay/0/State"
        value_key = ""  # Définir la clé de valeur pour l'état du relais
        
        super().__init__(device_name, id_site, mqtt_client, state_topic, value_key)
        
        self._attr_name = f"{device_name} Relay State"
        self._attr_unique_id = f"{id_site}_relay_state"
        self._attr_device_class = SensorDeviceClass.RELAY
        self._attr_native_unit_of_measurement = ""
        self._attr_is_read_only = True  # Indique que l'état est en lecture seule


class CerboRelaySensor2(CerboBaseSensor):
    """Capteur pour l'état des relais du Cerbo GX."""
    
    def __init__(self, device_name: str, id_site: str, mqtt_client: CerboMQTTClient):
        state_topic = f"N/{id_site}/system/0/Relay/1/State"
        value_key = ""  # Définir la clé de valeur pour l'état du relais
        
        super().__init__(device_name, id_site, mqtt_client, state_topic, value_key)
        
        self._attr_name = f"{device_name} Relay State 2"
        self._attr_unique_id = f"{id_site}_relay_state_2"
        self._attr_device_class = SensorDeviceClass.RELAY
        self._attr_native_unit_of_measurement = ""
        self._attr_is_read_only = True  # Indique que l'état est en lecture seule
