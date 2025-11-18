"""
Serveur Flask pour Hyxi Solar Monitor
Expose les données de télémétrie via API REST et interface web
"""
from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import pytz
import sys
import os
import time

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from app.api_client import HyxiAPIClient
from app.tempo import TempoAPI

# Timezone configuré
TIMEZONE = pytz.timezone(Config.TIMEZONE)

def now_tz():
    """Retourne l'heure actuelle dans le timezone configuré"""
    return datetime.now(TIMEZONE)

def from_timestamp_tz(timestamp):
    """Convertit un timestamp UTC en datetime avec le timezone configuré"""
    return datetime.fromtimestamp(timestamp, tz=pytz.UTC).astimezone(TIMEZONE)


def get_tempo_tarif(date_str):
    """
    Récupère les tarifs Tempo pour une date avec cache global
    Args:
        date_str: Date au format YYYY-MM-DD
    Returns:
        dict: {tarif_hp, tarif_hc, couleur, couleur_css}
    """
    with TEMPO_CACHE_LOCK:
        if date_str in TEMPO_CACHE:
            return TEMPO_CACHE[date_str]
        
        # Appel API
        day_info = TempoAPI.get_day_info(date_str)
        if day_info.get('success'):
            tarif_data = {
                'tarif_hp': day_info['tarif_hp'],
                'tarif_hc': day_info['tarif_hc'],
                'couleur': day_info.get('couleur', 'INCONNU'),
                'couleur_css': day_info.get('couleur_css', 'gray')
            }
        else:
            tarif_data = {
                'tarif_hp': Config.TARIF_ACHAT,
                'tarif_hc': Config.TARIF_ACHAT * 0.6,
                'couleur': 'INCONNU',
                'couleur_css': 'gray'
            }
        
        TEMPO_CACHE[date_str] = tarif_data
        return tarif_data


def get_daylight_hours(date_str):
    """
    Récupère les heures d'ensoleillement depuis l'API météo Hyxi
    Args:
        date_str: Date au format YYYY-MM-DD
    Returns:
        float: Nombre d'heures d'ensoleillement (sunrise à sunset)
    """
    try:
        weather_data = hyxi_client.get_plant_weather(Config.PLANT_ID)
        if weather_data.get('success') and 'data' in weather_data:
            days = weather_data['data'].get('days', [])
            for day in days:
                if day.get('date') == date_str:
                    sunrise = day.get('sunrise', '06:00')  # Format "HH:MM"
                    sunset = day.get('sunset', '18:00')
                    
                    # Calculer la différence en heures
                    sunrise_h, sunrise_m = map(int, sunrise.split(':'))
                    sunset_h, sunset_m = map(int, sunset.split(':'))
                    
                    sunrise_minutes = sunrise_h * 60 + sunrise_m
                    sunset_minutes = sunset_h * 60 + sunset_m
                    
                    daylight_minutes = sunset_minutes - sunrise_minutes
                    return daylight_minutes / 60.0
        
        # Fallback: moyenne de 12h
        return 12.0
    except Exception as e:
        print(f"Erreur récupération météo: {e}")
        return 12.0


# Initialisation de l'application Flask
app = Flask(__name__)
app.config.from_object(Config)

# Cache global pour les tarifs Tempo (partagé entre toutes les requêtes)
# {date_str: {tarif_hp, tarif_hc, couleur, couleur_css}}
TEMPO_CACHE = {}
TEMPO_CACHE_LOCK = __import__('threading').Lock()


# Initialisation du client Hyxi
hyxi_client = HyxiAPIClient(
    access_key=Config.HYXI_ACCESS_KEY,
    secret_key=Config.HYXI_SECRET_KEY,
    base_url=Config.HYXI_API_BASE_URL
)


# Routes pour l'interface web
@app.route('/')
def index():
    """Page d'accueil - Dashboard de télémétrie"""
    return render_template('index.html', plant_name=Config.PLANT_NAME)


# Routes API pour récupérer les données
@app.route('/api/status')
def api_status():
    """Test de connexion à l'API Hyxi"""
    result = hyxi_client.test_connection()
    return jsonify(result)


@app.route('/api/tempo/now')
def api_tempo_now():
    """Informations Tempo actuelles (couleur + tarif)"""
    result = TempoAPI.get_current_info()
    return jsonify(result)


