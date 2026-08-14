import { memo, useState } from "react";
import { MENU_SECTIONS, HOUSE_SPECIALS_ID } from "../lib/menuData";

function ChevronIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}

function formatPrice(price) {
  if (!price) return "Free";
  return `₹${price.toLocaleString("en-IN")}`;
}

function MenuSection({ section, showLabel, onSelectItem }) {
  return (
    <div className="menu-section">
      {showLabel && <div className="menu-section__label">{section.label}</div>}
      <ul className="menu-section__list">
        {section.items.map((item) => (
          <li key={item.name}>
            <button
              type="button"
              className="menu-item__row"
              onClick={onSelectItem ? () => onSelectItem(item) : undefined}
            >
              <span className="menu-item__name">{item.name}</span>
              <span className="menu-item__price">{formatPrice(item.price)}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function MenuPanel({ onSelectItem }) {
  const [expanded, setExpanded] = useState(false);

  const houseSpecials = MENU_SECTIONS.find((s) => s.id === HOUSE_SPECIALS_ID);
  const otherSections = MENU_SECTIONS.filter((s) => s.id !== HOUSE_SPECIALS_ID);

  return (
    <section className="menu-panel" aria-label="Menu">
      <div className="menu-panel__head">
        <div className="menu-panel__title">
          <h2>Menu</h2>
          <span className="menu-panel__subtitle">
            {expanded ? "Full menu" : "House Specials"}
          </span>
        </div>

        <button
          type="button"
          className="menu-panel__toggle"
          aria-expanded={expanded}
          onClick={() => setExpanded((v) => !v)}
        >
          {expanded ? "Less" : "More"}
          <ChevronIcon />
        </button>
      </div>

      <div className="menu-panel__body">
        {/* House Specials render first, unlabeled while collapsed */}
        <MenuSection
          section={houseSpecials}
          showLabel={expanded}
          onSelectItem={onSelectItem}
        />

        {expanded &&
          otherSections.map((section) => (
            <MenuSection
              key={section.id}
              section={section}
              showLabel
              onSelectItem={onSelectItem}
            />
          ))}
      </div>

      {!expanded && (
        <p className="menu-panel__hint">
          Say the dish name during your call to order — tap “More” for the
          full menu.
        </p>
      )}
    </section>
  );
}

export default memo(MenuPanel);