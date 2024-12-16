import paho.mqtt.client as mqtt
import ssl
import os
import asyncio

class CerboMQTTClient:
    def __init__(self, id_site, client_id=None, username=None, password=None):
        """Initialisation du client MQTT."""
        self.id_site = id_site
        self.client = mqtt.Client(client_id)
        self.username = username
        self.password = password
        
        # Calculer l'URL du broker basé sur l'ID du site
        self.broker_url = self._get_vrm_broker_url()

        # Configuration de l'authentification MQTT (si les informations sont disponibles)
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        
        # Spécification du chemin du certificat CA par défaut
        self.ca_cert_path = os.path.join(os.path.dirname(__file__), "venus-ca.crt")
        
        # Vérification de l'existence du certificat
        if os.path.exists(self.ca_cert_path):
            # Assurez-vous que tls_set est exécuté dans un thread séparé pour ne pas bloquer Home Assistant
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, self._configure_tls)
        else:
            raise FileNotFoundError(f"Le certificat CA n'a pas été trouvé à l'emplacement : {self.ca_cert_path}")
        
    def _configure_tls(self):
        """Configurer la connexion sécurisée dans un thread séparé."""
        self.client.tls_set(ca_certs=self.ca_cert_path, certfile=None, keyfile=None, tls_version=ssl.PROTOCOL_TLSv1_2)

    def _get_vrm_broker_url(self):
        """Calculer l'URL du serveur MQTT basé sur l'ID du site."""
        sum = 0
        for character in self.id_site.lower().strip():
            sum += ord(character)
        broker_index = sum % 128
        return f"mqtt{broker_index}.victronenergy.com"

    def connect(self):
        """Connexion au broker MQTT (asynchrone)."""
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self._connect_sync)

    def _connect_sync(self):
        """Connexion synchrone au broker MQTT (exécutée dans un thread séparé)."""
        self.client.connect(self.broker_url, 8883)
        self.client.loop_start()  # Lance la boucle dans un thread séparé pour ne pas bloquer

    def disconnect(self):
        """Déconnexion et arrêt de la boucle."""
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self._disconnect_sync)

    def _disconnect_sync(self):
        """Déconnexion synchrone du broker MQTT."""
        self.client.loop_stop()  # Arrêter la boucle
        self.client.disconnect()
        
    def add_subscriber(self, subscriber):
        """Ajouter un abonné pour recevoir les messages MQTT."""
        self.client.message_callback_add(subscriber.get_state_topic(), subscriber.on_mqtt_message)

    def subscribe(self, topic):
        """Souscrire à un topic MQTT."""
        self.client.subscribe(topic)
