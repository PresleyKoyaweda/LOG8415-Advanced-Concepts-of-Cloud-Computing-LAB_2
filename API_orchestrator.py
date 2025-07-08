from flask import Flask, request, jsonify
import threading
import json
import requests
import time

app = Flask(__name__)
lock = threading.Lock()
request_queue = []

def send_request_to_container(container_id, container_info, incoming_request_data):
    """
    Envoie une requête à un conteneur sur une instance de travail.

    Args:
        container_id (str): L'identifiant du conteneur (ex. "container1").
        container_info (dict): Informations sur le conteneur, y compris son IP et son port.
        incoming_request_data (dict): Les données à envoyer au conteneur.
    """
    container_ip = container_info['ip']
    container_port = container_info['port']

    # Construire l'URL pour l'endpoint du conteneur
    container_url = f"http://{container_ip}:{container_port}/run_model"

    try:
        print(f"Envoi de la requête à {container_id} à {container_url} avec les données : {incoming_request_data}...")
        
        # Envoyer la requête POST à l'API du conteneur
        response = requests.post(container_url, json=incoming_request_data, timeout=10)

        # Vérifier si la requête a été traitée avec succès
        if response.status_code == 200:
            print(f"Requête traitée avec succès par {container_id}. Réponse : {response.json()}")
        else:
            print(f"Erreur : Le conteneur {container_id} a répondu avec le code de statut {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Échec de l'envoi de la requête à {container_id} : {e}")

def update_container_status(container_id, status):
    """
    Met à jour le statut d'un conteneur dans le fichier de statut.

    Args:
        container_id (str): L'identifiant du conteneur.
        status (str): Le nouveau statut à attribuer (ex. "busy", "free").
    """
    with lock:
        with open("containers_status.json", "r") as f:
            data = json.load(f)
        data[container_id]["status"] = status
        with open("containers_status.json", "w") as f:
            json.dump(data, f)

def process_request(incoming_request_data):
    """
    Traite une requête entrante en vérifiant le statut des conteneurs.

    Args:
        incoming_request_data (dict): Les données de la requête entrante.
    """
    with lock:
        with open("containers_status.json", "r") as f:
            data = json.load(f)
        free_container = None
        for container_id, container_info in data.items():
            if container_info["status"] == "free":
                free_container = container_id
                break

    if free_container:
        update_container_status(free_container, "busy")
        send_request_to_container(free_container, data[free_container], incoming_request_data)
        update_container_status(free_container, "free")
    else:
        request_queue.append(incoming_request_data)

@app.route("/new_request", methods=["POST"])
def new_request():
    """
    Endpoint pour recevoir une nouvelle requête.
    """
    incoming_request_data = request.json
    threading.Thread(target=process_request, args=(incoming_request_data,)).start()
    return jsonify({"message": "Requête reçue et traitement commencé."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