@app.route('/api/tempo/tarifs')
def api_tempo_tarifs():
    """Tous les tarifs Tempo"""
    result = TempoAPI.get_all_tarifs()
    return jsonify(result)


@app.route('/api/tempo/tomorrow')
def api_tempo_tomorrow():
    """Informations Tempo pour demain (couleur + tarif HP)"""
    result = TempoAPI.get_tomorrow_info()
    return jsonify(result)


@app.route('/api/config')
def api_config():
    """Retourne la configuration de l'installation (PLANT_NAME uniquement pour affichage)"""
    return jsonify({
        'plant_name': Config.PLANT_NAME,
        'tarif_vente': Config.TARIF_VENTE
    })


@app.route('/api/plant/info')
def api_plant_info():
    """Informations détaillées de l'installation configurée"""
    result = hyxi_client.get_plant_info(Config.PLANT_ID)
    return jsonify(result)


@app.route('/api/plant/power-generation')
def api_plant_power_generation():
    """Production d'énergie (jour/mois/année/total)"""
    result = hyxi_client.get_plant_power_generation(Config.PLANT_ID)
    return jsonify(result)


@app.route('/api/plant/yield-statistics')
def api_plant_yield_statistics():
    """Statistiques de production par période"""
    time_type = int(request.args.get('time_type', 1))  # 1=mois, 2=année, 3=total
    start_time = request.args.get('start_time', now_tz().strftime('%Y-%m'))
    result = hyxi_client.get_plant_yield_statistics(Config.PLANT_ID, time_type, start_time)
    return jsonify(result)


@app.route('/api/plant/statistics')
def api_plant_statistics():
    """Statistiques de production de l'installation configurée"""
    start_time = request.args.get('start_time')

    # Si pas de start_time fournie, utiliser aujourd'hui
    if not start_time:
        start_time = now_tz().strftime('%Y-%m-%d')

    result = hyxi_client.get_plant_power_statistics(Config.PLANT_ID, start_time)
    return jsonify(result)


