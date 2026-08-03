import Select, { type StylesConfig } from "react-select";
import Creatable from "react-select/creatable";

interface Option {
  value: string;
  label: string;
}

const darkStyles: StylesConfig<Option, false> = {
  control: (base, state) => ({
    ...base,
    backgroundColor: "#0a0a0b",
    borderColor: state.isFocused ? "#6366f1" : "rgba(255,255,255,0.08)",
    boxShadow: "none",
    "&:hover": { borderColor: "#6366f1" },
  }),
  menu: (base) => ({
    ...base,
    backgroundColor: "#18181b",
    border: "1px solid rgba(255,255,255,0.08)",
    zIndex: 20,
  }),
  option: (base, state) => ({
    ...base,
    backgroundColor: state.isSelected ? "#6366f1" : state.isFocused ? "#27272a" : "#18181b",
    color: state.isSelected ? "#f4f4f5" : "#e5e5e5",
    cursor: "pointer",
  }),
  valueContainer: (base) => ({ ...base, justifyContent: "center" }),
  singleValue: (base) => ({ ...base, color: "#f4f4f5" }),
  input: (base) => ({ ...base, color: "#f4f4f5" }),
  placeholder: (base) => ({ ...base, color: "#9ca3af" }),
  indicatorSeparator: (base) => ({ ...base, backgroundColor: "rgba(255,255,255,0.08)" }),
};

export default function SearchableSelect({
  options,
  value,
  onChange,
  placeholder,
  allowCreate = false,
  ariaLabel,
}: {
  options: Option[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  allowCreate?: boolean;
  ariaLabel?: string;
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
      aria-label={ariaLabel}
      formatCreateLabel={allowCreate ? (input: string) => `Use "${input.toUpperCase()}"` : undefined}
    />
  );
}

export type { Option };
