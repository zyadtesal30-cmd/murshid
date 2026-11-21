#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مرشد الطالب الأكاديمي — هندسة الميكاترونيات والروبوتات الصناعية (بنظام الساعات المعتمدة)
تطوير: Zyad Tarek
=====================================================================
تشغيل:            python student_advisor.py
اختبار بدون واجهة: python student_advisor.py --selftest

الفكرة: الطالب يعلّم المقررات التي أنهاها (وتقديراتها اختيارياً)،
والبرنامج يوضّح له:
  • حالته ومتبقي التخرج (ساعات / مقررات / اختياري)
  • ماذا يمكنه تسجيله الفصل القادم وما الممنوع ولماذا
  • خطة دراسية حتى التخرج (عادية / سريعة / بالصيفي) وكم صيفي يحتاج
  • مسارات الاختياري المقترحة والأسرع منها
  • وإذا كان قريباً من التخرج: لماذا لم يتخرج بعد وما الذي يؤخره
  • شهر بداية كل فصل (خريف / ربيع / صيفي) يظهر بجانب اسم الفصل
  • المقررات التي يفتحها القسم في كل فصل (تُختار منها فقط) + المقررات الحرجة التي يجب طلب فتحها
  • دليل إرشادي خطوة بخطوة داخل البرنامج

