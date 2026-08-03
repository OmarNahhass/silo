import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ForecastProvider } from "./context/ForecastContext";
import Navbar from "./components/Navbar";
import DisclaimerModal from "./components/DisclaimerModal";
import HomePage from "./pages/HomePage";
import AssetPage from "./pages/AssetPage";
import LivePage from "./pages/LivePage";
import ComparePage from "./pages/ComparePage";

export default function App() {
  return (
    <ForecastProvider>
      <BrowserRouter>
        <DisclaimerModal />
        <div className="app-shell">
          <Navbar />
          <main className="content">
            <Routes>
              <Route path="/" element={<HomePage />} />
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
