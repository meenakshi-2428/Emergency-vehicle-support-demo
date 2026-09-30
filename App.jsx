import { useEffect, useState } from "react";
import { socket } from "./lib/socket";
import MapView from "./components/MapView";
import DecisionCard from "./components/DecisionCard";

export default function App() {
  const [position, setPosition] = useState(null);
  const [card, setCard] = useState(null);
  const [alertLog, setAlertLog] = useState([]);

  useEffect(() => {
    socket.on("position_update", (data) => setPosition(data));
    socket.on("decision_card", (data) => {
      setCard(data);
      setAlertLog((prev) => [data, ...prev].slice(0, 10));
    });
    return () => {
      socket.off("position_update");
      socket.off("decision_card");
    };
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <header style={{ padding: "12px 20px", background: "#151230", borderBottom: "1px solid #2d2a5e" }}>
        <strong>GeoAgentic</strong> — Laptop Admin Dashboard (Control Room Operator)
        {position && (
          <span style={{ float: "right", color: "#b9b6f0" }}>
            {position.call_sign} · {position.distance_m?.toFixed(0)} m from route
          </span>
        )}
      </header>

      <div style={{ position: "relative", flex: 1 }}>
        <MapView position={position} detourGeometry={card?.detour_geometry} />
        <DecisionCard card={card} currentPosition={position} onResolved={() => setCard(null)} />
      </div>

      <footer style={{ padding: "10px 20px", background: "#151230", borderTop: "1px solid #2d2a5e", maxHeight: 140, overflowY: "auto" }}>
        <div style={{ fontSize: 12, letterSpacing: 1, color: "#8886b8", marginBottom: 6 }}>
          ALERT CENTER
        </div>
        {alertLog.length === 0 && <div style={{ color: "#5a5a6e" }}>No deviations yet.</div>}
        {alertLog.map((a, i) => (
          <div key={i} style={{ fontSize: 13, marginBottom: 4 }}>
            {a.call_sign}: {a.explanation}
          </div>
        ))}
      </footer>
    </div>
  );
}
