from homeassistant import config_entries
from homeassistant.core import HomeAssistant
import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import area_registry
from homeassistant.components.area_registry import AreaRegistry
from homeassistant.components.device_registry import async_get as async_get_device_registry
from . import DOMAIN

class CerboGXConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gérer un flux de configuration pour Cerbo GX."""

    async def async_step_user(self, user_input=None):
        """Gérer la première étape de l'ajout de l'intégration."""
        if user_input is None:
            # Récupérer la liste des pièces depuis le registre des zones
            area_reg = area_registry.async_get(self.hass)
            areas = [area.name for area in area_reg.async_list_areas()]

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
        self.context["device_name"] = user_input["device_name"]
        self.context["cerbo_id"] = user_input["cerbo_id"]
        self.context["room"] = user_input["room"]

        # Passer à l'étape suivante
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
                    "room": self.context.get("room"),
                }
            )

        # Récupérer les informations des étapes précédentes
        device_name = self.context.get("device_name")
        cerbo_id = self.context.get("cerbo_id")
        room = self.context.get("room")
        username = user_input["username"]
        password = user_input["password"]

        # Trouver l'ID de la zone à partir du nom de la pièce
        area_reg = area_registry.async_get(self.hass)
        area_id = None
        for area in area_reg.async_list_areas():
            if area.name == room:
                area_id = area.id
                break

        # Créer l'entrée de configuration
        entry = self.async_create_entry(
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

        # Enregistrer l'entrée
        await self.async_set_unique_id(cerbo_id)
        self._abort_if_unique_id_configured()

        # Créer l'appareil dans le registre des appareils
        device_registry = await async_get_device_registry(self.hass)
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, cerbo_id)},
            name=device_name,
            area_id=area_id,  # Lier l'appareil à la zone
        )

        return entry