import subprocess

# Fonction pour exécuter un script et gérer les erreurs
def executer_script(nom_script, description_etape):
    print(f"{description_etape}...")
    try:
        subprocess.run(['python', nom_script], check=True)
        print(f"{description_etape} terminé avec succès.\n")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de {nom_script}: {str(e)}")
        exit(1)

# Fonction pour exécuter une commande Windows (par exemple icacls)
def executer_commande_windows(commande, description_etape):
    print(f"{description_etape}...")
    try:
        subprocess.run(commande, shell=True, check=True)
        print(f"{description_etape} terminé avec succès.\n")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de la commande: {str(e)}")
        exit(1)

# Étape 0 : Création du VPC
executer_script('get_vpc.py', "0. Création du VPC")

# Étape 1 : Récupération des IDs des sous-réseaux
executer_script('get_subnet_id.py', "1. Récupération des Subnet IDs")

# Étape 2 : Création du groupe de sécurité
executer_script('create_security_group.py', "2. Création du groupe de sécurité")

# Étape 4 : Lancement des instances EC2 et enregistrement dans les groupes cibles
executer_script('create_instances.py', "4. Lancement des instances EC2 pour l'orchestrateur")

# Étape 5 : Création et attachement des volumes aux instances
executer_script('create_volumes.py', "5. Création des volumes et attachement aux instances")

# Étape 6 : Montage des volumes sur les instances
executer_script('mount_volumes_on_instances.py', "6. Montage des volumes sur les instances")

# Étape 7 : Mise à jour du statut des conteneurs (Libre/Occupé)
executer_script('update_containers_status.py', "7. Mise à jour du statut des conteneurs")

# Étape 8 : Construction des images Docker
executer_script('build_images.py', "8. Construction des images Docker")

# Étape 9 : Transfert des fichiers vers les instances
executer_script('transfer_files_to_instances.py', "9. Transfert des fichiers vers les instances")

# Étape 10 : Déploiement des conteneurs d'application
executer_script('deployment.py', "10. Déploiement des conteneurs d'application")

# Étape 11 : Déploiement du conteneur orchestrateur
executer_script('deployment_orchestrator.py', "11. Déploiement du conteneur orchestrateur")

# Étape 12 : Test de la fonctionnalité de l'orchestrateur
executer_script('test_orchestrator.py', "12. Test de l'orchestrateur")
