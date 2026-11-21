# -*- coding: utf-8 -*-
"""الشاشات: ١) بياناتي  ٢) موادي  ٣) حالتي"""
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout

import engine as E
from engine import (COURSES, C, ELEC_MIN, GRADE_LIST, GROUP_NAME, MONTH_AR, TOTAL_REQUIRED, bar_text,
                    pre_of, term_label)
from ui import (AMBER, AMBER_BG, BLUE, BLUE_BG, CARD, CARD2, DARK, GOLD, GREEN, GREEN_BG, MUTED, RED, RED_BG,
                TEAL, TEXT, ALabel, Bar, Btn, Card, TapCard, TInput, chips, choice_popup, confirm_popup, hrow,
                info_popup, seg, stepper, toggle)

KIND_TXT = {'univ': 'جامعة', 'college': 'كلية', 'major': 'تخصص رئيسي', 'sub': 'تخصص فرعي'}
TYPE_OPTS = [('F', 'خريف'), ('S', 'ربيع'), ('U', 'صيفي')]


def sec(text, color=GOLD):
    return ALabel(text, size=17, bold=True, color=color)


def lab_row(title, ctrl, h=46):
    lb = ALabel(title, size=14, color=MUTED, size_hint_x=.42, pos_hint={'center_y': .5})
    ctrl.size_hint_x = .58
    r = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(h), spacing=dp(8))
    r.add_widget(ctrl)
    r.add_widget(lb)
    lb.bind(height=lambda w, hh: setattr(r, 'height', max(dp(h), hh + dp(8))))
    return r


