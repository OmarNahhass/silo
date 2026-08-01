import katex from "katex";
import "katex/dist/katex.min.css";
import { useMemo } from "react";

// Renders LaTeX directly via the katex package rather than through react-katex, which
// bundles its own (older) katex version internally -- that caused a real bug here: the
// CSS (from our top-level katex) didn't match the DOM react-katex's bundled, older katex
// actually produced, so equations rendered as broken, unstyled, mis-tokenized text.
export default function Math({ tex }: { tex: string }) {
  const html = useMemo(() => {
    try {
      return katex.renderToString(tex, { throwOnError: false, displayMode: true });
    } catch (e) {
      return `<span style="color:#ef4444">LaTeX error: ${String(e)}</span>`;
    }
  }, [tex]);

  // KaTeX doesn't reflow -- a wide formula (e.g. the ensemble's summation-with-fraction)
  // renders at its natural width regardless of container size, which can be wider than
  // an entire phone screen. Scope horizontal scrolling to just the formula rather than
  // letting it push the whole page wider.
  // eslint-disable-next-line react/no-danger
  return <div className="math-wrap" dangerouslySetInnerHTML={{ __html: html }} />;
}
