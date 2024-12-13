from homeassistant import config_entries
from homeassistant.core import HomeAssistant
import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from homeassistant.components.area_registry import area_registry
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

        # Passer à l'étape suivante
        return await self.async_step_area_selection()

    async def async_step_area_selection(self, user_input=None):
        """Gérer la sélection de la pièce où l'appareil sera associé."""
        if user_input is None:
            # Récupérer la liste des pièces disponibles dans Home Assistant
            areas = await self.hass.helpers.area_registry.async_get_registry()

            # Créer une liste des noms de pièces à afficher
            area_choices = {area.name: area.id for area in areas.areas}

            return self.async_show_form(
                step_id="area_selection",
                data_schema=vol.Schema({
                    vol.Required("area"): vol.In(area_choices),
                }),
                description_placeholders={
                    "device_name": self.context.get("device_name"),
                    "cerbo_id": self.context.get("cerbo_id"),
                }
            )

        # Stocker la pièce sélectionnée
        area_id = user_input["area"]
        self.context["area_id"] = area_id

        # Passer à l'étape suivante (si nécessaire)
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
                    "area_id": self.context.get("area_id"),
                }
            )

        # Récupérer les informations des étapes précédentes
        device_name = self.context.get("device_name")
        cerbo_id = self.context.get("cerbo_id")
        username = user_input["username"]
        password = user_input["password"]
        area_id = self.context.get("area_id")

        # Enregistrer directement l'entrée sans tentative de connexion
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
