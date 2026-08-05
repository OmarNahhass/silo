import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ForecastProvider } from "./context/ForecastContext";
import Navbar from "./components/Navbar";
import DisclaimerModal from "./components/DisclaimerModal";
import HomePage from "./pages/HomePage";
import AssetPage from "./pages/AssetPage";
import LivePage from "./pages/LivePage";
import ComparePage from "./pages/ComparePage";
import TrackRecordPage from "./pages/TrackRecordPage";
import ScrollToTopButton from "./components/ScrollToTopButton";

export default function App() {
  return (
    <ForecastProvider>
      <BrowserRouter>
        <DisclaimerModal />
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>
        <div className="app-shell">
          <Navbar />
          <main className="content" id="main-content" tabIndex={-1}>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/stock" element={<AssetPage key="stock" assetType="Stock" />} />
              <Route path="/crypto" element={<AssetPage key="crypto" assetType="Crypto" />} />
              <Route path="/live" element={<LivePage />} />
              <Route path="/compare" element={<ComparePage />} />
              <Route path="/track-record" element={<TrackRecordPage />} />
            </Routes>
          </main>
          <footer className="app-footer">© {new Date().getFullYear()} Omar Nahhas</footer>
        </div>
        <ScrollToTopButton />
      </BrowserRouter>
    </ForecastProvider>
  );
}
