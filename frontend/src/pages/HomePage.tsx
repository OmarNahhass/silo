import { Link } from "react-router-dom";

const CENTER = 240;
const RADIUS = 175;
const HUB = { w: 120, h: 50 };
const NODE = { w: 100, h: 36 };

const models = ["Linear", "ARIMA", "SARIMA", "ETS", "Prophet", "Poly Reg", "KNN", "R. Forest", "XGBoost", "SVR"];

const outerNodes = models.map((label, i) => {
  const angle = ((-90 + i * (360 / models.length)) * Math.PI) / 180;
  return {
    label,
    cx: CENTER + RADIUS * Math.cos(angle),
    cy: CENTER + RADIUS * Math.sin(angle),
  };
});

export default function HomePage() {
  return (
    <div className="home-hero">
      <div className="home-hero-text">
        <h1 className="home-headline">
          Uncovering the
          <span className="home-headline-big">
            Unknown<span className="home-accent-dot" />
          </span>
        </h1>
        <p className="home-sub">Utilizing data to predict future closing prices.</p>
        <Link to="/stock" className="home-cta">
          Start forecasting
        </Link>
      </div>
      <div className="home-hero-visual">
        <svg
          viewBox="0 0 480 480"
          className="roadmap-tree"
          role="img"
          aria-label="Ten forecasting models -- statistical and machine learning -- each feed into a central weighted ensemble"
        >
          {outerNodes.map((n) => (
            <line key={`line-${n.label}`} x1={CENTER} y1={CENTER} x2={n.cx} y2={n.cy} stroke="var(--border)" strokeWidth={2} />
          ))}
          <g className="roadmap-node">
            <rect x={CENTER - HUB.w / 2} y={CENTER - HUB.h / 2} width={HUB.w} height={HUB.h} rx={14} fill="var(--accent)" />
            <text x={CENTER} y={CENTER + 5} textAnchor="middle" fill="white" fontSize={15} fontWeight={800}>
              Ensemble
            </text>
          </g>
          {outerNodes.map((n) => (
            <g key={n.label} className="roadmap-node">
              <rect
                x={n.cx - NODE.w / 2}
                y={n.cy - NODE.h / 2}
                width={NODE.w}
                height={NODE.h}
                rx={9}
                fill="var(--surface)"
                stroke="var(--accent)"
                strokeWidth={1.5}
              />
              <text x={n.cx} y={n.cy + 4} textAnchor="middle" fill="var(--text)" fontSize={12} fontWeight={700}>
                {n.label}
              </text>
            </g>
          ))}
        </svg>
      </div>
      <div className="home-description">
        <p>
          CryptoCast runs 10 different forecasting models -- statistical and machine learning
          -- plus a weighted ensemble that combines them, on real stock and cryptocurrency
          price history to predict the next trading day's closing price. It tracks live
          intraday predictions against what actually happens, and lets you compare two
          tickers side by side, with the math and methodology shown alongside every
          prediction.
        </p>
      </div>
    </div>
  );
}
