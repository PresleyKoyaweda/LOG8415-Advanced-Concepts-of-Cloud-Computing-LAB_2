import requests
import concurrent.futures
import json
import os

# Fonction pour lire l'IP de l'orchestrateur à partir d'un fichier
def load_orchestrator_ip(file_path):
    """
    Charger l'adresse IP de l'orchestrateur à partir d'un fichier.

    Args:
    file_path (str): Le chemin du fichier contenant l'adresse IP de l'orchestrateur.

    Returns:
    str: L'adresse IP de l'orchestrateur.
    """
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()  # Lire l'IP et enlever les espaces inutiles
    except FileNotFoundError:
        print(f"Erreur : {file_path} est introuvable.")
        return None

# Fonction pour tester l'orchestrateur en envoyant des requêtes simultanément
def test_orchestrator(orchestrator_ip, num_requests, max_workers):
    """
    Tester l'orchestrateur en envoyant des requêtes simultanément.

    Args:
    orchestrator_ip (str): L'adresse IP ou l'URL de l'orchestrateur.
    num_requests (int): Le nombre de requêtes à envoyer.
    max_workers (int): Nombre de travailleurs concurrents.
    """
    orchestrator_url = f'http://{orchestrator_ip}/new_request'

    # Création du répertoire pour stocker les réponses si non existant
    if not os.path.exists('responses'):
        os.makedirs('responses')

    # Fonction pour envoyer une seule requête à l'orchestrateur
    def send_request(request_id):
        # Données à envoyer dans chaque requête
        data = {
            "text": f"Request number {request_id}"  # Message unique pour chaque requête
        }

        try:
            # Envoyer la requête POST à l'URL de l'orchestrateur
            response = requests.post(orchestrator_url, json=data)

            # Vérifier si la requête a été traitée avec succès
            if response.status_code == 200:
                response_data = response.json()

                # Enregistrer la réponse avec probabilités dans un fichier JSON
                file_path = f"responses/response_{request_id}.json"
                with open(file_path, 'w') as json_file:
                    json.dump(response_data, json_file, indent=4)

                return f"Requête {request_id} réussie ! Réponse enregistrée dans {file_path}."
            else:
                return f"Requête {request_id} échouée avec le code de statut : {response.status_code}"
        except requests.exceptions.RequestException as e:
            # Gérer les erreurs liées à l'envoi de la requête
            return f"Requête {request_id} échouée à cause d'une erreur : {e}"

    # Utilisation de ThreadPoolExecutor pour envoyer des requêtes simultanément
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Créer une liste des tâches pour envoyer les requêtes
        future_to_request = {executor.submit(send_request, i + 1): i for i in range(num_requests)}
        
        # Parcourir les futures pour récupérer les résultats
        for future in concurrent.futures.as_completed(future_to_request):
            request_id = future_to_request[future]
            try:
                # Afficher le résultat de chaque requête
                print(future.result())
            except Exception as exc:
                print(f"Requête {request_id} a généré une exception : {exc}")

# Chemin du fichier contenant l'IP de l'orchestrateur
orchestrator_ip_file = 'public_ips_orchestrateur.txt' 

# Lecture de l'IP de l'orchestrateur depuis le fichier
orchestrator_ip = load_orchestrator_ip(orchestrator_ip_file)

# Vérifier si l'IP a été lue correctement avant de procéder aux tests
if orchestrator_ip:
    # Nombre de requêtes à envoyer
    num_requests = 10

    # Nombre de requêtes simultanées
    max_workers = 5

    # Appel de la fonction pour tester l'orchestrateur
    test_orchestrator(orchestrator_ip, num_requests, max_workers)
else:
    print("L'adresse IP de l'orchestrateur est introuvable, vérifiez le fichier.")
