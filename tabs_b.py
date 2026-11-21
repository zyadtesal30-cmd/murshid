# -*- coding: utf-8 -*-
"""الشاشات: ٤) القسم  ٥) تسجيل  ٦) خطتي"""
from kivy.core.clipboard import Clipboard
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

import engine as E
from engine import C, COURSES, PROBATION_LOAD, Student, pre_of, recommended_codes, term_label, term_offers
from tabs_a import KIND_TXT, lab_row, sec
from ui import (AMBER, AMBER_BG, BLUE, BLUE_BG, CARD, CARD2, DARK, GOLD, GREEN, GREEN_BG, MUTED, RED, TEAL, TEXT,
                ALabel, Btn, Card, TapCard, TInput, choice_popup, hrow, info_popup, open_popup, seg, stepper)

SUMMER_KEY = 'SUMMER*'
LEVEL_TXT = {'crit': 'لازم يتفتح', 'imp': 'يفضل يتفتح', 'ok': 'ممكن بديل'}
LEVEL_COL = {'crit': RED, 'imp': AMBER, 'ok': GREEN}
STATE_TXT = {'open': '✔ مفتوح', 'closed': '✘ مش مفتوح', 'unknown': '؟ لسه ما أعلنوش'}
PICK_BG = (0.30, 0.25, 0.08, 1)


