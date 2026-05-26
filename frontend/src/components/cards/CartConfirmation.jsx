export default function CartConfirmation({ data }) {
  const { part, qty, subtotal } = data;

  return (
    <div className="card cart-card">
      <p className="cart-card__title">✓ Added to Cart</p>
      <p className="cart-card__item">
        {qty}× <strong>{part.name}</strong>
      </p>
      <p className="cart-card__id">{part.ps_number}</p>
      <p className="cart-card__subtotal">Subtotal: <strong>${Number(subtotal).toFixed(2)}</strong></p>
      <a className="cart-card__btn" href="https://www.partselect.com/cart.htm" target="_blank" rel="noreferrer">
        Checkout →
      </a>
    </div>
  );
}
