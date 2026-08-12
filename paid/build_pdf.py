#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Платные методички: docx клиента → брендированный PDF (светлая блочная вёрстка, A5).
Запуск: python3 paid/build_pdf.py [slug ...]   → paid/dist/*.pdf
Контент клиента по существу не меняется — только структура и оформление."""

import os, re, sys, zipfile
import xml.etree.ElementTree as ET

from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                HRFlowable, NextPageTemplate, PageBreak, KeepTogether,
                                CondPageBreak, Flowable)
from reportlab.platypus.flowables import _listWrapOn

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'assets-src', 'paid')
OUT = os.path.join(ROOT, 'paid', 'dist')
FDIR = os.path.join(ROOT, 'paid', 'fonts')
LOGO = os.path.join(ROOT, 'docs', 'img', 'logo-mark.png')

# ---------------------------------------------------------------- палитра (светлая, тёплая)
BG_TOP, BG_BOT = HexColor('#FBF7EE'), HexColor('#F4EDE0')   # бежевый ближе к белому
CARD = HexColor('#FFFCF5')
CARD_HI = HexColor('#F6EFE0')
HAIR = HexColor('#E3D8C2')
GOLD = HexColor('#B08E4A')          # линии, рамки, иконки
GOLD_HI = HexColor('#8A6A2E')       # золото в тексте — контраст 4.6:1 на светлом
GOLD_DIM = HexColor('#C3A76F')      # приглушённое золото для акцентных иконок
TXT = HexColor('#2A211A')
TXT_MUTED = HexColor('#6B5E4D')
DARK_ON_GOLD = HexColor('#221507')

W_PAGE, H_PAGE = A5                  # мельче формат → крупнее текст на экране телефона
MARGIN = 13 * mm
CONTENT_W = W_PAGE - 2 * MARGIN
RADIUS = 3.2 * mm

DOCS = {
    'pitanie':  dict(title='Рацион питания', sub='Золотые правила здорового пищеварения'),
    'limfa':    dict(title='Лимфодренажный протокол', sub='30-дневная система очищения и снятия отёчности'),
    'tubazh':   dict(title='Тюбажная система очищения', sub='Три вида тюбажей для печени и жёлчного пузыря'),
    'parazity': dict(title='Антипаразитарная чистка', sub='Безмедикаментозная программа на 2,5–3 месяца'),
    'kurs':     dict(title='Курс по восстановлению ЖКТ', sub='Полная система: питание · самомассаж · лимфа · тюбажи · чистка'),
}

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}
BULLET_RE = re.compile(r'^[\s]*[●•▪❖◦‣·]\s*|^[\s]*[-–—]\s+')

for name, fn in [('Cormorant-SB', 'Cormorant-600.ttf'), ('Cormorant-B', 'Cormorant-700.ttf'),
                 ('Mont', 'Montserrat-400.ttf'), ('Mont-M', 'Montserrat-500.ttf'),
                 ('Mont-SB', 'Montserrat-600.ttf')]:
    pdfmetrics.registerFont(TTFont(name, os.path.join(FDIR, fn)))

def num_centered(c, text, cx, cy, size, color=GOLD_HI, font='Mont-SB'):
    """Цифры по центру бейджа: Montserrat даёт ровные lining-цифры без свесов."""
    c.setFont(font, size); c.setFillColor(color)
    c.drawCentredString(cx, cy - size * 0.70 / 2, text)

# ---------------------------------------------------------------- стили
# A5 + крупный кегль: на телефоне текст вдвое крупнее прежнего A4-варианта
S_H2 = ParagraphStyle('h2', fontName='Cormorant-B', fontSize=20, leading=23, textColor=TXT)
S_H3 = ParagraphStyle('h3', fontName='Mont-SB', fontSize=12, leading=17, textColor=GOLD_HI,
                      spaceBefore=3 * mm, spaceAfter=2 * mm)
S_NUM = ParagraphStyle('num', fontName='Cormorant-B', fontSize=34, leading=34, textColor=GOLD_DIM)
S_P = ParagraphStyle('p', fontName='Mont', fontSize=11.5, leading=18.5, textColor=TXT,
                     spaceAfter=3.4 * mm)
S_LI = ParagraphStyle('li', parent=S_P, fontSize=11, leading=17, leftIndent=5.5 * mm,
                      bulletIndent=0, bulletFontName='Mont-SB', bulletFontSize=9.5,
                      bulletColor=GOLD, spaceAfter=2.2 * mm)
S_LI_PLAIN = ParagraphStyle('lip', parent=S_LI, spaceAfter=2.6 * mm, fontSize=11.5, leading=18)
S_CARD_H = ParagraphStyle('ch', fontName='Mont-SB', fontSize=9.2, leading=13, textColor=GOLD_HI)
S_TAIL = ParagraphStyle('tail', fontName='Mont', fontSize=10.5, leading=16, textColor=TXT_MUTED)
S_QUOTE = ParagraphStyle('q', fontName='Cormorant-B', fontSize=16, leading=20, textColor=DARK_ON_GOLD)
S_NOTE = ParagraphStyle('note', fontName='Mont-M', fontSize=11.2, leading=17.5, textColor=TXT)
S_TOC = ParagraphStyle('toc', fontName='Mont-M', fontSize=11, leading=15.5, textColor=TXT)
S_TOC_N = ParagraphStyle('tocn', fontName='Cormorant-B', fontSize=17, leading=18, textColor=GOLD)
S_COVER_H = ParagraphStyle('ch1', fontName='Cormorant-B', fontSize=27, leading=31,
                           textColor=TXT, alignment=TA_CENTER)
S_COVER_SUB = ParagraphStyle('csub', fontName='Mont', fontSize=10.5, leading=16,
                             textColor=TXT_MUTED, alignment=TA_CENTER)
S_FIN = ParagraphStyle('fin', parent=S_P, alignment=TA_CENTER, spaceAfter=2 * mm)
S_LEGAL = ParagraphStyle('legal', fontName='Mont', fontSize=8.2, leading=13,
                         textColor=TXT_MUTED, alignment=TA_CENTER)

def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def track_w(text, font, size, space):
    return pdfmetrics.stringWidth(text, font, size) + space * (len(text) - 1)

def track(cv, text, x, y, font, size, color, space, center=False):
    """Текст в разрядку (для меток капсом)."""
    cv.setFont(font, size); cv.setFillColor(color)
    w = track_w(text, font, size, space)
    t = cv.beginText(); t.setCharSpace(space)
    t.setTextOrigin(x - w / 2 if center else x, y)
    t.textOut(text)
    cv.drawText(t)
    return w

# ---------------------------------------------------------------- блоки
class Card(Flowable):
    """Скруглённая карточка с вложенными flowable'ами."""
    def __init__(self, flows, width=CONTENT_W, bg=CARD, border=HAIR, radius=RADIUS,
                 pad=(5 * mm, 5.5 * mm, 4.5 * mm, 5.5 * mm), bar=None, cols=1, gap=5 * mm):
        Flowable.__init__(self)
        self.flows, self.width, self.bg, self.border = flows, width, bg, border
        self.radius, self.pad, self.bar, self.cols, self.gap = radius, pad, bar, cols, gap

    def _split_cols(self, inner):
        if self.cols == 1:
            return [(self.flows, inner)]
        cw = (inner - self.gap * (self.cols - 1)) / self.cols
        n = (len(self.flows) + self.cols - 1) // self.cols
        return [(self.flows[i * n:(i + 1) * n], cw) for i in range(self.cols)]

    def wrap(self, aw, ah):
        inner = self.width - self.pad[1] - self.pad[3]
        heights = []
        for flows, w in self._split_cols(inner):
            # считаем ровно так же, как рисуем в draw(), иначе карточка «недозаполнена»
            heights.append(sum(f.wrap(w, ah)[1] for f in flows))
        self.height = max(heights or [0]) + self.pad[0] + self.pad[2]
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        if self.bg or self.border:
            if self.bg:
                c.setFillColor(self.bg)
            if self.border:
                c.setStrokeColor(self.border); c.setLineWidth(0.6)
            c.roundRect(0, 0, self.width, self.height, self.radius,
                        stroke=1 if self.border else 0, fill=1 if self.bg else 0)
        if self.bar:
            c.setFillColor(self.bar)
            c.roundRect(0, 0, 2.4 * mm, self.height, 1.2 * mm, stroke=0, fill=1)
            c.rect(1.2 * mm, 0, 1.2 * mm, self.height, stroke=0, fill=1)
        c.restoreState()
        inner = self.width - self.pad[1] - self.pad[3]
        x = self.pad[3]
        for flows, cw in self._split_cols(inner):
            y = self.height - self.pad[0]
            for f in flows:
                fw, fh = f.wrap(cw, y)
                y -= fh
                f.drawOn(c, x, y)
            x += cw + self.gap

class GoldQuote(Flowable):
    """Золотая плашка с тёмным текстом — акцентный блок."""
    def __init__(self, text, width=CONTENT_W):
        Flowable.__init__(self)
        self.width = width
        self.par = Paragraph('«%s»' % esc(text.rstrip('.')), S_QUOTE)

    def wrap(self, aw, ah):
        pw, ph = self.par.wrap(self.width - 22 * mm, ah)
        self.height = ph + 11 * mm
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(GOLD)
        c.roundRect(0, 0, self.width, self.height, RADIUS, stroke=0, fill=1)
        c.setFillColor(HexColor('#B08E4A'))
        c.setFont('Cormorant-B', 40)
        c.drawString(6 * mm, self.height - 13 * mm, '”')
        c.restoreState()
        self.par.drawOn(c, 15 * mm, 5.5 * mm)

class SectionHead(Flowable):
    """Бейдж с номером + заголовок секции + тематическая иконка справа."""
    BADGE = 11 * mm

    def __init__(self, num, title, width=CONTENT_W):
        Flowable.__init__(self)
        self.width, self.num = width, num
        self.icon = pick_icon(title)
        self.par = Paragraph(esc(title), S_H2)

    def wrap(self, aw, ah):
        pw, ph = self.par.wrap(self.width - 18 * mm - (13 * mm if self.icon else 0), ah)
        self.ph = ph
        self.height = max(ph, self.BADGE) + 8 * mm
        return self.width, self.height

    def draw(self):
        c = self.canv
        top = self.height - 2 * mm
        badge_mid = top - self.BADGE / 2
        c.saveState()
        c.setStrokeColor(GOLD); c.setLineWidth(0.8)
        c.setFillColor(CARD)
        c.roundRect(0, top - self.BADGE, 13 * mm, self.BADGE, 2.2 * mm, stroke=1, fill=1)
        num_centered(c, '%02d' % self.num, 6.5 * mm, badge_mid, 11)
        if self.icon:
            draw_icon(c, self.icon, self.width - 10 * mm, badge_mid - 5 * mm, 10 * mm, GOLD_DIM)
        c.restoreState()
        # одна строка — центрируем по бейджу, многострочный — прижимаем к верху бейджа
        y = (badge_mid - self.ph / 2 + 0.6 * mm) if self.ph <= self.BADGE else (top - self.ph)
        self.par.drawOn(c, 18 * mm, y)

# ---------------------------------------------------------------- иконки
def _circle_dots(c, s, n=3):
    import math
    c.circle(s * .5, s * .5, s * .3, stroke=1, fill=0)
    for k in range(n):
        a = math.pi * 2 * k / n + .4
        c.circle(s * .5 + math.cos(a) * s * .13, s * .5 + math.sin(a) * s * .13, s * .045, stroke=0, fill=1)

def draw_icon(c, name, x, y, s, color=GOLD):
    """Мини-иконки линиями — в стиле логотипа, без растровых картинок."""
    c.saveState()
    c.translate(x, y)
    c.setStrokeColor(color); c.setFillColor(color)
    c.setLineWidth(s * .055); c.setLineCap(1); c.setLineJoin(1)
    if name == 'drop':
        p = c.beginPath(); p.moveTo(s * .5, s * .88)
        p.curveTo(s * .82, s * .55, s * .8, s * .28, s * .5, s * .12)
        p.curveTo(s * .2, s * .28, s * .18, s * .55, s * .5, s * .88)
        c.drawPath(p, stroke=1, fill=0)
    elif name == 'leaf':
        p = c.beginPath(); p.moveTo(s * .16, s * .18)
        p.curveTo(s * .2, s * .8, s * .6, s * .92, s * .86, s * .84)
        p.curveTo(s * .9, s * .5, s * .68, s * .2, s * .16, s * .18)
        c.drawPath(p, stroke=1, fill=0)
        c.line(s * .24, s * .26, s * .74, s * .74)
    elif name == 'flame':
        p = c.beginPath(); p.moveTo(s * .5, s * .94)
        p.curveTo(s * .78, s * .7, s * .8, s * .46, s * .62, s * .24)
        p.curveTo(s * .62, s * .4, s * .54, s * .46, s * .48, s * .42)
        p.curveTo(s * .5, s * .26, s * .42, s * .16, s * .34, s * .1)
        p.curveTo(s * .36, s * .34, s * .2, s * .44, s * .22, s * .62)
        p.curveTo(s * .24, s * .78, s * .36, s * .88, s * .5, s * .94)
        c.drawPath(p, stroke=1, fill=0)
    elif name == 'clock':
        c.circle(s * .5, s * .5, s * .36, stroke=1, fill=0)
        c.line(s * .5, s * .5, s * .5, s * .72); c.line(s * .5, s * .5, s * .66, s * .44)
    elif name == 'moon':
        p = c.beginPath(); p.moveTo(s * .68, s * .18)
        p.curveTo(s * .3, s * .22, s * .22, s * .74, s * .66, s * .86)
        p.curveTo(s * .38, s * .68, s * .4, s * .34, s * .68, s * .18)
        c.drawPath(p, stroke=1, fill=1)
    elif name == 'sun':
        import math
        c.circle(s * .5, s * .5, s * .2, stroke=1, fill=0)
        for k in range(8):
            a = math.pi * 2 * k / 8
            c.line(s * .5 + math.cos(a) * s * .29, s * .5 + math.sin(a) * s * .29,
                   s * .5 + math.cos(a) * s * .38, s * .5 + math.sin(a) * s * .38)
    elif name == 'activity':
        p = c.beginPath(); p.moveTo(s * .1, s * .5); p.lineTo(s * .3, s * .5)
        p.lineTo(s * .42, s * .78); p.lineTo(s * .6, s * .2); p.lineTo(s * .7, s * .5)
        p.lineTo(s * .9, s * .5)
        c.drawPath(p, stroke=1, fill=0)
    elif name == 'shield':
        p = c.beginPath(); p.moveTo(s * .5, s * .9); p.lineTo(s * .84, s * .72)
        p.lineTo(s * .84, s * .3); p.lineTo(s * .5, s * .12); p.lineTo(s * .16, s * .3)
        p.lineTo(s * .16, s * .72); p.close()
        c.drawPath(p, stroke=1, fill=0)
    elif name == 'bug':
        _circle_dots(c, s, 4)
    elif name == 'fish':
        p = c.beginPath(); p.moveTo(s * .18, s * .5)
        p.curveTo(s * .38, s * .78, s * .62, s * .78, s * .74, s * .5)
        p.curveTo(s * .62, s * .22, s * .38, s * .22, s * .18, s * .5)
        c.drawPath(p, stroke=1, fill=0)
        p = c.beginPath(); p.moveTo(s * .74, s * .5); p.lineTo(s * .9, s * .66)
        p.lineTo(s * .9, s * .34); p.close()
        c.drawPath(p, stroke=1, fill=0)
        c.circle(s * .3, s * .53, s * .022, stroke=0, fill=1)
    elif name == 'meat':                      # стейк с косточкой
        c.saveState(); c.translate(s * .46, s * .46); c.rotate(-15)
        c.roundRect(-s * .3, -s * .22, s * .6, s * .44, s * .18, stroke=1, fill=0)
        c.restoreState()
        c.line(s * .68, s * .66, s * .82, s * .8)
        c.circle(s * .85, s * .84, s * .075, stroke=1, fill=0)
    elif name == 'plate':
        c.circle(s * .5, s * .5, s * .36, stroke=1, fill=0)
        c.circle(s * .5, s * .5, s * .2, stroke=1, fill=0)
    elif name == 'pill':
        c.roundRect(s * .16, s * .36, s * .68, s * .28, s * .14, stroke=1, fill=0)
        c.line(s * .5, s * .36, s * .5, s * .64)
    elif name == 'home':
        p = c.beginPath(); p.moveTo(s * .12, s * .48); p.lineTo(s * .5, s * .86)
        p.lineTo(s * .88, s * .48)
        c.drawPath(p, stroke=1, fill=0)
        c.rect(s * .24, s * .16, s * .52, s * .34, stroke=1, fill=0)
    elif name == 'paw':
        for dx, dy, r in ((.3, .68, .1), (.5, .76, .1), (.7, .68, .1)):
            c.circle(s * dx, s * dy, s * r, stroke=0, fill=1)
        c.circle(s * .5, s * .38, s * .19, stroke=0, fill=1)
    elif name == 'plane':
        p = c.beginPath(); p.moveTo(s * .1, s * .46); p.lineTo(s * .9, s * .2)
        p.lineTo(s * .62, s * .82); p.lineTo(s * .5, s * .5); p.close()
        c.drawPath(p, stroke=1, fill=0)
    elif name == 'cloud':
        c.circle(s * .36, s * .5, s * .18, stroke=1, fill=0)
        c.circle(s * .58, s * .56, s * .22, stroke=1, fill=0)
        c.line(s * .2, s * .34, s * .8, s * .34)
    elif name == 'hands':                     # контакт с людьми
        c.circle(s * .33, s * .68, s * .13, stroke=1, fill=0)
        c.circle(s * .67, s * .68, s * .13, stroke=1, fill=0)
        c.arc(s * .12, s * .1, s * .54, s * .58, 20, 140)
        c.arc(s * .46, s * .1, s * .88, s * .58, 20, 140)
    elif name == 'liver':                     # печень
        p = c.beginPath(); p.moveTo(s * .1, s * .66)
        p.curveTo(s * .34, s * .82, s * .7, s * .82, s * .9, s * .66)
        p.curveTo(s * .88, s * .38, s * .66, s * .18, s * .42, s * .22)
        p.curveTo(s * .2, s * .26, s * .1, s * .46, s * .1, s * .66)
        p.close()
        c.drawPath(p, stroke=1, fill=0)
        c.line(s * .5, s * .76, s * .5, s * .24)
        c.line(s * .5, s * .5, s * .68, s * .44)
    elif name == 'stomach':                   # жкт / желудок — читаемый «мешок»
        c.saveState()
        c.translate(s * .52, s * .44); c.rotate(-18)
        c.roundRect(-s * .26, -s * .28, s * .52, s * .56, s * .22, stroke=1, fill=0)
        c.restoreState()
        c.line(s * .36, s * .74, s * .3, s * .92)     # пищевод
        c.line(s * .74, s * .26, s * .86, s * .16)    # выход
    elif name == 'brain':                     # психика / нервы
        c.circle(s * .5, s * .55, s * .32, stroke=1, fill=0)
        c.line(s * .5, s * .23, s * .5, s * .87)
        c.arc(s * .2, s * .58, s * .5, s * .84, 270, 180)
        c.arc(s * .5, s * .3, s * .8, s * .56, 90, 180)
        c.line(s * .44, s * .2, s * .56, s * .2)
    elif name == 'skin':                      # кожа / высыпания
        c.circle(s * .5, s * .5, s * .34, stroke=1, fill=0)
        for dx, dy in ((.38, .58), (.6, .62), (.52, .38)):
            c.circle(s * dx, s * dy, s * .055, stroke=1, fill=0)
    elif name == 'weight':                    # снижение веса / уход отёков
        c.circle(s * .5, s * .5, s * .34, stroke=1, fill=0)
        c.line(s * .5, s * .7, s * .5, s * .32)
        p = c.beginPath(); p.moveTo(s * .37, s * .44); p.lineTo(s * .5, s * .3)
        p.lineTo(s * .63, s * .44)
        c.drawPath(p, stroke=1, fill=0)
    elif name == 'breath':                    # дыхание / поток воздуха
        for y, x2 in ((.72, .78), (.5, .88), (.28, .68)):
            p = c.beginPath(); p.moveTo(s * .12, s * y)
            p.curveTo(s * .4, s * (y + .1), s * .6, s * (y - .1), s * x2, s * y)
            c.drawPath(p, stroke=1, fill=0)
            c.circle(s * x2, s * y, s * .04, stroke=0, fill=1)
    elif name == 'ban':                       # исключить / запрет
        c.circle(s * .5, s * .5, s * .34, stroke=1, fill=0)
        c.line(s * .27, s * .73, s * .73, s * .27)
    elif name == 'check':                     # результат / получите
        p = c.beginPath(); p.moveTo(s * .22, s * .52); p.lineTo(s * .42, s * .3)
        p.lineTo(s * .8, s * .74)
        c.drawPath(p, stroke=1, fill=0)
    else:
        c.circle(s * .5, s * .5, s * .3, stroke=1, fill=0)
    c.restoreState()

ICON_MAP = [
    (('печен', 'гепат', 'желчн', 'пузыр', 'тюбаж', 'протоки'), 'liver'),
    (('кишечник', 'жкт', 'желудок', 'пищеварен', 'перистальт', 'стул', 'запор',
      'вздути', 'микробиот', 'слизист', 'кислотност'), 'stomach'),
    (('психик', 'стресс', 'нерв', 'вагус', 'медитац', 'эмоц', 'мозг', 'память',
      'настроен', 'сон ', 'бессонниц'), 'brain'),
    (('кож', 'высыпан', 'аллерг', 'зуд', 'волос', 'ногт', 'акне'), 'skin'),
    (('вес', 'отёк', 'отек', 'похуд', 'лишн', 'объём', 'объем', 'лимф'), 'weight'),
    (('дыхан', 'дышат', 'диафрагм', 'вдох', 'выдох', 'кислород'), 'breath'),
    (('исключ', 'запрещ', 'нельзя', 'отказ', 'убрат', 'не пить', 'не ешь', 'минимизир'), 'ban'),
    (('получит', 'результат', 'уйдут', 'уходит', 'восстановл', 'улучш', 'избавит'), 'check'),
    (('вод', 'пить', 'питьев', 'жидкост', 'желч', 'раствор'), 'drop'),
    (('трав', 'овощ', 'зелен', 'растит', 'natur', 'природ', 'ягод', 'фрукт'), 'leaf'),
    (('бан', 'грелк', 'тепл', 'пар', 'горяч', 'жар'), 'flame'),
    (('час', 'врем', 'минут', 'перерыв', 'график', 'распорядок', 'ритм'), 'clock'),
    (('ноч', 'сон', 'спат', 'вечер'), 'moon'),
    (('утр', 'день', 'зарядк', 'солн'), 'sun'),
    (('нагрузк', 'движен', 'спорт', 'упражн', 'ходьб', 'гимнаст', 'дыхан', 'приседан'), 'activity'),
    (('иммунит', 'защит', 'барьер', 'профилакт'), 'shield'),
    (('паразит', 'грибк', 'бактер', 'вирус', 'гельминт', 'микроб', 'патоген', 'биоплен'), 'bug'),
    (('рыб', 'морепродукт', 'суши', 'мидии', 'кревет'), 'fish'),
    (('мясо', 'мяс', 'говядин', 'свинин', 'курин', 'баранин'), 'meat'),
    (('питан', 'еда', 'пищ', 'рацион', 'завтрак', 'обед', 'ужин', 'кушат'), 'plate'),
    (('препарат', 'бад', 'капсул', 'таблет', 'сорбент', 'фермент', 'нутрицевт', 'дозиров'), 'pill'),
    (('дом', 'услови', 'быт'), 'home'),
    (('животн', 'питомц', 'собак', 'кошк'), 'paw'),
    (('путешеств', 'поездк', 'страна', 'перелёт', 'перелет'), 'plane'),
    (('эколог', 'воздух', 'загрязн', 'токсин', 'выброс'), 'cloud'),
    (('контакт', 'руки', 'рукопожат', 'общен', 'люд'), 'hands'),
]

def pick_icon(text):
    low = text.lower()
    for keys, name in ICON_MAP:
        if any(k in low for k in keys):
            return name
    return None

class IconTile(Flowable):
    """Плитка: иконка в круге + подпись — для коротких перечислений."""
    def __init__(self, icon, text, width):
        Flowable.__init__(self)
        self.icon, self.width = icon, width
        self.par = Paragraph(esc(text), ParagraphStyle(
            'tile', fontName='Mont-M', fontSize=9, leading=13.5, textColor=TXT, alignment=TA_CENTER))

    def wrap(self, aw, ah):
        pw, ph = self.par.wrap(self.width - 8 * mm, ah)
        self.ph = ph
        self.height = ph + 32 * mm          # 12 сверху + круг 15 + 8 воздуха + текст + 6 снизу
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(CARD); c.setStrokeColor(HAIR); c.setLineWidth(0.5)
        c.roundRect(0, 0, self.width, self.height, RADIUS, stroke=1, fill=1)
        cx, cy = self.width / 2, self.height - 12 * mm
        c.setStrokeColor(HexColor('#4A3F2C')); c.setLineWidth(0.6)
        c.circle(cx, cy, 7.5 * mm, stroke=1, fill=0)
        draw_icon(c, self.icon, cx - 4.5 * mm, cy - 4.5 * mm, 9 * mm)
        c.restoreState()
        self.par.drawOn(c, 4 * mm, 6 * mm)

def icon_tiles(lis):
    """Плитки в ряд; ряды — отдельные flowable'ы, чтобы переносились по страницам."""
    cols = 2                       # на узком A5 три плитки в ряд не читаются
    cw = (CONTENT_W - 4 * mm * (cols - 1)) / cols
    tiles = [IconTile(pick_icon(t) or 'plate', t.rstrip('.;'), cw) for t in lis]
    out = [Spacer(1, 1 * mm)]
    for i in range(0, len(tiles), cols):
        row = tiles[i:i + cols]
        # cols всегда полный, иначе неполный ряд расползается по ширине
        out += [Card(row, bg=None, border=None, cols=cols, gap=4 * mm, pad=(0, 0, 0, 0)),
                Spacer(1, 4 * mm)]
    return out

def figure(path):
    """Схема автора из docx — в рамке-карточке, по ширине полосы."""
    try:
        from reportlab.lib.utils import ImageReader
        from reportlab.platypus import Image as RLImage
        iw, ih = ImageReader(path).getSize()
    except Exception:
        return []
    w = CONTENT_W - 8 * mm
    h = w * ih / iw
    max_h = FRAME_H - 30 * mm
    if h > max_h:
        h, w = max_h, max_h * iw / ih
    img = RLImage(path, width=w, height=h)
    img.hAlign = 'CENTER'
    return [Spacer(1, 2 * mm),
            Card([img], bg=CARD, border=HAIR, pad=(4 * mm, 4 * mm, 4 * mm, 4 * mm)),
            Spacer(1, 4 * mm)]

def fits_page(card):
    """Карточка выше полосы не может быть разрезана — такие блоки верстаем без рамки."""
    try:
        return card.wrap(CONTENT_W, FRAME_H)[1] <= FRAME_H - 8 * mm
    except Exception:
        return False

def note_card(text):
    card = Card([Paragraph(esc(text), S_NOTE)], bg=CARD_HI, border=None, bar=GOLD)
    if not fits_page(card):
        return [Paragraph(esc(text), S_NOTE), Spacer(1, 3 * mm)]
    return [Spacer(1, 1 * mm), card, Spacer(1, 4 * mm)]

def bullets(lis, two_col=False):
    flows = [Paragraph(esc(t), S_LI, bulletText='◆') for t in lis]
    card = Card(flows, cols=2 if two_col else 1)
    if not fits_page(card):
        return [Paragraph(esc(t), S_LI_PLAIN, bulletText='◆') for t in lis] + [Spacer(1, 2 * mm)]
    return [Spacer(1, .5 * mm), card, Spacer(1, 4 * mm)]

def recipe(head, lis, tail):
    inner = [Paragraph(esc(head.upper()), S_CARD_H), Spacer(1, 3 * mm)]
    inner += [Paragraph(esc(t), S_LI, bulletText='◆') for t in lis]
    if tail:
        inner += [Spacer(1, 2 * mm),
                  HRFlowable(width='100%', thickness=0.5, color=HAIR, spaceAfter=2.5 * mm),
                  Paragraph(esc(tail), S_TAIL)]
    card = Card(inner, bar=GOLD, bg=CARD)
    if not fits_page(card):
        out = [Paragraph(esc(head), S_H3)]
        out += [Paragraph(esc(t), S_LI_PLAIN, bulletText='◆') for t in lis]
        if tail:
            out += [Spacer(1, 1.5 * mm), Paragraph(esc(tail), S_TAIL)]
        return out + [Spacer(1, 3 * mm)]
    return [Spacer(1, 1 * mm), card, Spacer(1, 4.5 * mm)]

STAGE_RE = re.compile(r'^\s*(?:\d+\s*[-–—]\s*)?\d+\s*(недел|дн|день|месяц|этап|фаз)', re.I)

def strip_num(t):
    t = re.sub(r'^\d+[.)]\s*', '', t).strip()
    if t.isupper() and len(t) > 6:
        t = t[0] + t[1:].lower()
    return t

class TocRow(Flowable):
    """Строка оглавления: номер в золоте + название в скруглённой плашке."""
    def __init__(self, num, title, width=CONTENT_W, compact=False):
        Flowable.__init__(self)
        self.width, self.num, self.compact = width, num, compact
        self.pad = 3.6 * mm if compact else 5.5 * mm
        self.gut = 13 * mm if compact else 15 * mm
        style = ParagraphStyle('tocc', parent=S_TOC, fontSize=9.2, leading=12.6) if compact else S_TOC
        self.par = Paragraph(esc(title), style)

    def wrap(self, aw, ah):
        pw, ph = self.par.wrap(self.width - self.gut - 5 * mm, ah)
        self.height = ph + self.pad
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(CARD); c.setStrokeColor(HAIR); c.setLineWidth(0.5)
        c.roundRect(0, 0, self.width, self.height, 2.4 * mm, stroke=1, fill=1)
        num_centered(c, '%02d' % self.num, self.gut / 2 + 0.5 * mm, self.height / 2,
                     8.5 if self.compact else 9.5, GOLD)
        c.setStrokeColor(HexColor('#3A352E')); c.setLineWidth(0.5)
        c.line(self.gut, 1.6 * mm, self.gut, self.height - 1.6 * mm)
        c.restoreState()
        pw, ph = self.par.wrap(self.width - self.gut - 5 * mm, self.height)
        self.par.drawOn(c, self.gut + 3.5 * mm, (self.height - ph) / 2 + 0.4 * mm)

class TimelineRow(Flowable):
    """Шаг схемы: кружок с номером на золотой вертикали + название справа."""
    R = 5.2 * mm

    def __init__(self, num, title, width=CONTENT_W, first=False, last=False, size=13):
        Flowable.__init__(self)
        self.width, self.num, self.first, self.last = width, num, first, last
        self.extra = 0
        self.icon = pick_icon(title)
        self.par = Paragraph(esc(title), ParagraphStyle(
            'tl', fontName='Mont-M', fontSize=size, leading=size * 1.4, textColor=TXT))

    def wrap(self, aw, ah):
        pw, ph = self.par.wrap(self.width - 30 * mm, ah)
        self.ph = ph
        self.height = max(ph, self.R * 2) + 6 * mm + self.extra
        return self.width, self.height

    def draw(self):
        c = self.canv
        cx, cy = 7 * mm, self.height - 3 * mm - self.R
        c.saveState()
        c.setStrokeColor(HexColor('#4A3F2C')); c.setLineWidth(0.8)
        if not self.first:
            c.line(cx, self.height, cx, cy + self.R)
        if not self.last:
            c.line(cx, cy - self.R, cx, 0)
        c.setFillColor(CARD); c.setStrokeColor(GOLD); c.setLineWidth(0.9)
        c.circle(cx, cy, self.R, stroke=1, fill=1)
        num_centered(c, str(self.num), cx, cy, 9.5, GOLD_HI)
        if self.icon:
            draw_icon(c, self.icon, self.width - 11 * mm, cy - 5 * mm, 10 * mm, GOLD_DIM)
        c.restoreState()
        self.par.drawOn(c, 18 * mm, cy - self.ph / 2 + 0.6 * mm)

FRAME_H = H_PAGE - 26 * mm      # рабочая высота полосы
HEAD_H = 22 * mm                # заголовок страницы с золотой чертой

def timeline_block(sections):
    """Схема шагов на одну полосу. Если не помещается даже мелким кеглем — None."""
    n = len(sections)
    avail = FRAME_H - HEAD_H
    for size in (13, 12, 11, 10):
        rows = [TimelineRow(i + 1, strip_num(t), first=(i == 0), last=(i == n - 1), size=size)
                for i, t in enumerate(sections)]
        for a, b in zip(rows, rows[1:]):
            if b.icon and b.icon == a.icon:      # одинаковый знак подряд читается как брак
                b.icon = None
        total = sum(r.wrap(CONTENT_W, FRAME_H)[1] for r in rows)
        if total <= avail:
            extra = min((avail - total) / n, 8 * mm)
            for r in rows:
                r.extra = extra
            return rows
    return None

def toc_block(sections, two_col=False):
    compact = len(sections) > 24          # длинное оглавление ужимаем, чтобы влезло на полосу
    rows = [TocRow(i + 1, strip_num(t), compact=compact) for i, t in enumerate(sections)]
    cw = (CONTENT_W - 4 * mm) / 2 if two_col else CONTENT_W
    for r in rows:
        r.width = cw
    n_rows = (len(rows) + 1) // 2 if two_col else len(rows)
    heights = [r.wrap(cw, FRAME_H)[1] for r in rows]
    if two_col:
        total = sum(max(heights[i:i + 2]) for i in range(0, len(rows), 2))
    else:
        total = sum(heights)
    # свободную высоту раздаём в межстрочные зазоры, чтобы список занимал полосу целиком
    gap = 1.6 * mm if compact else 2 * mm
    free = (FRAME_H - HEAD_H) - total - gap * n_rows
    if free > 0:
        gap = min(gap + free / max(n_rows, 1), 9 * mm)
    out = []
    if not two_col:
        for r in rows:
            out += [r, Spacer(1, gap)]
        return out
    for i in range(0, len(rows), 2):
        out += [Card(rows[i:i + 2], bg=None, border=None, cols=2, gap=4 * mm, pad=(0, 0, 0, 0)),
                Spacer(1, gap)]
    return out

# ---------------------------------------------------------------- docx
R_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
A_NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'

def extract_media(fn, slug):
    """Достаём вложенные картинки (схемы автора) и карту rId → файл."""
    media_dir = os.path.join(ROOT, 'paid', 'tmp', 'media', slug)
    rels = {}
    with zipfile.ZipFile(fn) as z:
        names = z.namelist()
        if 'word/_rels/document.xml.rels' not in names:
            return rels
        os.makedirs(media_dir, exist_ok=True)
        rroot = ET.fromstring(z.read('word/_rels/document.xml.rels'))
        for rel in rroot:
            rid, target = rel.get('Id'), rel.get('Target', '')
            if 'media/' not in target:
                continue
            src = 'word/' + target.lstrip('/').replace('../', '')
            if src not in names:
                continue
            out = os.path.join(media_dir, os.path.basename(target))
            with open(out, 'wb') as f:
                f.write(z.read(src))
            rels[rid] = out
    return rels

def docx_paragraphs(fn, slug=''):
    rels = extract_media(fn, slug) if slug else {}
    with zipfile.ZipFile(fn) as z:
        root = ET.fromstring(z.read('word/document.xml'))
    out = []
    for p in root.iter('{%s}p' % W):
        is_list = p.find('.//w:pPr/w:numPr', NS) is not None
        lines, cur, bolds = [], [], []
        for r in p.findall('.//w:r', NS):
            bold = r.find('.//w:rPr/w:b', NS) is not None
            for blip in r.iter('{%s}blip' % A_NS):          # вложенная картинка
                path = rels.get(blip.get('{%s}embed' % R_NS))
                if path:
                    lines.append((''.join(cur), list(bolds))); cur, bolds = [], []
                    lines.append(('\x00IMG\x00' + path, []))
            for node in r:
                tag = node.tag.split('}')[1]
                if tag == 't':
                    cur.append(node.text or ''); bolds.append(bold)
                elif tag == 'br':
                    lines.append((''.join(cur), list(bolds))); cur, bolds = [], []
        lines.append((''.join(cur), bolds))
        for text, bl in lines:
            if text.startswith('\x00IMG\x00'):
                out.append((False, False, False, text))
                continue
            t = text.strip()
            if not t: continue
            allbold = bool(bl) and all(bl)
            letters = [c for c in t if c.isalpha()]
            allcaps = len(letters) > 3 and all(c.upper() == c for c in letters)
            out.append((is_list, allbold, allcaps, t))
    return out

def tidy(t):
    t = re.sub(r'\s{2,}', ' ', t)
    t = re.sub(r'(?<=[а-яёa-z0-9)])(?=[А-ЯЁ][а-яё])', ' ', t)
    t = re.sub(r'([а-яёА-ЯЁa-zA-Z])\(', r'\1 (', t)
    t = re.sub(r'\(\s+', '(', t)
    t = re.sub(r'\s+([,.;:!?)])', r'\1', t)
    t = re.sub(r'([.,;:!?])(?=[а-яёА-ЯЁa-zA-Z])(?!\.\S)', r'\1 ', t)
    t = re.sub(r'\s*[—–]\s*', ' — ', t)
    t = re.sub(r' - ', ' — ', t)
    t = re.sub(r'\s{2,}', ' ', t)
    return t.replace(' .', '.').replace('“', '«').replace('”', '»').strip()

TERM = '.!?:;»)"'
ABBR_END = re.compile(r'(?:^|\s)(?:т\.\s?е|т\.\s?к|и\s?др|и\s?пр|т\.\s?д|см|напр)\.$', re.I)

def unfinished_text(t):
    """Абзац не закончен, если нет терминатора или он оборван сокращением («т. е.»)."""
    return t[-1:] not in TERM or bool(ABBR_END.search(t))

def merge_fragments(items):
    """Docx клиента рвёт абзацы переносами строк — склеиваем обрывки обратно.
    Обрывок = не закончен терминатором, а следующий кусок начинается со строчной."""
    out = []
    for kind, t in items:
        if out:
            pk, pt = out[-1]
            unfinished = unfinished_text(pt)
            # продолжение пункта списка: только со строчной буквы,
            # иначе это самостоятельная приписка после перечня
            if unfinished and pk == 'li' and kind in ('p', 'li') and t[:1].islower():
                out[-1] = ('li', (pt + ' ' + t).replace('  ', ' '))
                continue
            if unfinished and pk in ('p', 'h2', 'note') and kind in ('p', 'h2'):
                # заголовок склеиваем только с явным продолжением (со строчной буквы),
                # обычные абзацы — и с заглавной: docx рвёт их переносами строк
                if t[:1].islower() or (kind == 'p' and pk in ('p', 'note')):
                    out[-1] = (pk if pk == 'note' else 'p', (pt + ' ' + t).replace('  ', ' '))
                    continue
        out.append((kind, t))
    out = [(k if not (k == 'h2' and (t[:1].islower() or len(t) > 70 and t.endswith('.'))) else 'p', t)
           for k, t in out]
    # заголовок, за которым сразу идёт другой заголовок — рубрикатор без содержимого
    return [(k, t) for i, (k, t) in enumerate(out)
            if not (k == 'h2' and i + 1 < len(out) and out[i + 1][0] == 'h2')]

def classify(paras, slug):
    items, started = [], False
    for is_list, allbold, allcaps, t in paras:
        if t.startswith('\x00IMG\x00'):
            items.append(('img', t[5:]))
            started = True
            continue
        t = tidy(t)
        if not started:
            started = True
            continue
        if slug == 'pitanie' and t.startswith('(из Курса'):
            continue
        if BULLET_RE.match(t):
            body = BULLET_RE.sub('', t).strip()
            items.append(('h3' if body.endswith(':') and len(body) < 45 else 'li', body))
        elif is_list:
            items.append(('h3' if t.endswith(':') and len(t) < 45 else 'li', t))
        elif allcaps and len(t) > 40:
            items.append(('quote', t[0] + t[1:].lower()))
        elif allbold and t[0] in '-–—(' :
            items.append(('li', t.lstrip('-–— ').strip()))
        elif allbold and ('!' in t or (t.endswith('.') and len(t) > 30)):
            items.append(('note', t))
        elif allbold and len(t) < 95:
            head = t.rstrip(':')
            if items and items[-1] == ('h2', head):
                continue
            items.append(('h2', head))
        elif allbold:
            items.append(('note', t))
        else:
            items.append(('p', t))
    return merge_fragments(items)

# ---------------------------------------------------------------- страницы
def paint_bg(cv):
    steps = 40
    for i in range(steps):
        f = i / (steps - 1)
        cv.setFillColorRGB(BG_TOP.red + (BG_BOT.red - BG_TOP.red) * f,
                           BG_TOP.green + (BG_BOT.green - BG_TOP.green) * f,
                           BG_TOP.blue + (BG_BOT.blue - BG_TOP.blue) * f)
        cv.rect(0, H_PAGE - (i + 1) * H_PAGE / steps, W_PAGE, H_PAGE / steps + 1, stroke=0, fill=1)

def draw_cover(cv, doc):
    cv.saveState()
    paint_bg(cv)
    cv.setStrokeColor(GOLD); cv.setLineWidth(0.8)
    cv.roundRect(8 * mm, 8 * mm, W_PAGE - 16 * mm, H_PAGE - 16 * mm, 5 * mm, stroke=1, fill=0)
    lw = 36 * mm
    cv.drawImage(LOGO, W_PAGE / 2 - lw / 2, H_PAGE - 92 * mm, width=lw, height=lw * 512 / 416, mask='auto')
    track(cv, 'КЛУБ ВОССТАНОВЛЕНИЯ АНДРЕЯ БУЛАТНОГО', W_PAGE / 2, H_PAGE - 102 * mm,
          'Mont-SB', 7.2, GOLD_HI, 2.6, center=True)
    track(cv, 'МЕТОДИЧЕСКОЕ ПОСОБИЕ · ДЛЯ ЛИЧНОГО ИСПОЛЬЗОВАНИЯ', W_PAGE / 2, 15 * mm,
          'Mont-M', 6.2, TXT_MUTED, 2, center=True)
    cv.restoreState()

def draw_page(cv, doc):
    cv.saveState()
    paint_bg(cv)
    n = cv.getPageNumber() - 1
    cv.setFillColor(TXT_MUTED); cv.setFont('Mont-M', 8)
    cv.drawCentredString(W_PAGE / 2, 8.5 * mm, str(n))
    cv.setStrokeColor(HAIR); cv.setLineWidth(0.5)
    cv.line(W_PAGE / 2 - 11 * mm, 10 * mm, W_PAGE / 2 - 3.5 * mm, 10 * mm)
    cv.line(W_PAGE / 2 + 3.5 * mm, 10 * mm, W_PAGE / 2 + 11 * mm, 10 * mm)
    cv.restoreState()

def build(slug):
    meta = DOCS[slug]
    items = classify(docx_paragraphs(os.path.join(SRC, slug + '.docx'), slug), slug)

    doc = BaseDocTemplate(os.path.join(OUT, slug + '.pdf'), pagesize=A5,
                          title='%s — Клуб восстановления Андрея Булатного' % meta['title'],
                          author='Андрей Булатный')
    doc.addPageTemplates([
        PageTemplate(id='cover', frames=[Frame(14 * mm, 14 * mm, W_PAGE - 28 * mm, H_PAGE - 28 * mm)],
                     onPage=draw_cover),
        PageTemplate(id='page', frames=[Frame(MARGIN, 13 * mm, CONTENT_W, FRAME_H)],
                     onPage=draw_page),
    ])

    story = [Spacer(1, 86 * mm), Paragraph(esc(meta['title']), S_COVER_H), Spacer(1, 4 * mm),
             HRFlowable(width=26 * mm, thickness=1.2, color=GOLD, hAlign='CENTER'), Spacer(1, 4 * mm),
             Paragraph(esc(meta['sub']), S_COVER_SUB),
             NextPageTemplate('page'), PageBreak()]

    sections = [t for k, t in items if k == 'h2']
    tl = timeline_block(sections) if 4 <= len(sections) <= 12 else None
    if tl:
        # короткий документ — показываем не список, а схему прохождения
        story += [Paragraph('Как это устроено',
                            ParagraphStyle('th', parent=S_H2, fontSize=22, leading=26)),
                  HRFlowable(width=14 * mm, thickness=1.2, color=GOLD, hAlign='LEFT',
                             spaceBefore=2 * mm, spaceAfter=6 * mm)]
        story += tl + [PageBreak()]
    elif len(sections) >= 4:
        story += [Paragraph('Что внутри', ParagraphStyle('th', parent=S_H2, fontSize=22, leading=26)),
                  HRFlowable(width=16 * mm, thickness=1.2, color=GOLD, hAlign='LEFT',
                             spaceBefore=2.5 * mm, spaceAfter=6 * mm)]
        story += toc_block(sections, two_col=False)
        story += [PageBreak()]

    sec, i = 0, 0
    if items and items[0][0] == 'p':
        story += [Card([Paragraph(esc(items[0][1]),
                                  ParagraphStyle('lead', fontName='Mont-M', fontSize=11.5,
                                                 leading=19, textColor=GOLD_HI))],
                       bg=CARD_HI, border=None, bar=GOLD,
                       pad=(6 * mm, 6 * mm, 5.5 * mm, 6.5 * mm)),
                  Spacer(1, 5 * mm)]
        i = 1
    while i < len(items):
        kind, t = items[i]
        if kind == 'h2':
            sec += 1
            story += [CondPageBreak(46 * mm), Spacer(1, 4 * mm),
                      SectionHead(sec, strip_num(t)), Spacer(1, 1 * mm)]
            i += 1
        elif kind == 'h3':
            lis, j = [], i + 1
            while j < len(items) and items[j][0] == 'li':
                lis.append(items[j][1]); j += 1
            if lis and len(lis) <= 12:
                tail = None
                if (j < len(items) and items[j][0] == 'p' and len(items[j][1]) < 320
                        and not items[j][1].rstrip().endswith(':')):
                    tail = items[j][1]; j += 1
                story += recipe(t, lis, tail)
                i = j
            else:
                story.append(Paragraph(esc(t.upper()), ParagraphStyle(
                    'h3', parent=S_CARD_H, spaceBefore=3 * mm, spaceAfter=2.5 * mm)))
                i += 1
        elif kind == 'li':
            lis, j = [], i
            while j < len(items) and items[j][0] == 'li':
                lis.append(items[j][1]); j += 1
            iconable = sum(1 for x in lis if pick_icon(x))
            if len(lis) == 1 and len(lis[0]) < 90:
                story += [Spacer(1, 2.5 * mm),
                          Paragraph(esc(lis[0].rstrip('.')), S_H3),
                          HRFlowable(width=12 * mm, thickness=1, color=GOLD_DIM,
                                     hAlign='LEFT', spaceAfter=3 * mm)]
            elif (2 <= len(lis) <= 9 and all(len(x) < 54 for x in lis)
                  and iconable >= max(2, len(lis) * 0.5)):
                story += icon_tiles(lis)
            elif 4 <= len(lis) <= 14 and all(len(x) < 26 for x in lis):
                story += bullets(lis, two_col=True)
            elif len(lis) <= 12:
                story += bullets(lis)
            else:
                story += [Paragraph(esc(x), S_LI_PLAIN, bulletText='◆') for x in lis] + [Spacer(1, 2 * mm)]
            i = j
        elif kind == 'p' and STAGE_RE.match(t):
            # подряд идущие «0–4 неделя — …», «этап 2 — …» → схема этапов
            stages, j = [], i
            while j < len(items) and items[j][0] == 'p' and STAGE_RE.match(items[j][1]):
                stages.append(items[j][1]); j += 1
            if len(stages) >= 3:
                story += [Spacer(1, 2 * mm)]
                story += [TimelineRow(k + 1, s, first=(k == 0), last=(k == len(stages) - 1))
                          for k, s in enumerate(stages)]
                story += [Spacer(1, 4 * mm)]
                i = j
            else:
                story.append(Paragraph(esc(t), S_P)); i += 1
        elif kind == 'img':
            story += figure(t); i += 1
        elif kind == 'quote':
            story += [Spacer(1, 2 * mm), GoldQuote(t), Spacer(1, 5 * mm)]; i += 1
        elif kind == 'note':
            story += note_card(t); i += 1
        else:
            story.append(Paragraph(esc(t), S_P)); i += 1

    story += [PageBreak(), Spacer(1, 30 * mm)]
    story += [Card([
        Paragraph('Остались вопросы — я рядом',
                  ParagraphStyle('fh', parent=S_H2, fontSize=21, leading=25, alignment=TA_CENTER)),
        Spacer(1, 3 * mm),
        Paragraph('На всём пути восстановления вы можете обратиться ко мне напрямую.', S_FIN),
        Spacer(1, 4 * mm),
        Paragraph('<font color="#E2C185">Telegram:</font> @MassageTaganka', S_FIN),
        Paragraph('<font color="#E2C185">WhatsApp, телефон:</font> +7 (915) 243-88-42', S_FIN),
        Paragraph('<font color="#E2C185">Приём:</font> Москва, м. Таганская · г. Дзержинский · онлайн', S_FIN),
        Spacer(1, 6 * mm),
        Paragraph('С уважением, Андрей Булатный',
                  ParagraphStyle('sig', fontName='Cormorant-SB', fontSize=15, leading=19,
                                 textColor=GOLD_HI, alignment=TA_CENTER)),
    ], bg=CARD, border=HAIR, pad=(9 * mm, 8 * mm, 9 * mm, 8 * mm), radius=5 * mm)]
    story += [Spacer(1, 10 * mm),
              Paragraph('Материал носит ознакомительный характер, не является медицинской услугой и не заменяет '
                        'консультацию врача. При наличии заболеваний проконсультируйтесь со специалистом. '
                        'Пособие предназначено для личного использования покупателя — копирование, публикация '
                        'и передача третьим лицам запрещены. © Шмаров А.В., 2026', S_LEGAL)]

    doc.build(story)
    print('OK', slug, os.path.getsize(os.path.join(OUT, slug + '.pdf')) // 1024, 'KB')

# копия для клиента с человеческими именами — папка на Рабочем столе
EXPORT_NAMES = {
    'pitanie': 'Рацион питания.pdf',
    'limfa': 'Лимфодренажный протокол.pdf',
    'tubazh': 'Тюбажная система очищения.pdf',
    'parazity': 'Антипаразитарная чистка.pdf',
    'kurs': 'Курс по восстановлению ЖКТ.pdf',
}

def export(slugs):
    import shutil, unicodedata
    desk = os.path.expanduser('~/Desktop')
    base = next((os.path.join(desk, n) for n in os.listdir(desk)
                 if 'булатн' in unicodedata.normalize('NFC', n).lower()), None)
    if not base:
        return
    dst = os.path.join(base, 'ГОТОВЫЕ PDF')
    os.makedirs(dst, exist_ok=True)
    for s in slugs:
        shutil.copy2(os.path.join(OUT, s + '.pdf'), os.path.join(dst, EXPORT_NAMES[s]))
    print('→ копии для клиента:', dst)

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    slugs = sys.argv[1:] or ['pitanie', 'limfa', 'tubazh', 'parazity', 'kurs']
    for s in slugs:
        build(s)
    export(slugs)