الحفظ: Ctrl+S يحفظ بياناتك، وعند فتح البرنامج يفتح آخر ملف حفظته تلقائياً.
المصدر: لائحة قسم الميكاترونيات — كلية الهندسة — جامعة المنيا (2012).
"""
import sys, os, re, json, math, random, copy, threading
import datetime as dt
from html import escape as hesc

APP_TITLE = "مرشد الطالب الأكاديمي — هندسة الميكاترونيات"
DEVELOPER = "Zyad Tarek"
PROJ_EXT = ".advisor"

TERM_NAME = {'F': 'خريف', 'S': 'ربيع', 'U': 'صيفي'}
TERM_KEY = {'S': 1, 'U': 2, 'F': 3}
MONTH_AR = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
DEFAULT_MONTHS = {'F': 10, 'S': 2, 'U': 7}      # شهر بداية كل فصل (قابل للتعديل من «بياناتي»)
AR_DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹', '01234567890123456789')

GRADE_LIST = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'F']
GRADES = {'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7, 'C+': 2.3, 'C': 2.0, 'C-': 1.7,
          'D+': 1.3, 'D': 1.0, 'F': 0.0}

TOTAL_REQUIRED = 175
ELEC_MIN = {'univ': 8, 'major': 10, 'sub': 16}        # الحد الأدنى للاختياري في كل فئة
GROUP_TOTAL = {'univ': 24, 'college': 41, 'major': 57, 'sub': 53}
GROUP_NAME = {'univ': 'متطلبات الجامعة', 'college': 'متطلبات الكلية',
              'major': 'التخصص الرئيسي', 'sub': 'التخصص الفرعي (الميكاترونيات)'}
MAX_LOAD_DEFAULT = 21      # الحد الأقصى لساعات الفصل الأول/الثاني
SUMMER_MAX = 8             # الحد الأقصى للفصل الصيفي (مقرران)
PROBATION_LOAD = 12        # الحد الأقصى لمن معدله أقل من 2.0 (تحت الملاحظة)


class Course:
    __slots__ = ('code', 'name', 'cr', 'sem', 'grp', 'kind', 'pre')

    def __init__(self, code, name, cr, sem, grp, kind, pre):
        self.code, self.name, self.cr, self.sem, self.grp, self.kind, self.pre = code, name, cr, sem, grp, kind, pre


# (الكود، الاسم، الساعات المعتمدة، الفصل الدراسي المقترح، الفئة، النوع R إجباري/E اختياري، المتطلبات السابقة)
_RAW = [
    # ── متطلبات الجامعة (إجباري 16) ──
    ('HUMn 017', 'اللغة الإنجليزية (١)', 2, 1, 'univ', 'R', []),
    ('HUMn 016', 'مقدمة في الحاسب الآلي', 3, 1, 'univ', 'R', []),
    ('CSEn 026', 'برمجة الحاسب الآلي (١)', 3, 2, 'univ', 'R', ['HUMn 016']),
    ('HUMn 028', 'حقوق الإنسان', 2, 2, 'univ', 'R', []),
    ('HUMn 125', 'كتابة التقارير العلمية ومهارات الاتصال', 2, 4, 'univ', 'R', []),
    ('HUMn 225', 'مهارات مهنية وتسويق', 2, 6, 'univ', 'R', []),
    ('HUMn 315', 'حماية البيئة', 2, 7, 'univ', 'R', []),
    # ── متطلبات الجامعة (اختياري: 8 ساعات) ──
    ('HUMn 116', 'مقدمة في تكنولوجيا المعلومات', 2, 3, 'univ', 'E', []),
    ('HUMn 126', 'أخلاقيات المهن الهندسية', 2, 4, 'univ', 'E', []),
    ('HUMn 416', 'حساب التكاليف ودراسة الجدوى', 2, 9, 'univ', 'E', []),
    ('HUMn 419', 'الأثر البيئي للمشروعات', 2, 9, 'univ', 'E', []),
    ('HUMn 426', 'تشريعات وعقود', 2, 10, 'univ', 'E', []),
    # ── متطلبات الكلية (41) ──
    ('BSCn 011', 'رياضيات (١)', 3, 1, 'college', 'R', []),
    ('BSCn 012', 'فيزياء (١)', 3, 1, 'college', 'R', []),
    ('BSCn 014', 'رسم هندسي مدعم بالحاسب', 4, 1, 'college', 'R', []),
    ('PDEn 015', 'تكنولوجيا الإنتاج (١)', 3, 1, 'college', 'R', []),
    ('BSCn 021', 'رياضيات (٢)', 3, 2, 'college', 'R', ['BSCn 011']),
    ('BSCn 022', 'فيزياء (٢)', 3, 2, 'college', 'R', ['BSCn 012']),
    ('BSCn 023', 'ميكانيكا هندسية', 4, 2, 'college', 'R', []),
    ('PDEn 025', 'تكنولوجيا الإنتاج (٢)', 2, 2, 'college', 'R', ['PDEn 015']),
    ('HUMn 027', 'تاريخ الهندسة والتكنولوجيا', 2, 2, 'college', 'R', []),
    ('BSCn 111', 'رياضيات (٣)', 3, 3, 'college', 'R', ['BSCn 021']),
    ('BSCn 113', 'فيزياء (٣)', 3, 3, 'college', 'R', ['BSCn 022']),
    ('ELEn 114', 'هندسة كهربية وإلكترونية', 3, 3, 'college', 'R', []),
    ('HUMn 118', 'اللغة الإنجليزية (٢)', 2, 3, 'college', 'R', ['HUMn 017']),
    ('CSEn 124', 'برمجة الحاسب الآلي (٢)', 3, 4, 'college', 'R', ['CSEn 026']),
    # ── التخصص الرئيسي (إجباري 47) ──
    ('PDEn 112', 'ميكانيكا الآليات (١)', 3, 3, 'major', 'R', ['BSCn 023']),
    ('PDEn 121', 'تصميم أجزاء الماكينات (١)', 3, 4, 'major', 'R', []),
    ('PEEn 122', 'هندسة الموائع والديناميكا الحرارية', 3, 4, 'major', 'R', ['BSCn 012']),
    ('ELEn 123', 'إلكترونيات', 3, 4, 'major', 'R', ['ELEn 114']),
    ('PDEn 211', 'ميكانيكا الآليات (٢)', 3, 5, 'major', 'R', ['PDEn 112']),
    ('PDEn 212', 'القياس وأجهزة القياس', 3, 5, 'major', 'R', []),
    ('ELEn 213', 'دوائر إلكترونية', 3, 5, 'major', 'R', ['ELEn 114']),
    ('PEEn 214', 'منظومات توليد الطاقة', 3, 5, 'major', 'R', ['BSCn 113']),
    ('BSCn 215', 'أمن صناعي ورعاية عمالية', 2, 5, 'major', 'R', []),
    ('PDEn 221', 'تصميم أجزاء الماكينات (٢)', 3, 6, 'major', 'R', ['PDEn 121']),
    ('ELEn 223', 'إلكترونيات صناعية', 3, 6, 'major', 'R', ['ELEn 213']),
    ('ELEn 224', 'المحركات الكهربائية', 3, 6, 'major', 'R', ['ELEn 114']),
    ('PDEn 311', 'الربوتات الصناعية', 3, 7, 'major', 'R', ['PDEn 211']),
    ('PDEn 312', 'تحكم آلي (١)', 3, 7, 'major', 'R', ['BSCn 111']),
    ('PDEn 314', 'تصميم ماكينات الإنتاج', 3, 7, 'major', 'R', ['PDEn 221']),
    ('PDEn 322', 'تحكم آلي (٢)', 3, 8, 'major', 'R', ['PDEn 312']),
    # ── التخصص الرئيسي (اختياري: 10 ساعات) ──
    ('PDEn 115', 'هندسة الإنتاج', 3, 3, 'major', 'E', ['PDEn 025']),
    ('HUMn 117', 'قوانين المهن الهندسية', 2, 3, 'major', 'E', []),
    ('CHEn 119', 'كيمياء هندسية', 3, 3, 'major', 'E', []),
    ('PDEn 127', 'خواص المواد واختباراتها', 3, 4, 'major', 'E', []),
    ('PDEn 128', 'تحليل إجهادات', 3, 4, 'major', 'E', ['BSCn 023']),
    ('PEEn 216', 'ميكانيكا الموائع', 3, 5, 'major', 'E', ['PEEn 122']),
    ('BSCn 217', 'اقتصاد هندسي', 2, 5, 'major', 'E', []),
    ('BSCn 218', 'الإدارة والتسويق', 2, 5, 'major', 'E', []),
    ('PDEn 226', 'التشغيل اللانمطي', 3, 6, 'major', 'E', ['PDEn 115']),
    ('BSCn 327', 'إدارة المشروعات', 2, 8, 'major', 'E', []),
    ('BSCn 024', 'رسم وإسقاط هندسي', 2, 0, 'major', 'E', []),
    # ── التخصص الفرعي (إجباري 37) ──
    ('MREn 222', 'ميكاترونيات (١)', 3, 6, 'sub', 'R', ['ELEn 123']),
    ('MREn 313', 'ميكاترونيات (٢)', 3, 7, 'sub', 'R', ['MREn 222']),
    ('PDEn 321', 'ديناميكا المنظومات', 3, 8, 'sub', 'R', ['PDEn 311']),
    ('PDEn 323', 'ماكينات التشغيل المبرمجة', 3, 8, 'sub', 'R', ['PDEn 314']),
    ('MREn 324', 'معمل ميكاترونيات (١)', 1, 8, 'sub', 'R', ['MREn 313']),
    ('MREn 411', 'نمذجة ومحاكاة المنظومات الديناميكية', 3, 9, 'sub', 'R', ['PDEn 321']),
    ('PDEn 412', 'ربوتات صناعية وأوتوماتيه', 3, 9, 'sub', 'R', ['PDEn 311']),
    ('MREn 413', 'التحكم في العمليات الصناعية', 3, 9, 'sub', 'R', ['PDEn 322']),
    ('MREn 414', 'مشروع تخرج – الميكاترونيات (١)', 4, 9, 'sub', 'R', []),
    ('MREn 421', 'معمل ميكاترونيات (٢)', 1, 10, 'sub', 'R', ['MREn 324']),
    ('MREn 422', 'تصميم نظم الميكاترونيات', 3, 10, 'sub', 'R', ['MREn 222']),
    ('CSEn 423', 'الحاكمات المنطقية المبرمجة (PLC)', 3, 10, 'sub', 'R', []),
    ('MREn 424', 'مشروع تخرج – الميكاترونيات (٢)', 4, 10, 'sub', 'R', []),
    # ── التخصص الفرعي (اختياري: 16 ساعة) ──
    ('PEEn 227', 'المنظومات الهيدروليكية', 3, 6, 'sub', 'E', ['PEEn 216']),
    ('MREn 228', 'سيمنار الميكاترونيات والربوتات (١)', 1, 6, 'sub', 'E', []),
    ('MREn 316', 'ذكاء اصطناعي', 3, 7, 'sub', 'E', []),
    ('MREn 317', 'سيمنار الميكاترونيات والربوتات (٢)', 1, 7, 'sub', 'E', []),
    ('ATEn 318', 'إلكترونيات السيارات', 3, 7, 'sub', 'E', []),
    ('CSEn 325', 'شبكات الحاسبات', 3, 8, 'sub', 'E', []),
    ('CSEn 326', 'أسس المنظومات المنطقية والمعالجات الدقيقة', 3, 8, 'sub', 'E', ['PDEn 312']),
    ('BSCn 328', 'تحليل المخاطر', 2, 8, 'sub', 'E', []),
    ('PDEn 415', 'برمجة ماكينات التشغيل', 3, 9, 'sub', 'E', ['PDEn 323']),
    ('ELEn 417', 'التحكم الرقمي في الأنظمة الميكانيكية', 3, 9, 'sub', 'E', ['PDEn 312']),
    ('ELEn 418', 'المنظومات الكهروهيدروليكية المؤازرة', 3, 9, 'sub', 'E', ['PDEn 312']),
    ('CSEn 425', 'تصميم منظومات رقمية', 3, 10, 'sub', 'E', []),
    ('CSEn 427', 'نظم الحاسبات المدمجة', 3, 10, 'sub', 'E', []),
    ('PDEn 428', 'التصميم والتصنيع بمعاونة الحاسب', 3, 10, 'sub', 'E', []),
]
COURSES = [Course(*r) for r in _RAW]
C = {c.code: c for c in COURSES}
# افتراض من البرنامج (غير مذكور في اللائحة): مشروع التخرج (٢) بعد (١)
EXTRA_PRE = {'MREn 424': ['MREn 414']}


def _check_data():
    for g in GROUP_TOTAL:
        r = sum(c.cr for c in COURSES if c.grp == g and c.kind == 'R')
        e = ELEC_MIN.get(g, 0)
        assert r + e == GROUP_TOTAL[g], (g, r, e)
    assert sum(c.cr for c in COURSES if c.kind == 'R') + sum(ELEC_MIN.values()) == TOTAL_REQUIRED
    for c in COURSES:
        for p in c.pre:
            assert p in C, (c.code, p)


_check_data()

# مسارات اقتراحية للاختياري (اقتراح من البرنامج وليست من اللائحة)
TRACKS = [
    ('control', 'التحكم والروبوتات', 'تحكم رقمي، منظومات مؤازرة، ذكاء اصطناعي',
     ['ELEn 417', 'ELEn 418', 'MREn 316', 'CSEn 326', 'PEEn 227', 'PEEn 216', 'HUMn 126']),
    ('embedded', 'الحاسبات والأنظمة المدمجة', 'معالجات دقيقة، أنظمة مدمجة ورقمية، شبكات',
     ['CSEn 325', 'CSEn 326', 'CSEn 425', 'CSEn 427', 'MREn 316', 'HUMn 116', 'PDEn 128']),
    ('mfg', 'التصنيع والتصميم', 'CNC وCAD/CAM وخواص المواد وتحليل الإجهادات',
     ['PDEn 415', 'PDEn 428', 'PDEn 226', 'PDEn 115', 'PDEn 127', 'PDEn 128', 'BSCn 024', 'HUMn 117']),
    ('energy', 'الطاقة والموائع والسيارات', 'هيدروليك وموائع وإلكترونيات سيارات',
     ['PEEn 216', 'PEEn 227', 'ATEn 318', 'CHEn 119', 'PDEn 128', 'ELEn 418']),
    ('mgmt', 'الإدارة والاقتصاد (الأخف)', 'إدارة مشروعات وتكاليف ومخاطر — مواد أخف في الغالب',
     ['BSCn 327', 'BSCn 217', 'BSCn 218', 'BSCn 328', 'HUMn 416', 'HUMn 419', 'HUMn 426', 'HUMn 126', 'MREn 228', 'MREn 317']),
]


# ───────────────────────── حالة الطالب ─────────────────────────
class Student:
    """rec: كود -> {'s': 'done' | 'cur', 'g': تقدير أو ''}"""

    def __init__(self, rec=None):
        self.rec = rec or {}

    def s(self, c):
        return self.rec.get(c, {}).get('s', 'none')

    def g(self, c):
        return self.rec.get(c, {}).get('g', '')

    def passed(self, c):
        return self.s(c) == 'done' and self.g(c) != 'F'

    def cur(self, c):
        return self.s(c) == 'cur'

    def failed(self, c):
        return self.s(c) == 'done' and self.g(c) == 'F'

    def low(self, c):  # ناجح بتقدير D أو D+ (لا يصلح متطلباً سابقاً — يلزم C- على الأقل)
        return self.passed(c) and self.g(c) in ('D', 'D+')

    def satisfied(self, c):  # يُعتبر مكتملاً كمتطلب سابق
        return (self.passed(c) and not self.low(c)) or self.cur(c)


def pre_of(code, cfg):
    p = list(C[code].pre)
    if cfg.get('proj_order', True):
        p += EXTRA_PRE.get(code, [])
    return p


def calc_gpa(st):
    num = den = 0.0
    for c in COURSES:
        g = st.g(c.code)
        if st.s(c.code) == 'done' and g in GRADES:
            num += GRADES[g] * c.cr
            den += c.cr
    return (num / den if den else None), den


# ───────────────────────── التحليل العام ─────────────────────────
def analyze(st, cfg):
    an = {'groups': {}, 'req_left': [], 'fail': [], 'low': [], 'cur': [], 'done_n': 0}
    counted = 0
    for g in ('univ', 'college', 'major', 'sub'):
        req = [c for c in COURSES if c.grp == g and c.kind == 'R']
        req_done = sum(c.cr for c in req if st.passed(c.code))
        req_cur = sum(c.cr for c in req if st.cur(c.code))
        left = [c for c in req if not st.passed(c.code) and not st.cur(c.code)]
        info = {'req_total': sum(c.cr for c in req), 'req_done': req_done, 'req_cur': req_cur, 'left': left}
        if g in ELEC_MIN:
            el = [c for c in COURSES if c.grp == g and c.kind == 'E']
            e_done = sum(c.cr for c in el if st.passed(c.code))
            e_cur = sum(c.cr for c in el if st.cur(c.code))
            info.update(e_min=ELEC_MIN[g], e_done=e_done, e_cur=e_cur,
                        e_need=max(0, ELEC_MIN[g] - e_done - e_cur), e_courses=el)
            counted += min(e_done, ELEC_MIN[g])
        counted += req_done
        an['groups'][g] = info
        an['req_left'] += left
    an['counted'] = counted
    cur_h = sum(c.cr for c in COURSES if st.cur(c.code))
    an['cur_hours'] = cur_h
    an['remaining'] = max(0, TOTAL_REQUIRED - counted - cur_h)
    an['fail'] = [c for c in COURSES if st.failed(c.code)]
    an['low'] = [c for c in COURSES if st.low(c.code)]
    an['cur'] = [c for c in COURSES if st.cur(c.code)]
    an['done_n'] = sum(1 for c in COURSES if st.passed(c.code))
    gpa, gh = calc_gpa(st)
    an['gpa_calc'], an['gpa_hours'] = gpa, gh
    g = gpa if gpa is not None else cfg.get('gpa_manual')
    an['gpa'] = g
    an['probation'] = g is not None and g < 2.0
    return an


# ───────────────────────── التقويم والتخطيط ─────────────────────────
def term_label(typ, year, months=None):
    """اسم الفصل مع شهر بدايته، مثلاً: خريف 2026 (أكتوبر)"""
    try:
        m = int((months or {}).get(typ, 0))
    except (TypeError, ValueError):
        m = 0
    if 1 <= m <= 12:
        return '%s %d (%s)' % (TERM_NAME[typ], year, MONTH_AR[m - 1])
    return '%s %d' % (TERM_NAME[typ], year)


def tkey(typ, year):
    return '%s-%d' % (typ, year)


def term_offers(cfg, typ, year):
    """قائمة المقررات التي أعلن القسم فتحها في فصل معين (None = لم يُعلن بعد)."""
    lst = (cfg.get('offers') or {}).get(tkey(typ, year))
    return None if lst is None else set(lst)


def term_sequence(start_type, start_year, n=36, use_summer=True, disabled=()):
    seq = []
    typ, yr = start_type, start_year
    while len(seq) < n:
        if not (typ == 'U' and (not use_summer or (typ, yr) in disabled)):
            seq.append((typ, yr))
        if typ == 'F':
            typ, yr = 'S', yr + 1
        elif typ == 'S':
            typ = 'U'
        else:
            typ = 'F'
    return seq


def offered(code, typ, cfg, year=None):
    if year is not None:
        if (code, typ, year) in (cfg.get('block') or ()):
            return False
        lst = term_offers(cfg, typ, year)
        if lst is not None:          # القسم أعلن قائمة محددة لهذا الفصل: لا يُسجَّل غيرها
            return code in lst
    if typ == 'U':
        sc = cfg.get('summer_codes')
        return sc is None or code in sc
    if not cfg.get('parity', True):
        return True
    s = C[code].sem
    if s == 0:
        return True
    return (s % 2 == 1) == (typ == 'F')


def closure_unmet(code, st, cfg, skip=()):
    out, stack = set(), [code]
    while stack:
        x = stack.pop()
        if x in out:
            continue
        out.add(x)
        for p in pre_of(x, cfg):
            if not st.satisfied(p) and p not in skip:
                stack.append(p)
    return out


def choose_electives(st, cfg, prefs, pend_req):
    prefs = prefs or set()
    chosen = set()

    def hrs(grp):
        return sum(C[c].cr for c in chosen if C[c].grp == grp and C[c].kind == 'E')

    done_e = {g: sum(c.cr for c in COURSES if c.grp == g and c.kind == 'E' and (st.passed(c.code) or st.cur(c.code)))
              for g in ELEC_MIN}
    for grp in ('sub', 'major', 'univ'):
        guard = 0
        while done_e[grp] + hrs(grp) < ELEC_MIN[grp] and guard < 30:
            guard += 1
            need = ELEC_MIN[grp] - done_e[grp] - hrs(grp)
            cands = [c for c in COURSES if c.grp == grp and c.kind == 'E' and c.code not in chosen
                     and not st.passed(c.code) and not st.cur(c.code)]
            if not cands:
                break

            def score(c):
                cl = closure_unmet(c.code, st, cfg, skip=pend_req | chosen)
                extra = len(cl) - 1
                gain = sum(C[x].cr for x in cl if C[x].grp == grp and C[x].kind == 'E')
                return (extra, 0 if c.code in prefs else 1, max(0, gain - need), c.sem, c.code)
            best = min(cands, key=score)
            chosen |= closure_unmet(best.code, st, cfg, skip=pend_req | chosen)
    return chosen


def build_pending(st, cfg, prefs=None):
    pend = {c.code for c in COURSES if c.kind == 'R' and not st.passed(c.code) and not st.cur(c.code)}
    chosen = choose_electives(st, cfg, prefs, pend)
    retake = set()
    for x in chosen:
        if st.passed(x):
            retake.add(x)
        else:
            pend.add(x)
    changed = True
    while changed:
        changed = False
        for c in list(pend | retake):
            for p in pre_of(c, cfg):
                if not st.satisfied(p) and p not in pend and p not in retake:
                    (retake if st.passed(p) else pend).add(p)
                    changed = True
    return pend, retake, chosen


def make_plan(st, cfg, prefs=None, runs=40, seed=1, disabled=(), pending=None):
    rng = random.Random(seed)
    pend, retake, chosen = pending if pending else build_pending(st, cfg, prefs)
    allc = sorted(pend | retake)
    seq = term_sequence(cfg['start_type'], cfg['start_year'], 40, cfg.get('use_summer', True), disabled)
    if not allc:
        return {'terms': [], 'finish_key': 0, 'finish_label': 'خلّصت كل المتطلبات', 'n_terms': 0, 'n_summers': 0,
                'pend': pend, 'retake': retake, 'chosen': chosen, 'height': {}, 'chain': []}
    pset = set(allc)
    preq = {c: [p for p in pre_of(c, cfg) if p in pset] for c in allc}
    deps = {c: [] for c in allc}
    for c in allc:
        for p in preq[c]:
            deps[p].append(c)
    height = {}

    def h(c):
        if c in height:
            return height[c]
        height[c] = 1 + max([h(d) for d in deps[c]] or [0])
        return height[c]
    for c in allc:
        h(c)
    cap = cfg.get('cap', MAX_LOAD_DEFAULT)
    best = None
    for r in range(runs):
        noise = 0 if r == 0 else 2.0
        pr = {c: height[c] + rng.random() * noise + 0.05 * C[c].cr + (0.3 if c in retake else 0) for c in allc}
        rem = set(allc)
        done = set()
        terms = []
        for (typ, yr) in seq:
            if not rem:
                break
            lim = SUMMER_MAX if typ == 'U' else cap
            avail = [c for c in rem if all(p in done for p in preq[c]) and offered(c, typ, cfg, yr)]
            avail.sort(key=lambda c: -pr[c])
            ch, load = [], 0
            for c in avail:
                if load + C[c].cr <= lim and not (typ == 'U' and len(ch) >= 2):
                    ch.append(c)
                    load += C[c].cr
            extra = []
            mn = min(int(cfg.get('min_load') or 0), cap)
            if typ != 'U' and mn and load < mn and (rem - set(ch)):
                # الحد الأدنى للساعات: نكمّل بمواد اختيارية إضافية متاحة (مش لازمة للتخرج)
                while load < mn:
                    fill = [c for c in COURSES if c.kind == 'E' and c.code not in pset and c.code not in ch
                            and not st.passed(c.code) and not st.cur(c.code) and offered(c.code, typ, cfg, yr)
                            and load + c.cr <= lim
                            and all(st.satisfied(p) or p in done or p in ch for p in pre_of(c.code, cfg))]
                    if not fill:
                        break
                    f = min(fill, key=lambda c: (abs(mn - (load + c.cr)), c.sem, c.code))
                    ch.append(f.code)
                    extra.append(f.code)
                    load += f.cr
            terms.append({'typ': typ, 'year': yr, 'label': term_label(typ, yr, cfg.get('months')), 'codes': ch, 'credits': load,
                          'retake': [c for c in ch if c in retake], 'extra': extra})
            done |= set(ch)
            rem -= set(ch)
        if rem:
            continue
        n = len(terms)
        key = (n, max(t['credits'] for t in terms), sum(t['credits'] ** 2 for t in terms))
        if best is None or key < best[0]:
            best = (key, terms)
    if best is None:
        return None
    terms = best[1]
    last = terms[-1]
    chain = []
    if height:
        top = max(allc, key=lambda c: (height[c], -C[c].sem))
        cur = top
        # أطول سلسلة (من آخر مقرر للخلف نعيد بناءها للأمام)
        chain = [top]
        while deps[cur]:
            cur = max(deps[cur], key=lambda d: height[d])
            chain.append(cur)
    return {'terms': terms, 'finish_key': last['year'] * 10 + TERM_KEY[last['typ']], 'finish_label': last['label'],
            'n_terms': len(terms), 'n_summers': sum(1 for t in terms if t['typ'] == 'U' and t['codes']),
            'pend': pend, 'retake': retake, 'chosen': chosen, 'height': height, 'chain': chain}


def plan_min_summers(st, cfg, prefs=None, runs=40):
    """أسرع خطة بالصيفي، ثم نحاول إلغاء أي صيفي غير لازم دون تأخير التخرج."""
    c1 = dict(cfg, use_summer=True)
    pending = build_pending(st, c1, prefs)
    base = make_plan(st, c1, prefs, runs, pending=pending)
    if base is None or not base['terms']:
        return base
    disabled = set()
    cur = base
    used = [(t['typ'], t['year']) for t in cur['terms'] if t['typ'] == 'U' and t['codes']]
    used.sort(key=lambda k: sum(len(t['codes']) for t in cur['terms'] if (t['typ'], t['year']) == k))
    for k in used:
        trial = make_plan(st, c1, prefs, runs, disabled=disabled | {k}, pending=pending)
        if trial and trial['finish_key'] <= base['finish_key']:
            disabled.add(k)
            cur = trial
    return cur


def preset_plans(st, cfg, prefs=None):
    """مقارنة خطط جاهزة."""
    out = []
    pend = build_pending(st, dict(cfg), prefs)
    probation_cap = PROBATION_LOAD if cfg.get('probation') else None
    cap21 = min(MAX_LOAD_DEFAULT, probation_cap or 99)
    specs = [('fast', 'الأسرع: %d ساعة + صيفي' % cap21, cap21, True),
             ('nosum', 'سريعة بدون صيفي (%d ساعة)' % cap21, cap21, False),
             ('norm', 'عادية (18 ساعة)', min(18, cap21), False),
             ('easy', 'مريحة (15 ساعة)', min(15, cap21), False)]
    if cfg.get('custom_cap'):
        specs.append(('custom', 'مخصصة (%d ساعة%s)' % (cfg['custom_cap'], ' + صيفي' if cfg.get('custom_summer') else ''),
                      cfg['custom_cap'], bool(cfg.get('custom_summer'))))
    for key, name, cap, summer in specs:
        c2 = dict(cfg, cap=cap, use_summer=summer)
        pl = plan_min_summers(st, c2, prefs) if summer else make_plan(st, c2, prefs, pending=pend)
        if pl is not None:
            out.append((key, name, cap, summer, pl))
    return out


# ───────────────────────── التسجيل القادم ─────────────────────────
def eligible_now(st, cfg):
    typ, yr = cfg['start_type'], cfg['start_year']
    rows = []
    for c in COURSES:
        if st.passed(c.code) and not st.low(c.code):
            continue
        if st.cur(c.code):
            continue
        if st.low(c.code):
            continue
        missing = [p for p in pre_of(c.code, cfg) if not st.satisfied(p)]
        reasons = []
        if missing:
            reasons.append('محتاج الأول: ' + '، '.join(C[p].name for p in missing))
        if not offered(c.code, typ, cfg, yr):
            if term_offers(cfg, typ, yr) is not None:
                reasons.append('القسم مش فاتحه الفصل ده')
            elif typ == 'U':
                reasons.append('مش من مقررات الصيفي')
            else:
                want = 'الخريف' if (c.sem % 2 == 1) else 'الربيع'
                reasons.append('بيتطرح في فصل %s' % want)
        rows.append((c, reasons))
    return rows


# ───────────────────────── شروط التخرج والتشخيص ─────────────────────────
def checklist(st, cfg, an):
    items = []
    left_req = an['req_left']
    items.append(('كل المقررات الإجبارية', 'ok' if not left_req and not any(
        c.kind == 'R' and st.cur(c.code) for c in COURSES) else ('wait' if not left_req else 'no'),
        'باقي %d مقرر إجباري' % len(left_req) if left_req else
        ('مقررات إجبارية قيد الدراسة الآن' if any(c.kind == 'R' and st.cur(c.code) for c in COURSES) else 'مكتملة')))
    for g in ('univ', 'major', 'sub'):
        gi = an['groups'][g]
        ok = gi['e_need'] == 0
        det = 'تمام (%d من %d ساعة)' % (gi['e_done'] + gi['e_cur'], gi['e_min']) if ok else \
            'ناقص %d ساعة اختياري' % gi['e_need']
        items.append(('اختياري — ' + GROUP_NAME[g], 'ok' if ok else 'no', det))
    items.append(('إجمالي الساعات المعتمدة (%d)' % TOTAL_REQUIRED,
                  'ok' if an['remaining'] == 0 else 'no',
                  'محسوب %d ساعة — باقي %d' % (an['counted'] + an['cur_hours'], an['remaining'])))
    g = an['gpa']
    if g is None:
        items.append(('المعدل التراكمي ≥ 2.00', 'unk', 'لم تُدخل تقديرات ولا معدل'))
    else:
        items.append(('المعدل التراكمي ≥ 2.00', 'ok' if g >= 2.0 else 'no', 'معدلك %.2f' % g))
    items.append(('التدريب الصيفي (٦ أسابيع)', 'ok' if cfg.get('training') else 'unk',
                  'تم' if cfg.get('training') else 'علّم عليه لو أنهيته (مطلوب للتخرج)'))
    if an['fail']:
        items.append(('مقررات راسب فيها', 'no', '، '.join(c.name for c in an['fail'])))
    return items


def chain_names(chain):
    return ' ← '.join(C[c].name for c in reversed(chain)) if chain else ''


def diagnose(st, cfg, an, plan):
    """رسائل تشرح وضع الطالب وسبب التأخير. [(نوع, نص)]  نوع: ok/info/warn/bad"""
    msgs = []
    rem = an['remaining']
    if plan is None:
        return [('bad', 'تعذّر بناء خطة: راجع المقررات المحددة والإعدادات.')]
    pend = plan['pend']
    hours_pend = sum(C[c].cr for c in pend)
    if not plan['terms']:
        msgs.append(('ok', 'لا يوجد مقررات متبقية — لو معدلك ≥ 2.00 ومعاك التدريب الصيفي تقدر تتقدم للتخرج.'))
    else:
        msgs.append(('info', 'باقي لك %d ساعة معتمدة تقريباً (%d مقرر) وتتخرج — حسب الخطة الحالية — في %s (%d فصل%s).' % (
            hours_pend, len(pend), plan['finish_label'], plan['n_terms'],
            '، منها %d صيفي' % plan['n_summers'] if plan['n_summers'] else '')))
    cap = cfg.get('cap', MAX_LOAD_DEFAULT)
    if an['fail']:
        msgs.append(('bad', 'عندك مقررات راسب فيها لازم تعيدها: ' + '، '.join(c.name for c in an['fail']) +
                     '. (التقدير في الإعادة بيتحسب بحد أقصى C)'))
    blockers = [c for c in an['low'] if any(c.code in pre_of(x, cfg) for x in pend)]
    for c in blockers:
        deps = [C[x].name for x in pend if c.code in pre_of(x, cfg)]
        msgs.append(('warn', 'تقديرك في «%s» (%s) أقل من C- فلا يكفي كمتطلب سابق لـ: %s — لازم تعيده.' % (
            c.name, st.g(c.code), '، '.join(deps))))
    if an['probation']:
        msgs.append(('bad', 'معدلك %.2f أقل من 2.00: لازم ترفعه عشان تتخرج، والحد الأقصى للتسجيل %d ساعة. '
                            'أعد مقررات ذات تقدير D أو D+ لرفع المعدل.' % (an['gpa'], PROBATION_LOAD)))
        need = gpa_gap(st, an)
        if need:
            msgs.append(('info', need))
    for g in ('univ', 'major', 'sub'):
        gi = an['groups'][g]
        if gi['e_need'] > 0:
            msgs.append(('info', 'ناقص %d ساعة اختياري في «%s» — اختار من: %s' % (
                gi['e_need'], GROUP_NAME[g], '، '.join(c.name for c in gi['e_courses'] if not st.passed(c.code) and not st.cur(c.code))[:200])))
    off = term_offers(cfg, cfg['start_type'], cfg['start_year'])
    if off is not None:
        msgs.append(('info', 'القسم أعلن %d مقرر للفصل القادم، وخطتك بتختار منهم بس.' % len(off)))
        if plan['terms'] and not plan['terms'][0]['codes']:
            msgs.append(('bad', 'المقررات اللي القسم فاتحها مفيهاش حاجة تقدر تسجلها دلوقتي — فصل ضايع! '
                                'شوف تبويب «القسم» واطلب فتح المقررات الحرجة.'))
    if not cfg.get('training'):
        msgs.append(('warn', 'التدريب الصيفي (٦ أسابيع على الأقل) شرط للتخرج وغير محسوب هنا — أتممته؟ علّم عليه في تبويب مقرراتي.'))
    if plan['terms']:
        n = plan['n_terms']
        by_hours = math.ceil(hours_pend / float(cap)) if cap else n
        chain_len = max(plan['height'].values()) if plan['height'] else 0
        if n > by_hours and n >= chain_len:
            msgs.append(('info', 'السبب الرئيسي للتأخير: سلسلة المتطلبات السابقة. أطول سلسلة: %s — كل مقرر فيها لازم ينتظر اللي قبله.' % chain_names(plan['chain'])))
        elif by_hours >= n and hours_pend > 0:
            msgs.append(('info', 'السبب الرئيسي: عدد الساعات المتبقية (%d ساعة) مقابل حد %d ساعة في الفصل.' % (hours_pend, cap)))
        if cfg.get('parity', True):
            late = [C[c].name for t in plan['terms'] for c in t['codes']
                    if t['typ'] != 'U' and False]
            wait_terms = [t for t in plan['terms'] if not t['codes']]
            if wait_terms:
                msgs.append(('warn', 'فيه فصل/فصول انتظار (%s) لأن المقررات المتبقية بتتطرح في فصل مختلف.' % '، '.join(t['label'] for t in wait_terms)))
        if 'MREn 424' in pend and cfg.get('proj_order', True):
            msgs.append(('info', 'مشروع التخرج (٢) بيجي بعد مشروع (١)، فآخر فصل لازم يكون فيه المشروع.'))
        if cfg.get('parity', True) and plan['terms']:
            first = plan['terms'][0]
            skipped = [C[c].name for c in sorted(plan['pend']) if C[c].sem and
                       ((C[c].sem % 2 == 1) != (first['typ'] == 'F')) and first['typ'] != 'U' and
                       all(st.satisfied(p) for p in pre_of(c, cfg))]
            if skipped:
                msgs.append(('info', 'مقررات جاهزة ليك لكن بتتطرح في الفصل اللي بعده: ' + '، '.join(skipped[:8])))
    return msgs


def gpa_gap(st, an):
    """كم ساعة D/D+ نعيد بتقدير B لنصل 2.00؟ (تقدير تقريبي)"""
    gpa, den = an['gpa_calc'], an['gpa_hours']
    if gpa is None or gpa >= 2.0:
        return ''
    pts = gpa * den
    cands = []
    for c in COURSES:
        g = st.g(c.code)
        if st.s(c.code) == 'done' and g in GRADES:
            cap_g = 2.0 if g == 'F' else 3.0
            gain = (cap_g - GRADES[g]) * c.cr
            if gain > 0:
                cands.append((gain, c))
    cands.sort(key=lambda x: -x[0])
    picked = []
    cur_pts = pts
    for gain, c in cands:
        if cur_pts / den >= 2.0:
            break
        cur_pts += gain
        picked.append(c)
    if cur_pts / den >= 2.0:
        return 'لو أعدت (%s) وجبت B تقريباً (أو C للراسب)، معدلك هيوصل لـ 2.00 تقريباً.' % '، '.join(c.name for c in picked)
    return 'محتاج إعادة عدد أكبر من المقررات لرفع المعدل — اتكلم مع المرشد الأكاديمي.'


def track_report(st, cfg):
    rows = []
    base_cfg = dict(cfg)
    for key, name, desc, codes in TRACKS + [('auto', 'اختيار تلقائي (أسرع)', 'البرنامج يختار الاختياري الأنسب لأسرع تخرج', [])]:
        prefs = set(codes)
        pl = plan_min_summers(st, base_cfg, prefs) if base_cfg.get('use_summer') else make_plan(st, base_cfg, prefs)
        if pl is None:
            continue
        mine = [c for c in codes if c in C and C[c].kind == 'E']
        done_mine = [c for c in mine if st.passed(c) or st.cur(c)]
        will = [c for c in pl['chosen'] if c in prefs]
        rows.append({'key': key, 'name': name, 'desc': desc, 'plan': pl, 'courses': codes,
                     'done': done_mine, 'will': will, 'chosen': sorted(pl['chosen'])})
    return rows


def critical_to_open(st, cfg, prefs=None, look=2):
    """أي المقررات في أول `look` فصول من خطتك المثالية لو القسم ما فتحهاش يتأخر تخرجك؟
    نبني خطة «مثالية» (كأن القسم هيفتح اللازم)، ثم نجرّب منع كل مقرر من فصله ونقارن."""
    look = max(1, min(4, int(look or 2)))
    seq = term_sequence(cfg['start_type'], cfg['start_year'], look, cfg.get('use_summer', True))
    keys = [tkey(t, y) for t, y in seq]
    real = cfg.get('offers') or {}
    c0 = dict(cfg, offers={k: v for k, v in real.items() if k not in keys}, block=set())
    pending = build_pending(st, c0, prefs)
    base = make_plan(st, c0, prefs, runs=40, pending=pending)
    out = {'base': base, 'items': [], 'keys': keys}
    if not base or not base['terms']:
        return out
    chain = set(base.get('chain') or [])
    items = []
    for t in base['terms'][:look]:
        k = tkey(t['typ'], t['year'])
        for code in t['codes']:
            if code in t.get('extra', ()):
                continue
            blk = {(code, t['typ'], t['year'])}

            def worse(tr):
                return tr is None or tr['finish_key'] > base['finish_key']
            tr = make_plan(st, dict(c0, block=blk), prefs, runs=12, pending=pending)
            if worse(tr):
                tr = make_plan(st, dict(c0, block=blk), prefs, runs=40, pending=pending)
            if tr is None:
                level, why, delay = 'crit', 'مفيش بديل — لازم يتفتح', 99
            elif tr['finish_key'] > base['finish_key']:
                delay = tr['n_terms'] - base['n_terms']
                level = 'crit'
                why = 'هتتأخر: التخرج بعد كده في %s (+%d فصل)' % (tr['finish_label'], max(delay, 1))
            elif tr['n_summers'] > base['n_summers']:
                level, delay = 'imp', 0
                why = 'هتحتاج صيفي زيادة'
            else:
                level, delay = 'ok', 0
                why = 'ممكن بديل — مش هيأخر تخرجك'
            if k in real:
                state = 'open' if code in real[k] else 'closed'
            else:
                state = 'unknown'
            items.append({'code': code, 'name': C[code].name, 'label': t['label'], 'typ': t['typ'], 'year': t['year'],
                          'level': level, 'why': why, 'delay': delay, 'chain': code in chain, 'state': state,
                          'retake': code in t['retake']})
    order = {'crit': 0, 'imp': 1, 'ok': 2}
    items.sort(key=lambda x: (order[x['level']], x['year'] * 10 + TERM_KEY[x['typ']], x['code']))
    out['items'] = items
    return out


def dept_request_text(cfg, items, name=''):
    """نص طلب جاهز لرئيس القسم بالمقررات الحرجة والمهمة."""
    want = [i for i in items if i['level'] in ('crit', 'imp')]
    if not want:
        return ''
    L = ['السيد الأستاذ الدكتور / رئيس قسم الميكاترونيات',
         'تحية طيبة وبعد،', '']
    L.append('أتقدم %sبطلب التكرم بفتح المقررات التالية في الفصول المبيّنة، لأنها لازمة لإتمام خطتي الدراسية '
             'للتخرج في موعدها، وعدم فتحها يؤدي إلى تأخري عن التخرج:' % (('(%s) ' % name) if name else ''))
    cur = None
    for i in want:
        if i['label'] != cur:
            cur = i['label']
            L.append('')
            L.append('◾ فصل %s:' % cur)
        L.append('   - %s — %s (%d ساعة)%s' % (i['code'], i['name'], C[i['code']].cr,
                                              ' — %s' % i['why'] if i['level'] == 'crit' else ''))
    L += ['', 'وتفضلوا بقبول فائق الاحترام والتقدير.']
    return '\n'.join(L)


def eff_cfg(ui_cfg, an):
    c = dict(ui_cfg)
    cap = c.get('cap', MAX_LOAD_DEFAULT)
    c['probation'] = an['probation']
    if an['probation']:
        cap = min(cap, PROBATION_LOAD)
    c['cap'] = cap
    return c


# ═════════════════════════ الحزمة الكاملة للتحليل + التقارير ═════════════════════════
def next_term(today=None, months=None, use_summer=True):
    """أقرب فصل لم يبدأ شهره بعد (أو هو شهر اليوم) — يُقترح كـ «الفصل القادم»."""
    today = today or dt.date.today()
    months = months or DEFAULT_MONTHS
    for y in range(today.year - 1, today.year + 3):
        for typ in ('S', 'U', 'F'):
            if typ == 'U' and not use_summer:
                continue
            if (y, int(months.get(typ, DEFAULT_MONTHS[typ]))) >= (today.year, today.month):
                return typ, y
    return 'F', today.year


_ds = next_term()
DEFAULT_SET = {
    'name': '', 'start_type': _ds[0], 'start_year': _ds[1], 'cap': MAX_LOAD_DEFAULT, 'use_summer': True,
    'parity': True, 'summer_codes': None, 'proj_order': True, 'gpa_manual': None, 'training': False,
    'track': 'auto', 'months': dict(DEFAULT_MONTHS), 'offers': {}, 'look': 2, 'min_load': 0, 'picks': {},
}


def compute_all(rec, setg):
    st = Student(rec)
    cfg0 = dict(setg)
    an = analyze(st, cfg0)
    cfg = eff_cfg(cfg0, an)
    track = cfg.get('track', 'auto')
    prefs = set()
    for k, _n, _d, codes in TRACKS:
        if k == track:
            prefs = set(codes)
    cfg['custom_cap'] = cfg['cap']
    cfg['custom_summer'] = cfg['use_summer']
    my = plan_min_summers(st, cfg, prefs) if cfg['use_summer'] else make_plan(st, cfg, prefs)
    return {'st': st, 'cfg': cfg, 'an': an, 'prefs': prefs, 'my': my,
            'diag': diagnose(st, cfg, an, my), 'check': checklist(st, cfg, an), 'elig': eligible_now(st, cfg)}


def recommended_codes(pack):
    my = pack['my']
    if not my or not my['terms']:
        return [], None
    t = my['terms'][0]
    return t['codes'], t


# ───────────────────────── تقرير HTML (يُطبع PDF من المتصفح) ─────────────────────────
def report_html(pack, plans, tracks, crit=None):
    st, cfg, an = pack['st'], pack['cfg'], pack['an']
    name = cfg.get('name') or ''
    h = ['<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>تقرير الحالة الأكاديمية</title>',
         '<style>body{font-family:Tahoma,Arial,sans-serif;margin:24px;color:#222}h1{color:#1F4E79}h2{color:#1F4E79;'
         'border-bottom:2px solid #1F4E79;padding-bottom:4px;margin-top:26px}table{border-collapse:collapse;width:100%;'
         'margin:8px 0}td,th{border:1px solid #999;padding:5px 8px;text-align:right;font-size:14px}th{background:#D9E2F3}'
         '.ok{background:#E2F0D9}.no{background:#FCE4D6}.unk{background:#FFF2CC}.bad{color:#C00000}.warn{color:#C55A11}'
         '.foot{margin-top:30px;color:#777;font-size:12px}@media print{h2{page-break-after:avoid}}</style></head><body>']
    h.append('<h1>تقرير الحالة الأكاديمية — هندسة الميكاترونيات والروبوتات الصناعية</h1>')
    h.append('<p>الطالب: <b>%s</b> &nbsp;|&nbsp; التاريخ: %s &nbsp;|&nbsp; الفصل القادم: <b>%s</b></p>' % (
        hesc(name or '—'), dt.date.today().isoformat(), term_label(cfg['start_type'], cfg['start_year'], cfg.get('months'))))
    gpa = an['gpa']
    h.append('<p>الساعات المحسوبة: <b>%d</b> من %d &nbsp;|&nbsp; المتبقي: <b>%d</b> ساعة &nbsp;|&nbsp; المعدل: <b>%s</b></p>' % (
        an['counted'] + an['cur_hours'], TOTAL_REQUIRED, an['remaining'], '%.2f' % gpa if gpa is not None else '—'))
    h.append('<h2>شروط التخرج</h2><table><tr><th>الشرط</th><th>الحالة</th><th>التفاصيل</th></tr>')
    sym = {'ok': '✔', 'no': '✘', 'unk': '؟', 'wait': '…'}
    for t, s, d in pack['check']:
        h.append('<tr class="%s"><td>%s</td><td>%s</td><td>%s</td></tr>' % (s if s != 'wait' else 'unk', hesc(t), sym[s], hesc(d)))
    h.append('</table><h2>تحليل الوضع</h2><ul>')
    for k, m in pack['diag']:
        h.append('<li class="%s">%s</li>' % (k if k in ('bad', 'warn') else '', hesc(m)))
    h.append('</ul><h2>المتبقي حسب الفئة</h2><table><tr><th>الفئة</th><th>إجباري منجز</th><th>إجباري متبقٍ</th>'
             '<th>اختياري (منجز/مطلوب)</th></tr>')
    for g in ('univ', 'college', 'major', 'sub'):
        gi = an['groups'][g]
        e = '%d / %d' % (gi['e_done'] + gi['e_cur'], gi['e_min']) if 'e_min' in gi else '—'
        h.append('<tr><td>%s</td><td>%d / %d</td><td>%s</td><td>%s</td></tr>' % (
            GROUP_NAME[g], gi['req_done'] + gi['req_cur'], gi['req_total'],
            hesc('، '.join(c.name for c in gi['left'])) or '—', e))
    h.append('</table>')
    my = pack['my']
    if my and my['terms']:
        h.append('<h2>خطتي للتخرج (حمل أقصى %d ساعة%s)</h2><table><tr><th>الفصل</th><th>المقررات</th><th>الساعات</th></tr>' % (
            cfg['cap'], ' + صيفي' if cfg['use_summer'] else ''))
        for t in my['terms']:
            h.append('<tr><td>%s</td><td>%s</td><td>%d</td></tr>' % (
                t['label'], hesc('، '.join(C[c].name + (' (إعادة)' if c in t['retake'] else '') + (' (إضافي)' if c in t.get('extra', ()) else '') for c in t['codes'])) or 'انتظار — لا مقررات متاحة',
                t['credits']))
        h.append('</table>')
    if plans:
        h.append('<h2>مقارنة الخطط</h2><table><tr><th>الخطة</th><th>عدد الفصول</th><th>التخرج</th><th>صيفي</th></tr>')
        for _k, n, _cap, _s, p in plans:
            h.append('<tr><td>%s</td><td>%d</td><td>%s</td><td>%d</td></tr>' % (hesc(n), p['n_terms'], p['finish_label'], p['n_summers']))
        h.append('</table>')
    if crit and crit.get('items'):
        h.append('<h2>المقررات التي يجب طلب فتحها من القسم</h2><table><tr><th>الفصل</th><th>المقرر</th><th>الأهمية</th>'
                 '<th>لو لم يُفتح</th></tr>')
        lv = {'crit': 'حرج', 'imp': 'مهم', 'ok': 'له بديل'}
        for i in crit['items']:
            h.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                hesc(i['label']), hesc(i['name']), lv[i['level']], hesc(i['why'])))
        h.append('</table>')
    if tracks:
        h.append('<h2>المسارات المقترحة للاختياري</h2><table><tr><th>المسار</th><th>التخرج</th><th>عدد الفصول</th></tr>')
        for r in tracks:
            h.append('<tr><td>%s</td><td>%s</td><td>%d</td></tr>' % (hesc(r['name']), r['plan']['finish_label'], r['plan']['n_terms']))
        h.append('</table>')
    h.append('<p class="foot">أُعدّ بواسطة مرشد الطالب الأكاديمي — تطوير: %s. هذا تقرير إرشادي حسب لائحة 2012 '
             'ولا يغني عن مراجعة المرشد الأكاديمي وشئون الطلاب.</p></body></html>' % DEVELOPER)
    return '\n'.join(h)


# ───────────────────────── تقرير Word ─────────────────────────
def report_docx(path, pack, plans, tracks, crit=None):
    from docx import Document
    from docx.shared import Pt, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    FONT = 'Arial'
    st, cfg, an = pack['st'], pack['cfg'], pack['an']
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(1.8)

    def rtl_par(p, center=False, after=4):
        p.paragraph_format.space_after = Pt(after)
        if center:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pPr = p._p.get_or_add_pPr()
        pPr.insert_element_before(OxmlElement('w:bidi'), 'w:adjustRightInd', 'w:snapToGrid', 'w:spacing', 'w:ind',
                                  'w:contextualSpacing', 'w:mirrorIndents', 'w:suppressOverlap', 'w:jc',
                                  'w:textDirection', 'w:textAlignment', 'w:textboxTightWrap', 'w:outlineLvl',
                                  'w:divId', 'w:cnfStyle', 'w:rPr', 'w:sectPr', 'w:pPrChange')

    def run(p, text, size=11, bold=False):
        r = p.add_run(text)
        rPr = r._r.get_or_add_rPr()
        for ch in list(rPr):
            rPr.remove(ch)
        rf = OxmlElement('w:rFonts')
        for a in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
            rf.set(qn(a), FONT)
        rPr.append(rf)
        if bold:
            rPr.append(OxmlElement('w:b')); rPr.append(OxmlElement('w:bCs'))
        for tag in ('w:sz', 'w:szCs'):
            e = OxmlElement(tag); e.set(qn('w:val'), str(int(size * 2))); rPr.append(e)
        rPr.append(OxmlElement('w:rtl'))

    def para(text, size=11, bold=False, center=False):
        p = doc.add_paragraph()
        rtl_par(p, center)
        run(p, text, size, bold)

    def table(headers, rows, widths):
        t = doc.add_table(rows=1, cols=len(headers))
        t.style = 'Table Grid'
        tblPr = t._tbl.tblPr
        bv = OxmlElement('w:bidiVisual')
        tw = tblPr.find(qn('w:tblW'))
        (tw.addprevious(bv) if tw is not None else tblPr.append(bv))
        t.autofit = False
        for i, w in enumerate(widths):
            t.columns[i].width = Cm(w)

        def fill(cells, vals, bold=False, shade=None):
            for i, (c, v) in enumerate(zip(cells, vals)):
                c.width = Cm(widths[i])
                c.paragraphs[0].text = ''
                rtl_par(c.paragraphs[0], False, 0)
                run(c.paragraphs[0], str(v), 10, bold)
                if shade:
                    tcPr = c._tc.get_or_add_tcPr()
                    shd = OxmlElement('w:shd')
                    shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto'); shd.set(qn('w:fill'), shade)
                    tcPr.append(shd)
        fill(t.rows[0].cells, headers, True, 'D9E2F3')
        for r in rows:
            fill(t.add_row().cells, r)

    para('تقرير الحالة الأكاديمية', 20, True, True)
    para('هندسة الميكاترونيات والروبوتات الصناعية — الطالب: %s' % (cfg.get('name') or '—'), 12, False, True)
    gpa = an['gpa']
    para('الساعات المحسوبة %d من %d — المتبقي %d ساعة — المعدل %s' % (
        an['counted'] + an['cur_hours'], TOTAL_REQUIRED, an['remaining'], '%.2f' % gpa if gpa is not None else '—'), 12, True)
    para('شروط التخرج', 14, True)
    sym = {'ok': '✔', 'no': '✘', 'unk': '؟', 'wait': '…'}
    table(['الشرط', 'الحالة', 'التفاصيل'], [(t, sym[s], d) for t, s, d in pack['check']], [7, 1.5, 8.5])
    para('تحليل الوضع', 14, True)
    for _k, m in pack['diag']:
        para('• ' + m, 10.5)
    para('المتبقي حسب الفئة', 14, True)
    rows = []
    for g in ('univ', 'college', 'major', 'sub'):
        gi = an['groups'][g]
        rows.append((GROUP_NAME[g], '%d / %d' % (gi['req_done'] + gi['req_cur'], gi['req_total']),
                     '، '.join(c.name for c in gi['left']) or '—',
                     ('%d / %d' % (gi['e_done'] + gi['e_cur'], gi['e_min'])) if 'e_min' in gi else '—'))
    table(['الفئة', 'إجباري', 'المتبقي', 'اختياري'], rows, [4, 2.5, 8, 2.5])
    my = pack['my']
    if my and my['terms']:
        para('خطتي للتخرج', 14, True)
        table(['الفصل', 'المقررات', 'الساعات'],
              [(t['label'], '، '.join(C[c].name for c in t['codes']) or 'انتظار', t['credits']) for t in my['terms']], [3, 11.5, 1.5])
    if plans:
        para('مقارنة الخطط', 14, True)
        table(['الخطة', 'الفصول', 'التخرج', 'صيفي'], [(n, p['n_terms'], p['finish_label'], p['n_summers']) for _k, n, _c, _s, p in plans],
              [7, 2, 4, 2])
    if crit and crit.get('items'):
        para('المقررات التي يجب طلب فتحها من القسم', 14, True)
        lv = {'crit': 'حرج', 'imp': 'مهم', 'ok': 'له بديل'}
        table(['الفصل', 'المقرر', 'الأهمية', 'لو لم يُفتح'],
              [(i['label'], i['name'], lv[i['level']], i['why']) for i in crit['items']], [4, 5, 2, 5])
    para('أُعدّ بواسطة مرشد الطالب الأكاديمي — تطوير: %s. تقرير إرشادي حسب لائحة 2012.' % DEVELOPER, 9)
    doc.save(path)


# ───────────────────────── ملف المشروع ─────────────────────────
CONFIG = os.path.join(os.environ.get('ADVISOR_HOME') or os.path.expanduser('~'), '.student_advisor_config.json')


def load_config():
    try:
        with open(CONFIG, encoding='utf-8') as fh:
            return json.load(fh)
    except Exception:
        return {}


def save_config(d):
    try:
        with open(CONFIG, 'w', encoding='utf-8') as fh:
            json.dump(d, fh, ensure_ascii=False)
    except Exception:
        pass


def write_project(path, data):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def read_project(path):
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)


RULES_TEXT = """\
ملخص أهم قواعد اللائحة (من لائحة قسم الميكاترونيات 2012)
─────────────────────────────────────────────────────
• التخرج: ١٧٥ ساعة معتمدة = ١٤١ ساعة إجبارية + ٣٤ ساعة اختيارية كحد أدنى،
  بمعدل تراكمي لا يقل عن 2.00.
