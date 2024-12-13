from homeassistant.core import HomeAssistant

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Victron integration."""
    hass.data["victron_integration"] = {}
    return True
