const COLORS = {
  Supportive_of_Victim: "#0f766e",
  Neutral_Reporting: "#2563eb",
  Critical_of_Society: "#b45309",
  Critical_of_Govt: "#be123c",
  PRE: "#6d28d9",
  ACUTE: "#be123c",
  SUSTAINED: "#2563eb",
  RETROSPECTIVE: "#0f766e",
  UNKNOWN: "#64748b",
  reddit: "#2563eb",
  youtube: "#be123c",
};

let summaryData = null;

function formatNumber(value) {
  return new Intl.NumberFormat("en-US").format(value || 0);
}

function caseLabel(value) {
  return value.replaceAll("_", " ");
}

function displayLabel(mapping, value) {
  return mapping[value] || caseLabel(value);
}

function baseLayout(extra = {}) {
  return {
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    margin: { l: 58, r: 24, t: 18, b: 56 },
    font: {
      family:
        "Arial, Helvetica, sans-serif",
      color: "#111827",
    },
    xaxis: {
      gridcolor: "#e5edf5",
      zerolinecolor: "#d8e0ea",
    },
    yaxis: {
      gridcolor: "#e5edf5",
      zerolinecolor: "#d8e0ea",
    },
    legend: {
      orientation: "h",
      y: -0.18,
      x: 0,
    },
    ...extra,
  };
}

function renderMetrics(data) {
  const metrics = data.headline_metrics;
  document.getElementById("metric-rows").textContent = formatNumber(
    metrics.public_discourse_rows,
  );
  document.getElementById("metric-cases").textContent = formatNumber(
    metrics.case_count,
  );
  document.getElementById("metric-case-years").textContent =
    `Case years ${data.case_year_range}`;
  document.getElementById("metric-canonical").textContent = formatNumber(
    metrics.canonical_case_rows,
  );
  document.getElementById("metric-quality").textContent =
    `${metrics.duplicate_text_hash_extra_rows} / ${metrics.invalid_stance_count + metrics.invalid_phase_count}`;
  document.getElementById("evidence-rows").textContent =
    `${formatNumber(metrics.public_discourse_rows)} public rows, ${formatNumber(metrics.canonical_case_rows)} canonical case rows`;
  document.getElementById("evidence-generated").textContent =
    new Date(data.generated_at_utc).toLocaleString();
}

function setupSelector(data) {
  const select = document.getElementById("case-select");
  select.innerHTML = "";
  data.per_case.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.case;
    option.textContent = caseLabel(item.case);
    select.appendChild(option);
  });
  select.addEventListener("change", () => renderSelectedCase(select.value));
}

function selectedCase(caseName) {
  return summaryData.per_case.find((item) => item.case === caseName);
}

function renderCaseVolume(data) {
  const rows = [...data.per_case].sort((a, b) => a.n - b.n);
  Plotly.newPlot(
    "case-volume-chart",
    [
      {
        type: "bar",
        orientation: "h",
        x: rows.map((item) => item.n),
        y: rows.map((item) => caseLabel(item.case)),
        marker: { color: "#2563eb" },
        hovertemplate: "%{y}<br>%{x:,} rows<extra></extra>",
      },
    ],
    baseLayout({
      margin: { l: 150, r: 22, t: 12, b: 48 },
      xaxis: { title: "Rows", gridcolor: "#e5edf5" },
      yaxis: { automargin: true },
    }),
    { displayModeBar: false, responsive: true },
  );
}

function renderStanceMix(data) {
  const rows = [...data.per_case].sort((a, b) => b.n - a.n);
  const traces = data.stance_order.map((stance) => ({
    type: "bar",
    orientation: "h",
    name: displayLabel(data.display_stance, stance),
    x: rows.map((item) => item.stance_pct[stance] || 0),
    y: rows.map((item) => caseLabel(item.case)),
    marker: { color: COLORS[stance] },
    hovertemplate: `%{y}<br>${displayLabel(data.display_stance, stance)}: %{x:.2f}%<extra></extra>`,
  }));

  Plotly.newPlot(
    "stance-mix-chart",
    traces,
    baseLayout({
      barmode: "stack",
      margin: { l: 150, r: 22, t: 12, b: 58 },
      xaxis: {
        title: "Percent of case rows",
        range: [0, 100],
        ticksuffix: "%",
        gridcolor: "#e5edf5",
      },
      yaxis: { automargin: true },
    }),
    { displayModeBar: false, responsive: true },
  );
}

