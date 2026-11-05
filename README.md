# Swipe word dictionaries (Spanish, Brazilian Portuguese and French)

Word lists derived from the **RLA-ES Hunspell dictionary v2.9** (Santiago Bosio and contributors,
<https://github.com/sbosio/rla-es>), used under the **Mozilla Public License 2.0** (RLA-ES is offered under
"MPL 1.1 or later", among other licenses). This repository is the public Source Code Form of the modified files that
ship inside Tappller's word puzzle game for iOS, as the MPL 2.0 requires.

| File | What it is |
|---|---|
| `es/es-expandido-original.txt` | Every word form of RLA-ES 2.9 (level 5), expanded from `es.dic` + `es.aff` with `tools/hunspell_expand.py`: lower case, NFC, letters only, one per line, sorted by UTF-8 bytes. |
| `es/words.txt` | The game dictionary: the forms above normalized to upper case without accents (Ñ is kept as its own letter), 3 to 12 letters, minus a list of offensive words. Sorted by bytes. |
| `es/sensitive.txt` | Words from `words.txt` that the game accepts but never shows by name. |
| `es/words.bin` | `words.txt` in the SWD1 binary format, little endian: `"SWD1"`, `UInt32` version (1), `UInt32` count, `UInt32` blob size, then `UInt32 offsets[count + 1]` and the UTF-8 words concatenated in the same order, without separators. |
| `tools/hunspell_expand.py` | The expander used to produce `es-expandido-original.txt` (`python3 -I hunspell_expand.py es.aff es.dic out_dir originals.txt`). |
| `LICENSE`, `NOTICE` | MPL 2.0 text and the notice that ships with the files. |

The offensive-word filters are Tappller's own editorial lists and is not part of the covered files.


## Brazilian Portuguese (`pt/`) and French (`fr/`)

| File | What it is |
|---|---|
| `pt/pt-expandido-original.txt` | Every word form of **VERO 3.2** (pt_BR, Raimundo Santos Moura and contributors, <https://github.com/LibreOffice/dictionaries/tree/master/pt_BR>), expanded with `python3 -I tools/hunspell_expand.py --sin-truncadas-mo pt_BR.aff pt_BR.dic - pt-expandido-original.txt`. VERO is licensed "LGPLv3 and the Mozilla Public License"; it is used under the MPL (taken as MPL 1.1 and upgraded to MPL 2.0 under its section 6.2). `--sin-truncadas-mo` drops the rules that produce the hyphen-truncated first person plural (*cantarmo* from *cantarmo-nos*). |
| `fr/fr-expandido-original.txt` | Every word form of the **Grammalecte/Dicollecte French Hunspell dictionary v7.7**, "Classique" variant (Olivier R. and contributors, <https://grammalecte.net/>, MPL 2.0), expanded with `python3 -I tools/hunspell_expand.py fr-classique.aff fr-classique.dic - fr-expandido-original.txt`; entries with the KEEPCASE flag (units such as *kat*, *mol*) are left out. |
| `pt/words.txt`, `fr/words.txt` | The game dictionaries: the forms above normalized to upper case with every accent, cedilla and diaeresis folded to its base letter (A–Z), 3 to 12 letters, minus a list of offensive words. In French, Œ and Æ are also written as OE and AE. Sorted by bytes. |
| `pt/sensitive.txt`, `fr/sensitive.txt` | Words the game accepts but never shows by name. |
| `pt/words.bin`, `fr/words.bin` | `words.txt` in the SWD1 binary format (see above). |
| `pt/NOTICE`, `fr/NOTICE` | The notice that ships with each language's files. |

---

# Diccionarios del juego de palabras (español)

Listas de palabras derivadas del **diccionario Hunspell RLA-ES v2.9** (Santiago Bosio y colaboradores,
<https://github.com/sbosio/rla-es>), usadas bajo la **Mozilla Public License 2.0** (RLA-ES se ofrece bajo "MPL 1.1 o
posterior", entre otras licencias). Este repositorio es la forma fuente pública de los archivos modificados que viajan
dentro del juego de palabras de Tappller para iOS, como exige la MPL 2.0.

- `es/es-expandido-original.txt`: todas las formas de RLA-ES 2.9 (nivel 5), expandidas con `tools/hunspell_expand.py`.
- `es/words.txt`: el diccionario del juego (mayúsculas sin tildes, con la Ñ como letra propia, de 3 a 12 letras, sin
  una lista de palabras ofensivas).
- `es/sensitive.txt`: palabras que el juego acepta pero nunca muestra por su nombre.
- `es/words.bin`: `words.txt` en el formato binario SWD1.
- `LICENSE` y `NOTICE`: el texto de la MPL 2.0 y el aviso que acompaña a los archivos.

## Portugués de Brasil (`pt/`) y francés (`fr/`)

- `pt/pt-expandido-original.txt`: todas las formas de **VERO 3.2** (pt_BR de LibreOffice), expandidas con `tools/hunspell_expand.py --sin-truncadas-mo`; VERO dice "LGPLv3 and the Mozilla Public License" y se usa bajo la MPL (1.1, llevada a la 2.0 por su sección 6.2).
- `fr/fr-expandido-original.txt`: todas las formas de **Grammalecte/Dicollecte 7.7 « Classique »** (MPL 2.0), sin las entradas KEEPCASE.
- `pt/words.txt` y `fr/words.txt`: los diccionarios del juego (mayúsculas de la A a la Z, con acentos, cedilla y diéresis plegados; en francés, Œ y Æ también como OE y AE; de 3 a 12 letras; sin una lista de palabras ofensivas). `sensitive.txt`, `words.bin` y `NOTICE` como en español.
