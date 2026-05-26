export default function CompatibilityBadge({ data }) {
  const { part, model_number, compatible } = data;

  return (
    <div className={`card compat-badge ${compatible ? "compat-badge--yes" : "compat-badge--no"}`}>
      <span className="compat-badge__icon">{compatible ? "✓" : "✗"}</span>
      <div className="compat-badge__text">
        <p className="compat-badge__verdict">
          <strong>{part.name}</strong> is{" "}
          {compatible ? (
            <span className="compat-badge__yes">compatible</span>
          ) : (
            <span className="compat-badge__no">NOT compatible</span>
          )}{" "}
          with model <strong>{model_number}</strong>
        </p>
        <p className="compat-badge__sub">
          {compatible
            ? `${part.ps_number} is confirmed to work with this appliance.`
            : `This is a ${part.appliance_type?.toLowerCase()} part and is not listed for ${model_number}.`}
        </p>
      </div>
    </div>
  );
}
