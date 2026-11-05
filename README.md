# Swipe word dictionaries (Spanish)

Word lists derived from the **RLA-ES Hunspell dictionary v2.9** (Santiago Bosio and contributors,
<https://github.com/sbosio/rla-es>), used under the **Mozilla Public License 2.0** (RLA-ES is offered under
"MPL 1.1 or later", among other licenses). This repository is the public Source Code Form of the modified files that
ship inside Tappller's word puzzle game for iOS, as the MPL 2.0 requires.

| File | What it is |
|---|---|
| `es/es-expandido-original.txt` | Every word form of RLA-ES 2.9 (level 5), expanded from `es.dic` + `es.aff` with `tools/hunspell_expand.py`: lower case, NFC, letters only, one per line, sorted by UTF-8 bytes. |
| `es/words.txt` | The game dictionary: the forms above normalized to upper case without accents (Ñ is kept as its own letter), 3 to 12 letters, minus a list of offensive words. Sorted by bytes. |
| `es/sensitive.txt` | Words from `words.txt` that the game accepts but never shows by name. |
| `es/words.bin` | `words.txt` in the SWD1 binary format: a 16-byte header (`SWD1`, version, count), `UInt32` offsets (`count + 1`, little endian) and the words concatenated in the same order. |
| `tools/hunspell_expand.py` | The expander used to produce `es-expandido-original.txt` (`python3 -I hunspell_expand.py es.aff es.dic out_dir originals.txt`). |
| `LICENSE`, `NOTICE` | MPL 2.0 text and the notice that ships with the files. |

The offensive-word filter is Tappller's own editorial list and is not part of the covered files.

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
