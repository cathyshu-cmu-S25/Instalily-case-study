const DIFFICULTY_COLOR = { Easy: "badge--green", Moderate: "badge--yellow", Advanced: "badge--red" };

export default function InstallSteps({ data }) {
  const { part, install, part_url } = data;
  const steps = install.steps || [];
  const tools = install.tools?.length ? install.tools.join(", ") : "None";

  return (
    <div className="card install-card">
      <div className="install-card__header">
        <p className="install-card__title">{part.name}</p>
        <p className="install-card__part">Installation Guide · {part.ps_number}</p>
      </div>

      <div className="install-card__meta">
        <span className={`badge ${DIFFICULTY_COLOR[install.difficulty] || "badge--yellow"}`}>
          {install.difficulty}
        </span>
        {install.time && <span className="install-card__time">⏱ {install.time}</span>}
        <span className="install-card__tools">🔧 {tools}</span>
      </div>

      {steps.length > 0 ? (
        <ol className="install-card__steps">
          {steps.map((step, i) => (
            <li key={i} className="install-card__step">
              <span className="install-card__step-num">{i + 1}</span>
              <span>{step}</span>
            </li>
          ))}
        </ol>
      ) : part_url ? (
        <div className="install-card__links">
          <a className="install-card__ps-link" href={part_url} target="_blank" rel="noreferrer">
            View installation videos &amp; instructions on PartSelect →
          </a>
        </div>
      ) : null}
    </div>
  );
}
