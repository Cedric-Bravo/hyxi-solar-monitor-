// Configuration et état global
let currentPlantId = null;
let currentPlantName = null;
let refreshInterval = null;

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function () {
    console.log('HyxiCalculator Dashboard initialisé');

    // Initialiser le sélecteur de date avec la date du jour
    const dateSelect = document.getElementById('dateSelect');
    if (dateSelect) {
        const today = new Date();
        dateSelect.valueAsDate = today;
        dateSelect.max = today.toISOString().split('T')[0]; // Limite à aujourd'hui
    }

    // Vérifier le statut de l'API
    checkAPIStatus();

    // Charger les informations Tempo
    loadTempoInfo();
    loadTempoTomorrow();

    // Charger la configuration (PLANT_ID)
    loadConfig();

    // Rafraîchissement automatique toutes les 30 secondes
    refreshInterval = setInterval(() => {
        if (currentPlantId) {
            loadRealtimeData();
            loadEnergyProduction();
            loadEnergyCost();
        }
        // Rafraîchir Tempo toutes les 30 sec aussi
        loadTempoInfo();
        loadTempoTomorrow();
    }, 30000);
});

// Vérifier le statut de l'API
async function checkAPIStatus() {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        if (data.error) {
            statusDot.className = 'status-dot error';
            statusText.textContent = 'Erreur de connexion à l\'API Hyxi';
            console.error('Erreur API:', data);
        } else {
            statusDot.className = 'status-dot connected';
            statusText.textContent = 'Connecté à l\'API Hyxi';
        }
    } catch (error) {
        statusDot.className = 'status-dot error';
        statusText.textContent = 'Impossible de contacter l\'API';
        console.error('Erreur:', error);
    }
}

// Charger les informations Tempo
async function loadTempoInfo() {
    const badge = document.getElementById('tempoBadge');
    const emoji = document.getElementById('tempoEmoji');
    const text = document.getElementById('tempoText');
    const tarif = document.getElementById('tempoTarif');

    try {
        const response = await fetch('/api/tempo/now');
        const data = await response.json();

        if (data.success) {
            // Mettre à jour l'emoji et le texte
            emoji.textContent = data.couleur_emoji;
            text.textContent = `Jour ${data.couleur}`;

            // Appliquer la classe CSS selon la couleur
            badge.className = `tempo-badge tempo-${data.couleur_css}`;

            // Mettre à jour le tarif
            tarif.textContent = `${data.tarif_kwh.toFixed(4)} €/kWh (${data.horaire})`;

            console.log('Tempo Info:', data);
        } else {
            text.textContent = 'Tempo non disponible';
            tarif.textContent = '';
        }
    } catch (error) {
        console.error('Erreur Tempo:', error);
        text.textContent = 'Erreur Tempo';
        tarif.textContent = '';
    }
}

// Charger les informations Tempo de demain
async function loadTempoTomorrow() {
    const badge = document.getElementById('tempoTomorrowBadge');
    const emoji = document.getElementById('tempoTomorrowEmoji');
    const text = document.getElementById('tempoTomorrowText');
    const tarif = document.getElementById('tempoTomorrowTarif');

    try {
        const response = await fetch('/api/tempo/tomorrow');
        const data = await response.json();

        if (data.success) {
            // Mettre à jour l'emoji et le texte
            emoji.textContent = data.couleur_emoji;
            text.textContent = `Demain ${data.couleur}`;

            // Appliquer la classe CSS selon la couleur
            badge.className = `tempo-badge tempo-${data.couleur_css}`;

            // Mettre à jour le tarif HP
            tarif.textContent = `${data.tarif_hp.toFixed(4)} €/kWh (HP)`;

            console.log('Tempo Tomorrow Info:', data);
        } else {
            text.textContent = 'Demain inconnu';
            tarif.textContent = '';
        }
    } catch (error) {
        console.error('Erreur Tempo Tomorrow:', error);
        text.textContent = 'Demain inconnu';
        tarif.textContent = '';
    }
}

