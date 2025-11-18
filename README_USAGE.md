# Hyxi Solar Monitor - Guide d'utilisation

## Description

Hyxi Solar Monitor est une application web complète pour le monitoring de centrale solaire qui permet de :
- Récupérer les données de télémétrie via l'API Hyxi Cloud
- Afficher les informations en temps réel dans une interface web moderne
- Calculer le revenu énergétique avec les tarifs Tempo en temps réel
- Visualiser les données sur différentes périodes (jour, semaine, mois, année)
- Analyser les performances : autoconsommation, rendement PV, production
- Intégration complète avec l'API météo Hyxi pour les heures d'ensoleillement

## Architecture du projet

```
hyxi-solar-monitor/
├── app/
│   ├── __init__.py
│   ├── api_client.py          # Client pour l'API Hyxi Cloud
│   ├── server.py              # Serveur Flask avec routes API
│   ├── tempo.py               # Client API Tempo (tarifs électricité)
│   ├── static/
│   │   ├── style.css          # Styles CSS
│   │   └── script.js          # JavaScript frontend (Chart.js)
│   └── templates/
│       └── index.html         # Page HTML principale
├── config.py                  # Configuration de l'application
├── requirements.txt           # Dépendances Python
├── Dockerfile                 # Configuration Docker
├── docker-compose.yml         # Configuration Docker Compose
├── analyze_metrics.py         # Script d'analyse des métriques
└── .env.example              # Exemple de fichier d'environnement
```

## Installation et démarrage

### Option 1 : Avec Docker (recommandé)

1. **Construire et démarrer le container**
   ```bash
   docker-compose up --build
   ```

2. **Accéder à l'application**
   - Ouvrir votre navigateur à l'adresse : http://localhost:5000

3. **Arrêter l'application**
   ```bash
   docker-compose down
   ```

### Option 2 : Sans Docker

