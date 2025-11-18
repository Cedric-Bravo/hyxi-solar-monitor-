#!/usr/bin/env python3
"""
Analyse des métriques de la centrale avec calculs et interprétation
"""
from app.api_client import HyxiAPIClient
from app.tempo import TempoAPI
from config import Config
from datetime import datetime, timedelta
import json

# Configuration (récupérée depuis config.py)
PLANT_ID = Config.PLANT_ID
PLANT_NAME = Config.PLANT_NAME
TARIF_VENTE = Config.TARIF_VENTE

# TARIF_ACHAT sera récupéré dynamiquement depuis l'API Tempo
# avec fallback sur Config.TARIF_ACHAT si l'API est indisponible

def print_header(title):
    """Affiche un en-tête"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def wh_to_kwh(wh):
    """Convertit Wh en kWh"""
    return wh / 1000

def analyze_production_data(data, date, tarif_achat):
    """
    Analyse les données de production et fait des calculs
    
    Args:
        data: Données de production/consommation
        date: Date d'analyse
        tarif_achat: Tarif d'achat de l'électricité (€/kWh) - récupéré depuis Tempo API
    """

    print_header(f"Analyse des métriques - {PLANT_NAME}")
    print(f"Date: {date}")
    print(f"Intervalle: 5 minutes (300 secondes)")

    # Extraire les données
    time_points = data.get('timePoint', [])
    consume_power = data.get('consumePower', [])  # Consommation (W)
    yield_power = data.get('yieldPower', [])      # Production solaire (W)
    charged_power = data.get('chargedPower', [])  # Charge batterie (W)
    discharged_power = data.get('dischargedPower', [])  # Décharge batterie (W)
    buy_power = data.get('buyPower', [])          # Achat réseau (W)
    sell_power = data.get('sellPower', [])        # Vente réseau (W)

    nb_points = len(time_points)
    print(f"Nombre de points de données: {nb_points}")

    # Durée de chaque intervalle en heures (5 min = 300s = 0.0833h)
    interval_hours = 300 / 3600  # 5 minutes en heures

    print_header("1. Production Solaire")

    # Calcul énergie produite (W * h = Wh)
    energie_produite_wh = sum(p * interval_hours for p in yield_power)
    energie_produite_kwh = wh_to_kwh(energie_produite_wh)

    # Puissance max et moyenne
    puissance_max = max(yield_power) if yield_power else 0
    puissance_moy = sum(yield_power) / len(yield_power) if yield_power else 0

    # Heures de production (puissance > 0)
    heures_production = sum(1 for p in yield_power if p > 0) * 5 / 60

    print(f"  Énergie produite:        {energie_produite_kwh:.3f} kWh")
    print(f"  Puissance maximale:      {puissance_max:.0f} W")
    print(f"  Puissance moyenne:       {puissance_moy:.0f} W")
    print(f"  Heures de production:    {heures_production:.1f} h")
    print(f"  Taux de production:      {(puissance_moy/3000)*100:.1f}% de la capacité (3 kW)")

    print_header("2. Consommation")

    # Calcul énergie consommée
    energie_consommee_wh = sum(p * interval_hours for p in consume_power)
    energie_consommee_kwh = wh_to_kwh(energie_consommee_wh)

    puissance_conso_max = max(consume_power) if consume_power else 0
    puissance_conso_moy = sum(consume_power) / len(consume_power) if consume_power else 0

    print(f"  Énergie consommée:       {energie_consommee_kwh:.3f} kWh")
    print(f"  Puissance maximale:      {puissance_conso_max:.0f} W")
    print(f"  Puissance moyenne:       {puissance_conso_moy:.0f} W")

    print_header("3. Échanges avec le réseau")

    # Énergie achetée au réseau
    energie_achetee_wh = sum(p * interval_hours for p in buy_power)
    energie_achetee_kwh = wh_to_kwh(energie_achetee_wh)

    # Énergie vendue au réseau
    energie_vendue_wh = sum(p * interval_hours for p in sell_power)
    energie_vendue_kwh = wh_to_kwh(energie_vendue_wh)

    print(f"  Énergie achetée:         {energie_achetee_kwh:.3f} kWh")
    print(f"  Énergie vendue:          {energie_vendue_kwh:.3f} kWh")
    print(f"  Solde réseau:            {(energie_vendue_kwh - energie_achetee_kwh):.3f} kWh")

    print_header("4. Autoconsommation")

    # Autoconsommation = énergie produite et consommée directement
    # = production - vente
    energie_autoconsommee_kwh = energie_produite_kwh - energie_vendue_kwh

    # Taux d'autoconsommation (% de la production consommée sur place)
    taux_autoconso = (energie_autoconsommee_kwh / energie_produite_kwh * 100) if energie_produite_kwh > 0 else 0

    # Taux d'autoproduction (% de la consommation couverte par la production)
    taux_autoprod = (energie_autoconsommee_kwh / energie_consommee_kwh * 100) if energie_consommee_kwh > 0 else 0

    print(f"  Autoconsommation:        {energie_autoconsommee_kwh:.3f} kWh")
    print(f"  Taux d'autoconsommation: {taux_autoconso:.1f}% (énergie produite et consommée)")
    print(f"  Taux d'autoproduction:   {taux_autoprod:.1f}% (consommation couverte)")

    print_header("5. Analyse financière")
    
    print(f"  Tarif d'achat utilisé:   {tarif_achat:.4f} €/kWh")

    # Coût de l'énergie achetée
    cout_achat = energie_achetee_kwh * tarif_achat

    # Revenu de la vente
    revenu_vente = energie_vendue_kwh * TARIF_VENTE

    # Économie réalisée grâce à l'autoconsommation
    economie_autoconso = energie_autoconsommee_kwh * tarif_achat

    # Bénéfice total
    benefice_total = revenu_vente + economie_autoconso - cout_achat

    # Ce qu'aurait coûté sans panneaux
    cout_sans_panneaux = energie_consommee_kwh * tarif_achat

    # Économie réalisée
    economie_realisee = cout_sans_panneaux - cout_achat + revenu_vente

    print(f"  Coût d'achat réseau:     {cout_achat:.2f} €")
    print(f"  Revenu de vente:         {revenu_vente:.2f} €")
    print(f"  Économie autoconso:      {economie_autoconso:.2f} €")
    print(f"  ─────────────────────────────────")
    print(f"  Coût sans panneaux:      {cout_sans_panneaux:.2f} €")
    print(f"  Coût avec panneaux:      {cout_achat:.2f} €")
    print(f"  ÉCONOMIE TOTALE:         {economie_realisee:.2f} € ✓")

    print_header("6. Résumé détaillé par période")

    # Analyser par tranches horaires
    heures = {}
    for i, ts in enumerate(time_points):
        dt = datetime.fromtimestamp(ts)
        heure = dt.hour

        if heure not in heures:
            heures[heure] = {
                'production': [],
                'consommation': [],
                'achat': [],
                'vente': []
            }

        heures[heure]['production'].append(yield_power[i] if i < len(yield_power) else 0)
        heures[heure]['consommation'].append(consume_power[i] if i < len(consume_power) else 0)
        heures[heure]['achat'].append(buy_power[i] if i < len(buy_power) else 0)
        heures[heure]['vente'].append(sell_power[i] if i < len(sell_power) else 0)

    print("\n  Heure | Prod (W) | Conso (W) | Achat (W) | Vente (W) |")
    print("  " + "─" * 58)

    for h in sorted(heures.keys()):
        prod_moy = sum(heures[h]['production']) / len(heures[h]['production'])
        conso_moy = sum(heures[h]['consommation']) / len(heures[h]['consommation'])
        achat_moy = sum(heures[h]['achat']) / len(heures[h]['achat'])
        vente_moy = sum(heures[h]['vente']) / len(heures[h]['vente'])

        print(f"  {h:02d}h   | {prod_moy:7.0f}  | {conso_moy:8.0f}  | {achat_moy:8.0f}  | {vente_moy:8.0f}  |")

    print_header("7. Graphique ASCII de production")

    # Créer un graphique simple
    max_prod = max(yield_power) if yield_power else 1
    print("\n  Puissance solaire (W) sur la journée:")
    print(f"  Max: {max_prod:.0f}W")
    print()

    # Regrouper par heure pour le graphique
    hourly_data = {}
    for i, ts in enumerate(time_points):
        dt = datetime.fromtimestamp(ts)
        heure = dt.hour
        if heure not in hourly_data:
            hourly_data[heure] = []
        if i < len(yield_power):
            hourly_data[heure].append(yield_power[i])

    for h in range(24):
        if h in hourly_data:
            avg = sum(hourly_data[h]) / len(hourly_data[h])
            bar_length = int((avg / max_prod) * 50)
            bar = "█" * bar_length
            print(f"  {h:02d}h |{bar} {avg:.0f}W")
        else:
            print(f"  {h:02d}h |")

    # Retourner les données pour exploitation ultérieure
    return {
        'energie_produite_kwh': energie_produite_kwh,
        'energie_consommee_kwh': energie_consommee_kwh,
        'energie_achetee_kwh': energie_achetee_kwh,
        'energie_vendue_kwh': energie_vendue_kwh,
        'energie_autoconsommee_kwh': energie_autoconsommee_kwh,
        'taux_autoconso': taux_autoconso,
        'taux_autoprod': taux_autoprod,
        'economie_realisee': economie_realisee,
        'cout_achat': cout_achat,
        'revenu_vente': revenu_vente
    }


def main():
    # Initialiser le client
    client = HyxiAPIClient(
        access_key=Config.HYXI_ACCESS_KEY,
        secret_key=Config.HYXI_SECRET_KEY,
        base_url=Config.HYXI_API_BASE_URL,
        debug=False
    )

    # Obtenir le token
    print("Connexion à l'API Hyxi Cloud...")
    client.obtain_token()
    print("✓ Connecté\n")
    
    # Récupérer le tarif d'achat depuis l'API Tempo
    print("Récupération du tarif Tempo actuel...")
    tempo_info = TempoAPI.get_current_info()
    
    if tempo_info.get('success'):
        tarif_achat = tempo_info.get('tarif_kwh', Config.TARIF_ACHAT)
        print(f"✓ Tarif Tempo: {tarif_achat:.4f} €/kWh ({tempo_info.get('couleur')} - {tempo_info.get('horaire')})\n")
    else:
        tarif_achat = Config.TARIF_ACHAT
        print(f"⚠ Tempo API indisponible, utilisation du tarif par défaut: {tarif_achat:.4f} €/kWh\n")

    # Date d'analyse
    today = datetime.now().strftime('%Y-%m-%d')

    print(f"Récupération des données du {today}...")
    result = client.get_plant_power_statistics(PLANT_ID, today)

    if result.get('error'):
        print(f"✗ Erreur: {result.get('message')}")
        return

    data = result.get('data', {})

    # Analyser les données avec le tarif d'achat récupéré
    stats = analyze_production_data(data, today, tarif_achat)

    print_header("ANALYSE TERMINÉE")
    print(f"\nÉconomie réalisée aujourd'hui: {stats['economie_realisee']:.2f} €")
    print(f"Projection mensuelle: {stats['economie_realisee'] * 30:.2f} €")
    print(f"Projection annuelle: {stats['economie_realisee'] * 365:.2f} €\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAnalyse interrompue.")
    except Exception as e:
        print(f"\n✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
