from homeassistant.helpers.entity import Entity
from homeassistant.components.mqtt import async_subscribe
from homeassistant.const import STATE_UNKNOWN
import logging
import json

# Configure le logger
_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Configurer le capteur de batterie pour chaque dispositif Cerbo GX."""
    
    # Récupérer le cerbo_id stocké dans hass.data après la configuration
    cerbo_id = hass.data.get("cerbo_id")  # Le cerbo_id est stocké ici après la configuration
    if not cerbo_id:
        _LOGGER.error("cerbo_id non trouvé dans hass.data")
        return

    # Créer le capteur de batterie
    add_entities([BatterySensor(hass, cerbo_id)])


class BatterySensor(Entity):
    """Capteur pour le pourcentage de batterie."""
    
    def __init__(self, hass, cerbo_id):
        """Initialiser le capteur de batterie."""
        self.hass = hass
        self._cerbo_id = cerbo_id
        self._name = f"Battery Percent {self._cerbo_id}"
        self._state = STATE_UNKNOWN
        self._topic = f"N/{self._cerbo_id}/system/0/Batteries"

    @property
    def name(self):
        """Retourne le nom du capteur."""
        return self._name
    
    @property
    def state(self):
        """Retourne l'état (pourcentage de batterie) du capteur."""
        return self._state
    
    @property
    def device_class(self):
        """Retourne la classe du capteur (ici une batterie)."""
        return "battery"
    
    @property
    def unit_of_measurement(self):
        """Retourne l'unité de mesure (pourcentage)."""
        return "%"

    async def async_added_to_hass(self):
        """Abonnez-vous au topic MQTT lorsque le capteur est ajouté."""
        await self.hass.components.mqtt.async_subscribe(self._topic, self._message_received)

    def _message_received(self, msg):
        """Traitement du message reçu."""
        try:
            payload = json.loads(msg.payload)
            # Extraire la valeur du SOC à partir du payload JSON
            battery_percent = payload['value'][0].get('soc', None)
            if battery_percent is not None:
                # Appliquer le value_template et arrondir
                self._state = round(battery_percent, 0)
                self.async_write_ha_state()  # Met à jour l'état de l'entité dans Home Assistant
            else:
                _LOGGER.error("Valeur 'soc' non trouvée dans le message reçu.")
        except (json.JSONDecodeError, KeyError) as e:
            _LOGGER.error(f"Erreur de traitement du message MQTT: {e}")
            self._state = STATE_UNKNOWN
            self.async_write_ha_state()  # Met à jour l'état en cas d'erreur