class TabsA:
    # ───────────────── ١) بياناتي ─────────────────
    def t_info(self, box):
        s = self.set

        c = Card()
        c.add_widget(sec('أنا مين؟'))
        ti = TInput(text=s.get('name', ''), hint_text='الاسم (اختياري)')
        prev = ALabel(s.get('name', ''), size=16, color=TEAL)

        def on_name(w, v):
            s['name'] = v.strip()
            prev.set(v.strip())
            self.changed()
        ti.bind(text=on_name)
        c.add_widget(ti)
        c.add_widget(prev)
        g = TInput(text='' if s.get('gpa_manual') is None else str(s['gpa_manual']),
                   hint_text='المعدل التراكمي (اختياري)', input_filter='float', halign='center')

        def on_gpa(w, v):
            try:
                s['gpa_manual'] = float(v.translate(E.AR_DIGITS).replace(',', '.')) if v.strip() else None
            except ValueError:
                s['gpa_manual'] = None
            self.changed()
        g.bind(text=on_gpa)
        c.add_widget(lab_row('معدلي (بيتحسب لوحده لو دخلت تقديرات)', g))
        c.add_widget(toggle('أنهيت التدريب الصيفي (٦ أسابيع على الأقل — شرط للتخرج)', s.get('training'),
                            lambda v: (s.__setitem__('training', v), self.changed())))
        box.add_widget(c)

        c = Card()
        c.add_widget(sec('الفصل القادم اللي هسجّل فيه'))
        nxt = ALabel('', size=17, bold=True, color=TEAL, halign='center')
        warn = ALabel('', size=13, color=RED)

        def refresh():
            m = s['months']
            nxt.set('الفصل القادم: ' + term_label(s['start_type'], s['start_year'], m))
            warn.set('' if m['S'] < m['U'] < m['F'] else
                     '⚠ المفروض الربيع قبل الصيفي قبل الخريف في نفس السنة — راجع الشهور.')

        def set_type(k):
            s['start_type'] = k
            self.changed()
            self.show_tab(0)
        c.add_widget(seg(TYPE_OPTS, s['start_type'], set_type))
        c.add_widget(lab_row('السنة', stepper(s['start_year'], 2020, 2060,
                                              lambda v: (s.__setitem__('start_year', v), self.changed(), refresh()))))
        c.add_widget(nxt)
        box.add_widget(c)

        c = Card()
        c.add_widget(sec('ساعاتي في كل فصل'))
        c.add_widget(lab_row('أقصى عدد ساعات', stepper(s.get('cap', 21), 6, 21,
                                                       lambda v: (s.__setitem__('cap', v), self.changed()))))
        c.add_widget(lab_row('أقل عدد ساعات (0 = بدون حد)', stepper(s.get('min_load', 0), 0, 21,
                                                                    lambda v: (s.__setitem__('min_load', v), self.changed()))))
        c.add_widget(ALabel('لو المواد المطلوبة مش كفاية، البرنامج بيكمّل الفصل بمواد اختيارية إضافية (مكتوب جنبها «إضافي»).',
                            size=12, color=MUTED))
        c.add_widget(toggle('استخدام الفصل الصيفي في الخطة', s.get('use_summer', True),
                            lambda v: (s.__setitem__('use_summer', v), self.changed())))
        box.add_widget(c)

        c = Card()
        c.add_widget(sec('شهر بداية كل فصل'))
        for typ, nm in (('F', 'خريف'), ('S', 'ربيع'), ('U', 'صيفي')):
            c.add_widget(lab_row(nm, stepper(int(s['months'][typ]), 1, 12,
                                             lambda v, t=typ: (s['months'].__setitem__(t, v), self.changed(), refresh()),
                                             fmt=lambda v: MONTH_AR[v - 1])))
        c.add_widget(warn)
        box.add_widget(c)
        refresh()

        c = Card()
        c.add_widget(sec('إعدادات متقدمة (سيبها زي ما هي لو مش متأكد)', MUTED))
        c.add_widget(toggle('كل مقرر بيتطرح في نوع الفصل المقترح له فقط (فردي = خريف / زوجي = ربيع)', s.get('parity', True),
                            lambda v: (s.__setitem__('parity', v), self.changed())))
        c.add_widget(toggle('مشروع التخرج (٢) لازم يكون بعد مشروع (١)', s.get('proj_order', True),
                            lambda v: (s.__setitem__('proj_order', v), self.changed())))
        box.add_widget(c)

        c = Card()
        c.add_widget(sec('نسخة احتياطية'))
        c.add_widget(ALabel('بياناتك بتتحفظ تلقائياً على الموبايل. تقدر تشارك نسخة منها أو تلصق نسخة من جهاز تاني.', size=12, color=MUTED))
        e1 = Btn('مشاركة نسخة من بياناتي', h=46, size=13)
        e1.bind(on_release=lambda *a: self.export_data())
        e2 = Btn('استيراد من الحافظة', h=46, size=13)
        e2.bind(on_release=lambda *a: self.import_data())
        c.add_widget(hrow(e2, e1, h=46))
        box.add_widget(c)

        b = Btn('عن البرنامج وأهم قواعد اللائحة', h=50)
        b.bind(on_release=lambda *a: info_popup('أهم قواعد اللائحة', E.RULES_TEXT + '\n\nتطوير: ' + E.DEVELOPER, size=(0.94, 0.85)))
        box.add_widget(b)

    # ───────────────── ٢) موادي ─────────────────
    def is_passed(self, code):
        e = self.rec.get(code)
        return bool(e) and e.get('s') == 'done' and e.get('g') != 'F'

    def view_base(self, key):
        if key == 'E':
            return [c for c in COURSES if c.kind == 'E']
        if key == 'ALL':
            return list(COURSES)
        return [c for c in COURSES if c.sem == int(key)]

    def elective_hours(self):
        tot, per = 0, {}
        for g in ELEC_MIN:
            h = sum(c.cr for c in COURSES if c.grp == g and c.kind == 'E' and self.is_passed(c.code))
            per[g] = h
            tot += min(h, ELEC_MIN[g])
        return tot, per

    def visible_courses(self):
        q = self.f_q.strip().lower()
        out = []
        for c in self.view_base(self.view):
            if q and q not in c.name.lower() and q not in c.code.lower():
                continue
            if (self.f_kind == 'R' and c.kind != 'R') or (self.f_kind == 'E' and c.kind != 'E'):
                continue
            if self.f_left and self.is_passed(c.code):
                continue
            out.append(c)
        return sorted(out, key=lambda c: (c.sem if c.sem else 99, 0 if c.kind == 'R' else 1, c.code))

    def set_status(self, codes, s, g=''):
        for code in codes:
            if s == 'none':
                self.rec.pop(code, None)
            else:
                self.rec[code] = {'s': s, 'g': g}
        self.changed()

    def t_courses(self, box):
        items = []
        for i in range(1, 11):
            req = [c for c in COURSES if c.sem == i and c.kind == 'R']
            d = sum(1 for c in req if self.is_passed(c.code))
            items.append((str(i), 'ف%d  %d/%d%s' % (i, d, len(req), ' ✔' if req and d == len(req) else '')))
        items.append(('E', 'اختياري %d/%d' % (self.elective_hours()[0], sum(ELEC_MIN.values()))))
        items.append(('ALL', 'الكل %d/%d' % (sum(1 for c in COURSES if self.is_passed(c.code)), len(COURSES))))
        box.add_widget(chips(items, self.view, lambda k: (setattr(self, 'view', k), self.show_tab(1, top=True))))

        base = self.view_base(self.view)
        key = self.view
        if key.isdigit():
            req = [c for c in base if c.kind == 'R']
            el = [c for c in base if c.kind == 'E']
            info = 'جدول الفصل %s — إجباري: %d مقرر (%d ساعة) | اختياري متاح: %d مقرر | المنتهي من الإجباري: %d/%d' % (
                key, len(req), sum(c.cr for c in req), len(el), sum(1 for c in req if self.is_passed(c.code)), len(req))
        elif key == 'E':
            tot, per = self.elective_hours()
            info = 'الاختياري المطلوب %d ساعة — جامعة %d/%d | تخصص رئيسي %d/%d | تخصص فرعي %d/%d' % (
                sum(ELEC_MIN.values()), per['univ'], ELEC_MIN['univ'], per['major'], ELEC_MIN['major'], per['sub'], ELEC_MIN['sub'])
        else:
            info = 'كل مقررات اللائحة (%d مقرر) مرتبة حسب الفصل المقترح.' % len(base)
        cur = sum(1 for c in COURSES if self.rec.get(c.code, {}).get('s') == 'cur')
        info += '\nمنتهي: %d مقرر | يدرسها الآن: %d' % (sum(1 for c in COURSES if self.is_passed(c.code)), cur)
        box.add_widget(ALabel(info, size=13, color=MUTED))

        # فلاتر
        q = TInput(text=self.f_q, hint_text='بحث بالاسم أو الكود')
        q.bind(text=lambda w, v: setattr(self, 'f_q', v))
        q.bind(on_text_validate=lambda *a: self.show_tab(1))
        go = Btn('بحث', bg=GOLD, fg=DARK, size_hint_x=None, width=dp(70), h=46)
        go.bind(on_release=lambda *a: self.show_tab(1))
        box.add_widget(hrow(go, q))
        box.add_widget(seg([('ALL', 'الكل'), ('R', 'إجباري'), ('E', 'اختياري')], self.f_kind,
                           lambda k: (setattr(self, 'f_kind', k), self.show_tab(1)), h=40))
        box.add_widget(toggle('إخفاء اللي خلّصته', self.f_left, lambda v: (setattr(self, 'f_left', v), self.show_tab(1))))

        # أدوات
        a = Btn('وصلت لحد فصل…', h=44, size=13)
        a.bind(on_release=lambda *x: self.wizard())
        b = Btn('علّم الفصل كله', h=44, size=13)
        b.bind(on_release=lambda *x: self.mark_sem())
        d = Btn('مسح الكل', bg=RED_BG, fg=RED, h=44, size=13)
        d.bind(on_release=lambda *x: confirm_popup('تأكيد', 'مسح كل المقررات المعلّمة؟', self.clear_all) if self.rec else None)
        box.add_widget(hrow(d, b, a, h=44))
        box.add_widget(ALabel('اضغط على المربع للتعليم السريع، وعلى «تقدير» لاختيار التقدير أو «يدرسه الآن» أو «راسب».',
                              size=12, color=MUTED))

        for c in self.visible_courses():
            box.add_widget(self.course_row(c))

    def course_row(self, c):
        e = self.rec.get(c.code, {})
        s, g = e.get('s', 'none'), e.get('g', '')
        fail = s == 'done' and g == 'F'
        low = s == 'done' and g in ('D', 'D+')
        if fail:
            bg, sym, col = RED_BG, '✗', RED
        elif low:
            bg, sym, col = AMBER_BG, '☑', AMBER
        elif s == 'done':
            bg, sym, col = GREEN_BG, '☑', GREEN
        elif s == 'cur':
            bg, sym, col = BLUE_BG, '◔', BLUE
        else:
            bg, sym, col = CARD, '☐', MUTED
        card = Card(bg=bg, pad=10, spacing=4, radius=14)
        top = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(52), spacing=dp(8))
        chk = Btn(sym, bg=CARD2, fg=col, size=26, h=48, size_hint_x=None, width=dp(54), bold=False)
        chk.pos_hint = {'center_y': .5}
        chk.bind(on_release=lambda *a: (self.set_status([c.code], 'none') if s != 'none' else self.set_status([c.code], 'done'),
                                        self.show_tab(1)))
        gb = Btn(('تقدير ' + g) if g else 'تقدير', size=12, h=40, size_hint_x=None, width=dp(86))
        gb.pos_hint = {'center_y': .5}
        gb.bind(on_release=lambda *a: self.status_menu(c))
        title = ALabel(c.name, size=15, bold=True, pos_hint={'center_y': .5})
        top.add_widget(chk)
        top.add_widget(gb)
        top.add_widget(title)
        title.bind(height=lambda w, hh: setattr(top, 'height', max(dp(52), hh + dp(6))))
        card.add_widget(top)
        pre = '، '.join(C[p].name for p in pre_of(c.code, self.set)) or '—'
        meta = '%s  •  %d ساعة  •  فصل %s  •  %s — %s' % (c.code, c.cr, c.sem if c.sem else '—',
                                                         'إجباري' if c.kind == 'R' else 'اختياري', KIND_TXT[c.grp])
        card.add_widget(ALabel(meta, size=12, color=MUTED))
        card.add_widget(ALabel('المتطلب السابق: ' + pre, size=12, color=MUTED))
        return card

    def status_menu(self, c):
        opts = [('done:', 'منتهٍ (بدون تقدير)')]
        opts += [('done:' + g, 'منتهٍ — تقدير ' + g) for g in GRADE_LIST[:-1]]
        opts += [('done:F', 'راسب (F)'), ('cur:', 'يدرسه الآن'), ('none:', 'لم يدرسه')]

        def pick(k):
            st, g = k.split(':')
            self.set_status([c.code], st, g)
            self.show_tab(1)
        choice_popup(c.name, opts, pick)

    def wizard(self):
        from ui import open_popup
        root = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(8))
        root.add_widget(ALabel('أنهيت المقررات الإجبارية حتى الفصل رقم:', size=16, bold=True, halign='center'))
        val = [6]
        lbl_wrap = [None]
        st = stepper(6, 0, 10, lambda v: val.__setitem__(0, v))
        root.add_widget(st)
        root.add_widget(ALabel('هيعلّم كل الإجباري في الفصول 1…N كمنتهٍ. بعدها عدّل اللي رسبت فيه أو لسه ما أخذتوش، وأضف الاختياري اللي درسته.',
                               size=13, color=MUTED))
        rep = [False]
        root.add_widget(toggle('امسح اختياراتي الحالية أولاً', False, lambda v: rep.__setitem__(0, v)))
        p = open_popup('مساعد سريع', root, (0.9, 0.62))
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(48), spacing=dp(8))
        no = Btn('إلغاء', h=48)
        ok = Btn('تطبيق', bg=GOLD, fg=DARK, h=48)
        no.bind(on_release=lambda *a: p.dismiss())

        def go(*a):
            if rep[0]:
                self.rec = {}
            for c in COURSES:
                if c.kind == 'R' and 0 < c.sem <= val[0] and c.code not in self.rec:
                    self.rec[c.code] = {'s': 'done', 'g': ''}
            p.dismiss()
            self.changed()
            self.show_tab(1)
        ok.bind(on_release=go)
        row.add_widget(no)
        row.add_widget(ok)
        root.add_widget(row)

    def mark_sem(self):
        if not self.view.isdigit():
            info_popup('تنبيه', 'اختار جدول فصل معين (ف 1 … ف 10) الأول.', size=(0.85, 0.3))
            return
        for c in COURSES:
            if c.sem == int(self.view) and c.kind == 'R' and c.code not in self.rec:
                self.rec[c.code] = {'s': 'done', 'g': ''}
        self.changed()
        self.show_tab(1)

    def clear_all(self):
        self.rec = {}
        self.changed()
        self.show_tab(1)

    # ───────────────── ٣) حالتي ─────────────────
    def t_dash(self, box, p):
        an, my = p['an'], p['my']
        done_h = an['counted'] + an['cur_hours']
        if my is None:
            grad = '—'
        elif not my['terms']:
            grad = 'جاهز'
        else:
            grad = my['finish_label']
        tiles = [('الساعات المنجزة', '%d / %d' % (done_h, TOTAL_REQUIRED), GOLD),
                 ('المتبقي', '%d ساعة' % an['remaining'], TEAL),
                 ('المعدل التراكمي', '%.2f' % an['gpa'] if an['gpa'] is not None else '—',
                  RED if an['probation'] else GREEN),
                 ('التخرج المتوقع', grad, BLUE)]
        grid = GridLayout(cols=2, size_hint_y=None, spacing=dp(10), row_default_height=dp(92), row_force_default=True)
        grid.bind(minimum_height=grid.setter('height'))
        for t, v, col in tiles:
            cd = Card(spacing=2, pad=10, auto=False)
            cd.add_widget(ALabel(t, size=12, color=MUTED, halign='center'))
            cd.add_widget(ALabel(v, size=17, bold=True, color=col, halign='center'))
            grid.add_widget(cd)
        box.add_widget(grid)

        c = Card()
        pct = int(100.0 * done_h / TOTAL_REQUIRED)
        c.add_widget(ALabel('%d%% من متطلبات التخرج%s' % (pct, ('  —  الفصول المتبقية: %d' % my['n_terms']) if my and my['terms'] else ''),
                            size=14, bold=True))
        c.add_widget(Bar(done_h / float(TOTAL_REQUIRED)))
        box.add_widget(c)

        c = Card()
        c.add_widget(sec('التقدم في كل مجموعة'))
        for g in ('univ', 'college', 'major', 'sub'):
            gi = an['groups'][g]
            d = gi['req_done'] + gi['req_cur']
            el = '%d / %d' % (gi['e_done'] + gi['e_cur'], gi['e_min']) if 'e_min' in gi else '—'
            tot = gi['req_total'] + gi.get('e_min', 0)
            dn = d + min(gi.get('e_done', 0) + gi.get('e_cur', 0), gi.get('e_min', 0))
            c.add_widget(ALabel(GROUP_NAME[g], size=14, bold=True))
            c.add_widget(ALabel('إجباري %d / %d   |   اختياري %s' % (d, gi['req_total'], el), size=12, color=MUTED))
            c.add_widget(Bar(dn / float(tot) if tot else 0, color=TEAL, height=dp(8)))
        box.add_widget(c)

        c = Card()
        c.add_widget(sec('شروط التخرج'))
        sym = {'ok': ('✔', GREEN), 'no': ('✘', RED), 'unk': ('؟', AMBER), 'wait': ('…', MUTED)}
        for t, s_, d in p['check']:
            mk, col = sym.get(s_, ('', TEXT))
            r = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(8))
            body = ALabel('%s — %s' % (t, d), size=13, pos_hint={'center_y': .5})
            mark = ALabel(mk, size=20, bold=True, color=col, halign='center', size_hint_x=None, width=dp(30),
                          pos_hint={'center_y': .5})
            r.add_widget(mark)
            r.add_widget(body)
            body.bind(height=lambda w, hh, r=r: setattr(r, 'height', max(dp(36), hh + dp(6))))
            c.add_widget(r)
        box.add_widget(c)

        c = Card()
        c.add_widget(sec('إيه اللي بيأخّرني؟'))
        colors = {'ok': GREEN, 'info': TEXT, 'warn': AMBER, 'bad': RED}
        for k, m in p['diag']:
            c.add_widget(ALabel('• ' + m, size=14, color=colors.get(k, TEXT)))
        box.add_widget(c)