function renderGapTable(data) {
  const tbody = document.getElementById("gap-table");
  tbody.innerHTML = "";
  [...data.per_case]
    .sort(
      (a, b) =>
        b.stance_gap_vs_general_pct_points -
        a.stance_gap_vs_general_pct_points,
    )
    .slice(0, 8)
    .forEach((item) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${caseLabel(item.case)}</td>
        <td>${formatNumber(item.n)}</td>
        <td>${item.stance_gap_vs_general_pct_points.toFixed(2)}</td>
        <td>${displayLabel(data.display_stance, item.dominant_stance)}</td>
      `;
      tbody.appendChild(tr);
    });
}

function renderSelectedCase(caseName) {
  const data = summaryData;
  const item = selectedCase(caseName);
  if (!item) return;

  document.getElementById("case-note").textContent =
    `${formatNumber(item.n)} rows, peak month ${item.peak_month || "n/a"}, dominant stance: ${displayLabel(data.display_stance, item.dominant_stance)}.`;

  const platforms = Object.keys(item.platform_counts);
  Plotly.newPlot(
    "platform-chart",
    [
      {
        type: "bar",
        x: platforms.map((platform) => caseLabel(platform)),
        y: platforms.map((platform) => item.platform_counts[platform]),
        marker: { color: "#4d6f8b" },
        hovertemplate: "%{x}<br>%{y:,} rows<extra></extra>",
      },
    ],
    baseLayout({
      margin: { l: 58, r: 20, t: 8, b: 50 },
      xaxis: { title: "Platform" },
      yaxis: { title: "Rows", gridcolor: "#e5e5e5", rangemode: "tozero" },
      showlegend: false,
    }),
    { displayModeBar: false, responsive: true },
  );

  const phases = data.phase_order.filter((phase) => item.phase_counts[phase]);
  Plotly.newPlot(
    "phase-chart",
    [
      {
        type: "bar",
        x: phases.map((phase) => displayLabel(data.display_phase, phase)),
        y: phases.map((phase) => item.phase_counts[phase]),
        marker: { color: phases.map((phase) => COLORS[phase] || "#64748b") },
        hovertemplate: "%{x}<br>%{y:,} rows<extra></extra>",
      },
    ],
    baseLayout({
      margin: { l: 56, r: 16, t: 10, b: 86 },
      xaxis: { tickangle: -24 },
      yaxis: { title: "Rows", gridcolor: "#e5edf5" },
      showlegend: false,
    }),
    { displayModeBar: false, responsive: true },
  );

  const monthly = data.monthly_case_counts.filter((row) => row.case === caseName);
  Plotly.newPlot(
    "timeline-chart",
    [
      {
        type: "scatter",
        mode: "lines+markers",
        x: monthly.map((row) => row.month),
        y: monthly.map((row) => row.count),
        line: { color: "#0f766e", width: 3 },
        marker: { size: 6, color: "#0f766e" },
        hovertemplate: "%{x}<br>%{y:,} rows<extra></extra>",
      },
    ],
    baseLayout({
      margin: { l: 60, r: 20, t: 10, b: 54 },
      xaxis: { title: "Month", gridcolor: "#e5edf5" },
      yaxis: { title: "Rows", gridcolor: "#e5edf5" },
      showlegend: false,
    }),
    { displayModeBar: false, responsive: true },
  );
}

async function init() {
  const response = await fetch("data/public_summary.json");
  summaryData = await response.json();
  renderMetrics(summaryData);
  setupSelector(summaryData);
  renderCaseVolume(summaryData);
  renderStanceMix(summaryData);
  renderGapTable(summaryData);
  renderSelectedCase(summaryData.per_case[0].case);
}

init().catch((error) => {
  document.body.innerHTML = `<main class="evidence"><h1>Dashboard load failed</h1><p>${error.message}</p></main>`;
});
