// EdgeDC 360 - Operations Center Dashboard Application

document.addEventListener("DOMContentLoaded", () => {
    let selectedLocation = "global";

    // Interactive Rack Selector Card Listener
    const rackCards = document.querySelectorAll(".rack-card");
    const activeLocationBadge = document.getElementById("activeLocationBadge");

    rackCards.forEach(card => {
        card.addEventListener("click", () => {
            rackCards.forEach(c => c.classList.remove("active"));
            card.classList.add("active");

            selectedLocation = card.getAttribute("data-rack");
            
            const labels = {
                "global": "Global Fleet",
                "dublin-rack-01": "Dublin Rack-01",
                "dublin-rack-02": "Dublin Rack-02",
                "cork-rack-01": "Cork Rack-01",
                "cork-rack-02": "Cork Rack-02",
                "galway-rack-01": "Galway Rack-01",
                "galway-rack-02": "Galway Rack-02"
            };

            activeLocationBadge.innerText = labels[selectedLocation] || "Selected Rack";
            fetchTelemetry();
        });
    });

    function updateCardClass(cardId, newClass) {
        const card = document.getElementById(cardId);
        if (card) {
            card.className = "kpi-card " + newClass;
        }
    }

    // Theme Switch
    const themeSwitch = document.getElementById("themeSwitch");
    const body = document.body;

    themeSwitch.addEventListener("click", () => {
        if (body.classList.contains("dark-theme")) {
            body.classList.remove("dark-theme");
            body.classList.add("light-theme");
            themeSwitch.innerHTML = '<i class="fa-solid fa-sun"></i><span>Light Mode</span>';
        } else {
            body.classList.remove("light-theme");
            body.classList.add("dark-theme");
            themeSwitch.innerHTML = '<i class="fa-solid fa-moon"></i><span>Dark Mode</span>';
        }
        
        const isDark = body.classList.contains("dark-theme");
        Chart.defaults.color = isDark ? "#94a3b8" : "#64748b";
        Chart.defaults.borderColor = isDark ? "rgba(255, 255, 255, 0.05)" : "rgba(0, 0, 0, 0.05)";
        updateAllCharts();
    });

    // Navigation Tabs
    const navItems = document.querySelectorAll(".nav-item");
    const views = document.querySelectorAll(".dashboard-view");
    const pageTitle = document.getElementById("current-dashboard-title");
    const pageSubtitle = document.getElementById("current-dashboard-subtitle");

    const tabDetails = {
        'live-ops': { title: 'Live Operations Dashboard', sub: 'Real-time telemetry and health status of critical infrastructure' },
        'fog-computing': { title: 'Fog Computing Dashboard', sub: 'Edge processing efficiency, latency, and cloud bandwidth savings' },
        'analytics': { title: 'Infrastructure Analytics Dashboard', sub: 'Historical trends, PUE cooling efficiency, and energy logs' },
        'executive': { title: 'Executive Dashboard', sub: 'High-level SLAs, system availability, and cluster cost efficiency' }
    };

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            navItems.forEach(nav => nav.classList.remove("active"));
            item.classList.add("active");

            const target = item.getAttribute("data-target");
            views.forEach(view => {
                view.classList.remove("active");
                if (view.id === target) {
                    view.classList.add("active");
                }
            });

            if (tabDetails[target]) {
                pageTitle.innerText = tabDetails[target].title;
                pageSubtitle.innerText = tabDetails[target].sub;
            }
        });
    });

    // Global Chart.js Settings
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Outfit', sans-serif";
    Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.05)';

    // 1. Live Temp Chart
    const liveTempCtx = document.getElementById('liveTempChart').getContext('2d');
    const liveTempChart = new Chart(liveTempCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Temperature (°C)',
                data: [],
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            plugins: { legend: { display: false } },
            scales: { y: { min: 15, max: 95 } }
        }
    });

    // 2. Live Power Chart
    const livePowerCtx = document.getElementById('livePowerChart').getContext('2d');
    const livePowerChart = new Chart(livePowerCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Power Consumption (kW)',
                data: [],
                backgroundColor: [],
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            plugins: { legend: { display: false } }
        }
    });

    // 3. Fog Doughnut Chart
    const fogDoughnutCtx = document.getElementById('fogDoughnutChart').getContext('2d');
    const fogDoughnutChart = new Chart(fogDoughnutCtx, {
        type: 'doughnut',
        data: {
            labels: ['Filtered at Edge', 'Uploaded to Cloud'],
            datasets: [{
                data: [0, 0],
                backgroundColor: ['#3b82f6', '#f59e0b'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            cutout: '75%',
            plugins: { legend: { position: 'bottom' } }
        }
    });

    // 4. Fog Latency Chart
    const fogLatencyCtx = document.getElementById('fogLatencyChart').getContext('2d');
    const fogLatencyChart = new Chart(fogLatencyCtx, {
        type: 'bar',
        data: {
            labels: ['Edge Fog Computing', 'Direct Cloud Processing'],
            datasets: [{
                label: 'Latency (ms)',
                data: [5.0, 145.0],
                backgroundColor: ['#10b981', '#ef4444'],
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            plugins: { legend: { display: false } }
        }
    });

    // 5. Analytics Temperature Chart
    const analyticsTempCtx = document.getElementById('analyticsTempChart').getContext('2d');
    const analyticsTempChart = new Chart(analyticsTempCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: 'Dublin Rack (°C)', data: [], borderColor: '#10b981', tension: 0.4 },
                { label: 'Cork Rack (°C)', data: [], borderColor: '#f59e0b', tension: 0.4 },
                { label: 'Galway Rack (°C)', data: [], borderColor: '#0ea5e9', tension: 0.4 }
            ]
        },
        options: { responsive: true, maintainAspectRatio: false, animation: false }
    });

    // 6. Analytics Cooling Efficiency Chart
    const analyticsCoolingCtx = document.getElementById('analyticsCoolingChart').getContext('2d');
    const analyticsCoolingChart = new Chart(analyticsCoolingCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{ label: 'Cooling Speed (RPM)', data: [], borderColor: '#3b82f6', tension: 0.4 }]
        },
        options: { responsive: true, maintainAspectRatio: false, animation: false }
    });

    // 7. Analytics Energy Chart
    const analyticsEnergyCtx = document.getElementById('analyticsEnergyChart').getContext('2d');
    const analyticsEnergyChart = new Chart(analyticsEnergyCtx, {
        type: 'bar',
        data: {
            labels: ['Dublin Load', 'Cork Load', 'Galway Load'],
            datasets: [{ label: 'Power (kW)', data: [], backgroundColor: ['#3b82f6', '#0ea5e9', '#10b981'], borderRadius: 6 }]
        },
        options: { responsive: true, maintainAspectRatio: false, animation: false, plugins: { legend: { display: false } } }
    });

    // 8. Analytics UPS Chart
    const analyticsUpsCtx = document.getElementById('analyticsUpsChart').getContext('2d');
    const analyticsUpsChart = new Chart(analyticsUpsCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{ label: 'UPS Battery Charge (%)', data: [], borderColor: '#10b981', tension: 0.2 }]
        },
        options: { responsive: true, maintainAspectRatio: false, animation: false, scales: { y: { min: 80, max: 100 } } }
    });

    // 9. Executive SLA Chart
    const execSlaCtx = document.getElementById('execSlaChart').getContext('2d');
    const execSlaChart = new Chart(execSlaCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{ label: 'Health Score Trend', data: [], borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', fill: true, tension: 0.3 }]
        },
        options: { responsive: true, maintainAspectRatio: false, animation: false, scales: { y: { min: 0, max: 100 } } }
    });

    function updateAllCharts() {
        liveTempChart.update();
        livePowerChart.update();
        fogDoughnutChart.update();
        fogLatencyChart.update();
        analyticsTempChart.update();
        analyticsCoolingChart.update();
        analyticsEnergyChart.update();
        analyticsUpsChart.update();
        execSlaChart.update();
    }

    // Real-Time Backend Polling Function
    async function fetchTelemetry() {
        try {
            const response = await fetch("/api/metrics");
            if (!response.ok) return;
            const data = await response.json();

            // 1. Update Fog Layer Metrics
            if (data.fog) {
                document.getElementById("fog-gen").innerText = Number(data.fog.generated || 0).toLocaleString();
                document.getElementById("fog-filt").innerText = Number(data.fog.filtered || 0).toLocaleString();
                document.getElementById("fog-up").innerText = Number(data.fog.uploaded || 0).toLocaleString();
                
                const latencyVal = data.fog.latency !== undefined ? data.fog.latency : 5;
                document.getElementById("fog-lat").innerText = `${latencyVal} ms`;
                fogLatencyChart.data.datasets[0].data = [latencyVal, 145.0];
                fogLatencyChart.update();

                const savings = (data.fog.bandwidth_saved || 0).toFixed(1);
                document.getElementById("fog-savings").innerText = `${savings} %`;
                document.getElementById("exec-savings").innerText = `${savings} %`;

                fogDoughnutChart.data.datasets[0].data = [data.fog.filtered || 0, data.fog.uploaded || 0];
                fogDoughnutChart.update();
            }

            // 2. Process Racks Data
            const racks = data.racks || {};
            const rackKeys = Object.keys(racks);

            if (rackKeys.length > 0) {
                // Update individual rack card status pills & score tags
                rackKeys.forEach(rk => {
                    const rData = racks[rk];
                    const cardKey = rk.toLowerCase(); // e.g. "dublin-rack-01"
                    const badgeElem = document.getElementById(`badge-${cardKey}`);
                    const scoreElem = document.getElementById(`score-${cardKey}`);
                    if (badgeElem && scoreElem) {
                        const state = rData.health_state || "healthy";
                        badgeElem.innerText = state;
                        badgeElem.className = `status-pill status-${state}`;
                        scoreElem.innerText = `${rData.health_score || 100}/100`;
                    }
                });

                // Filter racks based on selected rack card
                let selectedRacks = [];
                if (selectedLocation === "global") {
                    selectedRacks = rackKeys;
                } else {
                    selectedRacks = rackKeys.filter(k => k.toLowerCase() === selectedLocation.toLowerCase());
                    if (selectedRacks.length === 0) {
                        // Fallback partial match
                        const sitePrefix = selectedLocation.split("-")[0];
                        selectedRacks = rackKeys.filter(k => k.toLowerCase().includes(sitePrefix));
                    }
                }

                if (selectedRacks.length > 0) {
                    let activeCriticals = 0, activeWarnings = 0, healthyCount = 0;
                    let maxTemp = -Infinity, maxTempRack = "";
                    let minHum = Infinity, maxHum = -Infinity;
                    let minUps = Infinity, minUpsRack = "";
                    let maxCooling = -Infinity, maxCoolingRack = "";
                    let totalPower = 0;
                    let minHealth = Infinity;

                    let singleTemp = 0, singleHum = 0, singleUps = 0, singleCooling = 0, singlePower = 0, singleHealth = 0;

                    selectedRacks.forEach(rk => {
                        const rData = racks[rk];
                        const s = rData.sensors || {};
                        
                        const tempVal = s.temperature ? s.temperature.value : 22.5;
                        const humVal = s.humidity ? s.humidity.value : 45.0;
                        const upsVal = s.ups ? s.ups.value : 100.0;
                        const coolVal = s.cooling ? s.cooling.value : 2200;
                        const pWatts = s.power ? s.power.value : 400;
                        const pKw = pWatts > 100 ? pWatts / 1000.0 : pWatts;
                        const score = rData.health_score !== undefined ? rData.health_score : 100;

                        if (rData.health_state === "critical") activeCriticals++;
                        else if (rData.health_state === "warning") activeWarnings++;
                        else healthyCount++;

                        totalPower += pKw;

                        if (tempVal > maxTemp) { maxTemp = tempVal; maxTempRack = rk; }
                        if (humVal < minHum) minHum = humVal;
                        if (humVal > maxHum) maxHum = humVal;
                        if (upsVal < minUps) { minUps = upsVal; minUpsRack = rk; }
                        if (coolVal > maxCooling) { maxCooling = coolVal; maxCoolingRack = rk; }
                        if (score < minHealth) minHealth = score;

                        singleTemp = tempVal;
                        singleHum = humVal;
                        singleUps = upsVal;
                        singleCooling = coolVal;
                        singlePower = pKw;
                        singleHealth = score;
                    });

                    if (selectedLocation === "global") {
                        // Option 1: Fleet Aggregates & Peak Extremity Highlighting
                        document.getElementById("val-temp").innerText = `${maxTemp.toFixed(1)} °C`;
                        document.getElementById("val-humidity").innerText = `${minHum.toFixed(1)} - ${maxHum.toFixed(1)} %`;
                        document.getElementById("val-ups").innerText = `${minUps.toFixed(1)} %`;
                        document.getElementById("val-cooling").innerText = `${Math.round(maxCooling)} RPM`;
                        document.getElementById("val-power").innerText = `${totalPower.toFixed(2)} kW`;
                        document.getElementById("val-health").innerText = `${minHealth} / 100`;

                        document.getElementById("status-temp").innerText = maxTemp >= 36 ? `Peak Temp (${maxTempRack}) [CRITICAL]` : maxTemp >= 30 ? `Peak Temp (${maxTempRack}) [WARNING]` : `Peak Temp (${maxTempRack})`;
                        document.getElementById("status-humidity").innerText = `Fleet Humidity Range`;
                        document.getElementById("status-ups").innerText = `Lowest Reserve (${minUpsRack})`;
                        document.getElementById("status-cooling").innerText = `Peak Cooling Load (${maxCoolingRack})`;
                        document.getElementById("status-power").innerText = `Total Combined Fleet Load`;
                        document.getElementById("status-health").innerText = `${healthyCount} Healthy, ${activeWarnings} Warn, ${activeCriticals} Crit`;

                        if (maxTemp >= 36 || activeCriticals > 0) {
                            updateCardClass("card-temp", "card-critical");
                        } else if (maxTemp >= 30 || activeWarnings > 0) {
                            updateCardClass("card-temp", "card-warning");
                        } else {
                            updateCardClass("card-temp", "card-healthy");
                        }
                    } else {
                        // Individual Rack View
                        document.getElementById("val-temp").innerText = `${singleTemp.toFixed(1)} °C`;
                        document.getElementById("val-humidity").innerText = `${singleHum.toFixed(1)} %`;
                        document.getElementById("val-ups").innerText = `${singleUps.toFixed(1)} %`;
                        document.getElementById("val-cooling").innerText = `${Math.round(singleCooling)} RPM`;
                        document.getElementById("val-power").innerText = `${singlePower.toFixed(2)} kW`;
                        document.getElementById("val-health").innerText = `${singleHealth} / 100`;

                        document.getElementById("status-humidity").innerText = `Optimal Range (40 - 60%)`;
                        document.getElementById("status-ups").innerText = `Mains Active`;
                        document.getElementById("status-cooling").innerText = `HVAC Operating Normally`;
                        document.getElementById("status-power").innerText = `Rack Power Load`;
                        document.getElementById("status-health").innerText = `All 5 Sensors Aggregated`;

                        if (singleTemp >= 36 || activeCriticals > 0) {
                            updateCardClass("card-temp", "card-critical");
                            document.getElementById("status-temp").innerText = "CRITICAL: Sensor Limit Exceeded";
                        } else if (singleTemp >= 30 || activeWarnings > 0) {
                            updateCardClass("card-temp", "card-warning");
                            document.getElementById("status-temp").innerText = "WARNING: Elevated Temperature";
                        } else {
                            updateCardClass("card-temp", "card-healthy");
                            document.getElementById("status-temp").innerText = "Normal Range (18 - 27°C)";
                        }
                    }

                    // Executive KPIs
                    const globalHealthSum = rackKeys.reduce((acc, rk) => acc + (racks[rk].health_score !== undefined ? racks[rk].health_score : 100), 0);
                    const globalHealthAvg = (globalHealthSum / rackKeys.length).toFixed(1);
                    const globalCriticals = rackKeys.filter(rk => racks[rk].health_state === "critical").length;
                    const globalWarnings = rackKeys.filter(rk => racks[rk].health_state === "warning").length;

                    document.getElementById("exec-health").innerText = `${globalHealthAvg}%`;
                    document.getElementById("exec-alerts").innerText = `${globalCriticals}`;
                    document.getElementById("exec-warnings").innerText = `${globalWarnings}`;

                    const healthSubtextElem = document.getElementById("exec-health-subtext");
                    if (globalCriticals > 0) {
                        updateCardClass("exec-card-health", "card-critical");
                        if (healthSubtextElem) healthSubtextElem.innerText = `CRITICAL: ${globalCriticals} Rack Failure(s)`;
                    } else if (globalWarnings > 0 || parseFloat(globalHealthAvg) < 95) {
                        updateCardClass("exec-card-health", "card-warning");
                        if (healthSubtextElem) healthSubtextElem.innerText = `WARNING: ${globalWarnings} Degradation(s)`;
                    } else {
                        updateCardClass("exec-card-health", "card-healthy");
                        if (healthSubtextElem) healthSubtextElem.innerText = `Global Fleet Operational`;
                    }

                    updateCardClass("exec-card-alerts", globalCriticals > 0 ? "card-critical" : "card-healthy");
                    updateCardClass("exec-card-warnings", globalWarnings > 0 ? "card-warning" : "card-healthy");

                    // Pulse Indicator
                    if (activeCriticals > 0) {
                        document.getElementById("systemStatusText").innerText = "System Critical Alert";
                        document.getElementById("systemPulseDot").className = "pulse-dot critical";
                    } else if (activeWarnings > 0) {
                        document.getElementById("systemStatusText").innerText = "System Warning Active";
                        document.getElementById("systemPulseDot").className = "pulse-dot warning";
                    } else {
                        document.getElementById("systemStatusText").innerText = "System Healthy";
                        document.getElementById("systemPulseDot").className = "pulse-dot";
                    }

                    // Update Live Power Bar Chart
                    livePowerChart.data.labels = selectedRacks;
                    livePowerChart.data.datasets[0].data = selectedRacks.map(rk => {
                        const p = racks[rk].sensors ? racks[rk].sensors.power.value : 400;
                        return (p > 100 ? p / 1000.0 : p).toFixed(2);
                    });
                    livePowerChart.data.datasets[0].backgroundColor = selectedRacks.map(rk => {
                        const state = racks[rk].health_state;
                        return state === "critical" ? "#ef4444" : state === "warning" ? "#f59e0b" : "#10b981";
                    });
                    livePowerChart.update();

                    // Update Infrastructure Analytics Energy Bar Chart
                    const dublinPower = rackKeys.filter(k => k.toLowerCase().includes("dublin")).reduce((acc, k) => acc + (racks[k].sensors.power.value / 1000.0), 0);
                    const corkPower = rackKeys.filter(k => k.toLowerCase().includes("cork")).reduce((acc, k) => acc + (racks[k].sensors.power.value / 1000.0), 0);
                    const galwayPower = rackKeys.filter(k => k.toLowerCase().includes("galway")).reduce((acc, k) => acc + (racks[k].sensors.power.value / 1000.0), 0);
                    analyticsEnergyChart.data.datasets[0].data = [dublinPower.toFixed(2), corkPower.toFixed(2), galwayPower.toFixed(2)];
                    analyticsEnergyChart.update();
                }
            }

            // 3. Update History Line Charts across dashboards
            if (data.history && data.history.timestamps && data.history.timestamps.length > 0) {
                const timeLabels = data.history.timestamps.map(t => {
                    if (t.includes("T")) {
                        return t.split("T")[1].substring(0, 8);
                    }
                    return t;
                });

                // Live Temperature Trend
                liveTempChart.data.labels = timeLabels;
                liveTempChart.data.datasets[0].data = data.history.temperature;
                liveTempChart.update();

                // Cooling Efficiency Chart
                analyticsCoolingChart.data.labels = timeLabels;
                analyticsCoolingChart.data.datasets[0].data = data.history.cooling;
                analyticsCoolingChart.update();

                // UPS Battery Chart
                analyticsUpsChart.data.labels = timeLabels;
                analyticsUpsChart.data.datasets[0].data = data.history.ups;
                analyticsUpsChart.update();

                // Executive SLA / Health Score Trend Chart
                execSlaChart.data.labels = timeLabels;
                const healthHistory = data.history.temperature.map(temp => (temp > 35 ? 0 : temp > 28 ? 60 : 98));
                execSlaChart.data.datasets[0].data = healthHistory;
                execSlaChart.update();
            }

            // Last Updated Timestamp
            const now = new Date();
            document.getElementById("lastUpdatedTime").innerText = `Updated: ${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;

        } catch (err) {
            console.log("Polling error:", err);
        }
    }

    // Initial fetch & continuous 3-second polling
    fetchTelemetry();
    setInterval(fetchTelemetry, 3000);
});
