"""
Configuration pour l'application Hyxi Solar Monitor
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration de base"""

    # API Hyxi Cloud
    HYXI_API_BASE_URL = os.getenv('HYXI_API_BASE_URL', 'https://open.hyxicloud.com')
    HYXI_ACCESS_KEY = os.getenv('HYXI_ACCESS_KEY')
    HYXI_SECRET_KEY = os.getenv('HYXI_SECRET_KEY')
    HYXI_APPLICATION = os.getenv('HYXI_APPLICATION', 'test')

    # Configuration de la centrale solaire
    PLANT_ID = os.getenv('PLANT_ID')
    PLANT_NAME = os.getenv('PLANT_NAME', 'Ma_Centrale_Solaire')
    
    # Tarifs énergétiques (€/kWh)
    TARIF_ACHAT = float(os.getenv('TARIF_ACHAT', '0.1494'))  # Prix d'achat de l'électricité du réseau (fallback si Tempo indisponible)
    TARIF_VENTE = float(os.getenv('TARIF_VENTE', '0.004'))  # Prix de revente du surplus
    
    # Revente d'électricité
    RESALE_ENABLED = os.getenv('RESALE_ENABLED', 'False').lower() == 'true'  # Active le calcul avec revente du surplus

    # Timezone
    TIMEZONE = os.getenv('TIMEZONE', 'Europe/Paris')

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
