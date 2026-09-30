import { useEffect, useState } from "react";
import { socket } from "../lib/socket";

/**
 * Civilian Driver's phone.
 * Sends its own location every few seconds (so the backend's Proximity
 * Alert Engine / ST_DWithin query can find it), and shows the geofenced
 * yield warning (step 8) the moment it arrives:
 *   "⚠️ Emergency Vehicle Approaching! Yield Right Lane."
 */
export default function CivilianView() {
  const [warning, setWarning] = useState(null);
  const [sharing, setSharing] = useState(false);

  useEffect(() => {
    socket.on("yield_warning", (data) => {
      setWarning(data.message);
      if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
      setTimeout(() => setWarning(null), 8000);
    });
    return () => socket.off("yield_warning");
  }, []);

  const startSharing = () => {
    if (!("geolocation" in navigator)) return;
    setSharing(true);
    navigator.geolocation.watchPosition(
      (pos) => {
        socket.emit("register_civilian", {
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
        });
      },
      (err) => console.error(err),
      { enableHighAccuracy: true, maximumAge: 5000 }
    );
  };

  return (
    <div style={{ padding: 20, height: "100vh", boxSizing: "border-box", position: "relative" }}>
      <h2 style={{ marginTop: 0 }}>GeoAgentic — Civilian Driver</h2>
      <p style={{ color: "#8886b8", fontSize: 14 }}>
        Share your location so nearby ambulances can reach you with a yield
        warning if one approaches within 500 m.
      </p>

      {!sharing ? (
        <button onClick={startSharing} style={{
          padding: "12px 20px", background: "#1e8e5a", color: "white",
          border: "none", borderRadius: 8, fontWeight: 600, cursor: "pointer",
        }}>
          Share My Location
        </button>
      ) : (
        <div style={{ color: "#1e8e5a" }}>● Sharing location</div>
      )}

      {warning && (
        <div style={{
          position: "fixed", top: 0, left: 0, right: 0, padding: 20,
          background: "#c62828", color: "white", fontSize: 18, fontWeight: 700,
          textAlign: "center",
        }}>
          {warning}
        </div>
      )}
    </div>
  );
}
