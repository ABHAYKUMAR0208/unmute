const BRANDS = [
  "Aurora Hotels",
  "Meridian Group",
  "Bayview Resorts",
  "Nordic Stay",
  "Cascade Inns",
  "Marbella Collection",
  "Harbor & Co.",
  "Solstice Suites",
];

export default function BrandMarquee() {
  // Duplicate the list so the CSS animation can loop seamlessly.
  const track = [...BRANDS, ...BRANDS];

  return (
    <section className="brand-marquee" aria-label="Trusted by hospitality brands">
      <div className="brand-marquee__fade brand-marquee__fade--left" />
      <div className="brand-marquee__fade brand-marquee__fade--right" />
      <div className="brand-marquee__track">
        {track.map((name, i) => (
          <span className="brand-marquee__item" key={`${name}-${i}`}>
            {name}
          </span>
        ))}
      </div>
    </section>
  );
}
