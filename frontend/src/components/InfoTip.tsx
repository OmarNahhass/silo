// A small "?" badge that reveals a plain-language explanation on hover/focus, so
// technical terms (RMSE, holdout, etc.) can stay visible for anyone who wants them
// without forcing beginners to already know what they mean.
export default function InfoTip({
  text,
  openDownward = false,
}: {
  text: string;
  // Table headers sit inside a horizontally-scrollable .table-wrap -- CSS forces
  // overflow-y to also become "auto" whenever overflow-x isn't "visible" (they can't
  // be mismatched), so a bubble popping *upward* from a header row gets silently
  // clipped by the container's own top edge. Opening downward instead keeps it
  // within the table's existing height (it just overlaps the row below, same as any
  // normal tooltip), so it never needs to escape the container at all.
  openDownward?: boolean;
}) {
  return (
    <span className={"info-tip" + (openDownward ? " info-tip-below" : "")} tabIndex={0}>
      <span className="info-tip-icon">?</span>
      <span className="info-tip-bubble">{text}</span>
    </span>
  );
}
