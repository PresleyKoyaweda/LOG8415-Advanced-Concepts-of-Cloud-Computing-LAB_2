import subprocess

# Variables
docker_image_name = "my-flask-ml-app"  # Nom de l'image Docker
local_image_tar = "container_image.tar"  # Nom du fichier compressé

# Fonction pour construire l'image Docker
def build_docker_image(docker_image_name):
    try:
        print(f"Construction de l'image Docker '{docker_image_name}'...")
        # Construction de l'image Docker
        subprocess.run(["docker", "build", "-t", docker_image_name, "."], check=True)
        print(f"Image Docker '{docker_image_name}' construite avec succès.")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de la construction de l'image Docker : {e}")

# Fonction pour compresser l'image Docker en un fichier tar
def compress_docker_image(docker_image_name, local_image_tar):
    try:
        print(f"Compression de l'image Docker '{docker_image_name}' en '{local_image_tar}'...")
        # Sauvegarde de l'image Docker dans un fichier tar
        subprocess.run(["docker", "save", "-o", local_image_tar, docker_image_name], check=True)
        print(f"Image Docker compressée en '{local_image_tar}'.")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de la compression de l'image Docker : {e}")

# Construire et compresser l'image Docker
build_docker_image(docker_image_name)
compress_docker_image(docker_image_name, local_image_tar)

print(f"Fichier '{local_image_tar}' prêt pour le transfert.")
