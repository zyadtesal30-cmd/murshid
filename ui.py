# -*- coding: utf-8 -*-
"""أدوات الواجهة: دعم العربية (تشكيل + RTL + التفاف الأسطر) وعناصر بتصميم فخم."""
import os
import re
from functools import lru_cache

import arabic_reshaper
from bidi.algorithm import get_display
from kivy.core.text import LabelBase, Label as CoreLabel
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

HERE = os.path.dirname(os.path.abspath(__file__))
LabelBase.register(name='AR',
                   fn_regular=os.path.join(HERE, 'fonts', 'DejaVuSans.ttf'),
                   fn_bold=os.path.join(HERE, 'fonts', 'DejaVuSans-Bold.ttf'))

# ── الألوان ──
BG = (0.043, 0.071, 0.133, 1)
CARD = (0.082, 0.118, 0.208, 1)
CARD2 = (0.125, 0.169, 0.282, 1)
GOLD = (0.957, 0.753, 0.243, 1)
TEAL = (0.200, 0.780, 0.700, 1)
TEXT = (0.930, 0.940, 0.970, 1)
MUTED = (0.600, 0.660, 0.780, 1)
GREEN = (0.250, 0.780, 0.450, 1)
RED = (0.930, 0.330, 0.330, 1)
AMBER = (0.980, 0.690, 0.200, 1)
BLUE = (0.330, 0.560, 0.960, 1)
DARK = (0.043, 0.071, 0.133, 1)
CREAM = (0.990, 0.930, 0.690, 1)
GREEN_BG = (0.090, 0.230, 0.170, 1)
RED_BG = (0.280, 0.110, 0.130, 1)
AMBER_BG = (0.290, 0.220, 0.090, 1)
BLUE_BG = (0.100, 0.170, 0.330, 1)

_EMOJI = re.compile('[\U0001F000-\U0001FFFF\uFE0F\u200d]')
_SPACE = 0.32


@lru_cache(maxsize=8192)
def shape(s):
    """نص منطقي -> نص جاهز للعرض (حروف متصلة + ترتيب RTL)."""
    s = _EMOJI.sub('', str(s)).strip()
    if not s:
        return ''
    return get_display(arabic_reshaper.reshape(s), base_dir='R')


@lru_cache(maxsize=16384)
def _wid(word, size, bold):
    cl = CoreLabel(font_name='AR', font_size=size, bold=bold)
    return cl.get_extents(shape(word))[0]


def wrap_text(text, width, size, bold=False):
    """يلفّ النص المنطقي على أسطر ثم يشكّل كل سطر (حل مشكلة ترتيب الأسطر العربية)."""
    text = _EMOJI.sub('', str(text))
    lines = []
    space = size * _SPACE
    limit = width * 0.95
    for para in text.split('\n'):
        words = para.split()
        if not words:
            lines.append('')
            continue
        cur, cw = [], 0.0
        for w in words:
            ww = _wid(w, size, bold)
            add = ww + (space if cur else 0)
            if cur and cw + add > limit:
                lines.append(' '.join(cur))
                cur, cw = [w], ww
            else:
                cur.append(w)
                cw += add
        lines.append(' '.join(cur))
    return '\n'.join(shape(l) if l else '' for l in lines)


class ALabel(Label):
    """نص عربي متعدد الأسطر، ارتفاعه تلقائي."""

    def __init__(self, text='', size=15, color=TEXT, bold=False, halign='right', **kw):
        kw.setdefault('size_hint_y', None)
        super().__init__(font_name='AR', font_size=sp(size), bold=bold, color=color,
                         halign=halign, valign='middle', **kw)
        self.raw = text
        self._bold = bold
        self.bind(width=self._upd)
        self._upd()

    def set(self, t):
        self.raw = t
        self._upd()

    def _upd(self, *a):
        w = self.width
        if w <= 20:
            w = dp(300)
        self.text = wrap_text(self.raw, w, self.font_size, self._bold)
        self.text_size = (self.width if self.width > 20 else None, None)
        self.texture_update()
        self.height = max(self.texture_size[1] + dp(6), dp(24))