@app.route('/api/plant/realtime')
def api_plant_realtime():
    """
    Données en temps réel de l'installation configurée
    Combine les infos de l'installation et les statistiques du jour
    """
    try:
        # Récupérer les infos de base de l'installation
        plant_info = hyxi_client.get_plant_info(Config.PLANT_ID)
        
        if plant_info.get('error'):
            return jsonify(plant_info)
        
        # Récupérer les statistiques du jour pour les données en temps réel
        today = now_tz().strftime('%Y-%m-%d')
        stats = hyxi_client.get_plant_power_statistics(Config.PLANT_ID, today)
        
        plant_data = plant_info.get('data', {})
        stats_data = stats.get('data', {}) if not stats.get('error') else {}
        
        # Extraire les tableaux de puissance et timestamps
        yield_power = stats_data.get('yieldPower', [])        # Production solaire (W)
        consume_power = stats_data.get('consumePower', [])    # Consommation (W)
        buy_power = stats_data.get('buyPower', [])            # Achat réseau (W)
        time_points = stats_data.get('timePoint', [])         # Timestamps (secondes Unix)
        
        # Calculer l'énergie totale du jour en kWh (intervalles de 5 min)
        interval_hours = 5 / 60  # 5 minutes en heures
        
        energy_produced_kwh = sum(p * interval_hours for p in yield_power) / 1000 if yield_power else 0
        energy_consumed_kwh = sum(p * interval_hours for p in consume_power) / 1000 if consume_power else 0
        energy_bought_kwh = sum(p * interval_hours for p in buy_power) / 1000 if buy_power else 0
        
        # Puissance actuelle (dernière valeur non nulle ou zéro)
        current_power_produced = yield_power[-1] if yield_power and len(yield_power) > 0 else 0
        current_power_consumed = consume_power[-1] if consume_power and len(consume_power) > 0 else 0
        current_power_bought = buy_power[-1] if buy_power and len(buy_power) > 0 else 0
        
        # Timestamp de la dernière mesure
        last_measurement_time = time_points[-1] if time_points and len(time_points) > 0 else None
        last_measurement_datetime = from_timestamp_tz(last_measurement_time).strftime('%Y-%m-%d %H:%M:%S') if last_measurement_time else None
        
        # Récupérer le tarif Tempo actuel
        tempo_info = TempoAPI.get_current_info()
        tarif_achat = tempo_info.get('tarif_kwh', Config.TARIF_ACHAT)
        
        # Calculer le revenu du jour
        if Config.RESALE_ENABLED:
            # Mode revente : calcul point par point
            interval_hours = 5 / 60
            revenu_autoconso = 0  # Économie sur achat évité
            revenu_vente = 0      # Gain sur surplus vendu
            
            for i in range(len(yield_power)):
                prod = yield_power[i] if i < len(yield_power) else 0
                cons = consume_power[i] if i < len(consume_power) else 0
                
                if prod >= cons:
                    # Surplus : autoconso complète + vente du surplus
                    autoconso_kwh = (cons * interval_hours) / 1000
                    surplus_kwh = ((prod - cons) * interval_hours) / 1000
                    revenu_autoconso += autoconso_kwh * tarif_achat
                    revenu_vente += surplus_kwh * Config.TARIF_VENTE
                else:
                    # Déficit : autoconso partielle
                    autoconso_kwh = (prod * interval_hours) / 1000
                    revenu_autoconso += autoconso_kwh * tarif_achat
            
            revenu_jour = revenu_autoconso + revenu_vente
        else:
            # Mode simple : toute la production est autoconsommée
            energy_autoconsummed_kwh = energy_produced_kwh
            revenu_jour = energy_autoconsummed_kwh * tarif_achat
        
        return jsonify({
            'success': True,
            'data': {
                # Puissances actuelles (W)
                'currentPowerProduced': round(current_power_produced, 0),
                'currentPowerConsumed': round(current_power_consumed, 0),
                'currentPowerBought': round(current_power_bought, 0),
                
                # Énergies du jour (kWh)
                'todayEnergyProduced': round(energy_produced_kwh, 2),
                'todayEnergyConsumed': round(energy_consumed_kwh, 2),
                'todayEnergyBought': round(energy_bought_kwh, 2),
                
                # Revenu du jour (€)
                'todayIncome': round(revenu_jour, 2),
                
                # Rendement instantané (%)
                'currentYieldPercent': round((current_power_produced / (plant_data.get('capacity', 1) * 1000)) * 100, 1) if plant_data.get('capacity', 0) > 0 else 0,
                
                # Timestamp dernière mesure
                'lastMeasurementTime': last_measurement_datetime,
                
                # Infos installation
                'plantName': plant_data.get('plantName', Config.PLANT_NAME),
                'capacity': plant_data.get('capacity', 0),
                'status': 1 if current_power_produced > 0 else 0,
                
                # Tarif utilisé
                'tarifAchat': round(tarif_achat, 4)
            }
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': str(e)
        })


@app.route('/api/energy/production')
def api_energy_production():
    """
    Production d'énergie pour une période donnée
    - Jour : données toutes les 5 min (queryPlantPowerStatistics)
    - Semaine : données agrégées par jour sur 7 jours glissants (queryPlantYieldStatistics type=2)
    - Mois : données agrégées par jour sur 30 jours glissants (queryPlantYieldStatistics type=2)
    - Année : données agrégées par mois sur 12 mois glissants (queryPlantYieldStatistics type=3)
    """
    period = request.args.get('period', 'day')
    selected_date = request.args.get('date', None)

    now = now_tz()
    
    if selected_date:
        try:
            reference_date = TIMEZONE.localize(datetime.strptime(selected_date, '%Y-%m-%d'))
        except ValueError:
            return jsonify({'error': True, 'message': 'Format de date invalide'}), 400
    else:
        reference_date = now
    
    # Router vers la fonction appropriée
    if period == 'day':
        return _handle_day_period(reference_date)
    elif period == 'week':
        return _handle_week_period(reference_date)
    elif period == 'month':
        return _handle_month_period(reference_date)
    elif period == 'year':
        return _handle_year_period(reference_date)
    else:
        return jsonify({'error': True, 'message': 'Période invalide'}), 400


