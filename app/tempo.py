"""
Module pour récupérer les informations Tempo EDF
API: https://www.api-couleur-tempo.fr
"""
import requests
from typing import Dict, Any
from datetime import datetime
import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config


class TempoAPI:
    """Client pour l'API Couleur Tempo"""

    BASE_URL = "https://www.api-couleur-tempo.fr/api"

    # Mapping des codes couleurs
    COULEURS = {
        1: {"nom": "BLEU", "emoji": "🔵", "css": "blue"},
        2: {"nom": "BLANC", "emoji": "⚪", "css": "white"},
        3: {"nom": "ROUGE", "emoji": "🔴", "css": "red"}
    }

    # Mapping des codes horaires
    HORAIRES = {
        1: {"nom": "HP", "label": "Heures Pleines"},
        2: {"nom": "HC", "label": "Heures Creuses"}
    }

    @classmethod
    def get_current_info(cls) -> Dict[str, Any]:
        """
        Récupère les informations actuelles (couleur + horaire + tarif)
        Utilise le tarif Tempo de l'API, ou fallback sur Config.TARIF_ACHAT si erreur

        Returns:
            {
                'couleur': 'BLEU',
                'couleur_emoji': '🔵',
                'horaire': 'HP',
                'tarif_kwh': 0.1494,
                'libelle': 'Bleu-HP',
                'timestamp': '2025-11-12 15:30:00'
            }
        """
        try:
            response = requests.get(f"{cls.BASE_URL}/now", timeout=5)
            response.raise_for_status()
            data = response.json()

            code_couleur = data.get('codeCouleur', 1)
            code_horaire = data.get('codeHoraire', 1)

            couleur_info = cls.COULEURS.get(code_couleur, cls.COULEURS[1])
            horaire_info = cls.HORAIRES.get(code_horaire, cls.HORAIRES[1])

            return {
                'success': True,
                'couleur': couleur_info['nom'],
                'couleur_emoji': couleur_info['emoji'],
                'couleur_css': couleur_info['css'],
                'horaire': horaire_info['nom'],
                'horaire_label': horaire_info['label'],
                'tarif_kwh': data.get('tarifKwh', Config.TARIF_ACHAT),
                'libelle': data.get('libTarif', 'Inconnu'),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'code_couleur': code_couleur,
                'code_horaire': code_horaire
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'couleur': 'BLEU',  # Valeur par défaut
                'couleur_emoji': '🔵',
                'couleur_css': 'blue',
                'horaire': 'HP',
                'tarif_kwh': Config.TARIF_ACHAT,  # Utilise le tarif de config en fallback
                'libelle': 'Erreur API'
            }

    @classmethod
    def get_all_tarifs(cls) -> Dict[str, Any]:
        """
        Récupère tous les tarifs Tempo

        Returns:
            {
                'bleuHC': 0.1232,
                'bleuHP': 0.1494,
                'blancHC': 0.1391,
                'blancHP': 0.173,
                'rougeHC': 0.146,
                'rougeHP': 0.6468
            }
        """
        try:
            response = requests.get(f"{cls.BASE_URL}/tarifs", timeout=5)
            response.raise_for_status()
            data = response.json()

            return {
                'success': True,
                'tarifs': {
                    'bleu': {
                        'HC': data.get('bleuHC', 0.1232),
                        'HP': data.get('bleuHP', 0.1494)
                    },
                    'blanc': {
                        'HC': data.get('blancHC', 0.1391),
                        'HP': data.get('blancHP', 0.173)
                    },
                    'rouge': {
                        'HC': data.get('rougeHC', 0.146),
                        'HP': data.get('rougeHP', 0.6468)
                    }
                },
                'date_debut': data.get('dateDebut', 'Inconnu')
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tarifs': {
                    'bleu': {'HC': 0.1232, 'HP': 0.1494},
                    'blanc': {'HC': 0.1391, 'HP': 0.173},
                    'rouge': {'HC': 0.146, 'HP': 0.6468}
                }
            }

    @classmethod
    def get_tarif_for_color_and_time(cls, couleur: str, horaire: str) -> float:
        """
        Récupère le tarif pour une couleur et une période donnée

        Args:
            couleur: 'bleu', 'blanc' ou 'rouge'
            horaire: 'HP' ou 'HC'

        Returns:
            Tarif en €/kWh
        """
        tarifs_data = cls.get_all_tarifs()
        if not tarifs_data.get('success'):
            return 0.1494  # Valeur par défaut

        couleur_lower = couleur.lower()
        return tarifs_data['tarifs'].get(couleur_lower, {}).get(horaire, 0.1494)

    @classmethod
    def get_tomorrow_info(cls) -> Dict[str, Any]:
        """
        Récupère les informations de demain (couleur + tarif HP)

        Returns:
            {
                'success': True,
                'couleur': 'BLEU',
                'couleur_emoji': '🔵',
                'couleur_css': 'bleu',
                'tarif_hp': 0.1494,
                'date': '2025-11-13'
            }
        """
        try:
            from datetime import datetime, timedelta
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            
            response = requests.get(f"{cls.BASE_URL}/jourTempo/{tomorrow}", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                couleur_code = data.get('codeJour')
                
                if couleur_code and couleur_code in cls.COULEURS:
                    couleur_info = cls.COULEURS[couleur_code]
                    couleur_nom = couleur_info['nom']
                    
                    # Récupérer le tarif HP
                    tarif_hp = cls.get_tarif_for_color_and_time(couleur_nom, 'HP')
                    
                    return {
                        'success': True,
                        'couleur': couleur_nom,
                        'couleur_emoji': couleur_info['emoji'],
                        'couleur_css': couleur_info['css'],
                        'tarif_hp': tarif_hp,
                        'date': tomorrow
                    }
            
            return {
                'success': False,
                'message': 'Données demain non disponibles',
                'couleur': 'Inconnu',
                'couleur_emoji': '❓',
                'tarif_hp': Config.TARIF_ACHAT
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
                'couleur': 'Erreur',
                'couleur_emoji': '⚠️',
                'tarif_hp': Config.TARIF_ACHAT
            }

    @classmethod
    def get_day_info(cls, date_str: str) -> Dict[str, Any]:
        """
        Récupère les informations Tempo pour une date spécifique
        API: https://www.api-couleur-tempo.fr/api/jourTempo/{datejour}

        Args:
            date_str: Date au format YYYY-MM-DD

        Returns:
            {
                'success': True,
                'date': '2024-11-14',
                'couleur': 'BLEU',
                'couleur_emoji': '🔵',
                'couleur_css': 'bleu',
                'tarif_hp': 0.1494,
                'tarif_hc': 0.1232
            }
        """
        try:
            response = requests.get(f"{cls.BASE_URL}/jourTempo/{date_str}", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                couleur_code = data.get('codeJour')
                
                if couleur_code and couleur_code in cls.COULEURS:
                    couleur_info = cls.COULEURS[couleur_code]
                    couleur_nom = couleur_info['nom']
                    
                    # Récupérer les tarifs HP et HC
                    tarif_hp = cls.get_tarif_for_color_and_time(couleur_nom, 'HP')
                    tarif_hc = cls.get_tarif_for_color_and_time(couleur_nom, 'HC')
                    
                    return {
                        'success': True,
                        'date': date_str,
                        'couleur': couleur_nom,
                        'couleur_emoji': couleur_info['emoji'],
                        'couleur_css': couleur_info['css'],
                        'tarif_hp': tarif_hp,
                        'tarif_hc': tarif_hc
                    }
            
            return {
                'success': False,
                'message': f'Données non disponibles pour {date_str}',
                'date': date_str,
                'tarif_hp': Config.TARIF_ACHAT,
                'tarif_hc': Config.TARIF_ACHAT * 0.6
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
                'date': date_str,
                'tarif_hp': Config.TARIF_ACHAT,
                'tarif_hc': Config.TARIF_ACHAT * 0.6
            }