class Card(BoxLayout):
    def __init__(self, bg=CARD, radius=18, pad=14, spacing=8, auto=True, **kw):
        kw.setdefault('size_hint_y', None)
        super().__init__(orientation='vertical', padding=dp(pad), spacing=dp(spacing), **kw)
        self._bg = bg
        with self.canvas.before:
            self._col = Color(*bg)
            self._rr = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(radius)])
        self.bind(pos=self._u, size=self._u)
        if auto:
            self.bind(minimum_height=self.setter('height'))

    def _u(self, *a):
        self._rr.pos = self.pos
        self._rr.size = self.size

    def set_bg(self, c):
        self._bg = c
        self._col.rgba = c


class TapCard(ButtonBehavior, Card):
    pass


class Btn(Button):
    def __init__(self, text='', bg=CARD2, fg=TEXT, size=15, h=46, radius=14, bold=True, **kw):
        kw.setdefault('size_hint_y', None)
        super().__init__(text=shape(text), font_name='AR', font_size=sp(size), bold=bold, color=fg,
                         background_normal='', background_down='', background_color=(0, 0, 0, 0),
                         height=dp(h), **kw)
        self.bg = bg
        with self.canvas.before:
            self._col = Color(*bg)
            self._rr = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(radius)])
        self.bind(pos=self._u, size=self._u, state=self._st)

    def set_text(self, t):
        self.text = shape(t)

    def set_bg(self, c, fg=None):
        self.bg = c
        self._col.rgba = c
        if fg:
            self.color = fg

    def _u(self, *a):
        self._rr.pos = self.pos
        self._rr.size = self.size

    def _st(self, *a):
        if self.state == 'down':
            self._col.rgba = tuple(min(1, x * 1.3) for x in self.bg[:3]) + (1,)
        else:
            self._col.rgba = self.bg


class Bar(Widget):
    def __init__(self, value=0.0, color=GOLD, **kw):
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(12))
        super().__init__(**kw)
        self.value = value
        with self.canvas:
            Color(*CARD2)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])
            self._c = Color(*color)
            self._fg = RoundedRectangle(pos=self.pos, size=(0, self.height), radius=[dp(6)])
        self.bind(pos=self._u, size=self._u)
        self._u()

    def _u(self, *a):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._fg.pos = self.pos
        self._fg.size = (max(0, min(1, self.value)) * self.width, self.height)


class TInput(TextInput):
    def __init__(self, **kw):
        kw.setdefault('multiline', False)
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(46))
        kw.setdefault('halign', 'right')
        super().__init__(font_name='AR', font_size=sp(16), background_normal='', background_active='',
                         background_color=CARD2, foreground_color=TEXT, cursor_color=GOLD,
                         hint_text_color=MUTED, padding=(dp(12), dp(12)), **kw)


def page(pad=12, spacing=12):
    """يرجع (ScrollView, BoxLayout رأسي) لإضافة المحتوى."""
    sv = ScrollView(do_scroll_x=False, bar_width=dp(3), bar_color=(*GOLD[:3], 0.6))
    box = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(pad), spacing=dp(spacing))
    box.bind(minimum_height=box.setter('height'))
    sv.add_widget(box)
    return sv, box


def hrow(*widgets, h=46, spacing=8):
    """صف أفقي (أول عنصر يظهر على اليسار؛ أضف عنصر العنوان آخراً ليظهر على اليمين)."""
    r = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(h), spacing=dp(spacing))
    for w in widgets:
        r.add_widget(w)
    return r


def chips(items, selected, on_pick, h=44):
    """شريط أزرار أفقي قابل للتمرير. items = [(key, label)] — الأول يظهر يمين."""
    sv = ScrollView(do_scroll_y=False, size_hint_y=None, height=dp(h + 6), bar_width=0)
    inner = BoxLayout(orientation='horizontal', size_hint=(None, None), height=dp(h), spacing=dp(6))
    inner.bind(minimum_width=inner.setter('width'))
    for key, label in reversed(items):
        on = key == selected
        b = Btn(label, bg=GOLD if on else CARD2, fg=DARK if on else TEXT, size=14, h=h - 4,
                size_hint_x=None, width=dp(max(64, 11 * len(label) + 28)))
        b.bind(on_release=lambda w, k=key: on_pick(k))
        inner.add_widget(b)
    sv.add_widget(inner)
    sv.scroll_x = 1
    return sv


def seg(options, value, on_change, h=44):
    """أزرار اختيار واحد (الأول يمين)."""
    r = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(h), spacing=dp(6))
    for key, label in reversed(options):
        on = key == value
        b = Btn(label, bg=GOLD if on else CARD2, fg=DARK if on else TEXT, size=14, h=h)
        b.bind(on_release=lambda w, k=key: on_change(k))
        r.add_widget(b)
    return r


