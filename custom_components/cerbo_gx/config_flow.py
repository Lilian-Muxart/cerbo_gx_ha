from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.area_registry import async_get_area_registry
import voluptuous as vol
from . import DOMAIN

class CerboGXConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gérer un flux de configuration pour Cerbo GX."""

    async def async_step_user(self, user_input=None):
        """Gérer la première étape de l'ajout de l'intégration."""
        if user_input is None:
            # Première étape : Demander à l'utilisateur le nom de l'appareil et l'ID du site
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({
                    vol.Required("device_name"): cv.string,
                    vol.Required("cerbo_id"): cv.string,
                })
            )

        # Stocker les informations pour l'étape suivante
        self.context["device_name"] = user_input["device_name"]
        self.context["cerbo_id"] = user_input["cerbo_id"]

        # Passer à l'étape suivante (credentials)
        return await self.async_step_credentials()

    async def async_step_credentials(self, user_input=None):
        """Gérer l'étape où l'utilisateur entre ses informations de connexion."""
        if user_input is None:
            # Demander l'email et le mot de passe
            return self.async_show_form(
                step_id="credentials",
                data_schema=vol.Schema({
                    vol.Required("username"): cv.string,
                    vol.Required("password"): cv.string,
                }),
                description_placeholders={
                    "device_name": self.context.get("device_name"),
                    "cerbo_id": self.context.get("cerbo_id"),
                }
            )

        # Récupérer les informations des étapes précédentes
        device_name = self.context.get("device_name")
        cerbo_id = self.context.get("cerbo_id")
        username = user_input["username"]
        password = user_input["password"]

        # Stocker ces informations et passer à l'étape suivante (sélection de la pièce)
        self.context["username"] = username
        self.context["password"] = password

        return await self.async_step_select_area()

    async def async_step_select_area(self, user_input=None):
        """Permettre à l'utilisateur de choisir une pièce pour l'appareil."""
        if user_input is None:
            # Obtenir la liste des pièces disponibles dans Home Assistant
            area_registry = await async_get_area_registry(self.hass)
            areas = area_registry.async_items()
            area_options = {area.name: area.id for area in areas}

            # Demander à l'utilisateur de sélectionner une pièce
            return self.async_show_form(
                step_id="select_area",
                data_schema=vol.Schema({
                    vol.Required("area_id"): vol.In(area_options),
                }),
                description_placeholders={
                    "device_name": self.context.get("device_name"),
                },
                options={"area_options": area_options}  # Passer les options de pièces
            )

        # Récupérer les informations de la pièce sélectionnée
        area_id = user_input["area_id"]
        device_name = self.context.get("device_name")
        cerbo_id = self.context.get("cerbo_id")
        username = self.context.get("username")
        password = self.context.get("password")

        # Créer l'entrée dans Home Assistant avec les données et l'ID de la pièce
        return self.async_create_entry(
            title=device_name,
            data={
                "device_name": device_name,
                "cerbo_id": cerbo_id,
                "username": username,
                "password": password,
                "area_id": area_id,  # Ajouter l'ID de la pièce sélectionnée
            }
        )