def _handle_day_period(reference_date):
    """Période 'jour' : données toutes les 5 min"""
    start_time = reference_date.strftime('%Y-%m-%d')
    result = hyxi_client.get_plant_power_statistics(Config.PLANT_ID, start_time)
    
    # Récupérer la capacité installée depuis l'API
    plant_info = hyxi_client.get_plant_info(Config.PLANT_ID)
    plant_capacity_kw = plant_info.get('data', {}).get('capacity', 0) if not plant_info.get('error') else 0
    
    # Traiter les données pour le graphique en courbes (points de 5 min)
    if not result.get('error'):
        stats_data = result.get('data', {})
        yield_power = stats_data.get('yieldPower', [])
        consume_power = stats_data.get('consumePower', [])
        time_points = stats_data.get('timePoint', [])
        
        interval_hours = 5 / 60  # 5 minutes en heures
        
        # Préparer les données pour le graphique en courbes
        labels = []
        production_power = []  # W
        consumption_power = []  # W
        
        for i, timestamp in enumerate(time_points):
            dt = from_timestamp_tz(timestamp)
            
            # Format HH:MM pour la journée
            label = dt.strftime('%H:%M')
            
            labels.append(label)
            production_power.append(yield_power[i] if i < len(yield_power) else 0)
            consumption_power.append(consume_power[i] if i < len(consume_power) else 0)
        
        # Calculer l'énergie totale en kWh
        total_production = sum(p * interval_hours for p in yield_power) / 1000 if yield_power else 0
        total_consumption = sum(p * interval_hours for p in consume_power) / 1000 if consume_power else 0
        
        # Calculer l'achat total (achat = consommation - production, avec minimum à 0)
        buy_power = stats_data.get('buyPower', [])
        total_buy = sum(p * interval_hours for p in buy_power) / 1000 if buy_power else 0
        
        chart_data = {
            'labels': labels,
            'production': production_power,  # En W pour affichage direct
            'consumption': consumption_power  # En W pour affichage direct
        }
        
        # Puissance de pointe
        peak_power_w = max(yield_power) if yield_power else 0
        peak_power_kw = peak_power_w / 1000
        
        # Calculer le revenu selon le mode avec tarifs historisés
        # Optimisation : cache des tarifs par date pour éviter trop d'appels API
        tarifs_cache = {}  # {date_str: {tarif_hp, tarif_hc, couleur, couleur_css}}
        
        if Config.RESALE_ENABLED:
            # Mode revente : calcul point par point avec tarifs historisés
            revenu_autoconso = 0
            revenu_vente = 0
            
            for i in range(len(yield_power)):
                prod = yield_power[i] if i < len(yield_power) else 0
                cons = consume_power[i] if i < len(consume_power) else 0
                timestamp = time_points[i] if i < len(time_points) else None
                
                if not timestamp:
                    tarif_achat = Config.TARIF_ACHAT
                else:
                    # Récupérer le tarif avec cache
                    dt = from_timestamp_tz(timestamp)
                    date_str = dt.strftime('%Y-%m-%d')
                    
                    if date_str not in tarifs_cache:
                        tarifs_cache[date_str] = get_tempo_tarif(date_str)
                    
                    # Déterminer HP/HC
                    hour = dt.hour
                    is_hp = 6 <= hour < 22
                    tarif_achat = tarifs_cache[date_str]['tarif_hp'] if is_hp else tarifs_cache[date_str]['tarif_hc']
                
                if prod >= cons:
                    # Surplus : autoconso complète + vente du surplus
                    autoconso_kwh = (cons * interval_hours) / 1000
                    surplus_kwh = ((prod - cons) * interval_hours) / 1000
                    revenu_autoconso += autoconso_kwh * tarif_achat
                    revenu_vente += surplus_kwh * Config.TARIF_VENTE
                else:
                    # Déficit : autoconso partielle
                    autoconso_kwh = (prod * interval_hours) / 1000
                    revenu_autoconso += autoconso_kwh * tarif_achat
            
            revenu = revenu_autoconso + revenu_vente
        else:
            # Mode simple : calcul avec tarifs historisés point par point
            revenu = 0
            for i in range(len(yield_power)):
                prod = yield_power[i] if i < len(yield_power) else 0
                timestamp = time_points[i] if i < len(time_points) else None
                
                if not timestamp:
                    tarif_achat = Config.TARIF_ACHAT
                else:
                    # Récupérer le tarif avec cache global
                    dt = from_timestamp_tz(timestamp)
                    date_str = dt.strftime('%Y-%m-%d')
                    
                    if date_str not in tarifs_cache:
                        tarifs_cache[date_str] = get_tempo_tarif(date_str)
                    
                    # Déterminer HP/HC
                    hour = dt.hour
                    is_hp = 6 <= hour < 22
                    tarif_achat = tarifs_cache[date_str]['tarif_hp'] if is_hp else tarifs_cache[date_str]['tarif_hc']
                
                # Calculer la production en kWh pour cet intervalle
                prod_kwh = (prod * interval_hours) / 1000
                revenu += prod_kwh * tarif_achat
        
        # Préparer les zones de couleur Tempo pour le graphique
        tempo_zones = []
        for date_str, tarif_data in sorted(tarifs_cache.items()):
            tempo_zones.append({
                'date': date_str,
                'couleur': tarif_data.get('couleur', 'INCONNU'),
                'couleur_css': tarif_data.get('couleur_css', 'gray')
            })
        
        chart_data['tempo_zones'] = tempo_zones
        
        # Calcul du taux d'autoconsommation (%)
        # Autoconsommation = production qui n'est pas vendue / production totale
        if total_production > 0:
            # En mode RESALE: on a revenu_vente qui représente l'énergie vendue
            if Config.RESALE_ENABLED and revenu_vente > 0:
                # Estimer l'énergie vendue depuis le revenu
                energie_vendue = revenu_vente / Config.TARIF_VENTE if Config.TARIF_VENTE > 0 else 0
                autoconso_rate = ((total_production - energie_vendue) / total_production) * 100
            else:
                # En mode simple, on considère que toute la production est autoconsommée
                autoconso_rate = min((total_production / total_consumption) * 100, 100) if total_consumption > 0 else 100
        else:
            autoconso_rate = 0
        
        # Rendement des panneaux (%)
        # Pour une journée : production réelle / (puissance crête × heures ensoleillement) × 100
        # Exemple : 3 kWc qui produit 10 kWh sur 10h = 10 / (3 × 10) = 33.3%
        daylight_hours = get_daylight_hours(start_time)
        theoretical_max = plant_capacity_kw * daylight_hours  # kWh théorique max sur les heures d'ensoleillement
        pv_performance = (total_production / theoretical_max * 100) if theoretical_max > 0 else 0
        
        return jsonify({
            'success': True,
            'period': 'day',
            'start_time': reference_date.strftime('%Y-%m-%d'),
            'data': {
                'energy': round(total_production, 2),
                'consumption': round(total_consumption, 2),
                'buy': round(total_buy, 2),
                'peakPower': round(peak_power_kw, 3),
                'income': round(revenu, 2),
                'autoconsoRate': round(autoconso_rate, 1),
                'pvPerformance': round(pv_performance, 1)
            },
            'chart_data': chart_data
        })
    
    return jsonify(result)


