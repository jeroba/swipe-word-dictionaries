"""Expansor sencillo de Hunspell (.dic/.aff). Nació para RLA-ES (FLAG UTF-8) y en la Fase 11B se generalizó
(FLAG long y num, SET, FULLSTRIP, NEEDAFFIX, FORBIDDENWORD, ONLYINCOMPOUND, CIRCUMFIX; las entradas con
KEEPCASE, que en francés son unidades como kat o mol, se descartan) para el francés y el
portugués. No arma compuestos (COMPOUND*): solo las formas del .dic con sus afijos.
Aplica: sufijo, sufijo+sufijo de continuación, prefijo, y prefijo×sufijo cuando ambos son cross-product.
Etiqueta cada forma con las categorías de las reglas usadas.
Como Hunspell sin FULLSTRIP, una regla no puede quitar la palabra entera (errar → *ierro*).
Las banderas son puntos de código (Hunspell 1.7 junta todas las de 4 bytes, los emoji, en una
sola y por eso acepta basura como *ohmmente*; aquí se respeta lo que quiso el autor).
Uso: python3 -I hunspell_expand.py es.aff es.dic salida_dir [originales.txt]
  originales.txt (opcional): todas las formas del nivel 5 sin normalizar (minúsculas, NFC,
  solo letras, sin filtro de largo), una por línea, ordenadas por bytes UTF-8.
  Los niveles de salida_dir (SFX_CAT) solo tienen sentido en español; para otro idioma usa
  salida_dir = "-" y solo se escribe originales.txt.
  --sin-truncadas-mo (VERO, pt-BR, D110): descarta las reglas de sufijo que dan la 1.ª persona del plural sin
  la s final (cantarmo, cantamo), que solo vale antes de un pronombre con guion (cantarmo-nos). Son las que
  terminan en -mo (no en -smo ni en el superlativo -íssimo) y tienen una hermana igual que termina en -mos.
"""
import sys, re, collections, os, gzip, unicodedata

drop_mo = "--sin-truncadas-mo" in sys.argv
if drop_mo: sys.argv.remove("--sin-truncadas-mo")
if len(sys.argv) < 4 or sys.argv[1] in ("-h", "--help"):
    print(__doc__); sys.exit(0 if len(sys.argv) > 1 else 2)
aff_path, dic_path, out_dir = sys.argv[1:4]
original_path = sys.argv[4] if len(sys.argv) > 4 else None

# Opciones del .aff (las que cambian qué formas salen).
encoding = "utf-8"; flag_mode = "char"
fullstrip = False; needaffix = forbidden = onlyincompound = circumfix = keepcase = None
with open(aff_path, "rb") as f:
    for raw in f:
        p = raw.decode("latin-1").split()
        if len(p) >= 2 and p[0] == "SET": encoding = p[1].lower()
for line in open(aff_path, encoding=encoding):
    p = line.split()
    if not p: continue
    if p[0] == "FLAG" and len(p) > 1: flag_mode = {"long": "long", "num": "num"}.get(p[1], "char")
    elif p[0] == "FULLSTRIP": fullstrip = True
    elif p[0] == "NEEDAFFIX" and len(p) > 1: needaffix = p[1]
    elif p[0] == "FORBIDDENWORD" and len(p) > 1: forbidden = p[1]
    elif p[0] == "ONLYINCOMPOUND" and len(p) > 1: onlyincompound = p[1]
    elif p[0] == "CIRCUMFIX" and len(p) > 1: circumfix = p[1]
    elif p[0] == "KEEPCASE" and len(p) > 1: keepcase = p[1]

def split_flags(s):
    """Las banderas de una entrada según FLAG: un punto de código (UTF-8 o por omisión), pares (long) o
    números separados por comas (num)."""
    if flag_mode == "long": return [s[i:i + 2] for i in range(0, len(s) - len(s) % 2, 2)]
    if flag_mode == "num": return [x for x in s.split(",") if x]
    return list(s)

