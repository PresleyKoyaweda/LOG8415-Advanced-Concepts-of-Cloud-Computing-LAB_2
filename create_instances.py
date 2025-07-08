import boto3
from botocore.exceptions import ClientError
import os

# Création des clients EC2
ec2 = boto3.client('ec2')

# Nom de la paire de clés
key_name = 'my-key-pair'

# Vérifie si la paire de clés existe
try:
    ec2.describe_key_pairs(KeyNames=[key_name])
    print(f"Key Pair '{key_name}' existe déjà.")
except ClientError as e:
    if 'InvalidKeyPair.NotFound' in str(e):
        try:
            key_pair = ec2.create_key_pair(KeyName=key_name)
            with open(f'{key_name}.pem', 'w') as file:
                file.write(key_pair['KeyMaterial'])
            os.chmod(f'{key_name}.pem', 0o400)
            print(f"Key Pair créée et enregistrée sous {key_name}.pem")
        except ClientError as create_key_error:
            print(f"Erreur lors de la création de la clé : {create_key_error}")
            raise
    else:
        print(f"Erreur lors de la vérification de la clé : {e}")
        raise

# Lecture de VPC ID, Subnet ID et Security Group ID depuis les fichiers
try:
    with open('vpc_id.txt', 'r') as file:
        vpc_id = file.read().strip()

    with open('subnet_id_1.txt', 'r') as file:
        selected_subnet_id = file.read().strip()

    with open('security_group_id.txt', 'r') as file:
        security_group_id = file.read().strip()
except FileNotFoundError as e:
    print(f"Fichier non trouvé : {e}")
    raise

# Utilisation d'un AMI valide (Amazon Linux 2)
ami_id = 'ami-007855ac798b5175e'

# Fonction pour lancer une instance et récupérer son ID et son IP élastique
def create_instance_with_elastic_ip(instance_name):
    try:
        response = ec2.run_instances(
            ImageId=ami_id,
            MinCount=1,
            MaxCount=1,
            InstanceType='t2.large',
            KeyName=key_name,
            SubnetId=selected_subnet_id,
            SecurityGroupIds=[security_group_id],
            TagSpecifications=[{
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Name', 'Value': instance_name}]
            }]
        )
        instance_id = response['Instances'][0]['InstanceId']
        print(f"Instance '{instance_name}' créée: {instance_id}")
        
        # Attendre que l'instance soit en état 'running'
        ec2.get_waiter('instance_running').wait(InstanceIds=[instance_id])
        
        # Créer une IP élastique
        allocation = ec2.allocate_address(Domain='vpc')
        elastic_ip = allocation['PublicIp']
        allocation_id = allocation['AllocationId']
        
        # Associer l'Elastic IP à l'instance
        ec2.associate_address(InstanceId=instance_id, AllocationId=allocation_id)
        print(f"Elastic IP '{elastic_ip}' associée à l'instance '{instance_name}'.")

        return instance_id, elastic_ip
    except ClientError as e:
        print(f"Erreur lors du lancement de l'instance '{instance_name}': {e}")
        raise

# Créer l'instance de l'orchestrateur et récupérer son IP élastique
instance_id_orchestrateur, ip_orchestrateur = create_instance_with_elastic_ip("orchestrateur")

# Créer les instances des workers (4 instances) et récupérer leurs IPs élastiques
instance_ids_workers = []
ips_workers = []
for i in range(1, 5):
    instance_id, elastic_ip = create_instance_with_elastic_ip(f"worker{i}")
    instance_ids_workers.append(instance_id)
    ips_workers.append(elastic_ip)

# Enregistrer les IDs et les IPs des instances
with open('instance_ids_orchestrateur.txt', 'w') as file:
    file.write(instance_id_orchestrateur)
with open('public_ips_orchestrateur.txt', 'w') as file:
    file.write(ip_orchestrateur)

with open('instance_ids_workers.txt', 'w') as file:
    file.write('\n'.join(instance_ids_workers))
with open('public_ips_workers.txt', 'w') as file:
    file.write('\n'.join(ips_workers))

print("Instances et IPs élastiques créées pour l'orchestrateur et les 4 workers.")
