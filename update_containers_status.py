import json

# Fonction pour lire les adresses IP à partir du fichier
def load_ips(ip_file):
    with open(ip_file, 'r') as file:
        return [line.strip() for line in file.readlines()]

# Fonction pour mettre à jour le fichier containers_status.json
def update_containers_status(ip_file, json_file):
    ips = load_ips(ip_file)

    try:
        with open(json_file, 'r') as file:
            data = json.load(file)
        
        # Mise à jour des IPs des conteneurs
        container_index = 0
        for i in range(1, 9, 2):
            container1 = f"container{i}"
            container2 = f"container{i+1}"
            if container_index < len(ips):
                # Mise à jour des conteneurs avec les IP des workers
                data[container1]['ip'] = ips[container_index]
                data[container2]['ip'] = ips[container_index]
                container_index += 1

        # Sauvegarde des changements dans le fichier JSON
        with open(json_file, 'w') as file:
            json.dump(data, file, indent=4)
        print("Mise à jour du fichier containers_status.json terminée.")

    except FileNotFoundError:
        print(f"Erreur : Le fichier {json_file} est introuvable.")
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")

# Exemple d'utilisation
ip_file = 'public_ips_workers.txt'  # Fichier contenant les adresses IP des workers
json_file = 'containers_status.json'      # Fichier JSON à mettre à jour

update_containers_status(ip_file, json_file)
