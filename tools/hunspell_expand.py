"""Expansor sencillo de Hunspell (.dic/.aff) para RLA-ES, FLAG UTF-8.
Aplica: sufijo, sufijo+sufijo de continuación, prefijo, y prefijo×sufijo cuando ambos son cross-product.
Etiqueta cada forma con las categorías de las reglas usadas.
Como Hunspell sin FULLSTRIP, una regla no puede quitar la palabra entera (errar → *ierro*).
Las banderas son puntos de código (Hunspell 1.7 junta todas las de 4 bytes, los emoji, en una
sola y por eso acepta basura como *ohmmente*; aquí se respeta lo que quiso el autor).
Uso: python3 -I hunspell_expand.py es.aff es.dic salida_dir [originales.txt]
  originales.txt (opcional): todas las formas del nivel 5 sin normalizar (minúsculas, NFC,
  solo letras, sin filtro de largo), una por línea, ordenadas por bytes UTF-8.
"""
import sys, re, collections, os, gzip, unicodedata

aff_path, dic_path, out_dir = sys.argv[1:4]
original_path = sys.argv[4] if len(sys.argv) > 4 else None

SFX_CAT = {}
for f in "SG": SFX_CAT[f] = "infl"          # plural, género
for f in "REIXD": SFX_CAT[f] = "verb"       # conjugación y participios
for f in "ABCFHJKLMOPQT": SFX_CAT[f] = "deriv"
for f in "NU": SFX_CAT[f] = "dimin"
for f in ["🧠", "🥇", "🏅"]: SFX_CAT[f] = "deriv"  # -mente, superlativos

def first_cp(s): return s[0]

class Rule:
    __slots__ = ("strip", "add", "cont", "cond", "kind")
def cond_regex(c, kind):
    if c == ".": return None
    return re.compile(("^" + c) if kind == "PFX" else (c + "$"))

rules = collections.defaultdict(list)   # flag -> list of Rule
cross = {}
kinds = {}
with open(aff_path, encoding="utf-8") as f:
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
        r.cont = set(cont)
        r.cond = cond_regex(p[4] if len(p) > 4 else ".", p[0])
        rules[flag].append(r)

def cat_of(flag):
    if kinds.get(flag) == "PFX": return "pref"
    return SFX_CAT.get(flag, "encl")

def apply_sfx(word, flag):
    for r in rules.get(flag, ()):
        if r.strip and not word.endswith(r.strip): continue
        if len(r.strip) >= len(word): continue   # sin FULLSTRIP: la raíz no puede quedar vacía
        if r.cond is not None and not r.cond.search(word): continue
        base = word[:len(word) - len(r.strip)] if r.strip else word
        yield base + r.add, r.cont
def apply_pfx(word, flag):
    for r in rules.get(flag, ()):
        if r.strip and not word.startswith(r.strip): continue
        if len(r.strip) >= len(word): continue
        if r.cond is not None and not r.cond.search(word): continue
        yield r.add + word[len(r.strip):], r.cont

def expand(root, flags):
    """devuelve dict forma -> frozenset de categorías (la combinación 'más simple' que la genera)."""
    out = {}
    def put(w, cats):
        cats = frozenset(cats)
        if w not in out or len(cats) < len(out[w]): out[w] = cats
    put(root, ())
    sfx_forms = []  # (form, cats, crossable)
    for fl in flags:
        if kinds.get(fl) != "SFX": continue
        c1 = cat_of(fl)
        for w1, cont in apply_sfx(root, fl):
            put(w1, {c1}); sfx_forms.append((w1, {c1}, cross.get(fl, False), cont))
            for fl2 in cont:
                if kinds.get(fl2) == "SFX":
                    for w2, _ in apply_sfx(w1, fl2):
                        c = {c1, cat_of(fl2)}; put(w2, c)
                        sfx_forms.append((w2, c, cross.get(fl, False) and cross.get(fl2, False), set()))
    for fl in flags:
        if kinds.get(fl) != "PFX": continue
        for wp, _ in apply_pfx(root, fl): put(wp, {"pref"})
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

lines = open(dic_path, encoding="utf-8").read().splitlines()[1:]
allforms = {}   # forma original -> cats (mínima)
roots_lower = 0; roots_proper = 0
for ln in lines:
    ln = ln.strip()
    if not ln: continue
    ln = ln.split("\t")[0].split(" ")[0]
    if "/" in ln: root, fl = ln.split("/", 1)
    else: root, fl = ln, ""
    if not root or root[0] != root[0].lower() or root != root.lower():
        roots_proper += 1; continue   # nombres propios, siglas, abreviaturas en mayúscula
    roots_lower += 1
    for w, cats in expand(root, list(fl)).items():
        if w not in allforms or len(cats) < len(allforms[w]): allforms[w] = cats

LEVELS = [
    ("1-lemas", set()),
    ("2-lemas+plural+genero", {"infl"}),
    ("3-+conjugacion", {"infl", "verb"}),
    ("4-+derivados+diminutivos+prefijos", {"infl", "verb", "deriv", "dimin", "pref"}),
    ("5-todo(+encliticos)", {"infl", "verb", "deriv", "dimin", "pref", "encl"}),
]
print(f"raíces en minúscula: {roots_lower}  descartadas (mayúscula/siglas): {roots_proper}")
print(f"formas totales (originales, sin filtrar): {len(allforms)}")
os.makedirs(out_dir, exist_ok=True)
for name, allowed in LEVELS:
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
