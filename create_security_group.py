import boto3
from botocore.exceptions import ClientError

# Création d'un client EC2
ec2 = boto3.client('ec2')

# Lecture de VPC ID depuis le fichier
with open('vpc_id.txt', 'r') as file:
    vpc_id = file.read().strip()

# Nom du groupe de sécurité
group_name = 'my-security-group'

# Vérifie si le groupe de sécurité existe
try:
    response = ec2.describe_security_groups(GroupNames=[group_name])
    security_group_id = response['SecurityGroups'][0]['GroupId']
    print(f"Le groupe de sécurité '{group_name}' existe déjà avec l'ID : {security_group_id}")

    # Vérifie si le groupe de sécurité est utilisé
    try:
        # Si le groupe est utilisé par d'autres ressources, ne pas tenter de le supprimer
        print(f"Le groupe de sécurité '{group_name}' est en cours d'utilisation. Il ne sera pas supprimé.")
    except ClientError as e:
        if 'DependencyViolation' in str(e):
            print(f"Impossible de supprimer le groupe de sécurité '{group_name}' car il est associé à des ressources.")
        else:
            raise e

except ClientError as e:
    if 'InvalidGroup.NotFound' in str(e):
        print(f"Le groupe de sécurité '{group_name}' n'existe pas encore, création d'un nouveau.")

        # Création d'un nouveau groupe de sécurité
        security_group = ec2.create_security_group(
            GroupName=group_name,
            Description="Security group for EC2 instances",  # Description en ASCII uniquement
            VpcId=vpc_id
        )

        security_group_id = security_group['GroupId']
        print(f"Groupe de sécurité créé : {security_group_id}")

        # Enregistrement de l'ID du groupe de sécurité dans un fichier
        with open('security_group_id.txt', 'w') as file:
            file.write(security_group_id)

        # Configuration des règles du groupe de sécurité
        ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 5000, 'ToPort': 5000, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 5001, 'ToPort': 5001, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
            ]
        )
        print(f"Groupe de sécurité configuré pour les ports 80, 443, 22, 5000 et 5001.")

    else:
        raise e
