import Select, { type StylesConfig } from "react-select";

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
}: {
  options: Option[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  const selected = options.find((o) => o.value === value) ?? null;

  return (
    <Select
      options={options}
      value={selected}
      onChange={(opt) => opt && onChange(opt.value)}
      placeholder={placeholder ?? "Search..."}
      styles={darkStyles}
      isSearchable
    />
  );
}

export type { Option };