def _handle_week_period(reference_date):
    """Période 'semaine' : données agrégées par jour sur 7 jours glissants"""
    # Récupérer la capacité installée depuis l'API
    plant_info = hyxi_client.get_plant_info(Config.PLANT_ID)
    plant_capacity_kw = plant_info.get('data', {}).get('capacity', 0) if not plant_info.get('error') else 0
    
    # Calculer la période de 7 jours
    end_date = reference_date
    start_date = end_date - timedelta(days=6)  # 7 jours incluant today
    
    # Récupérer les données agrégées par jour
    # On doit potentiellement appeler pour 2 mois si la semaine chevauche 2 mois
    results = []
    current_month = start_date.replace(day=1)
    
    while current_month <= end_date:
        month_str = current_month.strftime('%Y-%m')
        result = hyxi_client.get_plant_yield_statistics(Config.PLANT_ID, 2, month_str)
        if not result.get('error'):
            results.append(result.get('data', {}))
        current_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)
    
    # Fusionner et filtrer les données pour les 7 derniers jours
    all_data = {
        'yield': [],
        'consume': [],
        'buyYield': [],
        'sellYield': [],
        'timePoint': []
    }
    
    for data in results:
        for key in all_data.keys():
            all_data[key].extend(data.get(key, []))
    
    # Filtrer pour garder uniquement les 7 derniers jours
    filtered_data = {
        'yield': [],
        'consume': [],
        'buyYield': [],
        'sellYield': [],
        'timePoint': []
    }
    
    # Les timestamps de queryPlantYieldStatistics sont en SECONDES (pas ms)
    start_ts = int(start_date.timestamp())
    end_ts = int((end_date + timedelta(days=1)).timestamp())
    
    for i, ts in enumerate(all_data['timePoint']):
        if start_ts <= ts < end_ts:
            for key in filtered_data.keys():
                if i < len(all_data[key]):
                    filtered_data[key].append(all_data[key][i])
    
    return _process_aggregated_data(filtered_data, 'week', start_date, end_date, plant_capacity_kw)


