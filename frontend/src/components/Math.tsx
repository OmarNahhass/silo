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

  // eslint-disable-next-line react/no-danger
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}
