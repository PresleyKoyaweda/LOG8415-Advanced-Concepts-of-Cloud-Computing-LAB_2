import os
import subprocess

# Fonction pour lire les adresses IP des workers depuis un fichier
def read_worker_ips(filename):
    """
    Lit les adresses IP des workers depuis un fichier.
    Chaque IP doit être sur une nouvelle ligne.
    """
    with open(filename, 'r') as file:
        worker_ips = [line.strip() for line in file.readlines()]
    return worker_ips

# Fonction pour transférer une liste de fichiers vers une instance et changer les permissions
def transfer_files_to_instance(ip, key_file, files, destination):
    """
    Transfère une liste de fichiers vers une instance donnée en utilisant SCP et change les permissions du répertoire de destination.
    
    Paramètres:
    - ip : Adresse IP de l'instance
    - key_file : Fichier de clé privé pour la connexion SSH
    - files : Liste des fichiers à transférer
    - destination : Répertoire de destination sur l'instance
    """
    try:
        # Donner les permissions sur le répertoire de destination à "ubuntu"
        ssh_command = f'sudo chmod -R 777 {destination}'
        ssh = subprocess.Popen(['ssh', '-i', key_file, '-o', 'StrictHostKeyChecking=no', f'ubuntu@{ip}', ssh_command],
                               shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = ssh.communicate()
        if stderr:
            print(f"Erreur lors de la modification des permissions sur {ip}: {stderr.decode()}")
        else:
            print(f"Permissions modifiées avec succès sur {ip}:{destination}")
        
        # Transfert des fichiers
        for file in files:
            if os.path.exists(file):
                scp_command = ['scp', '-i', key_file, '-o', 'StrictHostKeyChecking=no', file, f'ubuntu@{ip}:{destination}']
                print(f"Transfert du fichier {file} vers l'instance {ip}...")
                subprocess.run(scp_command, check=True)
                print(f"Fichier {file} transféré avec succès vers {ip}:{destination}")
            else:
                print(f"Erreur : Le fichier {file} n'existe pas.")

    except subprocess.CalledProcessError as e:
        print(f"Erreur lors du transfert du fichier {file} vers {ip} : {e}")
    except Exception as e:
        print(f"Erreur inattendue : {e}")

# Fonction principale
def main():
    # Chemin vers le fichier contenant les IPs des instances workers et orchestrateur
    worker_ips_file = 'public_ips_workers.txt'
    orchestrator_ips_file = 'public_ips_orchestrateur.txt'
    
    # Fichier de clé pour la connexion SSH
    key_file = 'my-key-pair.pem'
    
    # Liste des fichiers à transférer vers les workers (chemin racine)
    worker_files_to_transfer = ["workers_image.tar.gz"]

    # Liste des fichiers à transférer vers l'orchestrateur (chemin racine)
    orchestrator_files_to_transfer = ["orchestrator_image.tar.gz"]
    
    # Répertoire de destination sur les instances
    destination = '/mnt/data/'
    
    # Lire les adresses IP des instances workers
    worker_ips = read_worker_ips(worker_ips_file)
    
    # Transférer les fichiers vers chaque instance worker
    for ip in worker_ips:
        transfer_files_to_instance(ip, key_file, worker_files_to_transfer, destination)

    # Lire les adresses IP des orchestrateurs
    orchestrator_ips = read_worker_ips(orchestrator_ips_file)  # Assuming same function for orchestrator
    
    # Transférer les fichiers vers l'orchestrateur
    for ip in orchestrator_ips:
        transfer_files_to_instance(ip, key_file, orchestrator_files_to_transfer, destination)

if __name__ == "__main__":
    main()