def _handle_month_period(reference_date):
    """Période 'mois' : données agrégées par jour sur 30 jours glissants"""
    # Récupérer la capacité installée depuis l'API
    plant_info = hyxi_client.get_plant_info(Config.PLANT_ID)
    plant_capacity_kw = plant_info.get('data', {}).get('capacity', 0) if not plant_info.get('error') else 0
    
    end_date = reference_date
    start_date = end_date - timedelta(days=29)  # 30 jours incluant today
    
    # Récupérer les données pour les mois concernés (potentiellement 2 mois)
    results = []
    current_month = start_date.replace(day=1)
    
    while current_month <= end_date:
        month_str = current_month.strftime('%Y-%m')
        result = hyxi_client.get_plant_yield_statistics(Config.PLANT_ID, 2, month_str)
        if not result.get('error'):
            results.append(result.get('data', {}))
        current_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)
    
    # Fusionner et filtrer les données
    all_data = {
        'yield': [],
        'consume': [],
        'buyYield': [],
        'sellYield': [],
        'timePoint': []
    }
    
    for data in results:
        for key in all_data.keys():
            all_data[key].extend(data.get(key, []))
    
    filtered_data = {
        'yield': [],
        'consume': [],
        'buyYield': [],
        'sellYield': [],
        'timePoint': []
    }
    
    # Les timestamps de queryPlantYieldStatistics sont en SECONDES
    start_ts = int(start_date.timestamp())
    end_ts = int((end_date + timedelta(days=1)).timestamp())
    
    for i, ts in enumerate(all_data['timePoint']):
        if start_ts <= ts < end_ts:
            for key in filtered_data.keys():
                if i < len(all_data[key]):
                    filtered_data[key].append(all_data[key][i])
    
    return _process_aggregated_data(filtered_data, 'month', start_date, end_date, plant_capacity_kw)


def _handle_year_period(reference_date):
    """Période 'année' : données agrégées par mois sur 12 mois glissants"""
    # Récupérer la capacité installée depuis l'API
    plant_info = hyxi_client.get_plant_info(Config.PLANT_ID)
    plant_capacity_kw = plant_info.get('data', {}).get('capacity', 0) if not plant_info.get('error') else 0
    
    end_date = reference_date
    year = end_date.year
    
    # Pour l'année, utiliser type=3 qui retourne les données mensuelles
    result = hyxi_client.get_plant_yield_statistics(Config.PLANT_ID, 3, year)
    
    if result.get('error'):
        return jsonify(result)
    
    data = result.get('data', {})
    
    # Filtrer pour garder les 12 derniers mois
    filtered_data = {
        'yield': [],
        'consume': [],
        'buyYield': [],
        'sellYield': [],
        'timePoint': []
    }
    
    # Calculer le timestamp de début (12 mois avant)
    start_date = end_date.replace(day=1) - timedelta(days=365)
    # Les timestamps de queryPlantYieldStatistics sont en SECONDES
    start_ts = int(start_date.timestamp())
    end_ts = int((end_date + timedelta(days=1)).timestamp())
    
    timePoints = data.get('timePoint', [])
    for i, ts in enumerate(timePoints):
        if start_ts <= ts < end_ts:
            for key in filtered_data.keys():
                values = data.get(key, [])
                if i < len(values):
                    filtered_data[key].append(values[i])
    
    return _process_aggregated_data(filtered_data, 'year', start_date, end_date, plant_capacity_kw)


