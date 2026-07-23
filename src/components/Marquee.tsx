const WORDS = ["Turnkey Design–Build", "Steel Structure", "Architecture", "Interior Craft", "Structural Engineering", "Mandalay"];

export default function Marquee() {
  const row = [...WORDS, ...WORDS];
  return (
    <div className="relative overflow-hidden border-y border-line bg-bronze py-4">
      <div className="flex w-max animate-marquee items-center">
        {[0, 1].map((half) => (
          <div key={half} className="flex items-center">
            {row.map((w, i) => (
              <span key={`${half}-${i}`} className="flex items-center">
                <span className="font-display px-8 text-2xl font-medium italic text-ink sm:text-3xl">
                  {w}
                </span>
                <span className="h-1.5 w-1.5 rounded-full bg-ink/40" />
              </span>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
