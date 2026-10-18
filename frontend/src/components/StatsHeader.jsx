import { useEffect, useState } from "react";
import { API_BASE_URL } from "../firebase";

export default function StatsHeader() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const load = () => {
      fetch(`${API_BASE_URL}/stats`)
        .then((r) => r.json())
        .then(setStats)
        .catch(() => {});
    };
    load();
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, []);

  const items = [
    { label: "Transactions today", value: stats?.transactions_today ?? "—" },
    { label: "Alerts today", value: stats?.alerts_today ?? "—" },
    { label: "High-risk open", value: stats?.high_risk_open ?? "—" },
    { label: "Avg investigation time", value: stats ? `${stats.avg_investigation_seconds}s` : "—" },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 px-6 pt-4">
      {items.map((item) => (
        <div
          key={item.label}
          className="bg-brand-panel border border-slate-800 rounded-xl p-4"
        >
          <p className="text-2xl font-semibold">{item.value}</p>
          <p className="text-slate-400 text-xs mt-1">{item.label}</p>
        </div>
      ))}
    </div>
  );
}

