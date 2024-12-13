from homeassistant import config_entries
from homeassistant.helpers import area_registry
import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN, CONF_DEVICE_NAME, CONF_CERBO_ID, CONF_ROOM, CONF_USERNAME, CONF_PASSWORD

class CerboGXConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gérer un flux de configuration pour Cerbo GX."""

    async def async_step_user(self, user_input=None):
        """Gérer la première étape de l'ajout de l'intégration."""
        if user_input is None:
            # Récupérer la liste des pièces depuis le registre des zones
            area_reg = area_registry.async_get(self.hass)
            areas = [area.name for area in area_reg.async_list_areas()]

            if not areas:
                return self.async_abort(reason="no_areas")  # Si aucune zone n'est disponible

            # Créer un schéma de validation avec les pièces disponibles
            data_schema = vol.Schema({
                vol.Required(CONF_DEVICE_NAME): cv.string,
                vol.Required(CONF_CERBO_ID): cv.string,
                vol.Required(CONF_ROOM): vol.In(areas),  # Utiliser les zones dans un menu déroulant
            })

            return self.async_show_form(
                step_id="user",
                data_schema=data_schema
            )

        # Stocker les informations pour l'étape suivante
        self.context[CONF_DEVICE_NAME] = user_input[CONF_DEVICE_NAME]
        self.context[CONF_CERBO_ID] = user_input[CONF_CERBO_ID]
        self.context[CONF_ROOM] = user_input[CONF_ROOM]

        # Passer à l'étape suivante
        return await self.async_step_credentials()

    async def async_step_credentials(self, user_input=None):
        """Gérer l'étape où l'utilisateur entre ses informations de connexion."""
        if user_input is None:
            # Demander l'email et le mot de passe
            return self.async_show_form(
                step_id="credentials",
                data_schema=vol.Schema({
                    vol.Required(CONF_USERNAME): cv.string,
                    vol.Required(CONF_PASSWORD): cv.string,
                }),
                description_placeholders={
                    "device_name": self.context.get(CONF_DEVICE_NAME),
                    "cerbo_id": self.context.get(CONF_CERBO_ID),
                    "room": self.context.get(CONF_ROOM),
                }
            )

        # Récupérer les informations des étapes précédentes
        device_name = self.context.get(CONF_DEVICE_NAME)
        cerbo_id = self.context.get(CONF_CERBO_ID)
        room = self.context.get(CONF_ROOM)
        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]

        # Créer une nouvelle entrée de configuration
        entry = self.async_create_entry(
            title=device_name,
            data={
                CONF_DEVICE_NAME: device_name,
                CONF_CERBO_ID: cerbo_id,
                CONF_ROOM: room,
                CONF_USERNAME: username,
                CONF_PASSWORD: password,
            }
        )