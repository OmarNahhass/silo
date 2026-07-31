import Select, { type StylesConfig } from "react-select";
import Creatable from "react-select/creatable";

interface Option {
  value: string;
  label: string;
}

// Matches the CSS custom properties in index.css -- react-select renders its own
// popup outside the normal DOM flow, so plain CSS classes can't reach it; it has to
// be styled through this `styles` override API instead.
const darkStyles: StylesConfig<Option, false> = {
  control: (base, state) => ({
    ...base,
    backgroundColor: "#1a1a1a",
    borderColor: state.isFocused ? "#f97316" : "rgba(255,255,255,0.08)",
    boxShadow: "none",
    "&:hover": { borderColor: "#f97316" },
  }),
  menu: (base) => ({
    ...base,
    backgroundColor: "#262626",
    border: "1px solid rgba(255,255,255,0.08)",
    zIndex: 20,
  }),
  option: (base, state) => ({
    ...base,
    backgroundColor: state.isSelected ? "#f97316" : state.isFocused ? "#333333" : "#262626",
    color: state.isSelected ? "#1a1a1a" : "#e5e5e5",
    cursor: "pointer",
  }),
  singleValue: (base) => ({ ...base, color: "#e5e5e5" }),
  input: (base) => ({ ...base, color: "#e5e5e5" }),
  placeholder: (base) => ({ ...base, color: "#9ca3af" }),
  indicatorSeparator: (base) => ({ ...base, backgroundColor: "rgba(255,255,255,0.08)" }),
};

export default function SearchableSelect({
  options,
  value,
  onChange,
  placeholder,
  allowCreate = false,
}: {
  options: Option[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  // Lets the user type a value that isn't in `options` and use it anyway -- for
  // tickers, where the curated list is just a shortcut, not the full set of what's
  // actually searchable against the API. Never set this for fixed-choice dropdowns
  // (e.g. the model picker), where every valid value is already in `options`.
  allowCreate?: boolean;
}) {
  const selected = options.find((o) => o.value === value) ?? (allowCreate && value ? { value, label: value } : null);
  const Component = allowCreate ? Creatable : Select;

  return (
    <Component
      options={options}
      value={selected}
      onChange={(opt) => opt && onChange(opt.value)}
      placeholder={placeholder ?? "Search..."}
      styles={darkStyles}
      isSearchable
      formatCreateLabel={allowCreate ? (input: string) => `Use "${input.toUpperCase()}"` : undefined}
    />
  );
}

export type { Option };
