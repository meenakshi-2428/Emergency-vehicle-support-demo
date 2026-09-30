import { useEffect, useRef } from "react";
import mapboxgl from "mapbox-gl";

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;

/**
 * Live city map: shows the ambulance's live position (step 2, "Broadcast Live
 * Position") and, once approved, the detour route (step 6's decision card
 * geometry) as a line overlay.
 */
export default function MapView({ position, detourGeometry }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const markerRef = useRef(null);

  useEffect(() => {
    if (!MAPBOX_TOKEN) return; // renders the fallback message instead, see below
    mapboxgl.accessToken = MAPBOX_TOKEN;
    mapRef.current = new mapboxgl.Map({
      container: containerRef.current,
      style: "mapbox://styles/mapbox/dark-v11",
      center: [77.605, 12.976],
      zoom: 13,
    });
    return () => mapRef.current?.remove();
  }, []);

  useEffect(() => {
    if (!mapRef.current || !position) return;
    const { lon, lat } = position;
    if (!markerRef.current) {
      markerRef.current = new mapboxgl.Marker({ color: "#c62828" })
        .setLngLat([lon, lat])
        .addTo(mapRef.current);
    } else {
      markerRef.current.setLngLat([lon, lat]);
    }
    mapRef.current.easeTo({ center: [lon, lat] });
  }, [position]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !detourGeometry) return;
    const draw = () => {
      if (map.getSource("detour")) {
        map.getSource("detour").setData({ type: "Feature", geometry: detourGeometry });
        return;
      }
      map.addSource("detour", { type: "geojson", data: { type: "Feature", geometry: detourGeometry } });
      map.addLayer({
        id: "detour-line",
        type: "line",
        source: "detour",
        paint: { "line-color": "#1e8e5a", "line-width": 4 },
      });
    };
    if (map.isStyleLoaded()) draw();
    else map.once("load", draw);
  }, [detourGeometry]);

  if (!MAPBOX_TOKEN) {
    return (
      <div style={{ padding: 24, background: "#1f1a5e", borderRadius: 8 }}>
        Set <code>VITE_MAPBOX_TOKEN</code> in <code>dashboard/.env</code> to
        render the live map (free token: account.mapbox.com/access-tokens).
      </div>
    );
  }

  return <div ref={containerRef} style={{ width: "100%", height: "100%" }} />;
}
