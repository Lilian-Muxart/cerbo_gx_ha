from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import area_registry
from homeassistant.components.area_registry import AreaRegistry
from homeassistant.components.device_registry import DeviceRegistry
from homeassistant.helpers.entity_registry import async_get_registry
import voluptuous as vol
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
        return await self.async_step_device_creation()

    async def async_step_device_creation(self):
        """Créer l'appareil et l'associer à la pièce choisie."""
        # Récupérer le nom de l'appareil et la pièce
        device_name = self.context["device_name"]
        room = self.context["room"]

        # Trouver l'ID de la zone (pièce) à partir du nom de la pièce
        area_reg = area_registry.async_get(self.hass)
        area_id = None
        for area in area_reg.async_list_areas():
            if area.name == room:
                area_id = area.id
                break

        if not area_id:
            # Si aucune zone trouvée, retourner une erreur
            return self.async_abort(reason="zone_not_found")

        # Créer un nouvel appareil (un device) dans Home Assistant
        device_registry = self.hass.data["device_registry"]
        device_entry = device_registry.async_get_or_create(
            config_entry_id=self.context["entry_id"],
            identifiers={(DOMAIN, self.context["cerbo_id"])},
            name=device_name,
            manufacturer="Cerbo",
            model="GX Device",
        )

        # Créer une entité associée à cet appareil
        entity_registry = await async_get_registry(self.hass)
        entity_registry.async_get_or_create(
            domain=DOMAIN,
            platform=DOMAIN,
            unique_id=self.context["cerbo_id"],
            name=device_name,
            device_id=device_entry.id,
            area_id=area_id  # Associer l'entité à la pièce sélectionnée
        )

        # Passer à l'étape suivante (création de l'entrée)
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

        # Enregistrer l'entrée dans Home Assistant
        return self.async_create_entry(
            title=device_name,
            data={
                "device_name": device_name,
                "cerbo_id": cerbo_id,
                "room": room,
                "username": username,
                "password": password,
            }
        )
