const STATUS_BADGE = {
  Processing: "badge--yellow",
  Shipped: "badge--blue",
  "Out for Delivery": "badge--blue",
  Delivered: "badge--green",
};

export default function OrderCard({ data }) {
  return (
    <div className="card order-card">
      <div className="order-card__header">
        <p className="order-card__title">Order Status</p>
        <span className={`badge ${STATUS_BADGE[data.status] || "badge--yellow"}`}>
          {data.status}
        </span>
      </div>

      <p className="order-card__id">Order # {data.order_id}</p>

      {data.items?.length > 0 && (
        <ul className="order-card__items">
          {data.items.map((item, i) => (
            <li key={i}>
              {item.qty}× {item.name} — ${Number(item.price).toFixed(2)}
            </li>
          ))}
        </ul>
      )}

      <div className="order-card__footer">
        {data.estimated_delivery && (
          <p>📦 Est. delivery: <strong>{data.estimated_delivery}</strong></p>
        )}
        {data.tracking_number && (
          <p>🚚 {data.carrier}: {data.tracking_number}</p>
        )}
      </div>
    </div>
  );
}
