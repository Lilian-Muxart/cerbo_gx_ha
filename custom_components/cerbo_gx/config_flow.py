import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import DOMAIN, CONF_DEVICE_NAME, CONF_DEVICE_ID, CONF_EMAIL, CONF_PASSWORD, CONF_ROOM

class MyIntegrationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Validate user_input here if necessary
            return self.async_create_entry(title=user_input[CONF_DEVICE_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_DEVICE_NAME): str,
                vol.Required(CONF_DEVICE_ID): str,
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_ROOM): selector({
                    "area": {}
                }),
            }),
            errors=errors,
        )

    async def async_step_import(self, user_input=None):
        return await self.async_step_user(user_input)
