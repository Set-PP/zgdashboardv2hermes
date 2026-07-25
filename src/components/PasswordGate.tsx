"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Lock, Eye, EyeOff } from "lucide-react";

interface Props {
  password: string;
  children: React.ReactNode;
  storageKey: string;
  title?: string;
  subtitle?: string;
}

export default function PasswordGate({ password, children, storageKey, title, subtitle }: Props) {
  const [authed, setAuthed] = useState(() => {
    if (typeof window === "undefined") return false;
    return sessionStorage.getItem(storageKey) === "true";
  });
  const [input, setInput] = useState("");
  const [error, setError] = useState(false);
  const [show, setShow] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input === password) {
      sessionStorage.setItem(storageKey, "true");
      setAuthed(true);
      setError(false);
    } else {
      setError(true);
      setInput("");
    }
  };

  if (authed) return <>{children}</>;

  return (
    <div className="min-h-screen bg-ink flex items-center justify-center p-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md bg-ink-light border border-white/10 rounded-2xl p-8"
      >
        <div className="flex justify-center mb-6">
          <div className="w-14 h-14 rounded-full bg-amber-500/10 flex items-center justify-center">
            <Lock className="w-7 h-7 text-amber-500" />
          </div>
        </div>
        
        {title && (
          <h1 className="text-xl font-display text-white text-center mb-1">{title}</h1>
        )}
        {subtitle && (
          <p className="text-white/40 text-sm text-center mb-6">{subtitle}</p>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <input
              type={show ? "text" : "password"}
              value={input}
              onChange={(e) => { setInput(e.target.value); setError(false); }}
              placeholder="Enter access password"
              className="w-full bg-ink border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-white/30 focus:outline-none focus:border-amber-500/50 transition-colors pr-12"
              autoFocus
            />
            <button
              type="button"
              onClick={() => setShow(!show)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors"
            >
              {show ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>

          <AnimatePresence>
            {error && (
              <motion.p
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="text-red-400 text-sm text-center"
              >
                Incorrect password. Please try again.
              </motion.p>
            )}
          </AnimatePresence>

          <button
            type="submit"
            disabled={!input}
            className="w-full bg-amber-500 hover:bg-amber-400 disabled:opacity-30 text-black font-semibold py-3 rounded-xl transition-colors"
          >
            Access Dashboard
          </button>
        </form>
      </motion.div>
    </div>
  );
}
