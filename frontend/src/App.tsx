import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ForecastProvider } from "./context/ForecastContext";
import Sidebar from "./components/Sidebar";
import Overview from "./pages/Overview";
import AssetPage from "./pages/AssetPage";
import LivePage from "./pages/LivePage";

export default function App() {
  return (
    <ForecastProvider>
      <BrowserRouter>
        <div className="app-shell">
          <Sidebar />
          <main className="content">
            <Routes>
              <Route path="/" element={<Overview />} />
              <Route path="/stock" element={<AssetPage key="stock" assetType="Stock" />} />
              <Route path="/crypto" element={<AssetPage key="crypto" assetType="Crypto" />} />
              <Route path="/live" element={<LivePage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </ForecastProvider>
  );
}
