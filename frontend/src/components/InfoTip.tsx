export default function InfoTip({
  text,
  openDownward = false,
}: {
  text: string;
  openDownward?: boolean;
}) {
  return (
    <span className={"info-tip" + (openDownward ? " info-tip-below" : "")} tabIndex={0}>
      <span className="info-tip-icon">?</span>
      <span className="info-tip-bubble">{text}</span>
    </span>
  );
}