def _process_aggregated_data(data, period_type, start_date, end_date, plant_capacity_kw):
    """Traite les données agrégées (semaine/mois/année) et calcule les revenus"""
    start_time_processing = time.time()
    
    timePoints = data.get('timePoint', [])
    yields = data.get('yield', [])
    consumes = data.get('consume', [])
    buyYields = data.get('buyYield', [])
    sellYields = data.get('sellYield', [])
    
    if not timePoints:
        return jsonify({
            'success': True,
            'period': period_type,
            'start_time': start_date.strftime('%Y-%m-%d'),
            'data': {
                'energy': 0,
                'consumption': 0,
                'buy': 0,
                'peakPower': 0,
                'income': 0
            },
            'chart_data': {
                'labels': [],
                'production': [],
                'consumption': [],
                'tempo_zones': []
            }
        })
    
    # Préparer les données pour le graphique
    labels = []
    production_values = []
    consumption_values = []
    tarifs_cache = {}
    
    for i, ts in enumerate(timePoints):
        dt = from_timestamp_tz(ts)
        
        # Format du label selon la période
        if period_type == 'week' or period_type == 'month':
            label = dt.strftime('%d/%m')
        else:  # year
            label = dt.strftime('%b %y')
        
        labels.append(label)
        
        # Les données sont déjà en kWh pour les agrégations
        prod_kwh = yields[i] if i < len(yields) else 0
        cons_kwh = consumes[i] if i < len(consumes) else 0
        
        production_values.append(prod_kwh)
        consumption_values.append(cons_kwh)
        
        # Collecter les tarifs pour cette date (avec cache global)
        date_str = dt.strftime('%Y-%m-%d')
        if date_str not in tarifs_cache:
            tarifs_cache[date_str] = get_tempo_tarif(date_str)
    
    # Calcul des totaux
    total_production = sum(production_values)
    total_consumption = sum(consumption_values)
    total_buy = sum(buyYields) if buyYields else 0
    
    # Calcul du revenu selon le mode
    if Config.RESALE_ENABLED:
        # Utiliser les données buyYield et sellYield de l'API
        revenu_autoconso = 0
        revenu_vente = 0
        
        for i, ts in enumerate(timePoints):
            dt = from_timestamp_tz(ts)
            date_str = dt.strftime('%Y-%m-%d')
            
            # Utiliser tarif HP moyen pour les journées (approximation)
            tarif_achat = tarifs_cache.get(date_str, {}).get('tarif_hp', Config.TARIF_ACHAT)
            
            buy_kwh = buyYields[i] if i < len(buyYields) else 0
            sell_kwh = sellYields[i] if i < len(sellYields) else 0
            prod_kwh = yields[i] if i < len(yields) else 0
            
            # Autoconso = production - vente
            autoconso_kwh = prod_kwh - sell_kwh
            revenu_autoconso += autoconso_kwh * tarif_achat
            revenu_vente += sell_kwh * Config.TARIF_VENTE
        
        revenu = revenu_autoconso + revenu_vente
    else:
        # Mode simple : toute la production est valorisée au tarif achat
        revenu = 0
        for i, ts in enumerate(timePoints):
            dt = from_timestamp_tz(ts)
            date_str = dt.strftime('%Y-%m-%d')
            tarif_achat = tarifs_cache.get(date_str, {}).get('tarif_hp', Config.TARIF_ACHAT)
            prod_kwh = yields[i] if i < len(yields) else 0
            revenu += prod_kwh * tarif_achat
    
    # Préparer les zones Tempo
    tempo_zones = []
    for date_str, tarif_data in sorted(tarifs_cache.items()):
        tempo_zones.append({
            'date': date_str,
            'couleur': tarif_data.get('couleur', 'INCONNU'),
            'couleur_css': tarif_data.get('couleur_css', 'gray')
        })
    
    chart_data = {
        'labels': labels,
        'production': production_values,
        'consumption': consumption_values,
        'tempo_zones': tempo_zones
    }
    
    # Puissance de pointe (approximation sur données agrégées)
    peak_power_kw = max(production_values) if production_values else 0
    
    # Calcul du taux d'autoconsommation (%)
    if total_production > 0:
        if Config.RESALE_ENABLED and sellYields:
            # Utiliser les données sellYield de l'API
            total_sell = sum(sellYields)
            autoconso_rate = ((total_production - total_sell) / total_production) * 100
        else:
            # Mode simple : production autoconsommée = min(production, consommation)
            autoconso_rate = min((total_production / total_consumption) * 100, 100) if total_consumption > 0 else 100
    else:
        autoconso_rate = 0
    
    # Rendement des panneaux (%)
    # Calculer les heures d'ensoleillement totales pour la période
    total_daylight_hours = 0
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        total_daylight_hours += get_daylight_hours(date_str)
        current_date += timedelta(days=1)
    
    theoretical_max = plant_capacity_kw * total_daylight_hours  # kWh théorique max sur les heures d'ensoleillement
    pv_performance = (total_production / theoretical_max * 100) if theoretical_max > 0 else 0
    
    elapsed = time.time() - start_time_processing
    print(f"[PERF] _process_aggregated_data took {elapsed*1000:.0f}ms for {len(timePoints)} points, {len(tarifs_cache)} tempo calls")
    
    return jsonify({
        'success': True,
        'period': period_type,
        'start_time': start_date.strftime('%Y-%m-%d'),
        'data': {
            'energy': round(total_production, 2),
            'consumption': round(total_consumption, 2),
            'buy': round(total_buy, 2),
            'peakPower': round(peak_power_kw, 3),
            'income': round(revenu, 2),
            'autoconsoRate': round(autoconso_rate, 1),
            'pvPerformance': round(pv_performance, 1)
        },
        'chart_data': chart_data
    })


