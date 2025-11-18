# Hyxi Solar Monitor

> 🇫🇷 **Note for international visitors:** This project is designed specifically for French solar installations using the EDF Tempo pricing system. Documentation is in French as the primary users are French-speaking. The Hyxi Cloud API itself is international, but the Tempo tariff integration (bleu/blanc/rouge) is France-specific.

## Description

Application web complète pour le monitoring et l'analyse de centrale solaire Hyxi.

**Fonctionnalités :**
- Récupération des données de télémétrie via l'API Hyxi Cloud
- Dashboard web interactif en temps réel avec graphiques Chart.js
- Calcul automatique du revenu avec tarifs Tempo en temps réel
- Métriques avancées : autoconsommation %, rendement PV %, couverture solaire
- Visualisation sur différentes périodes (jour, semaine, mois, année)
- Zones de couleur Tempo (bleu/blanc/rouge) sur les graphiques
- Calcul du rendement PV basé sur les heures d'ensoleillement réelles
- Containerisé avec Docker pour un déploiement facile

## Démarrage rapide

### Avec Docker (recommandé)
```bash
# Démarrer l'application
docker-compose up --build

# Ouvrir dans le navigateur
http://localhost:5000
```

### Avec Python
```bash
# Utiliser le script de démarrage
./start.sh

# OU manuellement
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app/server.py
```

## Configuration API

**Documentation API :** https://open.hyxicloud.com/#/document

**Clés API de test :**
- AK : your_access_key_here
- SK : your_secret_key_here
- Application : test

Pour utiliser vos propres clés, créer un fichier `.env` depuis `.env.example` :
```bash
cp .env.example .env
# Modifier les valeurs dans .env
```

### Variables de configuration disponibles

**Installation solaire :**
- `PLANT_ID` : ID de votre installation Hyxi
- `PLANT_NAME` : Nom de votre centrale

**Tarifs énergétiques :**
- `TARIF_ACHAT` : **Optionnel** - Fallback si l'API Tempo est indisponible (défaut: 0.1494 €/kWh)
- `TARIF_VENTE` : Prix de revente du surplus (€/kWh, défaut: 0.004)
- `RESALE_ENABLED` : Active le mode revente du surplus (true/false, défaut: false)

**Localisation :**
- `TIMEZONE` : Fuseau horaire (défaut: Europe/Paris)

**Tarifs automatiques :** L'application récupère automatiquement les **tarifs Tempo en temps réel** depuis l'API https://www.api-couleur-tempo.fr
Les tarifs varient selon la couleur du jour (bleu/blanc/rouge) et l'horaire (HP/HC). Le `TARIF_ACHAT` n'est qu'un fallback en cas d'indisponibilité de l'API.

## Structure du projet

```
hyxi-solar-monitor/
├── app/
│   ├── api_client.py      # Client API Hyxi Cloud
│   ├── server.py          # Serveur Flask avec routes API
│   ├── tempo.py           # Client API Tempo (tarifs électricité)
│   ├── static/            # CSS et JavaScript (Chart.js)
│   └── templates/         # Pages HTML
├── config.py              # Configuration
├── analyze_metrics.py     # Script d'analyse des métriques
├── Dockerfile             # Configuration Docker
└── docker-compose.yml     # Orchestration Docker
```

## Documentation

Consultez le fichier `README_USAGE.md` pour :
- Guide d'installation détaillé
- Configuration des variables d'environnement
- Documentation complète de l'API REST (13 endpoints)
- Guide de développement
- Limitations et roadmap des futures fonctionnalités
- Dépannage

## Limitations et prochaines fonctionnalités

**Actuellement :**
- Pas d'historisation (données récupérées en temps réel depuis l'API Hyxi)
- Seul le mode tarifaire Tempo est supporté

**À venir :**
- 🔜 Base de données MySQL pour historiser les productions et tarifs
- 🔜 Support des tarifs Base et Heures Creuses standard
- 💡 Prévisions et analyses avancées

Voir `README_USAGE.md` pour plus de détails.

## Technologies

- **Backend :** Python 3.11, Flask
- **Frontend :** HTML5, CSS3, JavaScript (Vanilla), Chart.js
- **API :** Hyxi Cloud REST API, API Tempo (couleur-tempo.fr)
- **Container :** Docker, Docker Compose
- **Timezone :** pytz pour gestion des fuseaux horaires

Le projet s'exécute dans un container Docker qui contient le serveur web.
