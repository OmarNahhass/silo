import katex from "katex";
import "katex/dist/katex.min.css";
import { useMemo } from "react";

export default function Math({ tex }: { tex: string }) {
  const html = useMemo(() => {
    try {
      return katex.renderToString(tex, { throwOnError: false, displayMode: true });
    } catch (e) {
      return `<span style="color:#ef4444">LaTeX error: ${String(e)}</span>`;
    }
  }, [tex]);

  // eslint-disable-next-line react/no-danger
  return <div className="math-wrap" dangerouslySetInnerHTML={{ __html: html }} />;
}
