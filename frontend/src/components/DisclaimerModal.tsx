import { useState } from "react";

export default function DisclaimerModal() {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-card" role="dialog" aria-modal="true" aria-labelledby="disclaimer-title">
        <h2 id="disclaimer-title">Welcome to CryptoCast</h2>
        <p>
          <strong>This is not financial advice.</strong> CryptoCast is an educational project for
          exploring forecasting techniques -- statistical models, machine learning models, and an
          ensemble that combines them. Nothing shown here is a recommendation to buy, sell, or
          hold anything, and its predictions should not be used to make real investment or trading
          decisions. Markets are unpredictable, and a model's past accuracy is no guarantee of
          future results.
        </p>
        <p>
          What the site actually does: it runs 10 different forecasting models (plus a weighted
          ensemble) on real stock and cryptocurrency price history to predict the next trading
          day's closing price, tracks live intraday predictions against what actually happens, and
          lets you compare two tickers side by side -- with the math and methodology shown
          alongside every prediction.
        </p>
        <button className="run-button" onClick={() => setDismissed(true)}>
          I Understand — Continue
        </button>
      </div>
    </div>
  );
}
