import { MapContainer, TileLayer, Marker, Popup, Polyline } from "react-leaflet";
import L from "leaflet";

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

export default function RouteMap({ route }) {
  if (!route || route.length === 0) {
    return <div className="map-placeholder">Selecciona un suburbio para ver el mapa.</div>;
  }

  const center = [route[0].latitude, route[0].longitude];
  const positions = route.map((h) => [h.latitude, h.longitude]);

  return (
    <MapContainer center={center} zoom={15} scrollWheelZoom className="route-map">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Polyline positions={positions} pathOptions={{ color: "#2f5d50", weight: 4, opacity: 0.85 }} />
      {route.map((house, idx) => (
        <Marker
          key={house.house_id}
          position={[house.latitude, house.longitude]}
          icon={idx === 0 ? startIcon : stopIcon(idx)}
        >
          <Popup>
            <strong>{house.address}</strong>
            <br />
            {house.house_id} · ${house.price.toLocaleString("en-AU")}
            <br />
            Parada #{idx} de la ruta
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
