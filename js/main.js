// Larry Seyer - Main JavaScript

document.addEventListener('DOMContentLoaded', () => {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Set current year in footer
  const yearSpan = document.getElementById('year');
  if (yearSpan) {
    yearSpan.textContent = new Date().getFullYear();
  }

  // Mark the current page in the nav, so no page has to hard-code it.
  const here = window.location.pathname.replace(/index\.html$/, '').replace(/\/$/, '');
  document.querySelectorAll('.nav a').forEach(link => {
    const target = new URL(link.getAttribute('href'), window.location.href).pathname
      .replace(/index\.html$/, '')
      .replace(/\/$/, '');
    if (target && target === here) {
      link.classList.add('active');
    }
  });

  // Cards light up under the cursor.
  document.querySelectorAll('.card').forEach(card => {
    card.addEventListener('pointermove', e => {
      const rect = card.getBoundingClientRect();
      card.style.setProperty('--mx', (e.clientX - rect.left) + 'px');
      card.style.setProperty('--my', (e.clientY - rect.top) + 'px');
    });
  });

  // Hero spectrum: a slow analyzer ridge lit magenta through to cyan.
  const canvas = document.getElementById('spectrum');
  if (canvas && canvas.getContext) {
    const ctx = canvas.getContext('2d');
    const BANDS = 96;
    const phase = [];
    for (let i = 0; i < BANDS; i++) {
      phase.push((Math.sin(i * 12.9898) * 43758.5453) % (Math.PI * 2));
    }

    const draw = time => {
      const w = canvas.width;
      const h = canvas.height;
      const bandWidth = w / BANDS;
      ctx.clearRect(0, 0, w, h);

      for (let i = 0; i < BANDS; i++) {
        // Energy falls off with frequency, the way a real spectrum does.
        const tilt = Math.pow(1 - i / BANDS, 1.25);
        const swing = reduceMotion ? 0.55 : 0.5 + 0.5 * Math.sin(time / 1100 + phase[i] + i * 0.14);
        const height = (0.14 + tilt * 0.86) * swing * h * 0.92;

        const gradient = ctx.createLinearGradient(0, h, 0, h - height);
        gradient.addColorStop(0, 'rgba(255, 61, 146, .10)');
        gradient.addColorStop(0.55, 'rgba(255, 182, 72, .42)');
        gradient.addColorStop(1, 'rgba(61, 220, 255, .85)');
        ctx.fillStyle = gradient;
        ctx.fillRect(i * bandWidth + bandWidth * 0.18, h - height, bandWidth * 0.64, height);
      }

      if (!reduceMotion) requestAnimationFrame(draw);
    };

    requestAnimationFrame(draw);
  }
});
