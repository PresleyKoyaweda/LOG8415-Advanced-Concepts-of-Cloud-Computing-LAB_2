import boto3
from botocore.exceptions import ClientError
import subprocess
import time

# Création des clients EC2
ec2 = boto3.client('ec2')

# Fonction pour lire les adresses IP des workers depuis le fichier
def read_worker_ips():
    try:
        with open('public_ips_workers.txt', 'r') as file:
            worker_ips = [line.strip() for line in file.readlines()]
        print(f"Adresses IP des workers lues : {worker_ips}")
        return worker_ips
    except FileNotFoundError as e:
        print(f"Fichier non trouvé : {e}")
        return []

# Fonction pour lire les identifiants des instances des workers depuis le fichier
def read_instance_ids_workers():
    try:
        with open('instance_ids_workers.txt', 'r') as file:
            instance_ids = [line.strip() for line in file.readlines()]
        print(f"Identifiants des instances des workers lus : {instance_ids}")
        return instance_ids
    except FileNotFoundError as e:
        print(f"Fichier non trouvé : {e}")
        return []

# Fonction pour lire l'IP de l'orchestrateur depuis le fichier
def read_orchestrator_ip():
    try:
        with open('public_ips_orchestrateur.txt', 'r') as file:
            orchestrator_ip = file.read().strip()
        print(f"Adresse IP de l'orchestrateur lue : {orchestrator_ip}")
        return orchestrator_ip
    except FileNotFoundError as e:
        print(f"Fichier non trouvé : {e}")
        return None

# Fonction pour lire l'ID de l'instance de l'orchestrateur
def read_instance_id_orchestrator():
    try:
        with open('instance_ids_orchestrateur.txt', 'r') as file:
            orchestrator_id = file.read().strip()
        print(f"ID de l'instance de l'orchestrateur lu : {orchestrator_id}")
        return orchestrator_id
    except FileNotFoundError as e:
        print(f"Fichier non trouvé : {e}")
        return None

# Fonction pour créer des volumes EBS de taille et de nombre spécifiés
def create_ebs_volumes(ec2, availability_zone, volume_size, num_volumes):
    '''
    Creates the specified number of EBS volumes in the given availability zone.

    Parameters:
        ec2: A Boto3 EC2 client object to interact with AWS EC2 service.
        availability_zone: The availability zone where the volumes will be created.
        volume_size: The size of each EBS volume in GiB.
        num_volumes: The number of EBS volumes to create.

    Returns:
        A list of volume IDs for the created EBS volumes.
    '''
    volume_ids = []
    for i in range(num_volumes):
        volume_response = ec2.create_volume(
            AvailabilityZone=availability_zone,
            Size=volume_size,
            VolumeType='gp3'
        )

        volume_id = volume_response['VolumeId']
        print(f"Created EBS volume {volume_id} in {availability_zone} with size {volume_size} GiB")
        
        # Wait for the volume to be available before attaching
        ec2.get_waiter('volume_available').wait(VolumeIds=[volume_id])
        print(f"EBS volume {volume_id} is now available.")

        # Add volume ID to the list
        volume_ids.append(volume_id)

    return volume_ids

# Fonction pour attacher un volume EBS à une instance EC2
def attach_volume_to_instance(ec2, instance_id, volume_id, device_name='/dev/sdf'):
    '''
    Attaches an existing EBS volume to an EC2 instance and waits until the attachment is complete.

    Parameters:
        ec2: A Boto3 EC2 client object to interact with AWS EC2 service.
        instance_id: The ID of the instance to attach the volume to.
        volume_id: The ID of the volume to attach.
        device_name: The device name (default is /dev/sdf).
    
    Returns:
        None
    '''
    # Attach the volume to the instance
    ec2.attach_volume(
        VolumeId=volume_id,
        InstanceId=instance_id,
        Device=device_name
    )
    print(f"Attached volume {volume_id} to instance {instance_id} as {device_name}")

    # Check the attachment status
    print("Waiting for volume to be attached...")
    while True:
        volume_description = ec2.describe_volumes(VolumeIds=[volume_id])
        attachment_state = volume_description['Volumes'][0]['Attachments'][0]['State']

        if attachment_state == 'attached':
            print(f"Volume {volume_id} successfully attached to {instance_id} as {device_name}")
            break
        else:
            print(f"Volume {volume_id} attachment state: {attachment_state}. Waiting...")
            time.sleep(5)  # Wait before checking again

# Fonction principale pour l'attachement des volumes aux workers et à l'orchestrateur
def process_instances():
    # Lecture des IPs et des IDs des workers
    worker_ips = read_worker_ips()
    instance_ids_workers = read_instance_ids_workers()

    # Lecture de l'IP et de l'ID de l'orchestrateur
    orchestrator_ip = read_orchestrator_ip()
    orchestrator_id = read_instance_id_orchestrator()

    # Vérification des correspondances entre les IPs et IDs des workers
    if len(worker_ips) != len(instance_ids_workers):
        print("Le nombre d'IP et d'ID d'instance des workers ne correspond pas.")
        return

    # Création et attachement des volumes pour chaque worker
    for ip, instance_id in zip(worker_ips, instance_ids_workers):
        print(f"Vérification des volumes attachés pour l'instance {instance_id} (IP : {ip})")

        # Récupérer la zone de disponibilité de l'instance
        instance_info = ec2.describe_instances(InstanceIds=[instance_id])
        availability_zone = instance_info['Reservations'][0]['Instances'][0]['Placement']['AvailabilityZone']
        print(f"Instance {instance_id} est dans la zone {availability_zone}")

        # Créer et attacher un volume de 20 GiB
        try:
            volume_ids = create_ebs_volumes(ec2, availability_zone, volume_size=20, num_volumes=1)
            for volume_id in volume_ids:
                attach_volume_to_instance(ec2, instance_id, volume_id)

        except ClientError as e:
            print(f"Erreur lors de la création ou de l'attachement du volume pour {instance_id} : {e}")
            continue

    # Création et attachement du volume pour l'orchestrateur
    if orchestrator_ip and orchestrator_id:
        print(f"Création du volume pour l'orchestrateur (ID : {orchestrator_id}, IP : {orchestrator_ip})")

        # Récupérer la zone de disponibilité de l'orchestrateur
        orchestrator_info = ec2.describe_instances(InstanceIds=[orchestrator_id])
        availability_zone = orchestrator_info['Reservations'][0]['Instances'][0]['Placement']['AvailabilityZone']
        print(f"Orchestrateur {orchestrator_id} est dans la zone {availability_zone}")

        # Créer et attacher un volume de 20 GiB pour l'orchestrateur
        try:
            volume_ids = create_ebs_volumes(ec2, availability_zone, volume_size=20, num_volumes=1)
            for volume_id in volume_ids:
                attach_volume_to_instance(ec2, orchestrator_id, volume_id)

        except ClientError as e:
            print(f"Erreur lors de la création ou de l'attachement du volume pour l'orchestrateur : {e}")
            return

# Lancer le processus
process_instances()
