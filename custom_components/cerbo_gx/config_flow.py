from .mqtt_client import CerboMQTTClient

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
        self.context["device_name"] = user_input["device_name"]
        self.context["cerbo_id"] = user_input["cerbo_id"]

        return self.async_show_form(
            step_id="credentials",
            data_schema=vol.Schema({
                vol.Required("username"): cv.string,
                vol.Required("password"): cv.string,
            }),
            description_placeholders={"device_name": self.context["device_name"], "cerbo_id": self.context["cerbo_id"]}
        )

    async def async_step_credentials(self, user_input):
        """Gérer l'étape où l'utilisateur entre ses informations de connexion."""
        device_name = self.context["device_name"]
        cerbo_id = self.context["cerbo_id"]
        username = user_input["username"]
        password = user_input["password"]

        # Tenter de se connecter au serveur MQTT
        try:
            # Initialiser le client MQTT
            mqtt_client = CerboMQTTClient(
                device_name=device_name,
                id_site=cerbo_id,
                username=username,
                password=password,
                session=None  # Pas besoin d'une session HTTP dans ce contexte
            )

            # Essayer la connexion
            await mqtt_client.connect()

            # Déconnexion propre après validation
            await mqtt_client.disconnect()

            # Si la connexion réussit, créer l'entrée de configuration
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
            _LOGGER.error("Erreur de connexion au serveur MQTT : %s", str(e))
            # Retourner le formulaire avec une erreur
            return self.async_show_form(
                step_id="credentials",
                data_schema=vol.Schema({
                    vol.Required("username"): cv.string,
                    vol.Required("password"): cv.string,
                }),
                errors={"base": "cannot_connect"}
            )
