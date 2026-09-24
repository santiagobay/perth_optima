import { useEffect, useMemo } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from "react-leaflet";
import L from "leaflet";
import { formatPrice } from "../format";

// Se usa OpenStreetMap a través de Leaflet en lugar de la API de Google
// Maps: no requiere llave de API ni facturación, lo cual es preferible
// para un proyecto académico que debe poder ejecutarse sin credenciales
// externas, y es la misma base que emplean varias herramientas
// comerciales de ruteo (p. ej. RoadWarrior, 2025) para su capa de mapa.

const startIcon = new L.DivIcon({
  className: "",
  html: `<div class="pin pin--start">0</div>`,
  iconSize: [28, 28],
});

function stopIcon(order) {
  return new L.DivIcon({
    className: "",
    html: `<div class="pin">${order}</div>`,
    iconSize: [26, 26],
  });
}

// `center` y `zoom` de MapContainer solo se aplican al montar el mapa: al
// cambiar de distrito el mapa se quedaba encuadrado en el anterior. Este
// componente auxiliar reencuadra cada vez que cambia la ruta.
function FitRoute({ positions }) {
  const map = useMap();
  const signature = positions.map((p) => p.join(",")).join("|");

  useEffect(() => {
    if (positions.length === 0) return;
    if (positions.length === 1) {
      map.setView(positions[0], 16);
      return;
    }
    map.fitBounds(L.latLngBounds(positions), { padding: [40, 40], maxZoom: 17 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, signature]);

  return null;
}

export default function RouteMap({ route }) {
  // El backend devuelve la ruta cerrada: la primera vivienda se repite al
  // final para dibujar el regreso. Esa repetición debe alimentar la
  // polilínea, pero no duplicar el marcador (antes generaba además dos
  // elementos de React con la misma `key`).
  const positions = useMemo(
    () => (route ?? []).map((h) => [h.latitude, h.longitude]),
    [route],
  );

  const stops = useMemo(() => {
    const items = route ?? [];
    if (items.length < 2) return items;
    const first = items[0];
    const last = items[items.length - 1];
    const isClosed = first.latitude === last.latitude && first.longitude === last.longitude;
    return isClosed ? items.slice(0, -1) : items;
  }, [route]);

  if (!route || route.length === 0) {
    return <div className="map-placeholder">Selecciona un suburbio para ver el mapa.</div>;
  }

  return (
    <MapContainer center={positions[0]} zoom={15} scrollWheelZoom className="route-map">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitRoute positions={positions} />
      <Polyline positions={positions} pathOptions={{ color: "#2f5d50", weight: 4, opacity: 0.85 }} />
      {stops.map((house, idx) => (
        <Marker
          key={`${house.house_id}-${idx}`}
          position={[house.latitude, house.longitude]}
          icon={idx === 0 ? startIcon : stopIcon(idx)}
        >
          <Popup>
            <strong>{house.address}</strong>
            <br />
            {house.house_id} · {formatPrice(house.price)}
            <br />
            {idx === 0
              ? "Punto de partida y de regreso"
              : `Parada #${idx} de ${stops.length - 1}`}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
