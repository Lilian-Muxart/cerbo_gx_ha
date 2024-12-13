import logging
from homeassistant import config_entries
from homeassistant.const import CONF_ID, CONF_NAME, CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers import selector
from .const import DOMAIN
from . import _get_vrm_broker_url  # Importer la fonction que nous allons définir ci-dessous

_LOGGER = logging.getLogger(__name__)

class VictronConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a configuration flow for Victron integration."""

    VERSION = 1

    def __init__(self):
        self.id_site = None
        self.device_name = None
        self.room = None
        self.email = None
        self.password = None

    async def async_step_user(self, user_input=None):
        """Handle the user input in the configuration flow."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=self._get_data_schema())

        # Enregistrez les informations d'entrée de l'utilisateur
        self.device_name = user_input[CONF_NAME]
        self.id_site = user_input[CONF_ID]
        self.room = user_input.get("room")
        self.email = user_input[CONF_EMAIL]
        self.password = user_input[CONF_PASSWORD]

        # Connexion au serveur MQTT
        broker_url = self._get_vrm_broker_url(self.id_site)
        _LOGGER.info(f"Connecting to MQTT broker: {broker_url}")
        # Connectez-vous au broker MQTT ici

        return self.async_create_entry(
            title=self.device_name,
            data={
                CONF_NAME: self.device_name,
                CONF_ID: self.id_site,
                "room": self.room,
                CONF_EMAIL: self.email,
                CONF_PASSWORD: self.password,
                "mqtt_broker": broker_url,
            },
        )

    def _get_data_schema(self):
        """Retourne un schéma de formulaire pour l'entrée utilisateur."""
        return {
            vol.Required(CONF_NAME): str,
            vol.Required(CONF_ID): str,
            vol.Required("room"): selector.selector(
                {
                    "select": {
                        "options": ["Living Room", "Kitchen", "Bedroom", "Bathroom"]  # Liste des pièces
                    }
                }
            ),
            vol.Required(CONF_EMAIL): str,
            vol.Required(CONF_PASSWORD): str,
        }

    def _get_vrm_broker_url(self, id_site):
        """Calculer l'URL du serveur MQTT basé sur l'ID du site."""
        sum = 0
        for character in id_site.lower().strip():
            sum += ord(character)
        broker_index = sum % 128
        return f"mqtt{broker_index}.victronenergy.com"
