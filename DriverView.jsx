import { useEffect, useState } from "react";
import { socket } from "../lib/socket";

/**
 * Mobile Driver PWA (Ambulance Driver).
 * Step 2: "Sync Navigation Route" keeps the live position in sync.
 * Step 7: "View Path & Audio Guidance" - shows the approved detour and
 * speaks the turn instruction with the Web Speech API (no extra library
 * needed, works in any modern mobile browser).
 */
export default function DriverView() {
  const [position, setPosition] = useState(null);
  const [instruction, setInstruction] = useState(null);

  useEffect(() => {
    socket.emit("register_driver", {});
    socket.on("position_update", (data) => setPosition(data));
    socket.on("route_update", (data) => {
      setInstruction(data.instruction);
      speak(data.instruction);
    });
    return () => {
      socket.off("position_update");
      socket.off("route_update");
    };
  }, []);

  const speak = (text) => {
    if (!("speechSynthesis" in window)) return;
    const utter = new SpeechSynthesisUtterance(text);
    window.speechSynthesis.speak(utter);
  };

  return (
    <div style={{ padding: 20, height: "100vh", boxSizing: "border-box" }}>
      <h2 style={{ marginTop: 0 }}>GeoAgentic — Driver</h2>
      <div style={{ fontSize: 13, color: "#8886b8", marginBottom: 20 }}>
        Turn-by-turn voice guidance
      </div>

      {position && (
        <div style={{ background: "#151230", borderRadius: 10, padding: 16, marginBottom: 16 }}>
          <div style={{ fontSize: 12, color: "#8886b8" }}>CURRENT POSITION</div>
          <div>{position.lat.toFixed(5)}, {position.lon.toFixed(5)}</div>
          <div style={{ fontSize: 12, color: "#8886b8", marginTop: 8 }}>
            {position.distance_m?.toFixed(0)} m from planned route
          </div>
        </div>
      )}

      <div style={{
        background: instruction ? "#1e8e5a" : "#151230", borderRadius: 10,
        padding: 20, textAlign: "center", fontSize: 18, fontWeight: 600,
      }}>
        {instruction || "On planned route. Waiting for updates..."}
      </div>
    </div>
  );
}
