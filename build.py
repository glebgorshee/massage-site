#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Генератор сайта «Студия массажа Андрея Булатного».
Контент страниц: content/*.html  →  сборка: python3 build.py  →  site/"""

import os, urllib.parse, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'docs')
CONTENT = os.path.join(ROOT, 'content')

def _v(rel):
    p = os.path.join(OUT, rel)
    return hashlib.md5(open(p, 'rb').read()).hexdigest()[:8] if os.path.exists(p) else '0'

PHONE_RAW = '79152438842'
PHONE_PRETTY = '+7 (915) 243-88-42'
BRAND = 'Андрей Булатный'
BRAND_FULL = 'Клуб восстановления Андрея Булатного'
BRAND_SUB = 'клуб восстановления'
TG = 'https://t.me/MassageTaganka'
SITE = 'https://bulatny.ru'          # основной адрес, для canonical и Success URL кассы
INN = '505601883579'
OGRNIP = '323508100135643'
FIO = 'Шмаров Андрей Владимирович'

# Файлы выдачи после оплаты: slug → (имя файла на сервере, подпись на кнопке)
FILES = {
    'pitanie':  ('pitanie-bbd950b19a.pdf',  'Рацион питания.pdf'),
    'limfa':    ('limfa-1ccde28a31.pdf',    'Лимфодренажный протокол.pdf'),
    'tubazh':   ('tubazh-453dce99c7.pdf',   'Тюбажная система очищения.pdf'),
    'parazity': ('parazity-273857cc4f.pdf', 'Антипаразитарная чистка.pdf'),
    'kurs':     ('kurs-4a807ab6af.pdf',     'Курс по восстановлению ЖКТ.pdf'),
}
# Видео-уроки (самомассаж): список файлов на сервере
VIDEO = {
    'zhivot': ['zhivot-d7c9b54e7d-1.mp4', 'zhivot-d7c9b54e7d-2.mp4', 'zhivot-d7c9b54e7d-3.mp4'],
}

# Ссылки оплаты (Робокасса). Пока пусто — кнопки ведут в мессенджеры.
# Как появятся: вписать сюда slug → ссылка, и весь сайт переключится на приём оплаты.
PAY = {
    'pitanie':  'https://auth.robokassa.ru/merchant/Invoice/2J9VSNT9CE6POkJxStvqiw',   # 1 490 ₽
    'zhivot':   'https://auth.robokassa.ru/merchant/Invoice/ArGfVT6YP0KqyR8F99BW9g',   # 1 990 ₽
    'limfa':    'https://auth.robokassa.ru/merchant/Invoice/Gj_YCTnIeU-IJ3rEtyz5Fw',   # 990 ₽
    'tubazh':   'https://auth.robokassa.ru/merchant/Invoice/9Tjr0hDC9kaYpHR1nNzioA',   # 2 490 ₽
    'parazity': 'https://auth.robokassa.ru/merchant/Invoice/1rl1QT-KTUqJh5dhqa4dEw',   # 2 990 ₽
    'kurs':     'https://auth.robokassa.ru/merchant/Invoice/dLvfBpnLbE2y-nJbyE6qXA',   # 14 990 ₽
}

def wa(text):
    return 'https://wa.me/%s?text=%s' % (PHONE_RAW, urllib.parse.quote(text))

WA_BOOK = wa('Здравствуйте, Андрей! Хочу записаться на приём.')
WA_ONLINE = wa('Здравствуйте, Андрей! Хочу записаться на онлайн-консультацию (60 минут, 5000 ₽).')

# ---------------------------------------------------------------- продукты
GUIDES = [
    dict(slug='pitanie', word='ПИТАНИЕ', step=1,
         title='Рацион питания',
         card='10 правил питания при проблемах с ЖКТ: как разгрузить пищеварение и вернуть лёгкость без диет.',
         lead='10 золотых правил питания, которые снимают нагрузку с ЖКТ и запускают восстановление — без жёстких диет и голодовок.',
         price=1490, img='work-1.jpg',
         meta='Методичка «Рацион питания» — 10 правил, которые разгружают ЖКТ и возвращают лёгкость. Автор — висцеральный терапевт Андрей Булатный.'),
    dict(slug='zhivot', word='ЖИВОТ', step=2,
         title='Самомассаж живота',
         card='Техника работы с животом своими руками: диафрагма, отток жёлчи, перистальтика, спокойные нервы.',
         lead='Освойте технику, которой я пользуюсь сам: руки или лопатка для самомассажа — всё, что нужно, чтобы поддерживать внутренние органы в тонусе.',
         price=1990, img='belly-1.jpg',
         meta='Методичка «Самомассаж живота» от висцерального терапевта: техника, которая улучшает отток жёлчи, перистальтику и снимает напряжение.'),
    dict(slug='limfa', word='ЛИМФА', step=3,
         title='Лимфодренажный протокол',
         card='30-дневная система против отёков и вздутия: нутрицевтики, ферменты, сорбенты и упражнения.',
         lead='30-дневная подготовительная система: мягкое очищение ЖКТ, восстановление оттока лимфы и снятие отёчности.',
         price=990, img='work-3.jpg',
         meta='Лимфодренажный протокол — 30-дневная система против отёков, вздутия и застоя лимфы. Пошаговая методичка.'),
    dict(slug='tubazh', word='ТЮБАЖ', step=4,
         title='Тюбажная система очищения',
         card='Домашнее очищение печени и жёлчного пузыря: три вида тюбажей и работа с блуждающим нервом.',
         lead='Проверенная десятилетиями методика: мягко сбросить застойную жёлчь и запустить самоочищение организма — в домашних условиях.',
         price=2490, img='belly-2.jpg',
         meta='Тюбажная система очищения печени и жёлчного пузыря: три вида тюбажей, дыхание и работа с вагусом. Методичка.'),
    dict(slug='parazity', word='ЧИСТКА', step=5,
         title='Антипаразитарная чистка',
         card='Безмедикаментозная программа на 2,5–3 месяца: биоплёнки, поэтапная санация, восстановление слизистых.',
         lead='Безопасная, физиологичная и полностью безмедикаментозная программа, построенная на природных механизмах самоочищения.',
         price=2990, img='belly-3.jpg',
         meta='Антипаразитарная чистка без химии: полный протокол на 2,5–3 месяца от висцерального терапевта Андрея Булатного.'),
]

KURS = dict(slug='kurs', word='КУРС', title='Курс по восстановлению ЖКТ',
            subtitle='«Курс Булатного»',
            card='Все пять методичек в одной системе + личное сопровождение в закрытом чате на все 3 месяца.',
            lead='Ваше практическое руководство к здоровью: все пять методичек, выстроенные в трёхмесячную систему, плюс моё личное сопровождение.',
            price=14990, img='neck.jpg',
            meta='«Курс Булатного» — трёхмесячная программа восстановления ЖКТ: питание, самомассаж, лимфа, тюбажи, антипаразитарная чистка + личное ведение.')

ONLINE = dict(slug='online', title='Онлайн-приём',
              lead='Полноценная 60-минутная консультация, которая даст вам столько же внимания и пользы, как очная встреча.',
              price=5000, img='portrait.jpg',
              meta='Онлайн-консультация висцерального терапевта Андрея Булатного: 60 минут, разбор состояния, персональный план восстановления. 5000 ₽.')

# ---------------------------------------------------------------- иконки
ICONS = {
 'arrow':   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>',
 'check':   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>',
 'phone':   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>',
 'pin':     '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>',
 'chat':    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/></svg>',
 'star':    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M11.5 1.9 14.4 8l6.6.8-4.9 4.5 1.3 6.5-5.9-3.3-5.9 3.3 1.3-6.5L2 8.8 8.6 8z"/></svg>',
 'gift':    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="8" width="18" height="4" rx="1"/><path d="M12 8v13"/><path d="M19 12v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-7"/><path d="M7.5 8a2.5 2.5 0 0 1 0-5C11 3 12 8 12 8s1-5 4.5-5a2.5 2.5 0 0 1 0 5"/></svg>',
 'clock':   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>',
 'leaf':    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>',
 'hands':   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 12.5V10a2 2 0 0 0-2-2 2 2 0 0 0-2 2v1.4"/><path d="M14 11V9a2 2 0 1 0-4 0v2"/><path d="M10 10.5V5a2 2 0 1 0-4 0v9"/><path d="m7 15-1.76-1.76a2 2 0 0 0-2.83 2.82l3.6 3.6C7.5 21.14 9.2 22 12 22h2a8 8 0 0 0 8-8V7a2 2 0 1 0-4 0v5"/></svg>',
 'drop':    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/></svg>',
 'activity':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/></svg>',
 'flame':   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>',
 'sun':     '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>',
 'moon':    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>',
 'tg':      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14.5 21.5 11 14l-7.5-3.5L21.5 3.5z"/><path d="M11 14 21.5 3.5"/></svg>',
 'card':    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/></svg>',
 'download':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/></svg>',
}

# favicon: docs/img/favicon.png (знак на шоколадном фоне)

# ---------------------------------------------------------------- каркас
def nav_links(root):
    return [
        ('%s#guides' % root, 'Методички'),
        ('%skurs/' % root, 'Курс'),
        ('%sonline/' % root, 'Онлайн-приём'),
        ('%s#about' % root, 'Обо мне'),
        ('%s#price' % root, 'Прайс'),
        ('%s#contacts' % root, 'Контакты'),
    ]

def header(root):
    links = ''.join('<a href="%s">%s</a>' % (h, t) for h, t in nav_links(root))
    mob = ''.join('<a href="%s">%s</a>' % (h, t) for h, t in nav_links(root))
    mob_guides = ''.join('<a href="%s%s/">%s · %s ₽</a>' % (root, g['slug'], g['title'], fmt(g['price'])) for g in GUIDES)
    return f'''
<header class="site-header">
  <div class="bar">
    <a class="brand" href="{root}">
      <img class="b-mark" src="{root}img/logo-mark.png" alt="" width="416" height="512">
      <span class="b-text">
        <span class="b-name">Клуб восстановления</span>
        <span class="b-sub">Андрея Булатного</span>
      </span>
    </a>
    <nav class="nav-desktop" aria-label="Основное меню">
      {links}
      <a class="nav-cta" href="{WA_BOOK}" target="_blank" rel="noopener">Записаться</a>
    </nav>
    <button class="theme-btn" aria-label="Переключить тему">
      <span class="ic-moon">{ICONS['moon']}</span>
      <span class="ic-sun">{ICONS['sun']}</span>
    </button>
    <button class="burger" aria-label="Открыть меню" aria-expanded="false">
      <svg class="ic-burger" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 7h16"/><path d="M4 12h16"/><path d="M4 17h16"/></svg>
      <svg class="ic-close" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="m6 6 12 12"/><path d="m18 6-12 12"/></svg>
    </button>
  </div>
</header>
<div class="mobile-menu">
  <nav aria-label="Мобильное меню">
    <p class="mm-label">Навигация</p>
    {mob}
    <p class="mm-label">Методички</p>
    {mob_guides}
  </nav>
  <div class="mm-contact">
    <a class="btn btn-gold" href="{WA_BOOK}" target="_blank" rel="noopener">{ICONS['chat']} Записаться в WhatsApp</a>
    <a class="btn btn-dark-outline" href="{TG}" target="_blank" rel="noopener">{ICONS['tg']} Написать в Telegram</a>
    <a class="btn btn-dark-outline" href="tel:+{PHONE_RAW}">{ICONS['phone']} {PHONE_PRETTY}</a>
  </div>
</div>'''

def footer(root):
    guides = ''.join('<li><a href="%s%s/">%s</a></li>' % (root, g['slug'], g['title']) for g in GUIDES)
    return f'''
<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div class="footer-brand">
        <p class="b-name">Андрей Булатный</p>
      </div>
      <div>
        <h4>Методички</h4>
        <ul>
          {guides}
          <li><a href="{root}kurs/">Курс по восстановлению ЖКТ</a></li>
        </ul>
      </div>
      <div>
        <h4>Контакты</h4>
        <ul>
          <li><a href="tel:+{PHONE_RAW}">{PHONE_PRETTY}</a></li>
          <li><a href="{WA_BOOK}" target="_blank" rel="noopener">WhatsApp</a></li>
          <li><a href="{TG}" target="_blank" rel="noopener">Telegram</a></li>
          <li>Москва, м.&nbsp;Таганская,<br>ул.&nbsp;Б.&nbsp;Каменщики,&nbsp;д.&nbsp;1</li>
          <li>г.&nbsp;Дзержинский,<br>ул.&nbsp;Лесная,&nbsp;д.&nbsp;11</li>
        </ul>
      </div>
    </div>
    <div class="footer-legal">
      <p>ИП {FIO} · ИНН {INN} · ОГРНИП {OGRNIP} · <a href="{root}oferta/">Публичная оферта</a> · <a href="{root}privacy/">Политика обработки персональных данных</a></p>
      <p>Информация на сайте носит ознакомительный характер, не является медицинской услугой, публичной офертой о медицинской помощи или заменой консультации врача. Имеются противопоказания — при хронических заболеваниях проконсультируйтесь со специалистом.</p>
    </div>
  </div>
</footer>
<script src="{root}js/main.js?v={_v('js/main.js')}" defer></script>'''

def page(root, title, meta, body, og_img=None, lenis=False, canon=''):
    lenis_tag = ''
    og = f'<meta property="og:image" content="{SITE}/{canon}img/{og_img}">' if og_img else ''
    canonical = f'<link rel="canonical" href="{SITE}/{canon}">'
    return f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{meta}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{meta}">
<meta name="theme-color" content="#241812">
{canonical}
<meta property="og:url" content="{SITE}/{canon}">
{og}
<link rel="icon" type="image/png" href="{root}img/favicon.png">
<script>(function(){{try{{if(localStorage.getItem('theme')==='dark')document.documentElement.dataset.theme='dark'}}catch(e){{}}}})()</script>
<link rel="stylesheet" href="{root}css/fonts.css?v={_v('css/fonts.css')}">
<link rel="stylesheet" href="{root}css/base.css?v={_v('css/base.css')}">
{lenis_tag}
</head>
<body>
{header(root)}
{body}
{footer(root)}
</body>
</html>'''

def fmt(n):
    return '{:,}'.format(n).replace(',', ' ')

def read(name):
    with open(os.path.join(CONTENT, name), encoding='utf-8') as f:
        return f.read()

def render_tokens(html, root):
    html = html.replace('{ROOT}', root).replace('{PHONE_PRETTY}', PHONE_PRETTY).replace('{PHONE_RAW}', PHONE_RAW)
    html = html.replace('{WA_BOOK}', WA_BOOK).replace('{WA_ONLINE}', WA_ONLINE).replace('{TG}', TG)
    html = html.replace('{PAY_KURS}', PAY.get('kurs', WA_BOOK))
    for k, svg in ICONS.items():
        html = html.replace('{icon:%s}' % k, svg)
    return html

# ---------------------------------------------------------------- сборка
def buy_buttons(g, dark=True):
    """Одна кнопка оплаты, если подключена касса; иначе — мессенджеры."""
    pay = PAY.get(g['slug'])
    wa_url = wa('Здравствуйте, Андрей! Хочу приобрести методичку «%s» (%s ₽).' % (g['title'], fmt(g['price'])))
    alt = 'btn-dark-outline' if dark else 'btn-outline'
    if pay:
        return f'''<div class="g-buy-btns">
              <a class="btn btn-gold" href="{pay}" target="_blank" rel="noopener">{ICONS['card']} Оплатить {fmt(g['price'])} ₽</a>
              <a class="btn {alt}" href="{TG}" target="_blank" rel="noopener">{ICONS['tg']} Задать вопрос</a>
            </div>'''
    return f'''<div class="g-buy-btns">
              <a class="btn btn-gold" href="{wa_url}" target="_blank" rel="noopener">{ICONS['chat']} Купить в WhatsApp</a>
              <a class="btn {alt}" href="{TG}" target="_blank" rel="noopener">{ICONS['tg']} Купить в Telegram</a>
            </div>'''

def buy_note(g):
    if PAY.get(g['slug']):
        return 'Оплата картой или через СБП. Сразу после оплаты файл придёт вам на почту, чек — автоматически.'
    return 'Напишете в удобный мессенджер — я отвечу лично, пришлю реквизиты и сразу после оплаты отправлю материал.'

def also_read(g):
    """Перелинковка: три соседние темы под статьёй."""
    others = [x for x in GUIDES if x['slug'] != g['slug']][:3]
    cards = ''.join(f'''
      <article class="guide-card reveal">
        <div class="g-img"><span class="g-step">Шаг {o['step']}</span><img src="../img/{o['img']}" alt="{o['title']}" loading="lazy"></div>
        <div class="g-body">
          <h3><a href="../{o['slug']}/">{o['title']}</a></h3>
          <p class="g-desc">{o['card']}</p>
          <div class="g-foot"><span class="g-price">{fmt(o['price'])} ₽</span><span class="g-more">Читать {ICONS['arrow']}</span></div>
        </div>
      </article>''' for o in others)
    return f'''
<section class="section section-soft">
  <div class="wrap">
    <div class="s-head reveal">
      <p class="eyebrow">Другие темы</p>
      <h2>Читайте дальше</h2>
      <p class="s-sub">Все методички собраны в одну систему — начните с той темы, которая ближе.</p>
    </div>
    <div class="guides-grid">{cards}</div>
    <div style="margin-top:26px" class="reveal">
      <a class="btn btn-outline" href="../kurs/">Смотреть полный курс {ICONS['arrow']}</a>
    </div>
  </div>
</section>'''

def guide_page(g, extra_result_html='', article_html=''):
    root = '../'
    wa_url = wa('Здравствуйте, Андрей! Хочу приобрести методичку «%s» (%s ₽).' % (g['title'], fmt(g['price'])))
    body = f'''
<main>
  <section class="g-hero">
    <div class="wrap">
      <nav class="crumbs" aria-label="Хлебные крошки"><a href="../">Главная</a><span>/</span><a href="../#guides">Методички</a><span>/</span>{g['title']}</nav>
      <div class="g-hero-grid">
        <div>
          <p class="eyebrow">Методичка · шаг {g['step']} из 5</p>
          <h1>{g['title']}</h1>
          <p class="lead">{g['lead']}</p>
          <div class="g-buy">
            <p class="g-price-big">{fmt(g['price'])} ₽ <small>единоразово, материал остаётся у вас</small></p>
            {buy_buttons(g)}
          </div>
          <p class="btn-note" style="color:rgba(240,231,212,.55)">{buy_note(g)}</p>
        </div>
        <div class="g-hero-photo"><img src="../img/{g['img']}" alt="{g['title']} — Андрей Булатный" width="1200" height="1600"></div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="article">
      {article_html}
      </div>
      {extra_result_html}
      <div class="buy-block reveal">
        <div>
          <h2>Готовы забрать «{g['title']}»?</h2>
          <p>Напишите мне в WhatsApp — отвечу лично и после оплаты сразу пришлю методичку. Останетесь с вопросами — помогу разобраться.</p>
        </div>
        <div class="bb-side">
          <p class="bb-price">{fmt(g['price'])} ₽</p>
          {buy_buttons(g)}
        </div>
      </div>
    </div>
  </section>
  {also_read(g)}
</main>
<div class="sticky-buy">
  <p class="sb-price">{fmt(g['price'])} ₽</p>
  <a class="sb-tg" href="{TG}" target="_blank" rel="noopener" aria-label="Написать в Telegram">{ICONS['tg']}</a>
  <a class="btn btn-gold" href="{PAY.get(g['slug']) or wa_url}" target="_blank" rel="noopener">Купить</a>
</div>'''
    return page(root, '%s — %s ₽ · %s' % (g['title'], fmt(g['price']), BRAND), g['meta'], body,
                og_img=g['img'], canon='%s/' % g['slug'])


def thanks_page(item):
    """Страница выдачи после оплаты — своя на каждый товар."""
    slug, title, price = item['slug'], item['title'], fmt(item['price'])
    root = '../../'
    if slug in VIDEO:
        vids = ''.join(f'''
            <a class="btn btn-gold" href="{root}files/{v}" download style="margin:0 0 12px">
              {ICONS['download']} Скачать урок {i}
            </a>''' for i, v in enumerate(VIDEO[slug], 1))
        block = f'''<div class="g-buy-btns" style="flex-direction:column;align-items:stretch;max-width:420px;margin:0 auto">{vids}</div>
          <p class="btn-note" style="color:rgba(240,231,212,.55);text-align:center">Три видеоурока. Можно смотреть онлайн или сохранить на телефон.</p>'''
    else:
        fname, human = FILES[slug]
        block = f'''<div class="g-buy-btns" style="justify-content:center">
            <a class="btn btn-gold" href="{root}files/{fname}" download="{human}">{ICONS['download']} Скачать методичку</a>
          </div>
          <p class="btn-note" style="color:rgba(240,231,212,.55);text-align:center">Файл PDF — откроется на телефоне и на компьютере. Сохраните его себе.</p>'''

    body = f'''
<main>
  <section class="g-hero">
    <div class="wrap">
      <div style="max-width:640px;margin:0 auto;text-align:center">
        <p class="eyebrow" style="justify-content:center">Оплата прошла</p>
        <h1 style="margin:16px 0 14px">Спасибо! Материал ваш</h1>
        <p class="lead" style="margin:0 auto 26px">«{title}» — {price} ₽. Забирайте файл, он остаётся у вас навсегда.</p>
        {block}
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="article" style="margin:0 auto">
        <h2>С чего начать</h2>
        <ol>
          <li><b>Прочитайте целиком</b>, не начиная действовать — сначала общая картина, потом практика.</li>
          <li><b>Подготовьте всё необходимое</b> по списку из материала.</li>
          <li><b>Выберите дату старта</b> и освободите этот день от лишних дел.</li>
          <li><b>Задавайте вопросы</b> — я на связи и помогу разобраться.</li>
        </ol>
        <div class="note">Файл не скачался или открылся с ошибкой? Напишите мне в <a href="{TG}">Telegram</a> или <a href="{WA_BOOK}">WhatsApp</a> — отправлю лично.</div>
      </div>
      <div class="buy-block reveal">
        <div>
          <h2>Нужен разбор вашего случая?</h2>
          <p>60 минут онлайн: разберём состояние, найдём первопричину и составим персональный план.</p>
        </div>
        <div class="bb-side">
          <p class="bb-price">5 000 ₽</p>
          <a class="btn btn-gold" href="{root}online/">{ICONS['arrow']} Об онлайн-приёме</a>
        </div>
      </div>
    </div>
  </section>
</main>'''
    return page(root, 'Спасибо за покупку — %s · %s' % (title, BRAND),
                'Материал «%s» готов к скачиванию.' % title, body,
                lenis=False, canon='spasibo/%s/' % slug)

def build():
    pages = {}

    # главная
    pages['index.html'] = page('', '%s — программы восстановления, массаж и методички' % BRAND_FULL,
        'Восстановительный массаж, висцеральная терапия, гирудотерапия и авторские методички по восстановлению ЖКТ. Москва, м. Таганская. Онлайн-приёмы.',
        render_tokens(read('index.html'), ''), og_img='hero.jpg', canon='')

    # методички
    for g in GUIDES:
        raw = read('%s.html' % g['slug'])
        parts = raw.split('<!--RESULTS-->')
        article = render_tokens(parts[0], '../')
        results = render_tokens(parts[1], '../') if len(parts) > 1 else ''
        pages['%s/index.html' % g['slug']] = guide_page(g, results, article)

    # курс и онлайн — свои фрагменты целиком
    pages['kurs/index.html'] = page('../',
        '%s — %s ₽ · %s' % (KURS['title'], fmt(KURS['price']), BRAND), KURS['meta'],
        render_tokens(read('kurs.html'), '../'), og_img=KURS['img'], canon='kurs/')
    pages['online/index.html'] = page('../',
        'Онлайн-приём — 60 минут, %s ₽ · %s' % (fmt(ONLINE['price']), BRAND), ONLINE['meta'],
        render_tokens(read('online.html'), '../'), og_img=ONLINE['img'], canon='online/')

    # персональные страницы выдачи: /spasibo/<товар>/
    for g in GUIDES + [KURS]:
        pages['spasibo/%s/index.html' % g['slug']] = thanks_page(g)

    # страница после оплаты (Success URL кассы)
    pages['spasibo/index.html'] = page('../', 'Спасибо за покупку · %s' % BRAND,
        'Оплата прошла успешно. Материал отправлен на вашу почту.',
        render_tokens(read('spasibo.html'), '../'), lenis=False, canon='spasibo/')

    # юридические
    pages['oferta/index.html'] = page('../', 'Публичная оферта · %s' % BRAND,
        'Условия приобретения информационных материалов.', render_tokens(read('oferta.html'), '../'), lenis=False, canon='oferta/')
    pages['privacy/index.html'] = page('../', 'Политика обработки персональных данных · %s' % BRAND,
        'Как обрабатываются персональные данные покупателей.', render_tokens(read('privacy.html'), '../'), lenis=False, canon='privacy/')

    for rel, html in pages.items():
        path = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        print('built', rel)

if __name__ == '__main__':
    build()
