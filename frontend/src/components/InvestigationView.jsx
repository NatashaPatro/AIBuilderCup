import { useEffect, useState } from "react";
import { API_BASE_URL } from "../firebase";
import ChatBox from "./ChatBox.jsx";

export default function InvestigationView({ alert }) {
  const [investigation, setInvestigation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [visibleSteps, setVisibleSteps] = useState(0);

  useEffect(() => {
    setInvestigation(null);
    setVisibleSteps(0);
  }, [alert?.id]);

  // Typewriter-style reveal of the reasoning trace for demo effect.
  useEffect(() => {
    if (!investigation) return;
    const total = investigation.reasoning_trace?.length || 0;
    if (visibleSteps >= total) return;
    const t = setTimeout(() => setVisibleSteps((v) => v + 1), 500);
    return () => clearTimeout(t);
  }, [investigation, visibleSteps]);

  const runInvestigation = async () => {
    if (!alert) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/investigate/${alert.id}`, {
        method: "POST",
      });
      const data = await res.json();
      setInvestigation(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (!alert) {
    return (
      <div className="bg-brand-panel border border-slate-800 rounded-xl p-8 h-full flex items-center justify-center text-slate-500">
        Select an alert from the queue to investigate.
      </div>
    );
  }

  return (
    <div className="bg-brand-panel border border-slate-800 rounded-xl p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-lg">
            Investigation — ${alert.amount?.toLocaleString()} at {alert.merchant}
          </h2>
          <p className="text-slate-400 text-sm">
            Customer {alert.customer_id?.slice(0, 8)} · {alert.country} · rule score{" "}
            {alert.score}
          </p>
        </div>
        {!investigation && (
          <button
            onClick={runInvestigation}
            disabled={loading}
            className="px-4 py-2 rounded-lg bg-brand-accent hover:bg-blue-500 font-medium disabled:opacity-50"
          >
            {loading ? "Investigating..." : "Run AI Investigation"}
          </button>
        )}
      </div>

      {investigation && (
        <>
          <div className="flex items-center gap-3">
            <span className="text-3xl font-bold">{investigation.risk_score}</span>
            <span className="text-slate-400 text-sm">/ 100 risk score</span>
            <span className="ml-auto text-xs uppercase tracking-wide px-2 py-1 rounded-full bg-slate-800">
              {investigation.severity}
            </span>
            {investigation.fallback && (
              <span className="text-xs text-yellow-400">(cached fallback)</span>
            )}
          </div>

          <p className="text-slate-300 text-sm">{investigation.summary}</p>

          <div>
            <h3 className="font-medium mb-2 text-sm text-slate-300">Evidence</h3>
            <ul className="list-disc list-inside space-y-1 text-sm text-slate-300">
              {investigation.evidence?.map((e, i) => (
                <li key={i}>{e}</li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="font-medium mb-2 text-sm text-slate-300">
              Agent Reasoning Trace
            </h3>
            <ol className="space-y-2">
              {investigation.reasoning_trace
                ?.slice(0, visibleSteps)
                .map((step, i) => (
                  <li
                    key={i}
                    className="text-sm bg-slate-800/50 rounded-lg px-3 py-2 animate-[fadeIn_0.3s_ease-in]"
                  >
                    <span className="font-medium">{i + 1}. {step.step}</span>
                    <p className="text-slate-400">{step.detail}</p>
                  </li>
                ))}
            </ol>
          </div>

          <div className="bg-slate-800/70 border border-slate-700 rounded-lg px-4 py-3">
            <h3 className="font-medium text-sm mb-1">Recommended Action</h3>
            <p className="text-sm text-slate-200">{investigation.recommended_action}</p>
          </div>

          <ChatBox alertId={alert.id} />
        </>
      )}
    </div>
  );
}

