import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { BarChart3, ChevronDown, Coins, ArrowLeftRight, Activity } from "lucide-react";

const destinations = [
  { to: "/stock", label: "Stock Forecasts", Icon: BarChart3 },
  { to: "/crypto", label: "Crypto Forecasts", Icon: Coins },
  { to: "/compare", label: "Compare Two Tickers", Icon: ArrowLeftRight },
  { to: "/live", label: "Live Intraday", Icon: Activity },
];

export default function StartForecastingMenu({ openUpward = false }: { openUpward?: boolean }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }

    document.addEventListener("mousedown", handleClick);
    document.addEventListener("keydown", handleKey);
    return () => {
      document.removeEventListener("mousedown", handleClick);
      document.removeEventListener("keydown", handleKey);
    };
  }, [open]);

  return (
    <div className="start-forecasting-menu" ref={ref}>
      <button
        type="button"
        className="home-cta"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-haspopup="true"
      >
        Start forecasting
        <ChevronDown
          size={16}
          strokeWidth={2.5}
          className={"start-forecasting-chevron" + (open ? " open" : "") + (openUpward ? " flipped" : "")}
        />
      </button>
      {open && (
        <div className={"start-forecasting-dropdown" + (openUpward ? " open-upward" : "")} role="menu">
          {destinations.map(({ to, label, Icon }) => (
            <Link key={to} to={to} className="start-forecasting-option" role="menuitem" onClick={() => setOpen(false)}>
              <Icon size={16} strokeWidth={2} />
              {label}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