// Charger la configuration (PLANT_NAME pour affichage)
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const data = await response.json();

        currentPlantName = data.plant_name;

        console.log(`Configuration chargée: ${currentPlantName}`);

        // Charger immédiatement les données
        currentPlantId = true; // Juste pour indiquer que c'est configuré
        loadRealtimeData();
        loadEnergyProduction();
        loadEnergyCost();

    } catch (error) {
        console.error('Erreur lors du chargement de la configuration:', error);
    }
}

// Charger les données en temps réel
async function loadRealtimeData() {
    const container = document.getElementById('realtimeData');

    try {
        const response = await fetch('/api/plant/realtime');
        const data = await response.json();

        if (data.error) {
            container.innerHTML = `<div class="error-message">Erreur: ${data.message || 'Impossible de charger les données en temps réel'}</div>`;
            return;
        }

        // Extraire les données
        const realtimeData = data.data || {};

        // Date et heure de la dernière mesure
        const lastMeasurement = realtimeData.lastMeasurementTime;
        const lastMeasurementHtml = lastMeasurement
            ? `<div class="last-measurement">📊 Dernière mesure : ${lastMeasurement}</div>`
            : '';

        // Définir les métriques avec icônes
        const metrics = [
            {
                label: 'Production Solaire',
                value: realtimeData.currentPowerProduced || 0,
                unit: 'W',
                icon: '☀️',  // Panneau solaire
                key: 'produced'
            },
            {
                label: 'Consommation',
                value: realtimeData.currentPowerConsumed || 0,
                unit: 'W',
                icon: '🏠',  // Maison
                key: 'consumed'
            },
            {
                label: 'Puissance achetée',
                value: realtimeData.currentPowerBought || 0,
                unit: 'W',
                icon: '⚡',  // Pylône électrique
                key: 'bought'
            },
            {
                label: 'Economie du jour',
                value: realtimeData.todayIncome || 0,
                unit: '€',
                icon: '💰',  // Pièces
                key: 'income'
            }
        ];

        container.innerHTML = lastMeasurementHtml + metrics.map(metric => {
            // Formatage selon le type de valeur : W sans décimales, € avec 2 décimales
            let formattedValue;
            if (metric.unit === 'W') {
                formattedValue = Math.round(metric.value);  // Watts sans décimales
            } else {
                formattedValue = metric.value.toFixed(2);   // Euros avec 2 décimales
            }

            return `
                <div class="data-item ${metric.value > 0 ? 'positive' : ''}">
                    <div class="data-icon">${metric.icon}</div>
                    <div class="data-content">
                        <div class="data-label">${metric.label}</div>
                        <div class="data-value">
                            ${formattedValue}
                            <span class="data-unit">${metric.unit}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // Afficher les données brutes dans la console pour débogage
        console.log('Données temps réel:', data);

        // Créer/mettre à jour le graphique d'autoconsommation
        createAutoconsoChart(realtimeData);

        // Créer/mettre à jour le graphique de rendement
        createYieldChart(realtimeData);

    } catch (error) {
        container.innerHTML = `<div class="error-message">Erreur: ${error.message}</div>`;
        console.error('Erreur:', error);
    }
}

// Créer le graphique d'autoconsommation (donut)
function createAutoconsoChart(realtimeData) {
    const canvas = document.getElementById('autoconsoChart');
    const labelDiv = document.getElementById('autoconsoLabel');

    if (!canvas || !labelDiv) return;

    // Calculer le pourcentage d'autoconsommation INSTANTANÉE
    const produced = realtimeData.currentPowerProduced || 0;
    const consumed = realtimeData.currentPowerConsumed || 0;

    let autoconsoPercent = 0;
    if (consumed > 0) {
        autoconsoPercent = Math.min((produced / consumed) * 100, 100);
    }

    const gridPercent = 100 - autoconsoPercent;

    // Afficher le label au centre
    labelDiv.style.display = 'block';
    labelDiv.innerHTML = `
        <div style="font-size: 1.5rem; font-weight: bold; color: #34d399;">
            ${autoconsoPercent.toFixed(1)}%
        </div>
        <div style="font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem;">
            Autoconsommation
        </div>
    `;

    // Détruire le graphique existant
    if (autoconsoChart) {
        autoconsoChart.destroy();
    }

    // Créer le graphique donut
    const ctx = canvas.getContext('2d');

    autoconsoChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Autoconsommation', 'Réseau'],
            datasets: [{
                data: [autoconsoPercent, gridPercent],
                backgroundColor: [
                    'rgba(52, 211, 153, 0.8)',
                    'rgba(239, 68, 68, 0.5)'
                ],
                borderColor: [
                    'rgba(52, 211, 153, 1)',
                    'rgba(239, 68, 68, 0.8)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return `${context.label}: ${context.parsed.toFixed(1)}%`;
                        }
                    }
                }
            }
        }
    });
}

// Créer le graphique de rendement (donut)
function createYieldChart(realtimeData) {
    const canvas = document.getElementById('yieldChart');
    const labelDiv = document.getElementById('yieldLabel');

    if (!canvas || !labelDiv) return;

    // Calculer le pourcentage de rendement
    const currentPower = realtimeData.currentPowerProduced || 0;  // W
    const capacity = realtimeData.capacity || 0;  // kW
    const maxPower = capacity * 1000;  // Convertir kW en W

    let yieldPercent = 0;
    if (maxPower > 0) {
        yieldPercent = Math.min((currentPower / maxPower) * 100, 100);
    }

    const unusedPercent = 100 - yieldPercent;

    // Afficher le label au centre
    labelDiv.style.display = 'block';
    labelDiv.innerHTML = `
        <div style="font-size: 1.5rem; font-weight: bold; color: #fbbf24;">
            ${yieldPercent.toFixed(1)}%
        </div>
        <div style="font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem;">
            Rendement (${capacity.toFixed(1)} kW)
        </div>
    `;

    // Détruire le graphique existant
    if (yieldChart) {
        yieldChart.destroy();
    }

    // Créer le graphique donut
    const ctx = canvas.getContext('2d');

    yieldChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Production actuelle', 'Capacité inutilisée'],
            datasets: [{
                data: [yieldPercent, unusedPercent],
                backgroundColor: [
                    'rgba(251, 191, 36, 0.8)',
                    'rgba(156, 163, 175, 0.3)'
                ],
                borderColor: [
                    'rgba(251, 191, 36, 1)',
                    'rgba(156, 163, 175, 0.5)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const value = context.parsed;
                            const power = (value / 100) * (capacity * 1000);
                            return `${context.label}: ${value.toFixed(1)}% (${power.toFixed(0)} W)`;
                        }
                    }
                }
            }
        }
    });
}

// Variable pour stocker l'instance du graphique
let energyChart = null;
let autoconsoChart = null;
let yieldChart = null;

// Charger la production d'énergie avec graphique
async function loadEnergyProduction() {
    const summaryContainer = document.getElementById('energySummary');
    const period = document.getElementById('periodSelect').value;
    const dateSelect = document.getElementById('dateSelect');
    const selectedDate = dateSelect ? dateSelect.value : null;

    try {
        let url = `/api/energy/production?period=${period}`;
        if (selectedDate) {
            url += `&date=${selectedDate}`;
        }

        const response = await fetch(url);
        const data = await response.json();

        if (data.error) {
            summaryContainer.innerHTML = `<div class="error-message">Erreur: ${data.message || 'Impossible de charger les données de production'}</div>`;
            return;
        }

        // Extraire les données calculées
        const productionData = data.data || {};
        const chartData = data.chart_data || {};
        const energy = productionData.energy || 0;
        const consumption = productionData.consumption || 0;
        const buy = productionData.buy || 0;
        const income = productionData.income || 0;
        const autoconsoRate = productionData.autoconsoRate || 0;
        const pvPerformance = productionData.pvPerformance || 0;

        // Afficher les métriques comme dans la section données instantanées
        summaryContainer.innerHTML = `
            <div class="data-item positive">
                <div class="data-icon">⚡</div>
                <div class="data-info">
                    <div class="data-value">${energy.toFixed(2)} kWh</div>
                    <div class="data-label">Production</div>
                </div>
            </div>
            <div class="data-item">
                <div class="data-icon">🏠</div>
                <div class="data-info">
                    <div class="data-value">${consumption.toFixed(2)} kWh</div>
                    <div class="data-label">Consommation</div>
                </div>
            </div>
            <div class="data-item negative">
                <div class="data-icon">🔌</div>
                <div class="data-info">
                    <div class="data-value">${buy.toFixed(2)} kWh</div>
                    <div class="data-label">Achat</div>
                </div>
            </div>
            <div class="data-item positive">
                <div class="data-icon">💰</div>
                <div class="data-info">
                    <div class="data-value">${income.toFixed(2)} €</div>
                    <div class="data-label">Économie</div>
                </div>
            </div>
            <div class="data-item">
                <div class="data-icon">♻️</div>
                <div class="data-info">
                    <div class="data-value">${autoconsoRate.toFixed(1)} %</div>
                    <div class="data-label">Autoconsommation</div>
                </div>
            </div>
            <div class="data-item">
                <div class="data-icon">📊</div>
                <div class="data-info">
                    <div class="data-value">${pvPerformance.toFixed(1)} %</div>
                    <div class="data-label">Rendement PV</div>
                </div>
            </div>
        `;

        // Mettre à jour le badge Tempo de la date sélectionnée
        updateSelectedDateTempo(chartData);

        // Créer le graphique
        createEnergyChart(chartData);

        console.log('Données production:', data);

    } catch (error) {
        summaryContainer.innerHTML = `<div class="error-message">Erreur: ${error.message}</div>`;
        console.error('Erreur:', error);
    }
}

// Mettre à jour le badge Tempo de la date sélectionnée
function updateSelectedDateTempo(chartData) {
    const tempoZones = chartData.tempo_zones || [];
    const dateSelect = document.getElementById('dateSelect');
    const selectedDate = dateSelect ? dateSelect.value : null;

    const emojiElement = document.getElementById('selectedDateTempoEmoji');
    const textElement = document.getElementById('selectedDateTempoText');

    if (!emojiElement || !textElement) return;

    // Trouver la couleur Tempo de la date sélectionnée (ou aujourd'hui)
    let targetDate = selectedDate;
    if (!targetDate) {
        // Pas de date sélectionnée, utiliser la date du premier tempo_zone
        if (tempoZones.length > 0) {
            targetDate = tempoZones[tempoZones.length - 1].date; // Dernière date (la plus récente)
        }
    }

    // Chercher la zone correspondant à cette date
    let tempoInfo = null;
    if (targetDate) {
        tempoInfo = tempoZones.find(zone => zone.date === targetDate);
    }

    // Fallback sur la première zone si pas trouvé
    if (!tempoInfo && tempoZones.length > 0) {
        tempoInfo = tempoZones[tempoZones.length - 1];
    }

    if (tempoInfo) {
        const couleur = tempoInfo.couleur || 'INCONNU';
        const emojiMap = {
            'BLEU': '🔵',
            'BLANC': '⚪',
            'ROUGE': '🔴',
            'INCONNU': '❓'
        };

        emojiElement.textContent = emojiMap[couleur] || '❓';
        textElement.textContent = couleur;
    } else {
        emojiElement.textContent = '❓';
        textElement.textContent = 'N/A';
    }
}

// Créer le graphique de production d'énergie avec courbes et aires
function createEnergyChart(chartData) {
    const ctx = document.getElementById('energyChart');

    if (!ctx) {
        console.error('Canvas energyChart non trouvé');
        return;
    }

    // Détruire l'ancien graphique s'il existe
    if (energyChart) {
        energyChart.destroy();
    }

    const labels = chartData.labels || [];
    const production = chartData.production || [];
    const consumption = chartData.consumption || [];
    const tempoZones = chartData.tempo_zones || [];

    // Calculer le maximum pour l'échelle Y
    const maxValue = Math.max(...production, ...consumption, 100);

    // Créer les annotations pour les zones Tempo
    const annotations = {};

    if (tempoZones.length > 0) {
        console.log('Tempo zones reçues:', tempoZones);

        // Mapper les zones Tempo par couleur CSS
        const tempoColorMap = {
            'blue': 'rgba(227, 242, 253, 0.6)',     // Bleu clair (jours BLEU)
            'white': 'rgba(245, 245, 245, 0.6)',    // Gris clair (jours BLANC)
            'red': 'rgba(255, 235, 238, 0.6)',      // Rouge clair (jours ROUGE)
            'gray': 'rgba(200, 200, 200, 0.4)'      // Gris pour inconnu
        };

        // Grouper les labels par date pour créer des zones
        const labelsByDate = {};

        // Si on a une seule zone Tempo et des labels sans date (format HH:MM), 
        // c'est probablement une vue journée - associer tous les labels à cette date
        if (tempoZones.length === 1 && labels.length > 0 && !labels[0].includes(' ') && !labels[0].includes('-')) {
            // Vue journée : labels = ["00:00", "00:05", ...]
            const dateStr = tempoZones[0].date;
            labelsByDate[dateStr] = labels.map((_, idx) => idx);
        } else if (tempoZones.length === 2 && labels.length > 0 && !labels[0].includes(' ') && !labels[0].includes('-')) {
            // Vue journée à cheval sur 2 jours (minuit) : séparer avant/après minuit
            // Les labels commencent à 23:00 la veille et finissent dans la journée actuelle
            const prevDate = tempoZones[0].date;
            const currDate = tempoZones[1].date;

            labels.forEach((label, idx) => {
                // Heure en format HH:MM
                const hour = parseInt(label.split(':')[0]);
                // Si heure >= 20, c'est probablement la veille
                const dateStr = hour >= 20 ? prevDate : currDate;

                if (!labelsByDate[dateStr]) {
                    labelsByDate[dateStr] = [];
                }
                labelsByDate[dateStr].push(idx);
            });
        } else {
            // Vue semaine/mois : labels au format dd/mm ou mmm yy
            // Il faut les associer aux tempo_zones qui ont des dates complètes (YYYY-MM-DD)

            // Créer un mapping index -> date complète depuis tempo_zones
            // On suppose que les labels sont dans le même ordre que les tempo_zones
            labels.forEach((label, idx) => {
                // Pour week/month, on a autant de labels que de tempo_zones
                if (idx < tempoZones.length) {
                    const dateStr = tempoZones[idx].date;
                    if (!labelsByDate[dateStr]) {
                        labelsByDate[dateStr] = [];
                    }
                    labelsByDate[dateStr].push(idx);
                }
            });
        }

        // Créer une annotation pour chaque jour avec sa couleur Tempo
        tempoZones.forEach((zone, zoneIdx) => {
            const dateStr = zone.date;
            const couleurCss = zone.couleur_css || 'gray';
            const indices = labelsByDate[dateStr];

            if (indices && indices.length > 0) {
                const xMin = indices[0];
                const xMax = indices[indices.length - 1];

                const annotation = {
                    type: 'box',
                    xMin: xMin,
                    xMax: xMax + 0.5,  // Étendre légèrement pour éviter les gaps
                    yMin: 0,
                    yMax: maxValue * 1.1,  // 110% du maximum pour couvrir tout le graphique
                    backgroundColor: tempoColorMap[couleurCss] || tempoColorMap['gray'],
                    borderWidth: 0,
                    z: -1,  // Placer derrière tous les autres éléments
                    drawTime: 'beforeDatasetsDraw'  // Dessiner avant les datasets
                };

                annotations[`tempo_zone_${zoneIdx}`] = annotation;
                console.log(`Zone ${zoneIdx} (${dateStr}, ${couleurCss}):`, annotation);
            }
        });

        console.log('Annotations créées:', annotations);
    }

    energyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Consommation (W)',
                    data: consumption,
                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                    borderColor: 'rgba(239, 68, 68, 1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 4
                },
                {
                    label: 'Production (W)',
                    data: production,
                    backgroundColor: function (context) {
                        const chart = context.chart;
                        const { ctx, chartArea } = chart;

                        if (!chartArea) {
                            return 'rgba(16, 185, 129, 0.3)';
                        }

                        // Créer un dégradé vert pour la production
                        const gradient = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
                        gradient.addColorStop(0, 'rgba(16, 185, 129, 0.1)');
                        gradient.addColorStop(1, 'rgba(16, 185, 129, 0.5)');
                        return gradient;
                    },
                    borderColor: 'rgba(16, 185, 129, 1)',
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2.5,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                annotation: {
                    annotations: annotations
                },
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y;
                            return `${label}: ${Math.round(value)} W`;
                        },
                        afterBody: function (tooltipItems) {
                            const idx = tooltipItems[0].dataIndex;
                            const prod = production[idx];
                            const cons = consumption[idx];
                            const surplus = prod - cons;

                            if (surplus > 0) {
                                return `\n🟢 Surplus: +${Math.round(surplus)} W (réinjection)`;
                            } else if (surplus < 0) {
                                return `\n🔴 Déficit: ${Math.round(surplus)} W (réseau)`;
                            } else {
                                return `\n⚖️ Équilibre parfait`;
                            }
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxTicksLimit: 24,
                        maxRotation: 45,
                        minRotation: 0
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Puissance (W)'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            }
        }
    });
}


// Charger le calcul de coût
async function loadEnergyCost() {
    const container = document.getElementById('costData');
    const period = document.getElementById('periodSelect').value;
    const tariff = parseFloat(document.getElementById('tariffInput').value) || 0.15;

    try {
        const url = `/api/energy/cost?period=${period}&tariff=${tariff}`;
        const response = await fetch(url);
        const data = await response.json();

        if (data.error) {
            container.innerHTML = `<div class="error-message">Erreur: ${data.message || 'Impossible de calculer le coût'}</div>`;
            return;
        }

        container.innerHTML = `
            <div class="metric-row">
                <span class="metric-label">Période</span>
                <span class="metric-value">${getPeriodLabel(period)}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Date de début</span>
                <span class="metric-value">${data.start_time || 'N/A'}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Énergie produite</span>
                <span class="metric-value">${(data.energy_kwh || 0).toFixed(2)} kWh</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Tarif appliqué</span>
                <span class="metric-value">${data.tariff.toFixed(3)} €/kWh</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Valeur estimée</span>
                <span class="metric-value">${(data.total_cost || 0).toFixed(2)} €</span>
            </div>
        `;

        // Mettre à jour les données de télémétrie brutes
        document.getElementById('telemetryRaw').textContent = JSON.stringify(data.raw_data || data, null, 2);

        console.log('Données coût:', data);

    } catch (error) {
        container.innerHTML = `<div class="error-message">Erreur: ${error.message}</div>`;
        console.error('Erreur:', error);
    }
}

// Fonctions utilitaires
function getPeriodLabel(period) {
    const labels = {
        'day': "Aujourd'hui",
        'week': 'Cette semaine (7 jours)',
        'month': 'Ce mois (30 jours)',
        'year': 'Cette année (365 jours)'
    };
    return labels[period] || period;
}

function refreshRealtime() {
    if (currentPlantId) {
        loadRealtimeData();
    }
}

function refreshEnergyProduction() {
    if (currentPlantId) {
        loadEnergyProduction();
        loadEnergyCost();
    }
}

function refreshEnergyCost() {
    if (currentPlantId) {
        loadEnergyCost();
    }
}

function toggleRawData() {
    const telemetryData = document.getElementById('telemetryData');
    telemetryData.classList.toggle('hidden');
}

// Nettoyage à la fermeture de la page
window.addEventListener('beforeunload', function () {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});
