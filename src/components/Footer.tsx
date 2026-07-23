"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import Reveal from "@/components/Reveal";

export default function Footer() {
  return (
    <footer className="relative overflow-hidden">
      {/* CTA */}
      <div className="mx-auto max-w-7xl px-6 py-28 text-center lg:px-10 lg:py-36">
        <Reveal>
          <p className="text-[11px] uppercase tracking-[0.4em] text-bronze">Your plot is waiting</p>
          <h2 className="font-display mx-auto mt-6 max-w-4xl text-5xl font-medium leading-[1.02] sm:text-7xl">
            Let&rsquo;s build <em className="text-bronze">yours.</em>
          </h2>
          <p className="mx-auto mt-6 max-w-md text-sm leading-relaxed text-mute">
            Free design consultation &amp; cost estimation — on site, in Mandalay and beyond.
          </p>
          <Link
            href="https://www.facebook.com/310908306475419"
            target="_blank"
            className="group mt-10 inline-flex items-center gap-3 rounded-full bg-bronze px-8 py-4 text-[12px] uppercase tracking-[0.25em] text-ink transition-all duration-300 hover:bg-bronze-2"
          >
            Start a Conversation
            <ArrowUpRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1 group-hover:-translate-y-1" />
          </Link>
        </Reveal>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-line">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-6 px-6 py-10 text-[11px] uppercase tracking-[0.2em] text-mute sm:flex-row lg:px-10">
          <span className="font-display text-lg normal-case tracking-tight text-bone">ZAW G</span>
          <div className="flex gap-8">
            <a href="https://www.facebook.com/310908306475419" target="_blank" className="transition-colors hover:text-bronze">Facebook</a>
            <a href="#" className="transition-colors hover:text-bronze">Telegram</a>
            <a href="#" className="transition-colors hover:text-bronze">Viber</a>
            <Link href="/portal" className="transition-colors hover:text-bronze">Client Portal</Link>
            <Link href="/admin" className="text-mute/50 transition-colors hover:text-bronze">Admin</Link>
          </div>
          <span>© 2026 Zaw G Design &amp; Construction · Mandalay</span>
        </div>
      </div>
    </footer>
  );
}
