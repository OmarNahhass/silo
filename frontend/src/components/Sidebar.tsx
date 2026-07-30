import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Overview", badge: "O" },
  { to: "/stock", label: "Stock", badge: "S" },
  { to: "/crypto", label: "Crypto", badge: "Cr" },
  { to: "/live", label: "Live", badge: "L" },
  { to: "/compare", label: "Compare", badge: "Co" },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">CryptoCast</div>
      <nav>
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === "/"}
            className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
          >
            <span className="nav-badge">{link.badge}</span>
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
