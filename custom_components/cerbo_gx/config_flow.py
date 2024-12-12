import logging
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .mqtt_client import CerboMQTTClient
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

class CerboGXConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gère le flux de configuration de l'intégration Cerbo GX."""

    def __init__(self):
        """Initialise le flux de configuration."""
        self.device_name = None
        self.cerbo_id = None
        self.username = None
        self.password = None
        self.mqtt_client = None

    async def async_step_user(self, user_input=None):
        """Gère le premier pas du flux de configuration."""

        if user_input is not None:
            self.device_name = user_input["device_name"]
            self.cerbo_id = user_input["cerbo_id"]
            self.username = user_input["username"]
            self.password = user_input["password"]

            # Initialiser la session HTTP pour la récupération du serveur MQTT
            session = async_get_clientsession(self.hass)

            # Initialisation du client MQTT avec les données de configuration
            self.mqtt_client = CerboMQTTClient(
                device_name=self.device_name,
                id_site=self.cerbo_id,
                username=self.username,
                password=self.password,
                session=session
            )

            try:
                # Connexion au serveur MQTT
                await self.mqtt_client.connect()
                _LOGGER.info("Connexion réussie au serveur MQTT pour %s", self.device_name)

                # Si la connexion fonctionne, nous enregistrons l'entrée
                return self.async_create_entry(
                    title=self.device_name,
                    data={
                        "device_name": self.device_name,
                        "cerbo_id": self.cerbo_id,
                        "username": self.username,
                        "password": self.password
                    }
                )

            except Exception as e:
                _LOGGER.error("Échec de la connexion au serveur MQTT: %s", str(e))
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._get_device_info_schema(),
                    errors={"base": "mqtt_connection_error"}
                )

        # Si l'utilisateur n'a pas encore saisi de données, afficher le formulaire
        return self.async_show_form(
            step_id="user",
            data_schema=self._get_device_info_schema()
        )

    def _get_device_info_schema(self):
        """Retourne le schéma pour la saisie des informations de configuration de l'appareil."""
        from homeassistant.helpers import config_validation as cv
        import voluptuous as vol

        return vol.Schema({
            vol.Required("device_name"): str,
            vol.Required("cerbo_id"): str,
            vol.Required("username"): str,
            vol.Required("password"): str,
        })
