import { formatNumber, formatPrice } from "../format";

export default function RouteList({ route }) {
  if (!route || route.length === 0) return null;

  return (
    <ol className="route-list">
      {route.map((house, idx) => (
        <li key={`${house.house_id}-${idx}`} className="route-list__item">
          <span className="route-list__order">{idx === route.length - 1 ? "fin" : idx}</span>
          <div className="route-list__info">
            <p className="route-list__address">{house.address}</p>
            <p className="route-list__meta">
              {house.house_id} · {formatNumber(house.bedrooms)} hab ·{" "}
              {formatNumber(house.bathrooms)} baños · {formatPrice(house.price)}
            </p>
          </div>
        </li>
      ))}
    </ol>
  );
}
