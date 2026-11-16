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
  // TODO(human): show the radar for `mode` (a key of RADAR_MODES).
  // - point radarImg at RADAR_MODES[mode].src and keep its alt text in sync
  // - set aria-pressed="true" on the matching button, "false" on the others
}

radarButtons.forEach((button) => {
  button.addEventListener("click", () => showRadarMode(button.dataset.mode));
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
