import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Walkthrough from "./pages/Walkthrough";
import Solutions from "./pages/Solutions";
import Console from "./pages/Console";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/walkthrough" element={<Walkthrough />} />
      <Route path="/solutions" element={<Solutions />} />
      <Route path="/console" element={<Console />} />
    </Routes>
  );
}
