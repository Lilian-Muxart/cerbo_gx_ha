import paho.mqtt.client as mqtt
import ssl
import os

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
        ca_cert_path = os.path.join(os.path.dirname(__file__), "venus-ca.crt")
        
        # Vérification de l'existence du certificat
        if os.path.exists(ca_cert_path):
            # Configurer la connexion sécurisée avec le certificat
            self.client.tls_set(ca_certs=ca_cert_path, certfile=None, keyfile=None, tls_version=ssl.PROTOCOL_TLSv1_2)
        else:
            raise FileNotFoundError(f"Le certificat CA n'a pas été trouvé à l'emplacement : {ca_cert_path}")
        
        # Se connecter au broker MQTT en utilisant le port sécurisé 8883
        self.client.connect(self.broker_url, 8883)
        self.client.loop_start()

    def _get_vrm_broker_url(self):
        """Calculer l'URL du serveur MQTT basé sur l'ID du site."""
        sum = 0
        for character in self.id_site.lower().strip():
            sum += ord(character)
        broker_index = sum % 128
        return f"mqtt{broker_index}.victronenergy.com"

    def add_subscriber(self, subscriber):
        """Ajouter un abonné pour recevoir les messages MQTT."""
        self.client.message_callback_add(subscriber.get_state_topic(), subscriber.on_mqtt_message)

    def subscribe(self, topic):
        """Souscrire à un topic MQTT."""
        self.client.subscribe(topic)
