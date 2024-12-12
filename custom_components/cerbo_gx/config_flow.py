import voluptuous as vol
from homeassistant import config_entries
from . import DOMAIN

class CerboGXConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cerbo GX."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            username = user_input["username"]
            password = user_input["password"]
            cerbo_id = user_input["cerbo_id"]

            # Validate the Cerbo ID and credentials
            try:
                from .mqtt_client import fetch_mqtt_server
                mqtt_data = await fetch_mqtt_server(cerbo_id, username, password)
                return self.async_create_entry(title=f"Cerbo GX {cerbo_id}", data={
                    "cerbo_id": cerbo_id,
                    "username": username,
                    "password": password,
                    "mqtt_server": mqtt_data["server"],
                    "mqtt_user": mqtt_data["user"],
                    "mqtt_password": mqtt_data["password"],
                })
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                "username": str,
                "password": str,
                "cerbo_id": str
            }),
            errors=errors
        )
