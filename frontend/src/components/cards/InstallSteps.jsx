const DIFFICULTY_COLOR = { Easy: "badge--green", Moderate: "badge--yellow", Advanced: "badge--red" };

export default function InstallSteps({ data }) {
  const { part, install } = data;
  const steps = install.steps || [];
  const tools = install.tools?.length ? install.tools.join(", ") : "None";

  return (
    <div className="card install-card">
      <div className="install-card__header">
        <p className="install-card__title">Installation Guide</p>
        <p className="install-card__part">{part.name} · {part.ps_number}</p>
      </div>

      <div className="install-card__meta">
        <span className={`badge ${DIFFICULTY_COLOR[install.difficulty] || "badge--yellow"}`}>
          {install.difficulty}
        </span>
        <span className="install-card__time">⏱ {install.time}</span>
        <span className="install-card__tools">🔧 {tools}</span>
      </div>

      <ol className="install-card__steps">
        {steps.map((step, i) => (
          <li key={i} className="install-card__step">
            <span className="install-card__step-num">{i + 1}</span>
            <span>{step}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
