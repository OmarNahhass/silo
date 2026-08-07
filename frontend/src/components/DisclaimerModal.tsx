import { useState } from "react";

export default function DisclaimerModal() {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-card" role="dialog" aria-modal="true" aria-labelledby="disclaimer-title">
        <h2 id="disclaimer-title">Not financial advice</h2>
        <p>
    Silo is a tool that showcases my knowledge in statistics. As such, it is not a tool meant literally. Do not use it to make financial decisions.
        </p>
        <button className="run-button" onClick={() => setDismissed(true)}>
          I Understand — Continue
        </button>
      </div>
    </div>
  );
}
