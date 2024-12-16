from homeassistant import config_entries
from homeassistant.core import HomeAssistant
import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import area_registry
from . import DOMAIN

class CerboGXConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gérer un flux de configuration pour Cerbo GX."""

    async def async_step_user(self, user_input=None):
        """Gérer la première étape de l'ajout de l'intégration."""
        if user_input is None:
            # Récupérer la liste des pièces depuis le registre des zones
            area_reg = area_registry.async_get(self.hass)
            areas = [area.name for area in await area_reg.async_list_areas()]

            if not areas:
                return self.async_abort(reason="no_areas_found")  # Pas de zones disponibles

            # Créer un schéma de validation avec les pièces disponibles
            data_schema = vol.Schema({
                vol.Required("device_name"): cv.string,
                vol.Required("cerbo_id"): cv.string,
                vol.Required("room"): vol.In(areas),  # Utiliser les zones dans un menu déroulant
            })

            return self.async_show_form(
                step_id="user",
                data_schema=data_schema
            )

        # Stocker les informations pour l'étape suivante
        device_name = user_input["device_name"]
        cerbo_id = user_input["cerbo_id"]
        room = user_input["room"]

        # Passer à l'étape suivante
        return await self.async_step_credentials(
            user_input={"device_name": device_name, "cerbo_id": cerbo_id, "room": room}
        )

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
                    "device_name": user_input.get("device_name"),
                    "cerbo_id": user_input.get("cerbo_id"),
                    "room": user_input.get("room"),
                }
            )

        # Récupérer les informations des étapes précédentes
        device_name = user_input["device_name"]
        cerbo_id = user_input["cerbo_id"]
        room = user_input["room"]
        username = user_input["username"]
        password = user_input["password"]

        # Trouver l'ID de la zone à partir du nom de la pièce
        area_reg = area_registry.async_get(self.hass)
        areas = await area_reg.async_list_areas()
        area_id = next((area.id for area in areas if area.name == room), None)

        if area_id is None:
            return self.async_abort(reason="area_not_found")

        # Enregistrer directement l'entrée sans tentative de connexion
        return self.async_create_entry(
            title=device_name,
            data={
                "device_name": device_name,
                "cerbo_id": cerbo_id,
                "room": room,
                "username": username,
                "password": password,
                "area_id": area_id,  # Associer l'appareil à la zone
            }
        )