def stepper(value, lo, hi, on_change, fmt=str, h=44):
    """[−] قيمة [+]"""
    cur = [value]
    lbl = ALabel(fmt(value), size=17, bold=True, color=GOLD, halign='center', size_hint_x=1)
    lbl.size_hint_y = 1

    def bump(d):
        v = max(lo, min(hi, cur[0] + d))
        cur[0] = v
        lbl.set(fmt(v))
        on_change(v)
    minus = Btn('−', size=22, h=h, size_hint_x=None, width=dp(54))
    plus = Btn('+', size=22, h=h, size_hint_x=None, width=dp(54))
    minus.bind(on_release=lambda *a: bump(-1))
    plus.bind(on_release=lambda *a: bump(1))
    return hrow(plus, lbl, minus, h=h, spacing=4)


def toggle(text, value, on_change, h=46):
    """سطر نص + زر تشغيل/إيقاف."""
    state = [bool(value)]
    b = Btn('مفعّل ✔' if state[0] else 'متوقف', bg=GREEN if state[0] else CARD2,
            fg=DARK if state[0] else MUTED, size=13, h=h - 6, size_hint_x=None, width=dp(96))

    def flip(*a):
        state[0] = not state[0]
        b.set_text('مفعّل ✔' if state[0] else 'متوقف')
        b.set_bg(GREEN if state[0] else CARD2, DARK if state[0] else MUTED)
        on_change(state[0])
    b.bind(on_release=flip)
    lb = ALabel(text, size=14, pos_hint={'center_y': .5})
    b.pos_hint = {'center_y': .5}
    r = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(52), spacing=dp(8))
    r.add_widget(b)
    r.add_widget(lb)
    lb.bind(height=lambda w, hh: setattr(r, 'height', max(dp(52), hh + dp(10))))
    r.height = max(dp(52), lb.height + dp(10))
    return r


# ── النوافذ ──
_popups = []


def open_popup(title, content, size=(0.92, 0.8)):
    p = Popup(title=shape(title), title_font='AR', title_size=sp(17), title_align='right',
              content=content, size_hint=size, auto_dismiss=True,
              background='', background_color=CARD, separator_color=GOLD,
              title_color=GOLD)
    _popups.append(p)
    p.bind(on_dismiss=lambda *a: _popups.remove(p) if p in _popups else None)
    p.open()
    return p


def close_top_popup():
    if _popups:
        _popups[-1].dismiss()
        return True
    return False


def info_popup(title, text, buttons=None, size=(0.92, 0.7)):
    """buttons = [(label, callback)] — يُضاف زر إغلاق دائماً."""
    root = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(8))
    sv = ScrollView(do_scroll_x=False)
    box = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(4))
    box.bind(minimum_height=box.setter('height'))
    box.add_widget(ALabel(text, size=15))
    sv.add_widget(box)
    root.add_widget(sv)
    p = open_popup(title, root, size)
    row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(48), spacing=dp(8))
    for lb, cb in (buttons or []):
        b = Btn(lb, bg=GOLD, fg=DARK, h=48)
        b.bind(on_release=lambda w, cb=cb: cb())
        row.add_widget(b)
    c = Btn('إغلاق', h=48)
    c.bind(on_release=lambda *a: p.dismiss())
    row.add_widget(c)
    root.add_widget(row)
    return p


def confirm_popup(title, text, on_yes):
    root = BoxLayout(orientation='vertical', spacing=dp(12), padding=dp(8))
    root.add_widget(ALabel(text, size=15))
    row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(48), spacing=dp(8))
    p = open_popup(title, root, (0.88, 0.4))
    no = Btn('إلغاء', h=48)
    yes = Btn('تأكيد', bg=RED, fg=TEXT, h=48)
    no.bind(on_release=lambda *a: p.dismiss())

    def go(*a):
        p.dismiss()
        on_yes()
    yes.bind(on_release=go)
    row.add_widget(no)
    row.add_widget(yes)
    root.add_widget(row)
    return p


def choice_popup(title, options, on_pick, size=(0.88, 0.7)):
    """قائمة اختيار. options = [(key, label)]."""
    sv, box = page(8, 8)
    p = open_popup(title, sv, size)
    for key, label in options:
        b = Btn(label, size=14, h=48)

        def pick(w, k=key):
            p.dismiss()
            on_pick(k)
        b.bind(on_release=pick)
        box.add_widget(b)
    return p
