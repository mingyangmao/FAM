// FAM-Bench project page: radar mode switcher and BibTeX copy button.

// ---------------------------------------------------------------------------
// Per-condition radar (paper appendix, one figure per prompting mode).
// The buttons in #radar carry data-mode="baseline" | "cot" | "ki" | "cot_ki".
// ---------------------------------------------------------------------------
const RADAR_MODES = {
  baseline: { label: "Baseline", src: "static/images/radar_baseline.webp" },
  cot: { label: "CoT", src: "static/images/radar_cot.webp" },
  ki: { label: "KI", src: "static/images/radar_ki.webp" },
  cot_ki: { label: "CoT + KI", src: "static/images/radar_cot_ki.webp" },
};

const radarImg = document.getElementById("radar-img");
const radarButtons = document.querySelectorAll("#radar [data-mode]");

function showRadarMode(mode) {
  const { label, src } = RADAR_MODES[mode];
  radarImg.src = src;
  radarImg.alt = "Radar chart of Task 1 decision macro-F1 for the eight models " +
    `across the 13 conditions, ${label} mode.`;
  // aria-pressed is also what the CSS uses to draw the selected button
  radarButtons.forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.mode === mode));
  });
}

radarButtons.forEach((button) => {
  button.addEventListener("click", () => showRadarMode(button.dataset.mode));
});

// Fetch the other charts after the page has loaded, so the first switch is instant.
window.addEventListener("load", () => {
  Object.values(RADAR_MODES).forEach(({ src }) => { new Image().src = src; });
});

// ---------------------------------------------------------------------------
// BibTeX copy button. navigator.clipboard only exists in secure contexts
// (https or localhost); elsewhere fall back to selecting the text.
// ---------------------------------------------------------------------------
document.querySelectorAll("[data-copy]").forEach((button) => {
  const target = document.querySelector(button.dataset.copy);
  button.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(target.textContent);
      button.textContent = "Copied";
    } catch {
      const range = document.createRange();
      range.selectNodeContents(target);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      button.textContent = "Press Ctrl+C";
    }
    setTimeout(() => { button.textContent = "Copy"; }, 2000);
  });
});
