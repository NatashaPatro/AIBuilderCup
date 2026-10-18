import { useEffect, useState } from "react";
import {
  collection,
  onSnapshot,
  orderBy,
  query,
  limit,
} from "firebase/firestore";
import { db } from "../firebase";
import StatsHeader from "./StatsHeader.jsx";
import TransactionFeed from "./TransactionFeed.jsx";
import AlertQueue from "./AlertQueue.jsx";
import InvestigationView from "./InvestigationView.jsx";

export default function Dashboard({ user, onSignOut }) {
  const [transactions, setTransactions] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [selectedAlert, setSelectedAlert] = useState(null);

  useEffect(() => {
    const txnQuery = query(
      collection(db, "transactions"),
      orderBy("timestamp", "desc"),
      limit(25)
    );
    const unsubTxn = onSnapshot(txnQuery, (snap) => {
      setTransactions(snap.docs.map((d) => d.data()));
    });

    const alertQuery = query(
      collection(db, "alerts"),
      orderBy("created_at", "desc"),
      limit(25)
    );
    const unsubAlerts = onSnapshot(alertQuery, (snap) => {
      setAlerts(snap.docs.map((d) => d.data()));
    });

    return () => {
      unsubTxn();
      unsubAlerts();
    };
  }, []);

  return (
    <div className="min-h-full bg-brand-bg">
      <header className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-semibold">InvestiGate</h1>
          <p className="text-slate-400 text-sm">Signed in as {user.email}</p>
        </div>
        <button
          onClick={onSignOut}
          className="text-sm px-3 py-1.5 rounded-lg border border-slate-700 hover:bg-slate-800"
        >
          Sign out
        </button>
      </header>

      <StatsHeader />

      <main className="grid grid-cols-1 lg:grid-cols-3 gap-4 p-6">
        <div className="lg:col-span-1 space-y-4">
          <TransactionFeed transactions={transactions} />
          <AlertQueue
            alerts={alerts}
            selectedAlert={selectedAlert}
            onSelect={setSelectedAlert}
          />
        </div>
        <div className="lg:col-span-2">
          <InvestigationView alert={selectedAlert} />
        </div>
      </main>
    </div>
  );
}


