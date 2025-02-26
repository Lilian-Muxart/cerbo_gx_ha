import logging
import json
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.core import HomeAssistant
from .mqtt_client import CerboMQTTClient  # Votre client MQTT
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistantType, entry, async_add_entities) -> None:
    """Configurer les switches pour une entrée donnée."""
    device_name = entry.data["device_name"]
    id_site = entry.data["cerbo_id"]

    # Récupérer le client MQTT initialisé dans __init__.py
    mqtt_client = hass.data[DOMAIN][entry.entry_id]["mqtt_client"]

    if not mqtt_client:
        _LOGGER.error("Le client MQTT n'est pas disponible pour %s", device_name)
        return

    _LOGGER.info(
        "Initialisation des switches pour le dispositif %s avec l'ID de site %s", device_name, id_site
    )

    switches = [
        CerboRelaySwitch(device_name, id_site, mqtt_client, 0),
        CerboRelaySwitch(device_name, id_site, mqtt_client, 1),
    ]

    async_add_entities(switches, update_before_add=True)

    _LOGGER.info("Switchs ajoutés pour %s", device_name)

class CerboRelaySwitch(SwitchEntity):
    """Classe représentant un switch pour le contrôle des relais."""

    def __init__(self, device_name: str, id_site: str, mqtt_client: CerboMQTTClient, relay_index: int):
        self._device_name = device_name
        self._id_site = id_site
        self._mqtt_client = mqtt_client
        self._relay_index = relay_index
        self._state = False  # Par défaut, l'état du relais est éteint

        self._attr_name = f"{device_name} Relay {relay_index + 1}"
        self._attr_unique_id = f"{id_site}_relay_{relay_index}"
        self._attr_is_on = False

    async def async_added_to_hass(self):
        """S'abonner au topic MQTT pour le relais à l'initialisation."""
        _LOGGER.info(f"Abonnement au topic MQTT pour le relais {self._relay_index + 1}")
        state_topic = f"R/{self._id_site}/system/0/Relay/{self._relay_index}/State"
        self._mqtt_client.add_subscription(state_topic, self.on_mqtt_message)

    async def async_will_remove_from_hass(self):
        """Désabonnement lors de la suppression de l'entité."""
        _LOGGER.info(f"Désabonnement du topic MQTT pour le relais {self._relay_index + 1}")
        state_topic = f"R/{self._id_site}/system/0/Relay/{self._relay_index}/State"
        self._mqtt_client.remove_subscription(state_topic, self.on_mqtt_message)

    def on_mqtt_message(self, client, userdata, msg):
        """Gestion des messages MQTT pour l'état du relais."""
        try:
            if not msg.payload:
                _LOGGER.warning("Message vide reçu sur le topic %s", msg.topic)
                return

            payload = json.loads(msg.payload)
            value = payload.get("value", None)
            if value is not None:
                self._state = (value == 1)
                self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)
        
        except json.JSONDecodeError as e:
            _LOGGER.error(f"Erreur de décodage du message JSON sur le topic {msg.topic}: {e}")
        except Exception as e:
            _LOGGER.error(f"Erreur lors du traitement du message : {e}")

    @property
    def is_on(self) -> bool:
        """Retourne l'état actuel du relais."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Active le relais (envoie la trame MQTT avec value=1)."""
        _LOGGER.info(f"Activation du relais {self._relay_index + 1} pour {self._device_name}")
        payload = json.dumps({"value": 1})
        state_topic = f"W/{self._id_site}/system/0/Relay/{self._relay_index}/State"
        self._mqtt_client.publish(state_topic, payload)
        self._state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Désactive le relais (envoie la trame MQTT avec value=0)."""
        _LOGGER.info(f"Désactivation du relais {self._relay_index + 1} pour {self._device_name}")
        payload = json.dumps({"value": 0})
        state_topic = f"W/{self._id_site}/system/0/Relay/{self._relay_index}/State"
        self._mqtt_client.publish(state_topic, payload)
        self._state = False
        self.async_write_ha_state()