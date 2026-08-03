import { useState } from "react";

export default function DisclaimerModal() {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-card" role="dialog" aria-modal="true" aria-labelledby="disclaimer-title">
        <h2 id="disclaimer-title">Not financial advice</h2>
        <p>
          CryptoCast is an educational project for exploring forecasting techniques --
          statistical models, machine learning models, and an ensemble that combines them.
          Nothing shown here is a recommendation to buy, sell, or hold anything, and its
          predictions should not be used to make real investment or trading decisions.
          Markets are unpredictable, and a model's past accuracy is no guarantee of future
          results.
        </p>
        <button className="run-button" onClick={() => setDismissed(true)}>
          I Understand — Continue
        </button>
      </div>
    </div>
  );
}
