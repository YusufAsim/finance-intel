import { BrowserRouter, Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import Anomalies from "./pages/Anomalies";
import Dashboard from "./pages/Dashboard";
import Forecast from "./pages/Forecast";
import Subscriptions from "./pages/Subscriptions";
import Transactions from "./pages/Transactions";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="transactions" element={<Transactions />} />
          <Route path="subscriptions" element={<Subscriptions />} />
          <Route path="anomalies" element={<Anomalies />} />
          <Route path="forecast" element={<Forecast />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
