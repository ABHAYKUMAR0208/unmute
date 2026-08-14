import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Walkthrough from "./pages/Walkthrough";
import Solutions from "./pages/Solutions";
import Console from "./pages/Console";
import Features from "./pages/Features";
import About from "./pages/About";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/walkthrough" element={<Walkthrough />} />
      <Route path="/features" element={<Features />} />
      <Route path="/solutions" element={<Solutions />} />
      <Route path="/about" element={<About />} />
      <Route path="/console" element={<Console />} />
    </Routes>
  );
}
