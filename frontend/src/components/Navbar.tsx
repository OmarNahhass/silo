import { Link, NavLink } from "react-router-dom";
import { TrendingUp, BarChart3, Coins, Activity, ArrowLeftRight, History } from "lucide-react";

const links = [
  { to: "/stock", label: "Stock", Icon: BarChart3 },
  { to: "/crypto", label: "Crypto", Icon: Coins },
  { to: "/compare", label: "Compare", Icon: ArrowLeftRight },
  { to: "/live", label: "Live", Icon: Activity },
  { to: "/track-record", label: "Track Record", Icon: History },
];

export default function Navbar() {
  return (
    <header className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="brand">
          <TrendingUp size={20} strokeWidth={2.5} />
          CryptoCast
        </Link>
        <nav className="navbar-nav">
          {links.map(({ to, label, Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
            >
              <Icon size={16} strokeWidth={2} />
              {label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