• توزيع الاختياري: جامعة ٨ ساعات — تخصص رئيسي ١٠ ساعات — تخصص فرعي ١٦ ساعة.
• التسجيل: حتى ٢١ ساعة في الفصل الأول أو الثاني، وحتى ٨ ساعات (مقرران) في الصيفي.
• الطالب تحت الملاحظة (معدل أقل من 2.00): يُخفَّض حمله ويكون الحد الأقصى ١٢ ساعة.
• لا يجوز التسجيل في مقرر له متطلب سابق قبل النجاح في المتطلب.
• لابد من النجاح بتقدير C- على الأقل في المقرر الذي يُعدّ متطلباً لمقررات تالية.
• النجاح في أي مقرر يحتاج D على الأقل. الراسب (F) يعيد المقرر، ويُحسب تقديره بحد أقصى C.
• إعادة مقرر بغرض تحسين المعدل: يُدرَس ويُمتحن من جديد وتُحسب النقاط الفعلية.
• نقاط التقدير: A=4.0  A-=3.7  B+=3.3  B=3.0  B-=2.7  C+=2.3  C=2.0  C-=1.7  D+=1.3  D=1.0  F=0
• التدريب الصيفي: ٦ أسابيع على الأقل (متصلة أو على مرتين) شرط للتخرج.
• مشروع التخرج: مقرران (١) و(٢)، ويُمنح ٤ أسابيع بعد امتحانات الفصل العاشر لإنجازه.
• مرتبة الشرف: معدل تراكمي ٣.٣ فأكثر بشرط ألا يكون قد رسب في أي مقرر.
• الحد الأقصى للدراسة ٨ سنوات.
• الحضور: لا يقل عن ٧٥٪ من كل مقرر وإلا حُرم من الامتحان النهائي.

