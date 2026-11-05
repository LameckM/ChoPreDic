import { useCallback, useEffect, useMemo, useState } from "react";
import DistrictRiskMap from "./DistrictRiskMap";
import {
  Activity, AlertTriangle, ArrowDownRight, ArrowUpRight, Bell, CheckCircle2,
  ChevronDown, ChevronRight, CircleHelp, Clock3, Database, Download, FileBarChart2,
  Gauge, HeartPulse, LayoutDashboard, MapPinned, Menu, RefreshCw, Search,
  ShieldAlert, ShieldCheck, SlidersHorizontal, Wifi, WifiOff, X
} from "lucide-react";
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, ComposedChart, Legend,
  Line, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis
} from "recharts";


const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const RISK_COLORS = { high: "#dc655b", medium: "#e7a84b", low: "#36a889" };
const LEVEL_ORDER = { high: 0, medium: 1, low: 2 };

async function getJson(path) {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(`${path}: ${response.status} ${message}`);
  }
  return response.json();
}

function prettyModel(value = "") {
  return value.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
function percent(value) {
  return Number.isFinite(Number(value)) ? `${(Number(value) * 100).toFixed(1)}%` : "—";
}
function number(value) {
  return Number(value || 0).toLocaleString();
}
function levelLabel(value = "") {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function SectionHeading({ eyebrow, title, action }) {
  return (
    <div className="section-heading">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h2>{title}</h2>
      </div>
      {action}
    </div>
  );
}

function MetricCard({ label, value, detail, icon: Icon, tone = "teal" }) {
  return (
    <article className="metric-card">
      <div className={`metric-icon ${tone}`}><Icon size={19} /></div>
      <div className="metric-copy">
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{detail}</small>
      </div>
    </article>
  );
}

function RiskPill({ level }) {
  return <span className={`risk-pill ${level || "unknown"}`}><i />{levelLabel(level || "unknown")}</span>;
}

function EmptyState({ title, detail }) {
  return <div className="empty-state"><CircleHelp size={22} /><strong>{title}</strong><span>{detail}</span></div>;
}

function DistrictModal({ district, onClose }) {
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    getJson(`/api/districts/${encodeURIComponent(district.district)}`)
      .then((data) => { if (active) setDetail(data); })
      .catch((err) => { if (active) setError(err.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [district.district]);

  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <section className="district-modal">
        <div className="modal-top">
          <div><span className="eyebrow">DISTRICT PROFILE</span><h2>{district.district}</h2></div>
          <button className="icon-button" onClick={onClose} aria-label="Close district details"><X size={19} /></button>
        </div>
        <div className="district-modal-summary">
          <div><span>Forecast risk score</span><strong>{percent(district.risk)}</strong></div>
          <RiskPill level={district.level} />
          <div><span>Latest recorded cases</span><strong>{district.cases_latest == null ? "—" : number(district.cases_latest)}</strong></div>
        </div>
        {loading ? <div className="loading-line">Loading district history…</div> :
          error ? <div className="inline-error">{error}</div> : detail && <>
            <div className="chart-title"><strong>Reported cholera cases</strong><span>Historical annual records</span></div>
            <div className="modal-chart">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={detail.history}>
                  <defs><linearGradient id="districtFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#279b83" stopOpacity={0.25}/><stop offset="100%" stopColor="#279b83" stopOpacity={0.02}/></linearGradient></defs>
                  <CartesianGrid stroke="#edf1ef" vertical={false} />
                  <XAxis dataKey="year" tickLine={false} axisLine={false} tick={{ fill: "#83918e", fontSize: 11 }} />
                  <YAxis tickLine={false} axisLine={false} tick={{ fill: "#83918e", fontSize: 11 }} />
                  <Tooltip />
                  <Area type="monotone" dataKey="cases" stroke="#279b83" fill="url(#districtFill)" strokeWidth={2.5} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="static-grid">
              {Object.entries(detail.static || {}).map(([key, value]) => (
                <div key={key}><span>{key.replaceAll("_", " ")}</span><strong>{value == null ? "—" : number(value)}</strong></div>
              ))}
            </div>
          </>}
        <p className="modal-note">Risk scores are model scores for relative ranking, not calibrated probabilities or a diagnosis.</p>
      </section>
    </div>
  );
}

export default function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [apiOnline, setApiOnline] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [search, setSearch] = useState("");
  const [levelFilter, setLevelFilter] = useState("all");
  const [selectedDistrict, setSelectedDistrict] = useState(null);
  const [activeNav, setActiveNav] = useState("overview");
  const [mobileNav, setMobileNav] = useState(false);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [health, summary, risk, alerts, trends, districts, model] = await Promise.all([
        getJson("/health"),
        getJson("/api/summary"),
        getJson("/api/risk"),
        getJson("/api/alerts?min_level=medium"),
        getJson("/api/trends/national"),
        getJson("/api/districts"),
        getJson("/api/model"),
      ]);
      setData({ health, summary, risk, alerts, trends, districts, model });
      setApiOnline(health.status === "ok");
      setLastUpdated(new Date());
    } catch (err) {
      setApiOnline(false);
      setError(err.message || "Unable to connect to the API.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadDashboard(); }, [loadDashboard]);

  const districtRows = useMemo(() => {
    const rows = data?.risk?.districts || [];
    return rows.filter((row) => {
      const matchesSearch = row.district.toLowerCase().includes(search.toLowerCase());
      const matchesLevel = levelFilter === "all" || row.level === levelFilter;
      return matchesSearch && matchesLevel;
    });
  }, [data, search, levelFilter]);

  const modelRows = useMemo(() => {
    const results = data?.model?.results || {};
    return Object.entries(results).map(([name, metrics]) => ({ name, ...metrics }));
  }, [data]);

  function navigate(id) {
    setActiveNav(id);
    setMobileNav(false);
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function exportRiskCsv() {
    const rows = data?.risk?.districts || [];
    const csv = ["District,Risk score,Risk level,Latest cases", ...rows.map((r) =>
      [r.district, r.risk, r.level, r.cases_latest ?? ""].map((v) => `"${String(v).replaceAll('"', '""')}"`).join(",")
    )].join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8;" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "zambia-district-risk.csv";
    link.click();
    URL.revokeObjectURL(url);
  }

  const summary = data?.summary;
  const levels = summary?.levels || {};
  const trendData = data?.trends || [];
  const pieData = ["high", "medium", "low"].map((level) => ({ name: levelLabel(level), value: levels[level] || 0, fill: RISK_COLORS[level] }));
  const selectedModel = data?.model?.selected || summary?.model;
  const highCount = levels.high || 0;
  const mediumCount = levels.medium || 0;
  const lowCount = levels.low || 0;
  const basedOn = data?.risk?.based_on_year;
  const forecast = data?.risk?.forecast_year;

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileNav ? "open" : ""}`}>
        <div className="brand">
          <div className="brand-mark"><Activity size={23} strokeWidth={2.5}/></div>
          <div><strong>Cholera Prediction</strong><span>EARLY-WARNING SYSTEM</span></div>
          <button className="sidebar-close icon-button" onClick={() => setMobileNav(false)}><X size={18}/></button>
        </div>
        <div className="nav-label">WORKSPACE</div>
        <nav className="side-nav">
          <button className={activeNav === "overview" ? "active" : ""} onClick={() => navigate("overview")}><LayoutDashboard size={18}/> Overview</button>
          <button className={activeNav === "districts" ? "active" : ""} onClick={() => navigate("districts")}><MapPinned size={18}/> District risk</button>
          <button className={activeNav === "alerts" ? "active" : ""} onClick={() => navigate("alerts")}><Bell size={18}/> Early warnings{mediumCount + highCount > 0 && <b>{mediumCount + highCount}</b>}</button>
          <button className={activeNav === "model" ? "active" : ""} onClick={() => navigate("model")}><FileBarChart2 size={18}/> Model evaluation</button>
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-status"><span className={apiOnline ? "status-dot online" : "status-dot"} /> <span>{apiOnline ? "API connected" : "API disconnected"}</span></div>
          <div className="sidebar-footnote">Zambia public-health decision support prototype.</div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <button className="mobile-menu icon-button" onClick={() => setMobileNav(true)} aria-label="Open navigation"><Menu size={20}/></button>
          <div className="breadcrumb">Zambia <ChevronRight size={14}/> <strong>National overview</strong></div>
          <div className="topbar-actions">
            <div className={`connection ${apiOnline ? "connected" : ""}`}>{apiOnline ? <Wifi size={15}/> : <WifiOff size={15}/>}<span>{apiOnline ? "Live API" : "API offline"}</span></div>
            <button className="refresh-button" onClick={loadDashboard} disabled={loading}><RefreshCw size={15} className={loading ? "spin" : ""}/> Refresh</button>
          </div>
        </header>

        <div className="page-wrap">
          <section id="overview" className="page-intro">
            <div>
              <div className="eyebrow">PUBLIC HEALTH INTELLIGENCE</div>
              <h1>Cholera early warning dashboard</h1>
              <p>Monitor historical cholera patterns and review model-estimated district risk across Zambia.</p>
            </div>
            <div className="intro-meta">
              <span className="period-tag"><Clock3 size={14}/> {basedOn ? `Data through ${basedOn}` : "Historical data"}</span>
              <span className="period-tag forecast"><Activity size={14}/> {forecast ? `Forecast period: ${forecast}` : "Forecast period —"}</span>
            </div>
          </section>

          {data && (forecast < new Date().getFullYear()) && (
            <div className="data-warning"><AlertTriangle size={18}/><div><strong>Historical dataset notice</strong><span>This dashboard is currently based on data through {basedOn} and displays a {forecast} forecast. It is a research prototype, not a current outbreak bulletin or operational public-health alert.</span></div></div>
          )}

          {error && <div className="error-banner"><WifiOff size={18}/><div><strong>Could not load dashboard data</strong><span>{error}. Check that the FastAPI server is running and that the API URL is correct.</span></div><button onClick={loadDashboard}>Try again</button></div>}

          <section className="metric-grid">
            <MetricCard label="Districts monitored" value={loading && !summary ? "—" : number(summary?.districts)} detail="Districts in the current dataset" icon={MapPinned} tone="blue"/>
            <MetricCard label="High risk" value={loading && !summary ? "—" : number(highCount)} detail="At or above the high threshold" icon={ShieldAlert} tone="red"/>
            <MetricCard label="Medium risk" value={loading && !summary ? "—" : number(mediumCount)} detail="Requires closer monitoring" icon={AlertTriangle} tone="amber"/>
            <MetricCard label="Low risk" value={loading && !summary ? "—" : number(lowCount)} detail="Below the medium threshold" icon={ShieldCheck} tone="green"/>
          </section>

          <section className="overview-grid">
            <article className="panel trend-panel">
              <SectionHeading eyebrow="HISTORICAL SURVEILLANCE" title="National cholera trend" action={<span className="chart-period">2008–2018 dataset</span>}/>
              {trendData.length ? <div className="trend-chart">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={trendData} margin={{ top: 10, right: 12, left: -12, bottom: 0 }}>
                    <CartesianGrid stroke="#edf1ef" vertical={false}/>
                    <XAxis dataKey="year" tickLine={false} axisLine={false} tick={{ fill: "#82908d", fontSize: 11 }}/>
                    <YAxis yAxisId="cases" tickLine={false} axisLine={false} tick={{ fill: "#82908d", fontSize: 11 }} />
                    <YAxis yAxisId="districts" orientation="right" hide/>
                    <Tooltip contentStyle={{ border: "1px solid #e7ece9", borderRadius: 12, boxShadow: "0 8px 24px #193a3012" }}/>
                    <Legend wrapperStyle={{ fontSize: 12, paddingTop: 10 }}/>
                    <Area yAxisId="cases" type="monotone" dataKey="cases" name="Reported cases" fill="#d9eee8" stroke="#279b83" strokeWidth={2.5}/>
                    <Line yAxisId="districts" type="monotone" dataKey="districts_affected" name="Districts with cases" stroke="#e4a34b" strokeWidth={2} dot={{ r: 3, fill: "#e4a34b" }}/>
                  </ComposedChart>
                </ResponsiveContainer>
              </div> : <EmptyState title="No trend data available" detail="The API has not returned national historical trends."/>}
            </article>

            <article className="panel distribution-panel">
              <SectionHeading eyebrow="MODEL OUTPUT" title="District risk distribution"/>
              <div className="distribution-content">
                {pieData.some((item) => item.value > 0) ? <>
                  <div className="donut-wrap">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart><Pie data={pieData} dataKey="value" nameKey="name" innerRadius={62} outerRadius={88} paddingAngle={3} stroke="none">{pieData.map((entry) => <Cell key={entry.name} fill={entry.fill}/>)}</Pie><Tooltip/></PieChart>
                    </ResponsiveContainer>
                    <div className="donut-center"><strong>{number(summary?.districts)}</strong><span>districts</span></div>
                  </div>
                  <div className="legend-list">{pieData.map((item) => <div key={item.name}><span><i style={{ background: item.fill }}/>{item.name}</span><strong>{item.value}</strong></div>)}</div>
                </> : <EmptyState title="Risk data unavailable" detail="No district risk categories were returned."/>}
              </div>
              <div className="distribution-foot"><span>Selected model</span><strong>{prettyModel(selectedModel || "Pending")}</strong></div>
            </article>
          </section>

          <section id="districts" className="panel district-panel page-section">
            <SectionHeading eyebrow="GEOGRAPHICAL RISK MONITORING" title="District risk assessment" action={<button className="text-button" onClick={exportRiskCsv} disabled={!data}><Download size={15}/> Export CSV</button>}/>
            <div className="table-toolbar">
              <div className="search-box"><Search size={16}/><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search district…"/></div>
              <div className="filter-box"><SlidersHorizontal size={15}/><select value={levelFilter} onChange={(e) => setLevelFilter(e.target.value)}><option value="all">All risk levels</option><option value="high">High risk</option><option value="medium">Medium risk</option><option value="low">Low risk</option></select><ChevronDown size={14}/></div>
            </div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>District</th><th>Risk score</th><th>Risk category</th><th>Latest recorded cases</th><th></th></tr></thead>
                <tbody>
                  {districtRows.map((row, index) => <tr key={row.district} onClick={() => setSelectedDistrict(row)} tabIndex={0} onKeyDown={(e) => e.key === "Enter" && setSelectedDistrict(row)}>
                    <td><span className="district-rank">{String(index + 1).padStart(2, "0")}</span><strong>{row.district}</strong></td>
                    <td><div className="score-cell"><span>{percent(row.risk)}</span><div className="score-track"><i style={{ width: `${Math.max(0, Math.min(100, row.risk * 100))}%`, background: RISK_COLORS[row.level] }}/></div></div></td>
                    <td><RiskPill level={row.level}/></td>
                    <td>{row.cases_latest == null ? "—" : number(row.cases_latest)}</td>
                    <td><button className="row-open" aria-label={`View ${row.district}`}><ChevronRight size={17}/></button></td>
                  </tr>)}
                  {!districtRows.length && <tr><td colSpan="5"><EmptyState title="No districts found" detail="Try another search or risk filter."/></td></tr>}
                </tbody>
              </table>
            </div>
            <div className="table-foot"><span>Showing {districtRows.length} of {data?.risk?.districts?.length || 0} districts</span><span>Select a district to view its history</span></div>
                        <DistrictRiskMap
              districts={data?.risk?.districts || []}
              onSelectDistrict={setSelectedDistrict}
            />
          </section>

          <section id="alerts" className="lower-grid page-section">
            <article className="panel alerts-panel">
              <SectionHeading eyebrow="ATTENTION REQUIRED" title="Early-warning list" action={<span className="count-tag">{data?.alerts?.count ?? "—"} alerts</span>}/>
              <p className="panel-description">Districts currently classified as medium or high risk by the selected model.</p>
              <div className="alert-list">
                {(data?.alerts?.alerts || []).slice(0, 8).map((alert) => <div className="alert-row" key={alert.district}>
                  <div className={`alert-symbol ${alert.level}`}><AlertTriangle size={17}/></div>
                  <div className="alert-copy"><strong>{alert.district}</strong><span>{number(alert.cases_latest)} latest recorded cases · risk score {percent(alert.risk)}</span></div>
                  <RiskPill level={alert.level}/>
                  <button className="row-open" onClick={() => setSelectedDistrict(alert)} aria-label={`Open ${alert.district}`}><ChevronRight size={17}/></button>
                </div>)}
                {data && !data.alerts?.alerts?.length && <EmptyState title="No elevated-risk districts" detail="No districts meet the current medium-risk alert threshold."/>}
                {!data && loading && <div className="loading-line">Loading alerts…</div>}
              </div>
            </article>

            <article id="model" className="panel model-panel page-section">
              <SectionHeading eyebrow="MACHINE-LEARNING PERFORMANCE" title="Model comparison"/>
              <div className="selected-model"><div className="selected-model-icon"><Gauge size={19}/></div><div><span>Selected for prediction</span><strong>{prettyModel(selectedModel || "Pending")}</strong></div><CheckCircle2 size={18}/></div>
              <div className="model-table-wrap">
                <table className="model-table">
                  <thead><tr><th>Model</th><th>PR-AUC</th><th>Recall</th><th>F1</th></tr></thead>
                  <tbody>{modelRows.map((row) => <tr key={row.name} className={row.name === selectedModel ? "chosen" : ""}><td>{prettyModel(row.name)}{row.name === selectedModel && <span className="chosen-label">SELECTED</span>}</td><td>{percent(row.pr_auc)}</td><td>{percent(row.recall)}</td><td>{percent(row.f1)}</td></tr>)}</tbody>
                </table>
              </div>
              <div className="model-note"><ShieldCheck size={15}/><span>Models are compared using historical rolling-period evaluation. Metrics describe this dataset and test period, not guaranteed future performance.</span></div>
              <div className="feature-heading"><strong>Top model features</strong><span>Relative importance / coefficient magnitude</span></div>
              <div className="feature-list">
                {Object.entries(data?.model?.feature_importance || {}).slice(0, 6).map(([name, value]) => <div className="feature-row" key={name}><span>{name.replaceAll("_", " ")}</span><div><i style={{ width: `${Math.max(3, (value / Math.max(...Object.values(data.model.feature_importance)) * 100))}%` }}/></div></div>)}
                {!data?.model?.feature_importance && <span className="muted">Feature information unavailable.</span>}
              </div>
            </article>
          </section>

          <footer className="page-footer">
            <div><HeartPulse size={16}/><span>ChoPreDic · Cholera Early-Warning System for Zambia</span></div>
            <span>{lastUpdated ? `Last refreshed ${lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : "Waiting for API data"}</span>
            <span>Decision-support prototype · Not a clinical diagnosis</span>
          </footer>
        </div>
      </main>
      {mobileNav && <button className="mobile-scrim" onClick={() => setMobileNav(false)} aria-label="Close navigation"/>}
      {selectedDistrict && <DistrictModal district={selectedDistrict} onClose={() => setSelectedDistrict(null)}/>}
    </div>
  );
}
