"""
Script d'export des données pour Figma
Récupère toutes les données de l'API et les exporte en JSON
"""
import requests
import json
from datetime import datetime

# URL de base de l'API
BASE_URL = "http://localhost:5000"

def export_data():
    """Exporte toutes les données de l'API dans un fichier JSON"""
    
    print("🔄 Récupération des données depuis l'API...")
    
    data = {
        "export_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "realtime": {},
        "production": {},
        "tempo_now": {},
        "tempo_tomorrow": {},
        "config": {}
    }
    
    try:
        # Données en temps réel
        print("  📊 Données temps réel...")
        response = requests.get(f"{BASE_URL}/api/plant/realtime", timeout=10)
        if response.status_code == 200:
            data["realtime"] = response.json()
            print("  ✅ Données temps réel récupérées")
        else:
            print(f"  ❌ Erreur temps réel: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Erreur temps réel: {e}")
    
    try:
        # Production du jour
        print("  📈 Production du jour...")
        response = requests.get(f"{BASE_URL}/api/energy/production?period=day", timeout=10)
        if response.status_code == 200:
            data["production"] = response.json()
            print("  ✅ Production récupérée")
        else:
            print(f"  ❌ Erreur production: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Erreur production: {e}")
    
    try:
        # Tempo aujourd'hui
        print("  🔵 Tempo aujourd'hui...")
        response = requests.get(f"{BASE_URL}/api/tempo/now", timeout=10)
        if response.status_code == 200:
            data["tempo_now"] = response.json()
            print("  ✅ Tempo aujourd'hui récupéré")
        else:
            print(f"  ❌ Erreur Tempo now: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Erreur Tempo now: {e}")
    
    try:
        # Tempo demain
        print("  🔵 Tempo demain...")
        response = requests.get(f"{BASE_URL}/api/tempo/tomorrow", timeout=10)
        if response.status_code == 200:
            data["tempo_tomorrow"] = response.json()
            print("  ✅ Tempo demain récupéré")
        else:
            print(f"  ❌ Erreur Tempo tomorrow: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Erreur Tempo tomorrow: {e}")
    
    try:
        # Configuration
        print("  ⚙️ Configuration...")
        response = requests.get(f"{BASE_URL}/api/config", timeout=10)
        if response.status_code == 200:
            data["config"] = response.json()
            print("  ✅ Configuration récupérée")
        else:
            print(f"  ❌ Erreur config: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Erreur config: {e}")
    
    # Export du fichier JSON
    output_file = "figma_data.json"
    print(f"\n💾 Export des données vers {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Export terminé ! Fichier créé : {output_file}")
    print(f"\n📋 Résumé des données exportées:")
    
    # Afficher un résumé
    if data["realtime"].get("success"):
        realtime_data = data["realtime"].get("data", {})
        print(f"  Production actuelle: {realtime_data.get('currentPowerProduced', 0)} W")
        print(f"  Consommation actuelle: {realtime_data.get('currentPowerConsumed', 0)} W")
        print(f"  Economie du jour: {realtime_data.get('todayIncome', 0)} €")
    
    if data["production"].get("success"):
        prod_data = data["production"].get("data", {})
        print(f"  Énergie produite: {prod_data.get('energy', 0)} kWh")
        print(f"  Puissance de pointe: {prod_data.get('peakPower', 0)} kW")
    
    if data["tempo_now"].get("success"):
        tempo = data["tempo_now"]
        print(f"  Tempo aujourd'hui: {tempo.get('couleur_emoji', '')} {tempo.get('couleur', '')} - {tempo.get('horaire', '')}")
        print(f"  Tarif: {tempo.get('tarif_kwh', 0):.4f} €/kWh")
    
    if data["tempo_tomorrow"].get("success"):
        tempo_tom = data["tempo_tomorrow"]
        print(f"  Tempo demain: {tempo_tom.get('couleur_emoji', '')} {tempo_tom.get('couleur', '')}")
        print(f"  Tarif HP: {tempo_tom.get('tarif_hp', 0):.4f} €/kWh")

if __name__ == "__main__":
    print("=" * 60)
    print("📊 EXPORT DE DONNÉES POUR FIGMA")
    print("=" * 60)
    print()
    export_data()
    print()
    print("=" * 60)
