import { useEffect, useState } from "react";
import { getModels } from "../api";
import type { ModelMeta } from "../types";
import MathFormula from "../components/Math";
import StartForecastingMenu from "../components/StartForecastingMenu";

const CENTER = 240;
const RADIUS = 175;
const HUB = { w: 120, h: 50 };
const NODE = { w: 100, h: 36 };

const MODEL_NODES = [
  { key: "lr", label: "Linear" },
  { key: "arima", label: "ARIMA" },
  { key: "sarima", label: "SARIMA" },
  { key: "ets", label: "ETS" },
  { key: "prophet", label: "Prophet" },
  { key: "poly", label: "Poly Reg" },
  { key: "knn", label: "KNN" },
  { key: "rf", label: "R. Forest" },
  { key: "gbm", label: "XGBoost" },
  { key: "svr", label: "SVR" },
];

const outerNodes = MODEL_NODES.map((node, i) => {
  const angle = ((-90 + i * (360 / MODEL_NODES.length)) * Math.PI) / 180;
  return {
    ...node,
    cx: CENTER + RADIUS * Math.cos(angle),
    cy: CENTER + RADIUS * Math.sin(angle),
  };
});

function scrollToModel(key: string) {
  document.getElementById(`model-${key}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
}

export default function HomePage() {
  const [models, setModels] = useState<ModelMeta[]>([]);

  useEffect(() => {
    getModels().then(setModels);
  }, []);

  const statistical = models.filter((m) => m.category === "Statistical");
  const machineLearning = models.filter((m) => m.category === "Machine Learning");
  const ensemble = models.find((m) => m.category === "Ensemble");

  return (
    <div className="home-hero">
      <div className="home-hero-text">
        <h1 className="home-headline">
          Uncovering the
          <span className="home-headline-big">
            Unknown<span className="home-accent-dot" />
          </span>
        </h1>
        <p className="home-sub">Utilizing data to predict future closing prices</p>
        <StartForecastingMenu />
      </div>
      <div className="home-hero-visual">
        <svg
          viewBox="0 0 480 480"
          className="roadmap-tree"
          role="img"
          aria-label="Ten forecasting models -- statistical and machine learning -- each feed into a central weighted ensemble. Select a model to jump to its formula."
        >
          {outerNodes.map((n) => (
            <line key={`line-${n.key}`} x1={CENTER} y1={CENTER} x2={n.cx} y2={n.cy} stroke="var(--border)" strokeWidth={2} />
          ))}
          <g
            className="roadmap-node"
            role="button"
            tabIndex={0}
            aria-label="Jump to Ensemble (Weighted Average) formula"
            onClick={() => scrollToModel("ensemble")}
            onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && scrollToModel("ensemble")}
          >
            <rect x={CENTER - HUB.w / 2} y={CENTER - HUB.h / 2} width={HUB.w} height={HUB.h} rx={14} fill="var(--accent)" />
            <text x={CENTER} y={CENTER + 5} textAnchor="middle" fill="white" fontSize={15} fontWeight={800}>
              Ensemble
            </text>
          </g>
          {outerNodes.map((n) => (
            <g
              key={n.key}
              className="roadmap-node"
              role="button"
              tabIndex={0}
              aria-label={`Jump to ${n.label} formula`}
              onClick={() => scrollToModel(n.key)}
              onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && scrollToModel(n.key)}
            >
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
          Silo runs 10 different forecasting models -- statistical and machine learning
          -- plus a weighted ensemble that combines them, on real stock and cryptocurrency
          price history to predict the next trading day's closing price. It tracks live
          intraday predictions against what actually happens, and lets you compare two
          tickers side by side, with the math and methodology shown alongside every
          prediction.
        </p>
      </div>

      {models.length > 0 && (
        <div className="model-showcase">
          <h2 className="model-showcase-title">10 Models, One Ensemble</h2>
          <div className="model-showcase-columns">
            <div className="model-column">
              <h3 className="model-column-title">Statistical</h3>
              {statistical.map((m) => (
                <div key={m.key} id={`model-${m.key}`} className="model-card">
                  <div className="model-card-name">{m.name}</div>
                  <MathFormula tex={m.math} />
                  <p className="model-card-note">{m.note}</p>
                </div>
              ))}
            </div>
            <div className="model-column">
              <h3 className="model-column-title">Machine Learning</h3>
              {machineLearning.map((m) => (
                <div key={m.key} id={`model-${m.key}`} className="model-card">
                  <div className="model-card-name">{m.name}</div>
                  <MathFormula tex={m.math} />
                  <p className="model-card-note">{m.note}</p>
                </div>
              ))}
            </div>
          </div>
          {ensemble && (
            <div id={`model-${ensemble.key}`} className="model-card model-card-ensemble">
              <div className="model-card-name">{ensemble.name}</div>
              <MathFormula tex={ensemble.math} />
              <p className="model-card-note">{ensemble.note}</p>
            </div>
          )}
          <div className="home-cta-bottom">
            <StartForecastingMenu openUpward />
          </div>
        </div>
      )}
    </div>
  );
}