@app.route('/api/energy/cost')
def api_energy_cost():
    """
    Calcul du coût de l'énergie pour l'installation configurée
    """
    period = request.args.get('period', 'day')
    tariff = request.args.get('tariff', type=float, default=0.15)  # €/kWh par défaut

    # Calculer la date de début selon la période
    now = datetime.now()
    if period == 'day':
        start_time = now.strftime('%Y-%m-%d')
    elif period == 'week':
        start_time = (now - timedelta(days=7)).strftime('%Y-%m-%d')
    elif period == 'month':
        start_time = (now - timedelta(days=30)).strftime('%Y-%m-%d')
    elif period == 'year':
        start_time = (now - timedelta(days=365)).strftime('%Y-%m-%d')
    else:
        start_time = now.strftime('%Y-%m-%d')

    # Récupérer les données de production
    production_data = hyxi_client.get_plant_power_statistics(Config.PLANT_ID, start_time)

    # Calculer le coût si les données sont disponibles
    if not production_data.get('error'):
        # Extraire les données selon la structure réelle de l'API
        # À adapter selon la réponse réelle de l'API
        data_section = production_data.get('data', {})

        # Tenter différentes clés possibles pour l'énergie
        energy_kwh = (
            data_section.get('totalEnergy', 0) or
            data_section.get('energy', 0) or
            data_section.get('powerGeneration', 0) or
            0
        )

        # Convertir en kWh si nécessaire (certaines APIs retournent en Wh)
        if energy_kwh > 100000:  # Probablement en Wh
            energy_kwh = energy_kwh / 1000

        total_cost = energy_kwh * tariff

        return jsonify({
            'success': True,
            'period': period,
            'start_time': start_time,
            'energy_kwh': round(energy_kwh, 2),
            'tariff': tariff,
            'total_cost': round(total_cost, 2),
            'currency': 'EUR',
            'raw_data': production_data
        })
    else:
        return jsonify(production_data)


@app.route('/api/summary')
def api_summary():
    """
    Résumé de l'installation configurée
    """
    try:
        # Récupérer les infos de l'installation
        plant_info = hyxi_client.get_plant_info(Config.PLANT_ID)

        if plant_info.get('error'):
            return jsonify(plant_info)

        return jsonify({
            'plant_id': Config.PLANT_ID,
            'plant_name': Config.PLANT_NAME,
            'plant_info': plant_info
        })

    except Exception as e:
        return jsonify({
            'error': True,
            'message': str(e)
        })


@app.errorhandler(404)
def not_found(error):
    """Gestion des erreurs 404"""
    return jsonify({'error': 'Route non trouvée'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Gestion des erreurs 500"""
    return jsonify({'error': 'Erreur serveur interne'}), 500


if __name__ == '__main__':
    print("=" * 50)
    print("Hyxi Solar Monitor - Démarrage du serveur")
    print("=" * 50)
    print(f"URL: http://{Config.HOST}:{Config.PORT}")
    print(f"Mode debug: {Config.DEBUG}")
    print(f"API Hyxi: {Config.HYXI_API_BASE_URL}")
    print("=" * 50)

    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
