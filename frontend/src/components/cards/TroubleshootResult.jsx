import ProductCard from "./ProductCard";

export default function TroubleshootResult({ data, onSend }) {
  const { symptom, guide, recommended_parts = [] } = data;

  return (
    <div className="card troubleshoot-card">
      <p className="troubleshoot-card__title">
        Diagnosis: <em>{symptom}</em>
      </p>

      <ol className="troubleshoot-card__steps">
        {guide.diagnosis_steps.map((step, i) => (
          <li key={i} className="install-card__step">
            <span className="install-card__step-num">{i + 1}</span>
            <span>{step}</span>
          </li>
        ))}
      </ol>

      {recommended_parts.length > 0 && (
        <div className="troubleshoot-card__parts">
          <p className="troubleshoot-card__parts-label">Likely replacement parts:</p>
          <div className="troubleshoot-card__parts-list">
            {recommended_parts.map((part) => (
              <div key={part.ps_number} className="troubleshoot-card__part-item">
                <ProductCard data={part} />
                {onSend && (
                  <button
                    className="troubleshoot-card__add-btn"
                    onClick={() => onSend(`Add ${part.ps_number} to cart`)}
                  >
                    + Add to cart
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
