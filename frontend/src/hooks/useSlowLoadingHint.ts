import { useEffect, useState } from "react";

const HINT_DELAY_MS = 4000;

export function useSlowLoadingHint(loading: boolean): boolean {
  const [showHint, setShowHint] = useState(false);

  useEffect(() => {
    if (!loading) {
      setShowHint(false);
      return;
    }
    const id = setTimeout(() => setShowHint(true), HINT_DELAY_MS);
    return () => clearTimeout(id);
  }, [loading]);

  return showHint;
}
