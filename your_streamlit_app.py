import streamlit as st
import requests
import json
from dotenv import load_dotenv
import os
from google.cloud import secretmanager
import logging

# Configurer le logging
logging.basicConfig(level=logging.DEBUG)

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

def get_secret(secret_id, version_id='latest'):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{os.getenv('GCP_PROJECT')}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(name=name)
    secret = response.payload.data.decode('UTF-8')
    logging.debug(f"Secret fetched: {secret}")
    return secret

# Récupérer la clé JSON depuis Google Secret Manager
def load_service_account_key():
    try:
        key_json = get_secret('my-service-account-key')
        logging.debug(f"Raw key data: {key_json}")
        key_data = json.loads(key_json)
        logging.debug("Key data successfully loaded.")
    except json.JSONDecodeError as e:
        logging.error(f"Failed to load key data: {e}")
        st.stop()
    except Exception as e:
        logging.error(f"Error retrieving key data: {e}")
        st.stop()

    # Définir le chemin du fichier de clé JSON
    credentials_path = '/tmp/service-account-key.json'

    # Sauvegarder temporairement la clé pour l'utiliser
    try:
        with open(credentials_path, 'w') as key_file:
            json.dump(key_data, key_file)
        logging.debug("Key file written successfully.")
    except IOError as e:
        logging.error(f"Failed   to write key file: {e}")
        st.stop()

    # Mettre à jour la variable d'environnement
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    logging.debug("Environment variable set successfully.")
    return credentials_path

# Charger la clé du compte de service
credentials_path = load_service_account_key()

# URL du job Cloud Run
CLOUD_RUN_JOB_URL = "https://helpdesk-service-lxazwit43a-od.a.run.app/query"

# Vérifier que l'URL est correctement chargée
if not CLOUD_RUN_JOB_URL:
    st.error("L'URL du service Cloud Run n'est pas définie. Vérifiez votre fichier .env.")
    st.stop()

# Fonction pour appeler le job Cloud Run
def call_cloud_run_job(question):
    try:
        st.write(f"Envoi de la question au service Cloud Run : {question}")  # Journal de débogage
        headers = {
            "Authorization": f"Bearer {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}"
        }
        response = requests.post(CLOUD_RUN_JOB_URL, json={"question": question}, headers=headers)
        response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
        result = response.json()
        st.write(f"Réponse   reçue du service Cloud Run : {result}")  # Journal de débogage
        return result.get("result", "No result found"), result.get("sources", "No sources found")
    except requests.exceptions.HTTPError as http_err:
        st.write(f"Erreur HTTP : {http_err}")  # Journal de débogage
        return f"Erreur HTTP : {http_err}", ""
    except requests.exceptions.ConnectionError as conn_err:
        st.write(f"Erreur de connexion : {conn_err}")  # Journal de débogage
        return f"Erreur de connexion : {conn_err}", ""
    except requests.exceptions.Timeout as timeout_err:
        st.write(f"Erreur de délai d'attente : {timeout_err}")  # Journal de débogage
        return f"Erreur de délai d'attente : {timeout_err}", ""
    except requests.exceptions.RequestException as req_err:
        st.write(f"Erreur : {req_err}")  # Journal de débogage
        return f"Erreur : {req_err}", ""

# Initialiser l'historique des messages dans l'état de session
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Comment puis-je vous aider ?"}]

# Afficher les messages de chat
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Saisie de l'invite de l'utilisateur
if prompt := st.chat_input("Comment puis-je vous aider ?"):
    # Ajouter le message de l'utilisateur à l'état de session
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Appeler le job Cloud Run et obtenir la réponse
    result, sources = call_cloud_run_job(prompt)

    # Formater la réponse
    response = f"{result}\n\n{sources}"

    # Ajouter la réponse de l'assistant à l'état de session
    st.chat_message("assistant").write(response)
    st.session_state["messages"].append({"role": "assistant", "content": response})
