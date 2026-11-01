// Larry Seyer - Main JavaScript ("Precision" design)

document.addEventListener('DOMContentLoaded', () => {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Set current year in footer
  const yearSpan = document.getElementById('year');
  if (yearSpan) yearSpan.textContent = new Date().getFullYear();

  // Mark the current page in the nav, so no page has to hard-code it.
  const here = window.location.pathname.replace(/index\.html$/, '').replace(/\/$/, '');
  document.querySelectorAll('.nav a').forEach(link => {
    if (link.getAttribute('href').includes('#')) return;
    const target = new URL(link.getAttribute('href'), window.location.href).pathname
      .replace(/index\.html$/, '').replace(/\/$/, '');
    if (target && target === here) link.classList.add('active');
  });

  // Mobile menu
  const header = document.querySelector('.header');
  const toggle = document.querySelector('.nav-toggle');
  const nav = document.querySelector('.nav');
  if (header && toggle && nav) {
    if (!nav.id) nav.id = 'site-nav';
    toggle.setAttribute('aria-controls', nav.id);
    toggle.setAttribute('aria-expanded', 'false');
    toggle.textContent = 'Menu';
    const set = open => {
      header.classList.toggle('nav-open', open);
      toggle.setAttribute('aria-expanded', String(open));
      toggle.textContent = open ? 'Close' : 'Menu';
    };
    toggle.addEventListener('click', () => set(!header.classList.contains('nav-open')));
    nav.querySelectorAll('a').forEach(a => a.addEventListener('click', () => set(false)));
    document.addEventListener('keydown', e => { if (e.key === 'Escape') set(false); });
  }

  // Practice meters
  document.querySelectorAll('[data-meter]').forEach(m => {
    for (let i = 0; i < 28; i++) m.appendChild(document.createElement('i'));
  });
  const bars = [...document.querySelectorAll('.meter i')];
  const vus = [...document.querySelectorAll('.ch:not(.ch--muted) .vu i')];
  const spec = document.getElementById('analyzer-spec');
  const tc = document.getElementById('tc');
  if (!bars.length && !vus.length && !spec && !tc) return;
  const t0 = performance.now();
  const pad = x => String(Math.floor(x)).padStart(2, '0');

  const frame = t => {
    bars.forEach((b, i) => {
      const v = .35 + .3 * Math.sin(t / 600 + i * .5) + .25 * Math.sin(t / 230 + i * 1.7);
      b.style.height = Math.max(8, v * 100) + '%';
      b.style.background = v > .82 ? '#f0b44c' : '#6fd6c8';
    });
    vus.forEach((v, i) => v.style.setProperty('--l', (45 + 30 * Math.sin(t / 300 + i * 1.3) + 15 * Math.sin(t / 97 + i)) + '%'));
    if (spec) {
      let d = 'M0,220';
      for (let x = 0; x <= 1200; x += 12) {
        const y = 185 - 38 * Math.abs(Math.sin(x / 90 + t / 900)) - 24 * Math.abs(Math.sin(x / 37 - t / 500)) - 28 * Math.exp(-Math.pow((x - 600) / 260, 2));
        d += ' L' + x + ',' + y.toFixed(1);
      }
      spec.setAttribute('d', d + ' L1200,220Z');
    }
    if (tc) {
      const e = (t - t0) / 1000;
      tc.textContent = pad(e / 3600) + ':' + pad(e / 60 % 60) + ':' + pad(e % 60) + ':' + pad(e * 30 % 30);
    }
    if (!reduceMotion) requestAnimationFrame(frame);
  };
  frame(1000);
});