افتراضات البرنامج (غير منصوص عليها في اللائحة) — يمكن تغييرها من تبويب «بياناتي» و«القسم»:
• كل مقرر يُطرح في نوع الفصل المقترح له (الفردي = خريف، الزوجي = ربيع).
• المقررات المتاحة في الصيفي: كل المقررات (عدّلها من تبويب «القسم»).
• لو أعلن القسم قائمة مقررات لفصل معين (تبويب «القسم») فالتسجيل يكون منها فقط.
• شهر بداية كل فصل افتراضي (خريف أكتوبر / ربيع فبراير / صيفي يوليو) — عدّله من «بياناتي».
• مشروع التخرج (٢) بعد (١).
• مسارات الاختياري اقتراح من البرنامج وليست تقسيماً رسمياً في اللائحة.
• هذا البرنامج إرشادي: راجع المرشد الأكاديمي وشئون الطلاب قبل التسجيل.
"""


BLUE = '#1F4E79'
GUIDE_BG = '#FFF4CC'
SYM = {'none': '☐', 'done': '☑', 'cur': '◔', 'fail': '✗'}
TYPE_AR = {'F': 'خريف', 'S': 'ربيع', 'U': 'صيفي'}
TYPE_FROM_AR = {v: k for k, v in TYPE_AR.items()}
KIND_TXT = {'univ': 'جامعة', 'college': 'كلية', 'major': 'تخصص رئيسي', 'sub': 'تخصص فرعي'}
LEVEL_TXT = {'crit': '🔴 لازم يتفتح', 'imp': '🟡 يفضل يتفتح', 'ok': '🟢 ممكن بديل'}
STATE_TXT = {'open': '✔ مفتوح', 'closed': '✘ مش مفتوح', 'unknown': '؟ لسه ما أعلنوش'}
SUMMER_KEY = 'SUMMER*'

# نص الدليل الإرشادي لكل خطوة (الخطوة = تبويب)
GUIDE = [
    ('بياناتك',
     'اكتب اسمك، واختار الفصل اللي هتسجّل فيه دلوقتي، وشهر بداية كل فصل. وحدّد أقل وأقصى ساعات تحب تدرسها في الفصل. '
     'بعدها اضغط «التالي».'),
    ('علّم موادك اللي خلّصتها',
     'اختار رقم الفصل من الأزرار فوق (ف1 … ف10)، وعلّم المواد اللي نجحت فيها بالضغط على المربع ☐. '
     'لو عارف التقدير اختاره من تحت. المواد اللي بتدرسها دلوقتي علّمها «بدرسه الآن».'),
    ('حالتك',
     'هنا بتشوف الساعات اللي باقية، وشروط التخرج، وسبب التأخير لو فيه. مفيش حاجة تعملها هنا غير إنك تقرا.'),
    ('المواد اللي القسم فاتحها',
     'اختار الفصل اللي بتسجّل فيه، واضغط «القسم أعلن مواد معيّنة»، وبعدين علّم المواد اللي القسم فاتحها. '
     'لو لسه ما أعلنش، اضغط «اعرف إيه اللازم يتفتح» تعرف تطلب إيه من القسم.'),
    ('اختار موادك',
     'هنا المواد المتاحة ليك في الفصل ده. اضغط على المادة عشان تختارها، وشوف مجموع ساعاتك فوق (لازم يكون بين الأقل والأقصى). '
     'الأخضر = موصى بيه، والرمادي = مش متاح (مكتوب السبب).'),
    ('خطتك للتخرج',
     'اضغط «احسب الخطط» وقارن بين الخطط (أسرع، عادية، مريحة). تقدر تختار مسار للاختياري. '
     'ولما تخلّص اطبع التقرير من قايمة «ملف». بالتوفيق! 🎓'),
]


def bar_text(done, total, width=14):
    if total <= 0:
        return ''
    f = max(0, min(width, int(round(width * done / float(total)))))
    return '█' * f + '░' * (width - f) + ' %d%%' % int(100 * done / float(total))

