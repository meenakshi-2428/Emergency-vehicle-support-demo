import { socket } from "../lib/socket";

/**
 * Step 6: "Display AI Decision Card & Delay Reason".
 * The operator reads Gemini's explanation and clicks Approve Reroute or
 * Override - which fires step 7 (driver PWA route update) and step 8
 * (civilian geofenced yield warning) on the backend.
 */
export default function DecisionCard({ card, currentPosition, onResolved }) {
  if (!card) return null;

  const decide = (decision) => {
    socket.emit("operator_decision", {
      vehicle_id: card.vehicle_id,
      deviation_log_id: card.deviation_log_id,
      decision,
      detour_geometry: card.detour_geometry,
      lat: currentPosition?.lat,
      lon: currentPosition?.lon,
    });
    onResolved();
  };

  return (
    <div style={{
      position: "absolute", top: 16, right: 16, width: 320,
      background: "#1f1a5e", border: "2px solid #c62828", borderRadius: 10,
      padding: 16, boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
    }}>
      <div style={{ fontSize: 12, letterSpacing: 1, color: "#f2b8b8", marginBottom: 6 }}>
        DEVIATION DETECTED · {card.distance_m.toFixed(0)} m off route
      </div>
      <p style={{ margin: "0 0 12px", lineHeight: 1.4 }}>{card.explanation}</p>
      <div style={{ fontSize: 13, color: "#b9b6f0", marginBottom: 12 }}>
        Suggested detour: +{card.detour_minutes} min
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <button onClick={() => decide("APPROVED")} style={btnStyle("#1e8e5a")}>
          Approve Reroute
        </button>
        <button onClick={() => decide("OVERRIDDEN")} style={btnStyle("#5a5a6e")}>
          Override
        </button>
      </div>
    </div>
  );
}

function btnStyle(bg) {
  return {
    flex: 1, padding: "10px 12px", background: bg, color: "white",
    border: "none", borderRadius: 6, cursor: "pointer", fontWeight: 600,
  };
}
