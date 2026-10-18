export default function TransactionFeed({ transactions }) {
  return (
    <div className="bg-brand-panel border border-slate-800 rounded-xl p-4">
      <h2 className="font-semibold mb-3">Live Transaction Feed</h2>
      <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
        {transactions.length === 0 && (
          <p className="text-slate-500 text-sm">Waiting for transactions...</p>
        )}
        {transactions.map((t) => (
          <div
            key={t.id}
            className="flex items-center justify-between text-sm bg-slate-800/50 rounded-lg px-3 py-2"
          >
            <div>
              <p className="font-medium">{t.merchant}</p>
              <p className="text-slate-400 text-xs">
                {t.country} · {new Date(t.timestamp).toLocaleTimeString()}
              </p>
            </div>
            <div className="text-right">
              <p className="font-medium">${t.amount?.toLocaleString()}</p>
              <p
                className={`text-xs ${
                  t.risk_score >= 55 ? "text-red-400" : "text-slate-500"
                }`}
              >
                risk {t.risk_score ?? 0}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

