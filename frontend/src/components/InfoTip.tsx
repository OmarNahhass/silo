// A small "?" badge that reveals a plain-language explanation on hover/focus, so
// technical terms (RMSE, holdout, etc.) can stay visible for anyone who wants them
// without forcing beginners to already know what they mean.
export default function InfoTip({ text }: { text: string }) {
  return (
    <span className="info-tip" tabIndex={0}>
      <span className="info-tip-icon">?</span>
      <span className="info-tip-bubble">{text}</span>
    </span>
  );
}
