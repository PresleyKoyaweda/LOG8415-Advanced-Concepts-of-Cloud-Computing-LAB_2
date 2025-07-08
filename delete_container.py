import paramiko
import time

# Fonction pour lire les IPs à partir d'un fichier
def load_ips(file_path):
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        print(f"Erreur : {file_path} est introuvable.")
        return []

# Fonction pour établir une connexion SSH et exécuter des commandes
def ssh_exec_command(ip_address, username, private_key_path, commands):
    key = paramiko.RSAKey.from_private_key_file(private_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=ip_address, username=username, pkey=key)
    
    for command in commands:
        print(f"Exécution de la commande sur {ip_address} : {command}")
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        stdout.channel.recv_exit_status()
        print(stdout.read().decode())
        print(stderr.read().decode())
    
    client.close()

# Fonction pour supprimer tous les conteneurs sur l'instance
def remove_all_containers(ip_address, username, private_key_path):
    commands = [
        'sudo docker rm -f $(sudo docker ps -aq) || true'  # Supprime tous les conteneurs
    ]
    ssh_exec_command(ip_address, username, private_key_path, commands)

# Fonction principale pour parcourir les instances et supprimer les conteneurs
def clean_instances(ip_file, username, private_key_path):
    ips = load_ips(ip_file)
    if not ips:
        print("Aucune adresse IP disponible pour le nettoyage.")
        return

    for ip in ips:
        print(f"--- Suppression des conteneurs sur {ip} ---")
        remove_all_containers(ip, username, private_key_path)
        time.sleep(2)  # Ajouter un délai pour éviter de surcharger les instances

# Exemple d'utilisation
ip_file = 'public_ips_workers.txt'  # Fichier contenant les adresses IP
username = 'ubuntu'  # Nom d'utilisateur SSH
private_key_path = 'my-key-pair.pem'  # Chemin vers la clé privée

# Exécution de la fonction pour nettoyer les instances
clean_instances(ip_file, username, private_key_path)
