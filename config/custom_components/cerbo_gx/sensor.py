from homeassistant.helpers.entity import Entity

class MonAppareilEntity(Entity):
    """Represent a Mon Appareil entity."""

    def __init__(self, name: str):
        """Initialize the entity."""
        self._name = name
        self._state = "Connecté"

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def state(self):
        """Return the state of the entity."""
        return self._state
