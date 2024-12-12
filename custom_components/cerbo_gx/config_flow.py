from homeassistant import config_entries
from homeassistant.core import HomeAssistant
import voluptuous as vol
from homeassistant.helpers import config_validation as cv
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

        # Si l'utilisateur a fourni le nom et l'ID du site, passez à l'étape suivante
        device_name = user_input["device_name"]
        cerbo_id = user_input["cerbo_id"]

        # Deuxième étape : Demander l'email et le mot de passe
        return self.async_show_form(
            step_id="credentials",
            data_schema=vol.Schema({
                vol.Required("username"): cv.string,
                vol.Required("password"): cv.string,
            }),
            description_placeholders={"device_name": device_name, "cerbo_id": cerbo_id}
        )

    async def async_step_credentials(self, user_input):
        """Gérer l'étape où l'utilisateur entre ses informations de connexion."""
        device_name = self.context.get("device_name")
        cerbo_id = self.context.get("cerbo_id")
        username = user_input["username"]
        password = user_input["password"]

        # Valider et connecter au serveur MQTT ici
        try:
            # Créer et connecter le client MQTT ici
            # Exemple : mqtt_client = CerboMQTTClient(...)
            # Essayer de se connecter au serveur MQTT
            # Si la connexion réussie, enregistrez l'entrée
            return self.async_create_entry(
                title=device_name,
                data={
                    "device_name": device_name,
                    "cerbo_id": cerbo_id,
                    "username": username,
                    "password": password,
                }
            )
        except Exception as e:
            # Gérer l'échec de la connexion
            return self.async_show_form(
                step_id="credentials",
                errors={"base": "cannot_connect"}
            )

