import subprocess
import time
import paramiko
import os

# Fonction pour ajuster les permissions de la clé sur Windows
def adjust_key_permissions(key_path):
    if not os.path.exists(key_path):
        print(f"Erreur : la clé {key_path} est introuvable.")
        return

    icacls_command = ["icacls", key_path, "/inheritance:r", "/grant:r", "gpres:F"]
    try:
        print(f"Réglage des permissions pour {key_path}...")
        subprocess.run(icacls_command, check=True)
        print(f"Permissions ajustées pour {key_path}.")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors du réglage des permissions pour {key_path}: {e}")

# Fonction pour lire les IPs à partir d'un fichier
def load_ips(file_path):
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        print(f"Erreur : {file_path} est introuvable.")
        return []

# Connexion SSH
def wait_for_ssh(ip_address, username, private_key_path, retries=10, delay=30):
    key = paramiko.RSAKey.from_private_key_file(private_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    for attempt in range(retries):
        try:
            print(f"Tentative de connexion SSH à {ip_address} (Tentative {attempt+1}/{retries})...")
            client.connect(hostname=ip_address, username=username, pkey=key, timeout=10)
            client.close()
            print(f"Connexion SSH à {ip_address} réussie !")
            return True
        except Exception as e:
            print(f"Erreur de connexion SSH (tentative {attempt+1}/{retries}) : {e}")

        print(f"Attente de {delay} secondes avant la prochaine tentative...")
        time.sleep(delay)

    print(f"Impossible d'établir une connexion SSH à {ip_address} après {retries} tentatives.")
    return False

# Fonction pour exécuter des commandes SSH via Paramiko
def ssh_exec_command(ip_address, username, private_key_path, commands):
    key = paramiko.RSAKey.from_private_key_file(private_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=ip_address, username=username, pkey=key)

    for command in commands:
        print("Exécution de la commande : ", command)
        try:
            stdin, stdout, stderr = client.exec_command(command, get_pty=True)
            stdout.channel.recv_exit_status()
            print(stdout.read().decode())
            print(stderr.read().decode())
        except Exception as e:
            print(f"Erreur lors de l'exécution de la commande {command} : {e}")

    client.close()

# Fonction pour supprimer les anciens conteneurs s'ils existent
def remove_existing_containers(ip_address, username, private_key_path):
    commands = [
        'sudo docker rm -f container1 || true',
        'sudo docker rm -f container2 || true',
        'sudo docker rm -f orchestrator_container || true'
    ]
    ssh_exec_command(ip_address, username, private_key_path, commands)

# Fonction pour configurer Docker et les conteneurs
def setup_ml_app(ip_address, username, private_key_path):
    if not wait_for_ssh(ip_address, username, private_key_path):
        print(f"Échec de l'établissement de la connexion SSH à {ip_address}")
        return

    remove_existing_containers(ip_address, username, private_key_path)
    time.sleep(2)  # Attendre 2 secondes après la suppression

    # Installation de Docker
    commands = [
        'sudo apt-get update -y',
        'sudo apt-get install -y ca-certificates curl',
        'sudo install -m 0755 -d /etc/apt/keyrings',
        'sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc',
        'sudo chmod a+r /etc/apt/keyrings/docker.asc',
        'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null',
        'sudo apt-get update -y',
        'sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin',
        'sudo docker run hello-world',
    ]
    ssh_exec_command(ip_address, username, private_key_path, commands)

    # Chargement de l'image Docker à partir du fichier tar situé dans /mnt/data
    commands = ['gzip -dc /mnt/data/workers_image.tar.gz | sudo docker load']
    try:
        ssh_exec_command(ip_address, username, private_key_path, commands)
    except Exception as e:
        print(f"Erreur lors du chargement de l'image Docker : {e}")

    # Démarrage des conteneurs
    commands = [
        f'sudo docker run -d --name container1 -p 5000:5000 workers_image:latest',
        f'sudo docker run -d --name container2 -p 5001:5000 workers_image:latest',
        f'sudo docker run -d --name orchestrator_container -p 80:80 orchestrator_image:latest'
    ]
    ssh_exec_command(ip_address, username, private_key_path, commands)

    print("Les conteneurs ont été démarrés avec succès.")

# Fonction principale pour déployer des conteneurs sur plusieurs instances
def deploy_on_instances(ip_file, username, private_key_path):
    ips = load_ips(ip_file)
    if not ips:
        print("Aucune adresse IP disponible pour le déploiement.")
        return

    for ip in ips:
        print(f"--- Déploiement sur {ip} ---")
        setup_ml_app(ip, username, private_key_path)
        time.sleep(5)

# Exemple d'utilisation
ip_file = 'public_ips_workers.txt'
username = 'ubuntu'
private_key_path = 'my-key-pair.pem'

# Ajuster les permissions de la clé avant de commencer le déploiement
adjust_key_permissions(private_key_path)

# Déploiement sur les instances
deploy_on_instances(ip_file, username, private_key_path)