SFX_CAT = {}
for f in "SG": SFX_CAT[f] = "infl"          # plural, género
for f in "REIXD": SFX_CAT[f] = "verb"       # conjugación y participios
for f in "ABCFHJKLMOPQT": SFX_CAT[f] = "deriv"
for f in "NU": SFX_CAT[f] = "dimin"
for f in ["🧠", "🥇", "🏅"]: SFX_CAT[f] = "deriv"  # -mente, superlativos

def first_cp(s): return s if flag_mode != "char" else s[0]

class Rule:
    __slots__ = ("strip", "add", "cont", "cond", "kind")
def cond_regex(c, kind):
    if c == ".": return None
    return re.compile(("^" + c) if kind == "PFX" else (c + "$"))

rules = collections.defaultdict(list)   # flag -> list of Rule
cross = {}
kinds = {}
with open(aff_path, encoding=encoding) as f:
    for line in f:
        p = line.split()
        if len(p) < 4 or p[0] not in ("SFX", "PFX"): continue
        flag = first_cp(p[1])
        if len(p) == 4 and p[2] in ("Y", "N"):
            cross[flag] = p[2] == "Y"; kinds[flag] = p[0]; continue
        r = Rule(); r.kind = p[0]
        r.strip = "" if p[2] == "0" else p[2]
        add = p[3]
        if "/" in add: add, cont = add.split("/", 1)
        else: cont = ""
        r.add = "" if add == "0" else add
        r.cont = set(split_flags(cont))
        r.cond = cond_regex(p[4] if len(p) > 4 else ".", p[0])
        rules[flag].append(r)

if drop_mo:
    for fl, rs in rules.items():
        keys = {(r.strip, r.add, r.cond.pattern if r.cond else None) for r in rs}
        kept = [r for r in rs if not (r.add.endswith("mo") and not r.add.endswith(("smo", "ssimo"))
                                      and (r.strip, r.add + "s", r.cond.pattern if r.cond else None) in keys)]
        print(f"--sin-truncadas-mo: bandera {fl}: {len(rs) - len(kept)} reglas fuera") if len(kept) < len(rs) else None
        rules[fl] = kept

def cat_of(flag):
    if kinds.get(flag) == "PFX": return "pref"
    return SFX_CAT.get(flag, "encl")

def apply_sfx(word, flag):
    for r in rules.get(flag, ()):
        if r.strip and not word.endswith(r.strip): continue
        if not fullstrip and len(r.strip) >= len(word): continue   # sin FULLSTRIP la raíz no puede quedar vacía
        if r.cond is not None and not r.cond.search(word): continue
        base = word[:len(word) - len(r.strip)] if r.strip else word
        yield base + r.add, r.cont
def apply_pfx(word, flag):
    for r in rules.get(flag, ()):
        if r.strip and not word.startswith(r.strip): continue
        if not fullstrip and len(r.strip) >= len(word): continue
        if r.cond is not None and not r.cond.search(word): continue
        yield r.add + word[len(r.strip):], r.cont

def standalone(cont):
    """Una forma cuya continuación pide NEEDAFFIX o CIRCUMFIX no vale sola (sirve de base para la siguiente)."""
    return not ((needaffix and needaffix in cont) or (circumfix and circumfix in cont))

def expand(root, flags):
    """devuelve dict forma -> frozenset de categorías (la combinación 'más simple' que la genera)."""
    out = {}
    def put(w, cats):
        cats = frozenset(cats)
        if w not in out or len(cats) < len(out[w]): out[w] = cats
    if not (needaffix and needaffix in flags): put(root, ())
    sfx_forms = []  # (form, cats, crossable)
    for fl in flags:
        if kinds.get(fl) != "SFX": continue
        c1 = cat_of(fl)
        for w1, cont in apply_sfx(root, fl):
            if standalone(cont): put(w1, {c1})
            sfx_forms.append((w1, {c1}, cross.get(fl, False), cont))
            for fl2 in cont:
                if kinds.get(fl2) == "SFX":
                    for w2, cont2 in apply_sfx(w1, fl2):
                        c = {c1, cat_of(fl2)}
                        if standalone(cont2): put(w2, c)
                        sfx_forms.append((w2, c, cross.get(fl, False) and cross.get(fl2, False), set()))
    for fl in flags:
        if kinds.get(fl) != "PFX": continue
        for wp, cont in apply_pfx(root, fl):
            if standalone(cont): put(wp, {"pref"})
        if cross.get(fl, False):
            for w, c, cr, cont in sfx_forms:
                if cr:
                    for wp, _ in apply_pfx(w, fl): put(wp, c | {"pref"})
    # prefijos pedidos como continuación de un sufijo
    for w, c, cr, cont in sfx_forms:
        for fl2 in cont:
            if kinds.get(fl2) == "PFX":
                for wp, _ in apply_pfx(w, fl2): put(wp, c | {"pref"})
    return out

