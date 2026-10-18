import { useEffect, useState } from "react";
import { onAuthStateChanged, signOut } from "firebase/auth";
import { auth } from "./firebase";
import Login from "./components/Login.jsx";
import Dashboard from "./components/Dashboard.jsx";

export default function App() {
  const [user, setUser] = useState(undefined); // undefined = loading, null = signed out

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, (u) => setUser(u));
    return unsub;
  }, []);

  if (user === undefined) {
    return (
      <div className="h-full w-full flex items-center justify-center text-slate-400">
        Loading...
      </div>
    );
  }

  if (!user) {
    return <Login />;
  }

  return <Dashboard user={user} onSignOut={() => signOut(auth)} />;
}

