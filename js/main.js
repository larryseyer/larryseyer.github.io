// Larry Seyer - Main JavaScript

document.addEventListener('DOMContentLoaded', () => {
  // Mobile navigation
  const navToggle = document.querySelector('.nav-toggle');
  const nav = document.querySelector('.nav');

  if (navToggle && nav) {
    navToggle.addEventListener('click', () => {
      nav.classList.toggle('active');
    });

    document.addEventListener('click', (e) => {
      if (!nav.contains(e.target) && !navToggle.contains(e.target)) {
        nav.classList.remove('active');
      }
    });
  }

  // Scroll animations
  const animateOnScroll = () => {
    const elements = document.querySelectorAll('.section');
    elements.forEach(el => {
      const rect = el.getBoundingClientRect();
      if (rect.top < window.innerHeight * 0.8) {
        el.classList.add('animate-in');
      }
    });
  };

  window.addEventListener('scroll', animateOnScroll);
  animateOnScroll();
});