TABLE = str.maketrans({"á":"a","é":"e","í":"i","ó":"o","ú":"u","ü":"u"})
OKN = re.compile(r"^[A-ZÑ]{3,12}$")
def normalize(w):
    w2 = unicodedata.normalize("NFC", w).translate(TABLE)
    return w2.upper()

lines = open(dic_path, encoding=encoding).read().splitlines()[1:]
allforms = {}   # forma original -> cats (mínima)
forbidden_words = set()
roots_lower = 0; roots_proper = 0
for ln in lines:
    ln = ln.strip()
    if not ln: continue
    ln = ln.split("\t")[0].split(" ")[0]
    if "/" in ln: root, fl = ln.split("/", 1)
    else: root, fl = ln, ""
    if not root or root[0] != root[0].lower() or root != root.lower():
        roots_proper += 1; continue   # nombres propios, siglas, abreviaturas en mayúscula
    flags = split_flags(fl)
    if forbidden and forbidden in flags:
        forbidden_words.add(root)   # Hunspell la rechaza aunque otra raíz la genere (menas, ague)
    if any(f and f in flags for f in (forbidden, onlyincompound, keepcase)):
        roots_proper += 1; continue   # prohibidas, solo dentro de compuestos o con mayúsculas fijas (unidades: kat, mol)
    roots_lower += 1
    for w, cats in expand(root, flags).items():
        if w not in allforms or len(cats) < len(allforms[w]): allforms[w] = cats

LEVELS = [
    ("1-lemas", set()),
    ("2-lemas+plural+genero", {"infl"}),
    ("3-+conjugacion", {"infl", "verb"}),
    ("4-+derivados+diminutivos+prefijos", {"infl", "verb", "deriv", "dimin", "pref"}),
    ("5-todo(+encliticos)", {"infl", "verb", "deriv", "dimin", "pref", "encl"}),
]
for w in forbidden_words: allforms.pop(w, None)
print(f"raíces en minúscula: {roots_lower}  descartadas (mayúscula/siglas/prohibidas): {roots_proper}")
if out_dir != "-": os.makedirs(out_dir, exist_ok=True)
print(f"formas totales (originales, sin filtrar): {len(allforms)}")
for name, allowed in (LEVELS if out_dir != "-" else []):
    orig = {w for w, c in allforms.items() if c <= allowed}
    norm = {}
    for w in orig:
        n = normalize(w)
        if OKN.match(n): norm.setdefault(n, set()).add(w)
    txt = ("\n".join(sorted(norm)) + "\n").encode("utf-8")
    gz = gzip.compress(txt, 9)
    print(f"{name:38s} originales {len(orig):8d}  normalizadas 3-12: {len(norm):8d}  txt {len(txt)/1024:7.0f} KB  gz {len(gz)/1024:6.0f} KB")
    with open(os.path.join(out_dir, f"{name}.txt"), "wb") as f: f.write(txt)
    # mapa normalizada -> originales (para colisiones)
    with open(os.path.join(out_dir, f"{name}.map.tsv"), "w", encoding="utf-8") as f:
        for n in sorted(norm): f.write(n + "\t" + ",".join(sorted(norm[n])) + "\n")
if original_path:
    orig = sorted({unicodedata.normalize("NFC", w) for w in allforms},
                  key=lambda w: w.encode("utf-8"))
    orig = [w for w in orig if w.isalpha() and w == w.lower()]
    with open(original_path, "wb") as f: f.write("\n".join(orig).encode("utf-8"))
    print(f"originales nivel 5 (solo letras): {len(orig)} -> {original_path}")
