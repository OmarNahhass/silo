import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Overview" },
  { to: "/stock", label: "Stock" },
  { to: "/crypto", label: "Crypto" },
  { to: "/live", label: "Live" },
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
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