1. **Créer un environnement virtuel Python**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Sur Linux/Mac
   # ou
   venv\Scripts\activate     # Sur Windows
   ```

2. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurer les variables d'environnement** (optionnel)
   ```bash
   cp .env.example .env
   # Éditer .env avec vos clés API
   ```

4. **Démarrer le serveur**
   ```bash
   python app/server.py
   ```

5. **Accéder à l'application**
   - Ouvrir votre navigateur à l'adresse : http://localhost:5000

## Configuration

### Comment configurer les variables d'environnement

Les variables peuvent être configurées de **trois façons** (par ordre de priorité) :

1. **Fichier .env** (recommandé pour la production et le développement local)
   ```bash
   # Créer le fichier .env depuis l'exemple
   cp .env.example .env
   
   # Éditer le fichier .env avec vos valeurs
   nano .env  # ou votre éditeur préféré
   ```

2. **Variables d'environnement système** (pour Docker/production)
   ```bash
   export PLANT_ID="your_plant_id_here"
   export TARIF_ACHAT="0.1494"
   ```

3. **docker-compose.yml** (pour déploiement Docker)
   ```yaml
   environment:
     - PLANT_ID=your_plant_id_here
     - TARIF_ACHAT=0.1494
   ```

**Note :** Si une variable n'est pas définie, les valeurs par défaut de `config.py` seront utilisées.

### Clés API Hyxi Cloud

Configuration minimale requise :

1. **Via fichier .env** (recommandé pour la production)
   ```env
   HYXI_API_BASE_URL=https://open.hyxicloud.com
   HYXI_ACCESS_KEY=votre_access_key
   HYXI_SECRET_KEY=votre_secret_key
   HYXI_APPLICATION=nom_application
   PLANT_ID=votre_plant_id
   PLANT_NAME=nom_de_votre_centrale
   ```

2. **Via docker-compose.yml**
   ```yaml
   environment:
     - HYXI_ACCESS_KEY=votre_access_key
     - HYXI_SECRET_KEY=votre_secret_key
     - PLANT_ID=votre_plant_id
   ```

### Variables de configuration

**API Hyxi Cloud :**
- `HYXI_API_BASE_URL` : URL de base de l'API (défaut: https://open.hyxicloud.com)
- `HYXI_ACCESS_KEY` : Clé d'accès API
- `HYXI_SECRET_KEY` : Clé secrète API
- `HYXI_APPLICATION` : Nom de l'application (défaut: test)

**Installation solaire :**
- `PLANT_ID` : ID de votre centrale solaire (exemple: PlXXXXXXXXXXXXXXXXXX)
- `PLANT_NAME` : Nom de votre centrale (exemple: Ma_Centrale_Solaire)

**Tarifs énergétiques :**
- `TARIF_ACHAT` : **Fallback uniquement** - Prix d'achat électricité (€/kWh) utilisé si l'API Tempo est indisponible (défaut: 0.1494)
- `TARIF_VENTE` : Prix de revente du surplus (€/kWh) (défaut: 0.004)
- `RESALE_ENABLED` : Active le mode revente (true/false, défaut: false)

**Important :** Les tarifs Tempo (bleu/blanc/rouge, HP/HC) sont automatiquement récupérés depuis l'API https://www.api-couleur-tempo.fr.
Le `TARIF_ACHAT` n'est utilisé qu'en cas d'échec de l'API Tempo.

**Localisation :**
- `TIMEZONE` : Fuseau horaire (défaut: Europe/Paris)

**Flask :**
- `SECRET_KEY` : Clé secrète Flask (à changer en production)
- `DEBUG` : Mode debug (true/false, défaut: true)
- `HOST` : Adresse d'écoute (défaut: 0.0.0.0)
- `PORT` : Port d'écoute (défaut: 5000)

### Clés API

```
AK: your_access_key_here
SK: your_secret_key_here
Application: test
```

**Note sur les tarifs :** L'application récupère automatiquement les tarifs Tempo en temps réel depuis l'API officielle.
Vous n'avez **pas besoin** de configurer manuellement les tarifs d'achat, sauf si vous souhaitez un fallback personnalisé.

## Fonctionnalités

### 1. Dashboard principal (/)
- Affichage des données en temps réel
- Visualisation de la production et consommation d'énergie
- Graphiques interactifs avec Chart.js
- Calcul automatique du revenu avec tarifs Tempo
- Métriques : autoconsommation, rendement PV, couverture solaire
- Sélection de période : jour, semaine, mois, année
- Zones de couleur Tempo (bleu/blanc/rouge) sur les graphiques

### 2. API REST

#### Endpoints disponibles :

**Système et configuration :**
- `GET /api/status` - Vérifier le statut de connexion à l'API Hyxi
- `GET /api/config` - Configuration de l'application (tarifs, modes)

**Tarifs Tempo :**
- `GET /api/tempo/now` - Tarif Tempo actuel (bleu/blanc/rouge, HP/HC)
- `GET /api/tempo/tomorrow` - Prévision du tarif pour demain
- `GET /api/tempo/tarifs` - Tous les tarifs Tempo disponibles

**Centrale solaire :**
- `GET /api/plant/info` - Informations de la centrale (capacité, nom, etc.)
- `GET /api/plant/realtime` - Données en temps réel (puissance, production du jour)
- `GET /api/plant/statistics?date=YYYY-MM-DD` - Statistiques de puissance (jour)
- `GET /api/plant/yield-statistics?type=1&date=YYYY-MM-DD` - Statistiques de production
- `GET /api/plant/power-generation` - Génération de puissance actuelle

**Énergie et revenus :**
- `GET /api/energy/production?period=day&date=YYYY-MM-DD` - Production avec métriques
  - Paramètres : `period` (day/week/month/year), `date` (optionnel, défaut aujourd'hui)
  - Retourne : énergie, consommation, achat, pic de puissance, revenu, autoconsommation %, rendement PV %
- `GET /api/energy/cost?period=day&tariff=0.15` - Calcul du coût (endpoint legacy)
- `GET /api/summary` - Résumé général de la centrale

#### Paramètres :
- `period` : day, week, month, year
- `date` : YYYY-MM-DD (optionnel, défaut aujourd'hui)
- `type` : 1 (jour), 2 (mois), 3 (année) pour yield-statistics

### 3. Fonctionnalités avancées

**Calcul de revenu avec Tempo :**
- Récupération automatique des tarifs Tempo (bleu/blanc/rouge, HP/HC)
- Cache des tarifs pour optimiser les performances
- Calcul point par point pour les périodes agrégées
- Mode autoconsommation ou revente du surplus

**Métriques calculées :**
- **Autoconsommation (%)** : Part de la production autoconsommée
- **Rendement PV (%)** : Production réelle / (capacité × heures ensoleillement) × 100
  - Utilise les heures de lever/coucher du soleil de l'API météo Hyxi
- **Revenu (€)** : Valeur de l'énergie selon les tarifs Tempo

**Optimisations :**
- Cache global des tarifs Tempo (thread-safe)
- Réduction du temps de chargement : semaine 3.6s→0.2s, mois 11.5s→0.4s

### 4. Rafraîchissement automatique

Les données sont automatiquement rafraîchies toutes les 30 secondes sur le dashboard.

## Développement

### Modifier l'authentification API

Si l'API Hyxi Cloud utilise un schéma d'authentification différent, modifier le fichier `app/api_client.py`, méthode `_generate_signature()`.

### Adapter le format des données

Les endpoints de l'API Hyxi peuvent retourner des données dans un format différent. Adapter :
- `app/api_client.py` : Les méthodes de requête
- `app/server.py` : Les routes API
- `app/static/script.js` : Le traitement des données frontend

### Ajouter de nouveaux endpoints

1. Ajouter la méthode dans `app/api_client.py`
2. Créer la route dans `app/server.py`
3. Mettre à jour le frontend dans `app/static/script.js`

## Limitations et futures fonctionnalités

### Limitations actuelles

**Pas d'historisation des données :**
- Les données sont récupérées en temps réel depuis l'API Hyxi à chaque requête
- Les tarifs Tempo sont mis en cache uniquement pendant l'exécution du serveur
- Pas de stockage persistant des métriques historiques

**Mode tarifaire :**
- Seul le tarif Tempo (bleu/blanc/rouge, HP/HC) est supporté actuellement
- Les autres modes tarifaires (Base, Heures Creuses standard) ne sont pas disponibles

### Roadmap des prochaines fonctionnalités

**Phase 1 - Historisation des données** 🔜
- Intégration d'une base de données MySQL pour stocker :
  - Historique des productions et consommations
  - Historique des tarifs Tempo
  - Calculs de revenus historiques
- Permet de générer des statistiques sur de longues périodes sans appels API multiples
- Amélioration des performances pour les périodes longues (mois, année)

**Phase 2 - Modes tarifaires avancés** 🔜
- Support du tarif Base (prix unique 24h/24)
- Support du tarif Heures Creuses standard (non Tempo)
- Configuration du mode tarifaire dans les variables d'environnement
- Interface pour sélectionner le mode tarifaire

**Phase 3 - Analyse avancée** 💡
- Prévisions de production basées sur historique
- Alertes sur performances anormales
- Export des données (CSV, Excel)
- Rapports mensuels automatiques

## Dépannage

### L'API Hyxi ne répond pas
- Vérifier que les clés API sont correctes
- Vérifier la connexion internet
- Consulter les logs : `docker-compose logs -f`

### Erreur de connexion au serveur
- Vérifier que le port 5000 n'est pas déjà utilisé
- Sur Linux : `sudo lsof -i :5000`
- Changer le port dans `config.py` ou `docker-compose.yml`

### Les données ne s'affichent pas
- Ouvrir la console du navigateur (F12)
- Vérifier les erreurs JavaScript
- Vérifier la structure des données retournées par l'API dans la section "Données de télémétrie (brutes)"

## Sécurité

**IMPORTANT** : Ne jamais commiter les fichiers suivants dans Git :
- `.env` (contient les clés secrètes)
- `config_local.py`

Les clés API de test fournies dans ce README sont publiques. En production, utilisez vos propres clés et stockez-les de manière sécurisée.

## Support

Pour toute question ou problème :
1. Consulter la documentation de l'API Hyxi : https://open.hyxicloud.com/#/document
2. Vérifier les logs de l'application
3. Ouvrir une issue sur le repository du projet

## Licence

Ce projet est fourni à titre d'exemple et d'éducation.
