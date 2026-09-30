import DriverView from "./pages/DriverView";
import CivilianView from "./pages/CivilianView";

/**
 * One small React app serving both phones in the flowchart's Client Layer:
 *   ?role=driver   -> Mobile Driver PWA   (Ambulance Driver)
 *   ?role=civilian -> the Civilian Driver's yield-warning listener
 * In production you'd likely ship these as two separate PWAs; keeping them
 * in one app keeps the college-project repo simpler to run and demo.
 */
export default function App() {
  const role = new URLSearchParams(window.location.search).get("role") || "driver";
  return role === "civilian" ? <CivilianView /> : <DriverView />;
}
