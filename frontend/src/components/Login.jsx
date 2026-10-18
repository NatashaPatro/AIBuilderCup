import { useState } from "react";
import { signInWithEmailAndPassword } from "firebase/auth";
import { auth } from "../firebase";

export default function Login() {
  const [email, setEmail] = useState("analyst@demo.com");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await signInWithEmailAndPassword(auth, email, password);
    } catch (err) {
      setError("Sign-in failed. Check the demo credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full w-full flex items-center justify-center bg-brand-bg">
      <form
        onSubmit={handleSubmit}
        className="bg-brand-panel rounded-2xl shadow-xl p-8 w-full max-w-sm border border-slate-700"
      >
        <h1 className="text-2xl font-semibold mb-1">InvestiGate</h1>
        <p className="text-slate-400 text-sm mb-6">
          Sign in to monitor live transactions and investigate flagged alerts.
        </p>

        <label className="block text-sm mb-1 text-slate-300">Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full mb-4 px-3 py-2 rounded-lg bg-slate-800 border border-slate-600 focus:outline-none focus:border-brand-accent"
        />

        <label className="block text-sm mb-1 text-slate-300">Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full mb-4 px-3 py-2 rounded-lg bg-slate-800 border border-slate-600 focus:outline-none focus:border-brand-accent"
        />

        {error && <p className="text-red-400 text-sm mb-3">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2 rounded-lg bg-brand-accent hover:bg-blue-500 transition font-medium disabled:opacity-50"
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>

        <p className="text-xs text-slate-500 mt-4">
          Demo credentials: analyst@demo.com / (see README) — create this user
          in Firebase Auth before the demo.
        </p>
      </form>
    </div>
  );
}


