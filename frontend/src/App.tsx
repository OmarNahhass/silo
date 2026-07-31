import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ForecastProvider } from "./context/ForecastContext";
import Sidebar from "./components/Sidebar";
import AssetPage from "./pages/AssetPage";
import LivePage from "./pages/LivePage";
import ComparePage from "./pages/ComparePage";

export default function App() {
  return (
    <ForecastProvider>
      <BrowserRouter>
        <div className="app-shell">
          <Sidebar />
          <main className="content">
            <Routes>
              <Route path="/" element={<Navigate to="/stock" replace />} />
              <Route path="/stock" element={<AssetPage key="stock" assetType="Stock" />} />
              <Route path="/crypto" element={<AssetPage key="crypto" assetType="Crypto" />} />
              <Route path="/live" element={<LivePage />} />
              <Route path="/compare" element={<ComparePage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </ForecastProvider>
  );
}
