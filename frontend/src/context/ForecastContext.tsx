import { createContext, useContext, useState, type ReactNode } from "react";
import type { ForecastResponse } from "../types";

interface ForecastContextValue {
  forecast: ForecastResponse | null;
  setForecast: (forecast: ForecastResponse) => void;
}

const ForecastContext = createContext<ForecastContextValue | undefined>(undefined);

export function ForecastProvider({ children }: { children: ReactNode }) {
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  return (
    <ForecastContext.Provider value={{ forecast, setForecast }}>
      {children}
    </ForecastContext.Provider>
  );
}

export function useForecast() {
  const ctx = useContext(ForecastContext);
  if (!ctx) throw new Error("useForecast must be used within a ForecastProvider");
  return ctx;
}
