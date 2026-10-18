const SEVERITY_COLORS = {
  critical: "bg-red-500/20 text-red-300 border-red-500/40",
  high: "bg-orange-500/20 text-orange-300 border-orange-500/40",
  medium: "bg-yellow-500/20 text-yellow-300 border-yellow-500/40",
  low: "bg-slate-500/20 text-slate-300 border-slate-500/40",
};

export default function AlertQueue({ alerts, selectedAlert, onSelect }) {
  return (
    <div className="bg-brand-panel border border-slate-800 rounded-xl p-4">
      <h2 className="font-semibold mb-3">Alert Queue</h2>
      <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
        {alerts.length === 0 && (
          <p className="text-slate-500 text-sm">No alerts yet. Waiting for anomalies...</p>
        )}
        {alerts.map((a) => (
          <button
            key={a.id}
            onClick={() => onSelect(a)}
            className={`w-full text-left text-sm rounded-lg px-3 py-2 border transition ${
              selectedAlert?.id === a.id
                ? "border-brand-accent bg-slate-800"
                : "border-slate-800 bg-slate-800/40 hover:bg-slate-800"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-medium">${a.amount?.toLocaleString()}</span>
              <span
                className={`text-xs px-2 py-0.5 rounded-full border ${SEVERITY_COLORS[a.severity] || ""}`}
              >
                {a.severity}
              </span>
            </div>
            <p className="text-slate-400 text-xs mt-1">
              {a.merchant} · {a.country} · score {a.score}
            </p>
            <p className="text-slate-500 text-xs">{a.status}</p>
          </button>
        ))}
      </div>
    </div>
  );
}

