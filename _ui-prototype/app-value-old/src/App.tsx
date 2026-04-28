import { HashRouter, Routes, Route } from "react-router-dom";
import Layout from "./sections/Layout";
import DiscoveryHub from "./sections/DiscoveryHub";
import DriverTree from "./sections/DriverTree";
import HypothesisCanvas from "./sections/HypothesisCanvas";
import EvidenceLibrary from "./sections/EvidenceLibrary";
import ValueCalculator from "./sections/ValueCalculator";
import ValueCaseBuilder from "./sections/ValueCaseBuilder";

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DiscoveryHub />} />
          <Route path="driver-tree" element={<DriverTree />} />
          <Route path="hypotheses" element={<HypothesisCanvas />} />
          <Route path="evidence" element={<EvidenceLibrary />} />
          <Route path="calculator" element={<ValueCalculator />} />
          <Route path="value-case" element={<ValueCaseBuilder />} />
        </Route>
      </Routes>
    </HashRouter>
  );
}
