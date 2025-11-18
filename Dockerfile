# Image de base Python
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . .

# Exposer le port 5000
EXPOSE 5000

# Variables d'environnement par défaut
ENV FLASK_APP=app/server.py
ENV PYTHONUNBUFFERED=1

# Commande de démarrage
CMD ["python", "app/server.py"]
