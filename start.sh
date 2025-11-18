#!/bin/bash

echo "========================================="
echo "  HyxiCalculator - Démarrage"
echo "========================================="
echo ""

# Vérifier si Docker est installé
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé."
    echo "Installation avec Python local..."
    echo ""

    # Vérifier si Python est installé
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 n'est pas installé."
        echo "Veuillez installer Python 3 et réessayer."
        exit 1
    fi

    # Créer l'environnement virtuel si nécessaire
    if [ ! -d "venv" ]; then
        echo "Création de l'environnement virtuel Python..."
        python3 -m venv venv
    fi

    # Activer l'environnement virtuel
    echo "Activation de l'environnement virtuel..."
    source venv/bin/activate

    # Installer les dépendances
    echo "Installation des dépendances..."
    pip install -r requirements.txt

    # Démarrer le serveur
    echo ""
    echo "========================================="
    echo "✅ Démarrage du serveur..."
    echo "📍 URL: http://localhost:5000"
    echo "========================================="
    echo ""
    python app/server.py

else
    echo "🐳 Docker détecté - Utilisation de Docker Compose"
    echo ""

    # Vérifier si docker-compose est installé
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose n'est pas installé."
        echo "Veuillez installer Docker Compose et réessayer."
        exit 1
    fi

    # Construire et démarrer les containers
    echo "Construction et démarrage des containers..."
    docker-compose up --build

fi
