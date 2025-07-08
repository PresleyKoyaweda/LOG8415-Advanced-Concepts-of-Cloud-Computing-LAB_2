import subprocess
import os
import gzip
import shutil

def build_and_compress_image(image_name, dockerfile_path):
    """
    Construit une image Docker à partir d'un Dockerfile et l'enregistre sous forme de fichier compressé tar.gz.
    
    Arguments :
    - image_name (str) : Le nom de l'image Docker à construire.
    - dockerfile_path (str) : Le chemin vers le Dockerfile à utiliser pour la construction.
    """
    # Construction de l'image Docker à partir du Dockerfile spécifié
    print(f"Construction de l'image Docker {image_name} en utilisant {dockerfile_path}...")
    build_command = ["docker", "build", "-f", dockerfile_path, "-t", image_name, "."]
    result = subprocess.run(build_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        # Affichage d'une erreur si la construction échoue
        print(f"Erreur lors de la construction de l'image Docker {image_name} : {result.stderr.decode('utf-8')}")
        return
    
    print(f"Image Docker {image_name} construite avec succès.")

    # Sauvegarde de l'image Docker sous forme de fichier .tar
    tar_file = f"{image_name}.tar"
    print(f"Sauvegarde de l'image Docker {image_name} sous {tar_file}...")

    try:
        # Exécution de la commande docker save pour sauvegarder l'image
        with open(tar_file, "wb") as f_out:
            save_command = ["docker", "save", image_name]
            save_process = subprocess.Popen(save_command, stdout=f_out)
            save_process.communicate()

            if save_process.returncode == 0:
                print(f"Image Docker sauvegardée sous {tar_file}.")
            else:
                print(f"Erreur lors de la sauvegarde de l'image Docker {image_name}.")
                return

        # Compression du fichier .tar en tar.gz avec gzip
        tar_gz_file = f"{image_name}.tar.gz"
        print(f"Compression de l'image Docker en {tar_gz_file}...")

        with open(tar_file, 'rb') as f_in, gzip.open(tar_gz_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

        print(f"Image Docker compressée sous {tar_gz_file}.")

        # Optionnel : suppression du fichier .tar original après compression
        os.remove(tar_file)

    except Exception as e:
        # Gestion des erreurs si la sauvegarde ou la compression échoue
        print(f"Échec de la sauvegarde ou de la compression de l'image Docker {image_name} : {e}")

# Construction et compression des images Docker

# Construire l'image de l'orchestrateur
orchestrator_image_name = "orchestrator_image"
orchestrator_dockerfile_path = "Dockerfile_orchestrator"  # Nom du Dockerfile de l'orchestrateur
build_and_compress_image(orchestrator_image_name, orchestrator_dockerfile_path)

# Construire l'image des workers
workers_image_name = "workers_image"
workers_dockerfile_path = "Dockerfile_workers"  # Nom du Dockerfile des travailleurs
build_and_compress_image(workers_image_name, workers_dockerfile_path)
