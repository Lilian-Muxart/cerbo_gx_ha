from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_NAME, CONF_ID, CONF_USERNAME, CONF_PASSWORD
import logging

_LOGGER = logging.getLogger(__name__)

class MQTTClientConfigFlow(config_entries.ConfigFlow, domain="mqtt_client"):
    """Handle a config flow for MQTT Client."""

    def __init__(self):
        """Initialize the config flow."""
        self._user_input = {}

    async def async_step_user(self, user_input=None):
        """Handle the user step."""
        if user_input is not None:
            # Sauvegarder les informations fournies par l'utilisateur
            self._user_input = user_input
            # Créer une entrée de configuration pour cet appareil
            return self.async_create_entry(
                title=user_input[CONF_NAME], 
                data=user_input
            )

        # Demander les informations à l'utilisateur (nom, id_site, email, mot de passe)
        return self.async_show_form(
            step_id="user", 
            data_schema=self._get_schema()
        )

    def _get_schema(self):
        """Retourne le schéma de la configuration."""
        from homeassistant.helpers import config_validation as cv
        import voluptuous as vol

        return vol.Schema({
            vol.Required(CONF_NAME): str,
            vol.Required(CONF_ID): str,
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str
        })
