import subprocess
import time
import paramiko

# Fonction pour ajuster les permissions de la clé sur Windows
def adjust_key_permissions(key_path):
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
            ips = [line.strip() for line in file.readlines()]
            if not ips:
                print(f"Aucune IP trouvée dans {file_path}.")
            return ips
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
        except paramiko.ssh_exception.NoValidConnectionsError as e:
            print(f"Échec de la connexion SSH : {e}")
        except paramiko.AuthenticationException as e:
            print(f"Échec de l'authentification SSH : {e}")
        except paramiko.SSHException as e:
            print(f"Erreur SSH générale : {e}")
        except Exception as e:
            print(f"Erreur inattendue : {e}")

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
        print(f"Exécution de la commande : {command}")
        try:
            stdin, stdout, stderr = client.exec_command(command, get_pty=True)
            stdout.channel.recv_exit_status()
            print(stdout.read().decode())
            error = stderr.read().decode()
            if error:
                print(f"Erreur lors de l'exécution de la commande '{command}': {error}")
        except Exception as e:
            print(f"Erreur lors de l'exécution de la commande '{command}': {e}")

    client.close()

# Fonction pour supprimer les anciens conteneurs s'ils existent
def remove_existing_containers(ip_address, username, private_key_path):
    print(f"Suppression des conteneurs existants sur {ip_address}...")
    commands = [
        'sudo docker rm -f orchestrator_container || true'
    ]
    ssh_exec_command(ip_address, username, private_key_path, commands)

# Fonction pour configurer Docker et le conteneur orchestrateur
def setup_orchestrator(ip_address, username, private_key_path):
    if not wait_for_ssh(ip_address, username, private_key_path):
        print(f"Échec de l'établissement de la connexion SSH à {ip_address}")
        return

    remove_existing_containers(ip_address, username, private_key_path)

    # Installation de Docker
    print(f"Installation de Docker sur {ip_address}...")
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

    # Chargement de l'image Docker de l'orchestrateur
    print(f"Chargement de l'image Docker de l'orchestrateur sur {ip_address}...")
    commands = ['gzip -dc /mnt/data/orchestrator_image.tar.gz | sudo docker load']
    ssh_exec_command(ip_address, username, private_key_path, commands)

    # Démarrage de l'orchestrateur sur le port 80
    print(f"Démarrage du conteneur orchestrateur sur {ip_address}...")
    commands = [f'sudo docker run -d --name orchestrator_container -p 80:80 orchestrator_image:latest']
    ssh_exec_command(ip_address, username, private_key_path, commands)

    print("Le conteneur orchestrateur a été démarré avec succès.")

# Fonction principale pour déployer l'orchestrateur
def deploy_orchestrator(ip_file, username, private_key_path):
    ips = load_ips(ip_file)
    if not ips:
        print("Aucune adresse IP disponible pour le déploiement de l'orchestrateur.")
        return

    for ip in ips:
        print(f"--- Déploiement de l'orchestrateur sur {ip} ---")
        setup_orchestrator(ip, username, private_key_path)
        time.sleep(5)

# Exemple d'utilisation
if __name__ == "__main__":
    ip_file = 'public_ips_orchestrateur.txt'  # Fichier contenant l'adresse IP de l'orchestrateur
    username = 'ubuntu'
    private_key_path = 'my-key-pair.pem'

    # Ajuster les permissions de la clé avant de commencer le déploiement
    adjust_key_permissions(private_key_path)

    # Déploiement sur l'orchestrateur
    deploy_orchestrator(ip_file, username, private_key_path)
