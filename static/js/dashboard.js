/**
 * SafeDrive AI Dashboard — Frontend Logic
 * 
 * Fetches metrics from the Flask API and renders
 * charts, metrics, and the events table. Auto-refreshes
 * every 10 seconds.
 */

(function () {
    "use strict";

    const API_METRICS = "/api/metrics";
    const REFRESH_INTERVAL_MS = 10_000;

    // Color palette matching CSS variables
    const COLORS = [
        "#ef4444", "#f97316", "#eab308", "#22c55e",
        "#06b6d4", "#3b82f6", "#a855f7", "#ec4899",
    ];

    /**
     * Determine severity level from event name.
     */
    function getSeverity(event) {
        if (event.includes("EMERGENCY") || event.includes("SMS")) return "critical";
        if (event.includes("BUZZER") || event.includes("PHONE")) return "warning";
        if (event.includes("DROWSY") || event.includes("DISTRACTION")) return "info";
        return "low";
    }

    /**
     * Animate a number from 0 to target.
     */
    function animateNumber(element, target) {
        const current = parseInt(element.textContent) || 0;
        if (current === target) return;

        const duration = 800;
        const start = performance.now();

        function step(now) {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
            element.textContent = Math.round(current + (target - current) * eased);
            if (progress < 1) requestAnimationFrame(step);
        }

        requestAnimationFrame(step);
    }

    /**
     * Update the SVG score ring.
     */
    function updateScoreRing(score) {
        const ring = document.getElementById("score-ring-fill");
        if (!ring) return;

        const circumference = 2 * Math.PI * 52; // r=52
        const offset = circumference - (score / 100) * circumference;
        ring.style.strokeDashoffset = offset;

        // Change color based on score
        if (score >= 80) {
            ring.style.stroke = "#22c55e";
        } else if (score >= 50) {
            ring.style.stroke = "#eab308";
        } else {
            ring.style.stroke = "#ef4444";
        }

        const scoreEl = document.getElementById("safety-score");
        if (scoreEl) animateNumber(scoreEl, score);
    }

    /**
     * Render the distribution bar chart.
     */
    function renderDistributionChart(distribution) {
        const container = document.getElementById("distribution-chart");
        if (!container) return;

        if (!distribution || distribution.length === 0) {
            container.innerHTML = '<div class="chart-empty">No events to display</div>';
            return;
        }

        const maxCount = Math.max(...distribution.map(d => d.count), 1);

        let html = '<div class="bar-chart">';
        distribution.forEach((item, i) => {
            const height = Math.max((item.count / maxCount) * 200, 4);
            const color = COLORS[i % COLORS.length];
            const label = item.event
                .replace(/_/g, " ")
                .replace(/\b\w/g, c => c.toUpperCase());

            html += `
                <div class="bar-item">
                    <div class="bar" 
                         style="height: ${height}px; background: ${color};" 
                         data-count="${item.count}"></div>
                    <span class="bar-label">${label}</span>
                </div>`;
        });
        html += "</div>";
        container.innerHTML = html;
    }

    /**
     * Render the timeline bar chart.
     */
    function renderTimelineChart(timeline) {
        const container = document.getElementById("timeline-chart");
        if (!container) return;

        if (!timeline || timeline.length === 0) {
            container.innerHTML = '<div class="chart-empty">No timeline data</div>';
            return;
        }

        const maxCount = Math.max(...timeline.map(d => d.count), 1);

        let html = '<div class="timeline-chart">';
        timeline.forEach(item => {
            const height = Math.max((item.count / maxCount) * 200, 4);
            html += `
                <div class="timeline-bar" 
                     style="height: ${height}px;" 
                     data-tooltip="${item.date}: ${item.count} alerts"></div>`;
        });
        html += "</div>";
        container.innerHTML = html;
    }

    /**
     * Render the events table.
     */
    function renderEventsTable(events) {
        const tbody = document.getElementById("events-tbody");
        const countEl = document.getElementById("table-count");
        if (!tbody) return;

        if (countEl) countEl.textContent = `${events.length} events`;

        if (!events || events.length === 0) {
            tbody.innerHTML = '<tr class="empty-row"><td colspan="4">No events recorded yet</td></tr>';
            return;
        }

        let html = "";
        events.forEach(e => {
            const severity = getSeverity(e.Event);
            const eventLabel = e.Event.replace(/_/g, " ");
            html += `
                <tr>
                    <td>${e.Date}</td>
                    <td>${e.Time}</td>
                    <td>${eventLabel}</td>
                    <td><span class="severity-badge severity-${severity}">${severity}</span></td>
                </tr>`;
        });
        tbody.innerHTML = html;
    }

    /**
     * Fetch metrics and update the entire dashboard.
     */
    async function refreshDashboard() {
        try {
            const res = await fetch(API_METRICS);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            // Update metrics
            animateNumber(document.getElementById("total-alerts"), data.total_alerts || 0);
            animateNumber(document.getElementById("drowsy-count"), data.drowsy_count || 0);
            animateNumber(document.getElementById("yawn-count"), data.yawn_count || 0);
            animateNumber(document.getElementById("phone-count"), data.phone_count || 0);
            animateNumber(document.getElementById("distraction-count"), data.distraction_count || 0);

            // Update score ring
            updateScoreRing(data.safety_score ?? 100);

            // Render charts
            renderDistributionChart(data.distribution || []);
            renderTimelineChart(data.timeline || []);

            // Render table
            renderEventsTable(data.recent_events || []);

            // Update timestamp
            const updated = document.getElementById("last-updated");
            if (updated) {
                updated.textContent = "Updated " + new Date().toLocaleTimeString();
            }

        } catch (err) {
            console.error("Dashboard refresh failed:", err);
        }
    }

    // Initial load
    document.addEventListener("DOMContentLoaded", () => {
        refreshDashboard();
        setInterval(refreshDashboard, REFRESH_INTERVAL_MS);
    });

})();
