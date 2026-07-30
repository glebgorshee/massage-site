/* Студия массажа Андрея Булатного — прогрессивное улучшение.
   Контент полностью доступен без JS; здесь только меню и анимации. */
(function () {
  document.documentElement.classList.add('js');

  /* --- мобильное меню --- */
  var burger = document.querySelector('.burger');
  var menu = document.querySelector('.mobile-menu');
  if (burger && menu) {
    var setOpen = function (open) {
      menu.classList.toggle('open', open);
      document.body.classList.toggle('menu-open', open);
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      burger.querySelector('.ic-burger').style.display = open ? 'none' : '';
      burger.querySelector('.ic-close').style.display = open ? 'block' : '';
    };
    burger.addEventListener('click', function () {
      setOpen(!menu.classList.contains('open'));
    });
    menu.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') setOpen(false);
    });
    window.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && menu.classList.contains('open')) setOpen(false);
    });
  }

  /* --- появление блоков --- */
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var targets = document.querySelectorAll('.reveal');
  if (!reduced && 'IntersectionObserver' in window && targets.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          en.target.classList.add('in');
          io.unobserve(en.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    targets.forEach(function (t) { io.observe(t); });
  } else {
    targets.forEach(function (t) { t.classList.add('in'); });
  }

  /* --- липкая панель покупки на страницах методичек --- */
  var sticky = document.querySelector('.sticky-buy');
  var heroBuy = document.querySelector('.g-buy');
  if (sticky && heroBuy && 'IntersectionObserver' in window) {
    document.body.classList.add('has-sticky-buy');
    var sio = new IntersectionObserver(function (entries) {
      sticky.classList.toggle('visible', !entries[0].isIntersecting);
    }, { rootMargin: '-60px 0px 0px 0px' });
    sio.observe(heroBuy);
  }
})();
