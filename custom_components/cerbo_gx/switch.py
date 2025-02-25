import logging
import json
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.core import HomeAssistant
from .mqtt_client import CerboMQTTClient  # Client MQTT à définir dans mqtt_client.py
from .. import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistantType, entry, async_add_entities) -> None:
    """Configurer les interrupteurs pour une entrée donnée."""
    device_name = entry.data["device_name"]
    id_site = entry.data["cerbo_id"]

    # Récupérer le client MQTT initialisé dans __init__.py
    mqtt_client: CerboMQTTClient = hass.data[DOMAIN][entry.entry_id]["mqtt_client"]

    if not mqtt_client:
        _LOGGER.error("Le client MQTT n'est pas disponible pour %s", device_name)
        return

    _LOGGER.info("Initialisation des interrupteurs pour le dispositif %s avec l'ID de site %s", device_name, id_site)

    # Création des interrupteurs pour les relais souhaités
    switches = [
        CerboRelayInterrupteur(device_name, id_site, mqtt_client, 0),
        CerboRelayInterrupteur(device_name, id_site, mqtt_client, 1),
    ]

    async_add_entities(switches, update_before_add=True)
    _LOGGER.info("Interrupteurs ajoutés pour %s", device_name)


class CerboRelayInterrupteur(SwitchEntity):
    """Interrupteur pour contrôler l'état des relais du Cerbo GX."""

    def __init__(self, device_name: str, id_site: str, mqtt_client: CerboMQTTClient, relay_number: int):
        self._device_name = device_name
        self._id_site = id_site
        self._relay_number = relay_number
        self._mqtt_client = mqtt_client
        self._state = False  # État initial : OFF
        self._state_topic = f"N/{id_site}/system/0/Relay/{relay_number}/State"  # Pour recevoir l'état
        self._command_topic = f"W/{id_site}/system/0/Relay/{relay_number}/State"  # Pour envoyer les commandes
        self._attr_device_info = {
            "identifiers": {(DOMAIN, id_site)},
            "name": device_name,
            "manufacturer": "Victron Energy",
            "model": "Cerbo GX",
        }
        self._attr_name = f"{device_name} Relay {relay_number} Interrupteur"
        self._attr_unique_id = f"{id_site}_relay_inter_{relay_number}"
        self._attr_icon = "mdi:power"
        self._attr_is_on = False

    async def async_added_to_hass(self):
        """S'abonner au topic MQTT lors de l'ajout de l'entité."""
        _LOGGER.info("Abonnement au topic MQTT pour %s", self._attr_name)
        self._mqtt_client.add_subscription(self._state_topic, self.on_mqtt_message)

    async def async_will_remove_from_hass(self):
        """Se désabonner du topic MQTT lors du retrait de l'entité."""
        _LOGGER.info("Désabonnement du topic MQTT pour %s", self._attr_name)
        self._mqtt_client.remove_subscription(self._state_topic, self.on_mqtt_message)

    def on_mqtt_message(self, client, userdata, msg):
        """Traiter le message MQTT reçu pour mettre à jour l'état."""
        try:
            if not msg.payload:
                _LOGGER.warning("Message vide reçu sur le topic %s", msg.topic)
                return

            payload = json.loads(msg.payload)
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
        """Retourne True si l'interrupteur est activé."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Active l'interrupteur et envoie la commande MQTT correspondante."""
        _LOGGER.info(f"Activation de l'interrupteur du relais {self._relay_number}")
        payload = json.dumps({"value": 1})
        # Optimistic update : on met à jour l'état local immédiatement
        self._state = True
        self._attr_is_on = True
        self.async_write_ha_state()
        self._mqtt_client.publish(self._command_topic, payload)

    async def async_turn_off(self, **kwargs):
        """Désactive l'interrupteur et envoie la commande MQTT correspondante."""
        _LOGGER.info(f"Désactivation de l'interrupteur du relais {self._relay_number}")
        payload = json.dumps({"value": 0})
        self._state = False
        self._attr_is_on = False
        self.async_write_ha_state()
        self._mqtt_client.publish(self._command_topic, payload)
