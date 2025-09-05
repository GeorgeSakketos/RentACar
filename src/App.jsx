import { BrowserRouter as Router, Routes, Route, Link, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import { CSSTransition, TransitionGroup } from "react-transition-group";
import Home from "./pages/Home";
import Cars from "./pages/Cars";
import About from "./pages/About";
import Contact from "./pages/Contact";
import Loading from "./components/Loading";
import "./styles.css";

function AnimatedRoutes() {
  const location = useLocation();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    const timer = setTimeout(() => setLoading(false), 400);
    return () => clearTimeout(timer);
  }, [location]);

  return (
    <>
      {loading && <Loading />}
      <TransitionGroup>
        <CSSTransition key={location.pathname} classNames="page" timeout={500}>
          <Routes location={location}>
            <Route path="/" element={<Home />} />
            <Route path="/cars" element={<Cars />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
          </Routes>
        </CSSTransition>
      </TransitionGroup>
    </>
  );
}

export default function App() {
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem("darkMode") === "true";
  });

  useEffect(() => {
    if (darkMode) {
      document.body.classList.add("dark");
      localStorage.setItem("darkMode", "true");
    } else {
      document.body.classList.remove("dark");
      localStorage.setItem("darkMode", "false");
    }
  }, [darkMode]);

  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <h1 className="logo">DreamRide</h1>
          <div className="nav-links">
            <Link to="/">Home</Link>
            <Link to="/cars">Cars</Link>
            <Link to="/about">About</Link>
            <Link to="/contact">Contact</Link>
            <button className="dark-toggle" onClick={() => setDarkMode(!darkMode)}>
              {darkMode ? "☀️" : "🌙"}
            </button>
          </div>
        </nav>
        <AnimatedRoutes />
      </div>
    </Router>
  );
}