class TabsB:
    # ───────────────── ٤) القسم ─────────────────
    def dept_scopes(self):
        s = self.set
        offers = s.setdefault('offers', {})
        out = []
        for typ, yr in E.term_sequence(s['start_type'], s['start_year'], 6, s.get('use_summer', True)):
            k = E.tkey(typ, yr)
            out.append((k, term_label(typ, yr, s['months']) + ('   ✔ معلن' if k in offers else '')))
        if s.get('use_summer', True):
            out.append((SUMMER_KEY, 'كل الصيفيات (افتراضي)' + ('   ✔' if s.get('summer_codes') is not None else '')))
        return out

    def load_dept_scope(self):
        s = self.set
        codes = s.get('summer_codes') if self.dept_key == SUMMER_KEY else s.setdefault('offers', {}).get(self.dept_key)
        self.dept_mode = 'auto' if codes is None else 'list'
        self.dept_sel = set(codes or [])

    def dept_save(self):
        s = self.set
        val = sorted(self.dept_sel) if self.dept_mode == 'list' else None
        if self.dept_key == SUMMER_KEY:
            s['summer_codes'] = val
        elif val is None:
            s.setdefault('offers', {}).pop(self.dept_key, None)
        else:
            s.setdefault('offers', {})[self.dept_key] = val
        self.changed()

    def dept_rows(self):
        st = Student(self.rec)
        q = self.dept_q.strip().lower()
        rows = []
        for c in COURSES:
            if q and q not in c.name.lower() and q not in c.code.lower():
                continue
            passed = st.passed(c.code) and not st.low(c.code)
            missing = [p for p in pre_of(c.code, self.set) if not st.satisfied(p)]
            if self.dept_filter == 'avail' and (passed or st.cur(c.code) or missing):
                continue
            if self.dept_filter == 'req' and (c.kind != 'R' or passed or st.cur(c.code)):
                continue
            note = ('خلّصته' if passed else 'بتدرسه الآن' if st.cur(c.code) else
                    ('ناقص متطلب: ' + '، '.join(C[p].name for p in missing)) if missing else 'جاهز ليك ✔')
            rows.append((c, note))
        rows.sort(key=lambda r: (r[0].sem if r[0].sem else 99, 0 if r[0].kind == 'R' else 1, r[0].code))
        return rows

    def t_dept(self, box):
        scopes = self.dept_scopes()
        keys = [k for k, _ in scopes]
        if self.dept_key not in keys:
            self.dept_key = keys[0]
            self.load_dept_scope()
        label = dict(scopes)[self.dept_key]

        c = Card()
        c.add_widget(sec('الفصل اللي بتسجّل فيه'))
        b = Btn(label + '   ▼', bg=GOLD, fg=DARK, h=50)

        def pick_scope(k):
            self.dept_key = k
            self.load_dept_scope()
            self.show_tab(3, top=True)
        b.bind(on_release=lambda *a: choice_popup('اختار الفصل', scopes, pick_scope))
        c.add_widget(b)

        def set_mode(m):
            self.dept_mode = m
            self.dept_save()
            self.show_tab(3)
        c.add_widget(seg([('auto', 'لسه ما أعلنوش'), ('list', 'القسم أعلن مواد')], self.dept_mode, set_mode))
        c.add_widget(ALabel('لو القسم ما أعلنش، البرنامج بيفترض إن كل مقرر بيتفتح في نوع فصله المعتاد. '
                            'لو أعلن، علّم المواد المفتوحة وهيتسجّل منها فقط.', size=12, color=MUTED))
        if self.dept_mode == 'list':
            c.add_widget(ALabel('علّمت %d مادة مفتوحة.' % len(self.dept_sel), size=14, bold=True, color=GREEN))
        box.add_widget(c)

        # ─ طلب المواد الحرجة ─
        c = Card()
        c.add_widget(sec('إيه اللازم يتفتح؟'))
        c.add_widget(lab_row('أبحث في أول (عدد) فصول', stepper(self.set.get('look', 2), 1, 4,
                                                              lambda v: (self.set.__setitem__('look', v), self.changed()))))
        go = Btn('اعرف إيه اللازم يتفتح', bg=GOLD, fg=DARK, h=50)
        go.bind(on_release=lambda *a: self.compute_crit())
        c.add_widget(go)
        self.show_crit(c)
        box.add_widget(c)

        # ─ اختيار المواد المفتوحة ─
        box.add_widget(sec('المواد المفتوحة'))
        box.add_widget(seg([('avail', 'المتاحة لي'), ('req', 'الإجباري المتبقي'), ('all', 'كل المواد')], self.dept_filter,
                           lambda k: (setattr(self, 'dept_filter', k), self.show_tab(3)), h=40))
        q = TInput(text=self.dept_q, hint_text='بحث بالاسم أو الكود')
        q.bind(text=lambda w, v: setattr(self, 'dept_q', v))
        q.bind(on_text_validate=lambda *a: self.show_tab(3))
        go2 = Btn('بحث', bg=GOLD, fg=DARK, size_hint_x=None, width=dp(70), h=46)
        go2.bind(on_release=lambda *a: self.show_tab(3))
        box.add_widget(hrow(go2, q))
        rows = self.dept_rows()

        def all_():
            self.dept_mode = 'list'
            self.dept_sel |= {c.code for c, _ in rows}
            self.dept_save()
            self.show_tab(3)

        def clr():
            self.dept_sel = set()
            self.dept_save()
            self.show_tab(3)
        a = Btn('تحديد كل الظاهر', h=44, size=13)
        a.bind(on_release=lambda *x: all_())
        d = Btn('مسح التحديد', h=44, size=13)
        d.bind(on_release=lambda *x: clr())
        box.add_widget(hrow(d, a, h=44))

        for cr, note in rows:
            box.add_widget(self.dept_row(cr, note))

    def dept_row(self, c, note):
        on = c.code in self.dept_sel
        card = TapCard(bg=GREEN_BG if on else CARD, pad=10, spacing=4, radius=14)
        top = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(34), spacing=dp(8))
        chk = ALabel('☑' if on else '☐', size=24, color=GREEN if on else MUTED, halign='center',
                     size_hint_x=None, width=dp(36), pos_hint={'center_y': .5})
        title = ALabel(c.name, size=15, bold=True, pos_hint={'center_y': .5})
        top.add_widget(chk)
        top.add_widget(title)
        title.bind(height=lambda w, hh: setattr(top, 'height', max(dp(34), hh + dp(4))))
        card.add_widget(top)
        card.add_widget(ALabel('%s  •  %d ساعة  •  فصل %s  •  %s — %s' % (
            c.code, c.cr, c.sem if c.sem else '—', 'إجباري' if c.kind == 'R' else 'اختياري', KIND_TXT[c.grp]),
            size=12, color=MUTED))
        card.add_widget(ALabel(note, size=12, color=TEAL if 'جاهز' in note else MUTED))

        def tap(*a):
            self.dept_mode = 'list'
            if c.code in self.dept_sel:
                self.dept_sel.discard(c.code)
            else:
                self.dept_sel.add(c.code)
            self.dept_save()
            on2 = c.code in self.dept_sel
            card.set_bg(GREEN_BG if on2 else CARD)
            chk.color = GREEN if on2 else MUTED
            chk.set('☑' if on2 else '☐')
        card.bind(on_release=tap)
        return card

    def compute_crit(self):
        def with_p(p):
            look = self.set.get('look', 2)

            def done(res):
                self.crit_cache = res
                if self.tab == 3:
                    self.show_tab(3)
            self.run_async(lambda: E.critical_to_open(p['st'], p['cfg'], p['prefs'], look), done)
        self.with_pack(with_p)

    def show_crit(self, card):
        cr = self.crit_cache
        if cr is None:
            card.add_widget(ALabel('اضغط الزر عشان تعرف تطلب من القسم إيه.', size=13, color=MUTED))
            return
        if not cr or not cr['base'] or not cr['base']['terms']:
            card.add_widget(ALabel('مفيش مقررات متبقية تحتاج فتح من القسم.', size=14, color=GREEN))
            return
        items = cr['items']
        n = {k: sum(1 for i in items if i['level'] == k) for k in LEVEL_TXT}
        closed = [i for i in items if i['level'] == 'crit' and i['state'] == 'closed']
        txt = 'لو القسم فتح اللازم هتتخرج %s.\nلازم يتفتح: %d | يفضل: %d | ممكن بديل: %d' % (
            cr['base']['finish_label'], n['crit'], n['imp'], n['ok'])
        card.add_widget(ALabel(txt, size=14, bold=True, color=GOLD))
        if closed:
            card.add_widget(ALabel('⚠ %d مادة لازم تتفتح والقسم مش فاتحها — اطلبها!' % len(closed), size=14, bold=True, color=RED))
        for i in items:
            cd = Card(bg=CARD2, pad=10, spacing=3, radius=12)
            cd.add_widget(ALabel('%s — %s%s' % (i['code'], i['name'], ' (إعادة)' if i['retake'] else ''), size=14, bold=True))
            cd.add_widget(ALabel('%s  •  %s  •  %s' % (i['label'], LEVEL_TXT[i['level']], STATE_TXT[i['state']]),
                                 size=12, color=LEVEL_COL[i['level']]))
            cd.add_widget(ALabel(i['why'], size=12, color=MUTED))
            card.add_widget(cd)
        rq = Btn('نص الطلب الجاهز للقسم', bg=GOLD, fg=DARK, h=50)
        rq.bind(on_release=lambda *a: self.show_request())
        card.add_widget(rq)

    def show_request(self):
        def with_p(p):
            cr = self.crit_cache
            txt = E.dept_request_text(p['cfg'], cr['items'] if cr else [], p['cfg'].get('name', ''))
            if not txt:
                info_popup('طلب للقسم', 'مفيش مقررات حرجة أو مهمة محتاجة طلب خاص — أي مقررات متاحة هتنفع.', size=(0.88, 0.3))
                return
            info_popup('طلب للقسم', txt, [('نسخ', lambda: self.copy_text(txt)), ('مشاركة', lambda: self.share_text(txt))],
                       size=(0.94, 0.85))
        self.with_pack(with_p)

    # ───────────────── ٥) تسجيل ─────────────────
    def reg_key(self):
        return E.tkey(self.set['start_type'], self.set['start_year'])

    def reg_picks(self):
        return set(self.set.setdefault('picks', {}).get(self.reg_key(), [])) & self._reg_ok

    def reg_set_picks(self, s):
        self.set.setdefault('picks', {})[self.reg_key()] = sorted(s)
        self.schedule_save()

    def refresh_reg_total(self, p):
        cfg = p['cfg']
        picks = self.reg_picks()
        tot = sum(C[c].cr for c in picks)
        mx = cfg['cap']
        mn = min(int(cfg.get('min_load') or 0), mx)
        lim = 'الأدنى %d — الأقصى %d' % (mn, mx) if mn else 'الأقصى %d' % mx
        head = 'اخترت %d مادة = %d ساعة  (%s)' % (len(picks), tot, lim)
        if not picks:
            self._reg_tot.set(head + '\nاضغط على مادة عشان تختارها')
            self._reg_tot.color = AMBER
        elif tot > mx:
            self._reg_tot.set(head + '\n✘ زيادة %d ساعة عن الأقصى' % (tot - mx))
            self._reg_tot.color = RED
        elif tot < mn:
            self._reg_tot.set(head + '\n⚠ ناقص %d ساعة عن الأدنى' % (mn - tot))
            self._reg_tot.color = AMBER
        else:
            self._reg_tot.set(head + '\n✔ تمام')
            self._reg_tot.color = GREEN

    def t_reg(self, box, p):
        cfg, my = p['cfg'], p['my']
        nxt = term_label(cfg['start_type'], cfg['start_year'], cfg.get('months'))
        rec, term = recommended_codes(p)
        valid_rec = term is not None and term['typ'] == cfg['start_type'] and term['year'] == cfg['start_year']
        recs = set(rec) if valid_rec else set()
        self._reg_recs = sorted(recs)
        self._reg_ok = {c.code for c, reasons in p['elig'] if not reasons}
        height = my['height'] if my else {}

        c = Card()
        c.add_widget(ALabel('الفصل اللي بتسجّل فيه: %s' % nxt, size=16, bold=True, color=GOLD))
        c.add_widget(ALabel('الموصى بيه: %d مادة (%d ساعة)' % (len(recs), sum(C[x].cr for x in recs)), size=14, color=TEAL))
        notes = []
        off = term_offers(cfg, cfg['start_type'], cfg['start_year'])
        if off is not None:
            notes.append('القسم فاتح %d مادة في الفصل ده — اختار منهم بس.' % len(off))
        if p['an']['probation']:
            notes.append('معدلك أقل من 2.00: أقصى حد %d ساعة.' % PROBATION_LOAD)
        if my and my['terms'] and not valid_rec:
            notes.append('خطتك ما فيهاش مواد في %s — شوف تبويب «خطتي».' % nxt)
        notes.append('أخضر = موصى بيها  •  أزرق = متاحة  •  رمادي = مش متاحة (مكتوب السبب).')
        c.add_widget(ALabel('\n'.join(notes), size=12, color=MUTED))
        box.add_widget(c)

        tc = Card(bg=CARD2)
        self._reg_tot = ALabel('', size=15, bold=True, halign='center')
        tc.add_widget(self._reg_tot)
        box.add_widget(tc)

        a = Btn('اختار الموصى بيه', bg=GOLD, fg=DARK, h=46, size=13)
        d = Btn('مسح اختياراتي', h=46, size=13)
        cp = Btn('نسخ / مشاركة', bg=TEAL, fg=DARK, h=46, size=13)

        def pick_rec(*x):
            self.reg_set_picks(set(self._reg_recs) & self._reg_ok)
            self.show_tab(4)

        def clear(*x):
            self.reg_set_picks(set())
            self.show_tab(4)
        a.bind(on_release=pick_rec)
        d.bind(on_release=clear)
        cp.bind(on_release=lambda *x: self.copy_register())
        box.add_widget(hrow(cp, d, a, h=46))

        picks = self.reg_picks()
        rows = []
        for cr_, reasons in p['elig']:
            if cr_.code in recs:
                state, order = 'rec', 0
            elif not reasons:
                state, order = 'ok', 1
            else:
                state, order = 'no', 2
            h = height.get(cr_.code, 0)
            prio = 'لازم' if h >= 4 else ('مهمة' if h >= 2 else '')
            why = '؛ '.join(reasons) if reasons else ('مطلوبة للتخرج' if cr_.kind == 'R' else (
                'ضمن اختيارات خطتك' if my and cr_.code in my['chosen'] else 'اختيارية'))
            if p['st'].failed(cr_.code):
                why = 'راسب فيها — لازم تعيدها. ' + why
                prio = 'لازم'
            rows.append((order, 0 if prio == 'لازم' else 1, cr_.sem, cr_.code, cr_, state, prio, why))
        for order, _pr, _sem, _code, cr_, state, prio, why in sorted(rows, key=lambda r: r[:4]):
            box.add_widget(self.reg_row(p, cr_, state, prio, why, cr_.code in picks))
        self.refresh_reg_total(p)

    def reg_row(self, p, c, state, prio, why, picked):
        bg = {'rec': GREEN_BG, 'ok': BLUE_BG, 'no': CARD}[state]
        card = TapCard(bg=PICK_BG if picked else bg, pad=10, spacing=4, radius=14)
        top = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(34), spacing=dp(8))
        sym = '☑' if picked else ('☐' if state != 'no' else '')
        chk = ALabel(sym, size=24, color=GOLD, halign='center', size_hint_x=None, width=dp(36), pos_hint={'center_y': .5})
        title = ALabel(c.name, size=15, bold=True, color=MUTED if state == 'no' else TEXT, pos_hint={'center_y': .5})
        top.add_widget(chk)
        top.add_widget(title)
        title.bind(height=lambda w, hh: setattr(top, 'height', max(dp(34), hh + dp(4))))
        card.add_widget(top)
        tag = {'rec': 'موصى بيها', 'ok': 'متاحة', 'no': 'مش متاحة'}[state]
        meta = '%s  •  %d ساعة  •  %s  •  %s — %s%s' % (c.code, c.cr, tag, 'إجباري' if c.kind == 'R' else 'اختياري',
                                                       KIND_TXT[c.grp], ('  •  أولوية: ' + prio) if prio else '')
        card.add_widget(ALabel(meta, size=12, color={'rec': GREEN, 'ok': BLUE, 'no': MUTED}[state]))
        card.add_widget(ALabel(why, size=12, color=MUTED))
        if state == 'no':
            return card

        def tap(*a):
            s = self.reg_picks()
            s.symmetric_difference_update({c.code})
            self.reg_set_picks(s)
            on = c.code in s
            card.set_bg(PICK_BG if on else bg)
            chk.set('☑' if on else '☐')
            self.refresh_reg_total(p)
        card.bind(on_release=tap)
        return card

    def copy_register(self):
        codes = sorted(self.reg_picks()) or self._reg_recs
        if not codes:
            info_popup('تنبيه', 'لسه ما اخترتش مواد.', size=(0.85, 0.28))
            return
        txt = 'موادي للتسجيل:\n' + '\n'.join('%s — %s (%d)' % (c, C[c].name, C[c].cr) for c in codes)
        info_popup('موادي', txt, [('نسخ', lambda: self.copy_text(txt)), ('مشاركة', lambda: self.share_text(txt))], size=(0.92, 0.75))

    # ───────────────── ٦) خطتي ─────────────────
    def t_plan(self, box):
        box.add_widget(seg([('plans', 'الخطط'), ('tracks', 'مسارات الاختياري')], self.plan_sub,
                           lambda k: (setattr(self, 'plan_sub', k), self.show_tab(5, top=True))))
        if self.plan_sub == 'plans':
            self.t_plans(box)
        else:
            self.t_tracks(box)

    def compute_plans(self):
        def with_p(p):
            def done(res):
                self.plans = res
                self._plans_tried = True
                self.plan_sel = res[0][0] if res else None
                if self.tab == 5:
                    self.show_tab(5)
            self.run_async(lambda: E.preset_plans(p['st'], p['cfg'], p['prefs']), done)
        self.with_pack(with_p)

    def t_plans(self, box):
        if not self.plans and not self._plans_tried:
            self.compute_plans()
            return
        b = Btn('إعادة حساب الخطط', bg=GOLD, fg=DARK, h=48)
        b.bind(on_release=lambda *a: self.compute_plans())
        box.add_widget(b)
        if not self.plans:
            box.add_widget(ALabel('تعذّر بناء خطط — راجع المقررات والإعدادات.', size=14, color=RED))
            return
        fast = next((x for x in self.plans if x[0] == 'fast'), None)
        nos = next((x for x in self.plans if x[0] == 'nosum'), None)
        txt = ''
        if fast and nos:
            fp, np_ = fast[4], nos[4]
            if not fp['terms']:
                txt = 'خلّصت كل المقررات — مفيش حاجة تتسجل.'
            elif fp['finish_key'] < np_['finish_key']:
                sm = ['%s (%s)' % (t['label'], '، '.join(C[c].name for c in t['codes'])) for t in fp['terms']
                      if t['typ'] == 'U' and t['codes']]
                txt = 'الصيفي هيخليك تتخرج %s بدل %s.\nالصيفي المطلوب: %s' % (fp['finish_label'], np_['finish_label'], ' | '.join(sm))
            else:
                txt = 'مش محتاج صيفي: بتتخرج %s بالحمل الأقصى سواء نزلت صيفي أو لأ.' % fp['finish_label']
        if txt:
            c = Card(bg=BLUE_BG)
            c.add_widget(ALabel(txt, size=14, bold=True, color=GOLD))
            box.add_widget(c)
        for k, n, cap, s_, pl in self.plans:
            on = k == self.plan_sel
            cd = TapCard(bg=GREEN_BG if on else CARD, pad=12, spacing=3)
            cd.add_widget(ALabel(n, size=15, bold=True, color=GOLD if on else TEXT))
            cd.add_widget(ALabel('التخرج: %s  •  %d فصل  •  %d صيفي' % (pl['finish_label'], pl['n_terms'], pl['n_summers']),
                                 size=13, color=MUTED))
            cd.bind(on_release=lambda w, k=k: (setattr(self, 'plan_sel', k), self.show_tab(5)))
            box.add_widget(cd)
        sel = next((x for x in self.plans if x[0] == self.plan_sel), self.plans[0])
        pl = sel[4]
        box.add_widget(sec('جدول الفصول — ' + sel[1]))
        if not pl['terms']:
            box.add_widget(ALabel('خلّصت كل المتطلبات', size=14, color=GREEN))
            return
        for t in pl['terms']:
            cd = Card(bg=AMBER_BG if t['typ'] == 'U' else CARD, pad=12, spacing=3)
            if not t['codes']:
                cd.add_widget(ALabel(t['label'], size=14, bold=True, color=MUTED))
                cd.add_widget(ALabel('فصل انتظار — مفيش مواد متاحة (بتتفتح في فصل تاني أو القسم مش فاتحها)', size=12, color=MUTED))
            else:
                cd.add_widget(ALabel('%s  —  %d ساعة' % (t['label'], t['credits']), size=14, bold=True, color=GOLD))
                for c in t['codes']:
                    tag = (' (إعادة)' if c in t['retake'] else '') + (' (إضافي)' if c in t.get('extra', ()) else '')
                    cd.add_widget(ALabel('• %s%s (%d)' % (C[c].name, tag, C[c].cr), size=13))
            box.add_widget(cd)

    def compute_tracks(self):
        def with_p(p):
            def done(res):
                self.tracks = res
                self.track_sel = res[0]['key'] if res else None
                if self.tab == 5:
                    self.show_tab(5)
            self.run_async(lambda: E.track_report(p['st'], p['cfg']), done)
        self.with_pack(with_p)

    def t_tracks(self, box):
        cur = next((t[1] for t in E.TRACKS if t[0] == self.set.get('track', 'auto')), 'تلقائي (الأسرع)')
        box.add_widget(ALabel('المسار الحالي: ' + cur, size=14, bold=True, color=TEAL))
        b = Btn('قارن المسارات', bg=GOLD, fg=DARK, h=48)
        b.bind(on_release=lambda *a: self.compute_tracks())
        box.add_widget(b)
        if not self.tracks:
            box.add_widget(ALabel('اضغط «قارن المسارات» عشان تشوف أسرع مسار اختياري ليك.', size=13, color=MUTED))
            return
        p = self.cache
        best = min(r['plan']['finish_key'] for r in self.tracks)
        if p and p['my'] and p['my']['chain']:
            box.add_widget(ALabel('المسار الحرج (أطول سلسلة متطلبات): %s = %d فصل على الأقل' % (
                E.chain_names(p['my']['chain']), len(p['my']['chain'])), size=12, color=MUTED))
        for r in self.tracks:
            pl = r['plan']
            on = r['key'] == self.track_sel
            cd = TapCard(bg=GREEN_BG if pl['finish_key'] == best else CARD, pad=12, spacing=3)
            cd.add_widget(ALabel(r['name'] + ('   ◀' if on else ''), size=15, bold=True, color=GOLD if on else TEXT))
            cd.add_widget(ALabel('التخرج: %s  •  %d فصل  •  %d صيفي' % (pl['finish_label'], pl['n_terms'], pl['n_summers']),
                                 size=13, color=MUTED))
            cd.bind(on_release=lambda w, k=r['key']: (setattr(self, 'track_sel', k), self.show_tab(5)))
            box.add_widget(cd)
        r = next((x for x in self.tracks if x['key'] == self.track_sel), self.tracks[0])
        st = p['st'] if p else Student(self.rec)
        d = Card(bg=CARD2)
        d.add_widget(ALabel(r['name'], size=16, bold=True, color=GOLD))
        d.add_widget(ALabel(r['desc'], size=13, color=MUTED))
        if r['courses']:
            d.add_widget(ALabel('مقررات المسار:', size=14, bold=True, color=TEAL))
            for c in r['courses']:
                mark = '✔ خلصته' if (st.passed(c) or st.cur(c)) else ('● هتدرسه في الخطة' if c in r['plan']['chosen'] else '○ اختياري')
                d.add_widget(ALabel('%s  %s  (%d ساعة)  —  %s' % (mark, C[c].name, C[c].cr, KIND_TXT[C[c].grp]), size=13))
        d.add_widget(ALabel('الاختياري اللي هتدرسه في هذا المسار:', size=14, bold=True, color=TEAL))
        for c in r['chosen']:
            d.add_widget(ALabel('• %s (%d)' % (C[c].name, C[c].cr), size=13))
        box.add_widget(d)
        ad = Btn('اعتمد المسار ده واحسب خطتي', bg=GOLD, fg=DARK, h=52)
        ad.bind(on_release=lambda *a: self.adopt_track(r['key']))
        box.add_widget(ad)

    def adopt_track(self, key):
        self.set['track'] = key
        self.changed()
        self.plan_sub = 'plans'
        self.show_tab(5)
