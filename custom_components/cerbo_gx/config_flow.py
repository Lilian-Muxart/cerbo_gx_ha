from homeassistant import config_entries
from homeassistant.core import HomeAssistant
import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.area_registry import AreaRegistry  # Utiliser AreaRegistry
from . import DOMAIN


class CerboGXConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gérer un flux de configuration pour Cerbo GX."""

    async def async_step_user(self, user_input=None):
        """Gérer la première étape de l'ajout de l'intégration."""
        if user_input is None:
            # Créer l'instance de AreaRegistry
            area_registry = AreaRegistry(self.hass)

            # Liste des zones
            areas = list(area_registry.areas.values())  # Convertir en liste
            area_names = [area.name for area in areas]  # Extraire les noms des zones

            # Créer un schéma de validation avec les pièces disponibles
            data_schema = vol.Schema({
                vol.Required("device_name"): cv.string,
                vol.Required("cerbo_id"): cv.string,
                vol.Optional("room", default=""): vol.In(area_names),  # Menu déroulant avec les zones
            })

            return self.async_show_form(
                step_id="user",
                data_schema=data_schema
            )

        # Stocker les informations pour l'étape suivante
        self.context["device_name"] = user_input["device_name"]
        self.context["cerbo_id"] = user_input["cerbo_id"]
        self.context["room"] = user_input.get("room")

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
                    "room": self.context.get("room") or "Non spécifiée",
                }
            )

        # Récupérer les informations des étapes précédentes
        device_name = self.context.get("device_name")
        cerbo_id = self.context.get("cerbo_id")
        room = self.context.get("room")
        username = user_input["username"]
        password = user_input["password"]

        # Trouver l'ID de la zone à partir du nom de la pièce
        area_id = None
        if room:
            area_registry = AreaRegistry(self.hass)
            areas = list(area_registry.areas.values())  # Convertir en liste
            area_id = next(
                (area.id for area in areas if area.name == room), None
            )

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