import boto3
import paramiko
import time
import os
import stat
import subprocess

# Fonction pour ajuster les permissions sur le fichier my-key-pair.pem
def set_key_permissions(key_file):
    """
    Configure the correct permissions for the private key file.
    """
    try:
        icacls_command = f'icacls "{key_file}" /inheritance:r /grant:r gpres:F'
        subprocess.run(icacls_command, check=True, shell=True)
        print(f"Permissions configurées avec succès pour la clé {key_file}.")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de la configuration des permissions pour la clé {key_file} : {e}")

# Fonction pour lire les adresses IP
def read_ips(filename):
    if not os.path.exists(filename):
        print(f"Erreur: Le fichier {filename} est introuvable.")
        return []
    with open(filename, 'r') as file:
        ips = [line.strip() for line in file.readlines()]
    return ips

# Fonction pour lire les identifiants d'instances
def read_instance_ids(filename):
    if not os.path.exists(filename):
        print(f"Erreur: Le fichier {filename} est introuvable.")
        return []
    with open(filename, 'r') as file:
        instance_ids = [line.strip() for line in file.readlines()]
    return instance_ids

# Fonction pour se connecter à une instance et monter un volume
def connect_and_mount_volume(ip, instance_id, key_file):
    """
    Connects to an instance via SSH, checks if the volume is formatted, 
    and mounts the volume if necessary.
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(hostname=ip, username='ubuntu', key_filename=key_file)

        # Vérification si le volume est formaté
        stdin, stdout, stderr = ssh.exec_command('sudo file -s /dev/xvdf')
        filesystem_check = stdout.read().decode().strip()
        print(f"Vérification du système de fichiers sur l'instance {instance_id} (IP : {ip}) : {filesystem_check}")

        if "ext4" in filesystem_check:
            print(f"Le volume est déjà formaté avec ext4 sur l'instance {instance_id} (IP : {ip}), montage uniquement.")
        else:
            print(f"Le volume n'est pas formaté sur l'instance {instance_id} (IP : {ip}), formatage en cours.")
            stdin, stdout, stderr = ssh.exec_command('sudo mkfs -t ext4 /dev/xvdf')
            format_error = stderr.read().decode()

            if format_error:
                print(f"Erreur lors du formatage : {format_error}")
            else:
                print(f"Formatage du volume complété sur l'instance {instance_id} (IP : {ip}).")

        # Vérification si le volume est monté
        stdin, stdout, stderr = ssh.exec_command('lsblk')
        output = stdout.read().decode()
        print(f"Sortie de la commande lsblk sur l'instance {instance_id} (IP : {ip}) :\n{output}")

        if '/mnt/data' not in output:
            print(f"Montage du volume sur l'instance {instance_id} (IP : {ip})")
            ssh.exec_command('sudo mkdir -p /mnt/data')
            ssh.exec_command('sudo mount /dev/xvdf /mnt/data')
            print(f"Volume monté avec succès sur l'instance {instance_id} (IP : {ip})")
        else:
            print(f"Le volume est déjà monté sur l'instance {instance_id} (IP : {ip})")

    except Exception as e:
        print(f"Erreur lors de la connexion ou du montage du volume sur l'instance {instance_id} (IP : {ip}) : {e}")
    finally:
        ssh.close()

def process_instances(ips_file, ids_file, key_file):
    # Lire les IPs et les IDs des instances
    ips = read_ips(ips_file)
    instance_ids = read_instance_ids(ids_file)

    if not ips or not instance_ids:
        print("Erreur: IPs ou IDs d'instances manquants.")
        return

    for ip, instance_id in zip(ips, instance_ids):
        connect_and_mount_volume(ip, instance_id, key_file)

def main():
    # Chemins des fichiers pour les workers et orchestrateur
    key_file = './my-key-pair.pem'

    # Workers
    worker_ips_file = 'public_ips_workers.txt'
    worker_ids_file = 'instance_ids_workers.txt'
    
    # Orchestrateur
    orchestrator_ips_file = 'public_ips_orchestrateur.txt'
    orchestrator_ids_file = 'instance_ids_orchestrateur.txt'

    # Vérifier l'existence du fichier de clé
    if not os.path.exists(key_file):
        print(f"Erreur: Le fichier de clé {key_file} est introuvable.")
        return

    set_key_permissions(key_file)

    # Exécution deux fois du processus
    for i in range(2):
        print(f"--- Exécution {i+1} ---")
        # Traiter les volumes pour les workers
        print("Traitement des volumes pour les workers...")
        process_instances(worker_ips_file, worker_ids_file, key_file)

        # Traiter les volumes pour l'orchestrateur
        print("Traitement des volumes pour l'orchestrateur...")
        process_instances(orchestrator_ips_file, orchestrator_ids_file, key_file)

if __name__ == "__main__":
    main()
