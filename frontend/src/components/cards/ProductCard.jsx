export default function ProductCard({ data }) {
  const stock = data.in_stock;
  const stars = Math.round(data.rating || 0);
  const Wrapper = data.url ? "a" : "div";
  const wrapperProps = data.url
    ? { href: data.url, target: "_blank", rel: "noreferrer", className: "card product-card product-card--link" }
    : { className: "card product-card" };

  return (
    <Wrapper {...wrapperProps}>
      <div className="product-card__header">
        <div>
          <p className="product-card__name">{data.name}</p>
          <p className="product-card__id">
            {data.ps_number}
            {data.manufacturer_number && (
              <span className="product-card__mfr"> · {data.manufacturer_number}</span>
            )}
          </p>
        </div>
        <div className="product-card__price-col">
          <span className="product-card__price">${Number(data.price).toFixed(2)}</span>
          <span className={`badge ${stock ? "badge--green" : "badge--red"}`}>
            {stock ? "In Stock" : "Out of Stock"}
          </span>
        </div>
      </div>

      {data.brands?.length > 0 && (
        <div className="product-card__brands">
          {data.brands.map((b) => (
            <span key={b} className="tag">{b}</span>
          ))}
        </div>
      )}

      {data.rating != null && (
        <div className="product-card__rating">
          <span className="stars">{"★".repeat(stars)}{"☆".repeat(5 - stars)}</span>
          <span className="product-card__review-count">
            {data.rating.toFixed(1)} ({data.review_count} reviews)
          </span>
        </div>
      )}
    </Wrapper>
  );
}
