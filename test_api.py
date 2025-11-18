#!/usr/bin/env python3
"""
Script de test pour l'API Hyxi Cloud
Teste l'authentification et les requêtes de base
"""
import sys
import json
from app.api_client import HyxiAPIClient
from config import Config


def print_section(title):
    """Affiche un titre de section"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_success(message):
    """Affiche un message de succès"""
    print(f"✓ {message}")


def print_error(message):
    """Affiche un message d'erreur"""
    print(f"✗ {message}")


def print_json(data, indent=2):
    """Affiche des données JSON formatées"""
    print(json.dumps(data, indent=indent, ensure_ascii=False))


def main():
    print_section("Test de l'API Hyxi Cloud")
    print(f"API URL: {Config.HYXI_API_BASE_URL}")
    print(f"Access Key: {Config.HYXI_ACCESS_KEY}")
    print(f"Secret Key: {Config.HYXI_SECRET_KEY[:10]}... (masqué)")

    # Initialiser le client API
    client = HyxiAPIClient(
        access_key=Config.HYXI_ACCESS_KEY,
        secret_key=Config.HYXI_SECRET_KEY,
        base_url=Config.HYXI_API_BASE_URL
    )

    # Test 1: Obtenir un token
    print_section("Test 1: Obtention du token")
    try:
        token = client.obtain_token()
        print_success(f"Token obtenu avec succès!")
        print(f"Token: {token[:50]}... (tronqué)")
        print(f"Expire à: {client.token_expires_at}")
    except Exception as e:
        print_error(f"Erreur lors de l'obtention du token: {str(e)}")
        print("\nDétails de l'erreur:")
        import traceback
        traceback.print_exc()
        return

    # Test 2: Récupérer la liste des plants
    print_section("Test 2: Récupération de la liste des plants")
    try:
        result = client.get_plant_list(page_size=10)

        if result.get('error'):
            print_error(f"Erreur: {result.get('message')}")
            print("\nRéponse complète:")
            print_json(result)
        else:
            print_success("Liste des plants récupérée!")

            # Extraire les plants
            data = result.get('data', {})
            plants = data.get('list', [])
            total = data.get('total', 0)

            print(f"\nNombre total de plants: {total}")
            print(f"Plants dans cette page: {len(plants)}")

            if plants:
                print("\nListe des installations:")
                for i, plant in enumerate(plants, 1):
                    print(f"\n  {i}. {plant.get('plantName', 'Sans nom')}")
                    print(f"     ID: {plant.get('plantId')}")
                    print(f"     Capacité: {plant.get('capacity', 0)} kW")
                    print(f"     Statut: {'En ligne' if plant.get('status') == 1 else 'Hors ligne'}")

                # Stocker le premier plant pour les tests suivants
                first_plant_id = plants[0].get('plantId')
                first_plant_name = plants[0].get('plantName', 'Premier plant')
            else:
                print("\nAucun plant trouvé.")
                return
    except Exception as e:
        print_error(f"Erreur lors de la récupération des plants: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    # Test 3: Récupérer les infos d'un plant spécifique
    print_section(f"Test 3: Informations détaillées de '{first_plant_name}'")
    try:
        result = client.get_plant_info(first_plant_id)

        if result.get('error'):
            print_error(f"Erreur: {result.get('message')}")
            print("\nRéponse complète:")
            print_json(result)
        else:
            print_success("Informations du plant récupérées!")
            print("\nDonnées du plant:")
            print_json(result.get('data', {}))
    except Exception as e:
        print_error(f"Erreur lors de la récupération des infos du plant: {str(e)}")
        import traceback
        traceback.print_exc()

    # Test 4: Récupérer les statistiques de production
    print_section(f"Test 4: Statistiques de production de '{first_plant_name}'")
    try:
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')

        result = client.get_plant_power_statistics(first_plant_id, today)

        if result.get('error'):
            print_error(f"Erreur: {result.get('message')}")
            print("\nRéponse complète:")
            print_json(result)
        else:
            print_success(f"Statistiques récupérées pour le {today}!")
            print("\nDonnées de production:")
            print_json(result.get('data', {}))
    except Exception as e:
        print_error(f"Erreur lors de la récupération des statistiques: {str(e)}")
        import traceback
        traceback.print_exc()

    # Test 5: Récupérer les données en temps réel
    print_section(f"Test 5: Données en temps réel de '{first_plant_name}'")
    try:
        result = client.get_plant_realtime_data(first_plant_id)

        if result.get('error'):
            print_error(f"Erreur: {result.get('message')}")
            print("\nRéponse complète:")
            print_json(result)
        else:
            print_success("Données en temps réel récupérées!")
            print("\nDonnées temps réel:")
            print_json(result.get('data', {}))
    except Exception as e:
        print_error(f"Erreur lors de la récupération des données temps réel: {str(e)}")
        import traceback
        traceback.print_exc()

    # Résumé
    print_section("Résumé des tests")
    print("Tests terminés! Vérifiez les résultats ci-dessus.")
    print("\nSi tous les tests sont réussis (✓), l'application devrait fonctionner correctement.")
    print("Si des erreurs apparaissent (✗), vérifiez:")
    print("  - Les clés API (AK/SK)")
    print("  - La connexion internet")
    print("  - Les permissions de votre compte API")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrompu par l'utilisateur.")
        sys.exit(0)
    except Exception as e:
        print_error(f"Erreur inattendue: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
