# Chapter 3 – Formatting Text

## Overview
This chapter upgrades the browser to handle real English text layout: words of different widths, styled text (bold, italic), and mixed font sizes. It introduces font metrics, baseline alignment, word-by-word line breaking, and font caching for performance. The browser can now render web pages with visually rich typographic features.

## Key Concepts

### Fonts and Font Objects
- **Font**: In Tkinter, a font is defined by family, size (in points), weight (bold/normal), and style (italic/roman).
- **Font Creation**:
    ```python
    import tkinter.font
    font = tkinter.font.Font(family="Times", size=16, weight="bold", slant="italic")
    ```
- **Font Usage**: Pass font objects to `canvas.create_text` to draw styled text.
    ```python
    canvas.create_text(x, y, text="Hi!", font=font)
    ```
- **Font Metrics**: Use `.metrics()` and `.measure(text)` to get vertical/horizontal dimensions for layout.

### Measuring and Laying Out Text
- Use `font.measure(word)` for word width and `font.metrics()` for ascent/descent/linespace.
- **Words** are laid out horizontally; lines break only at word boundaries.
- **Line Wrapping**: If `cursor_x + word_width > WIDTH - HSTEP`, call `flush()` to break the line.
- **Line Spacing**: Add 25% extra space between lines for readability (`leading`).



### Display List Structure
- Each entry in the display list is a tuple:
    ```
    (x, y, word, font)
    ```
- The draw function iterates through this list and calls `canvas.create_text` for each word, using the correct font and position.

### Word-by-Word Layout
- Text is split into words using `str.split()`.
- Each word is measured and placed at `cursor_x`; then `cursor_x` is updated.
    ```python
    for word in text.split():
        w = font.measure(word)
        display_list.append((cursor_x, cursor_y, word, font))
        cursor_x += w + font.measure(" ")
    ```
- Words are never split across lines (no hyphenation).

### Styling Text with Tags
- **Lexing** produces a list of `Text` and `Tag` objects.
    ```python
    class Text:  def __init__(self, text): ...
    class Tag:   def __init__(self, tag): ...
    ```
- Tags (`<b>`, `<i>`, `<big>`, `<small>`, etc.) change font weight, style, or size.
    - `<b>`/`</b>`: bold/normal
    - `<i>`/`</i>`: italic/roman
    - `<big>`/`</big>`: size +4/-4
    - `<small>`/`</small>`: size -2/+2
- Tag changes persist until the corresponding closing tag.

### Baseline Alignment for Mixed Sizes
- When different font sizes are on the same line, align all words to a shared baseline, not to their tops.
- **Two-pass layout**:
    - First pass: Add words to `self.line` buffer with x-position and font.
    - Second pass (flush): Compute baseline using max ascent of all fonts; align each word's y-position accordingly.
    ```python
    baseline = self.cursor_y + 1.25 * max_ascent
    y = baseline - font.metrics("ascent")
    ```
- After flush, update `cursor_y` using max descent for next line.


### Layout Algorithm for Mixed Styles/Sizes


```python
class Layout:
    def __init__(self, tokens):
        self.display_list = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 12
        self.line = []
        for tok in tokens:
            self.token(tok)
        self.flush()

    def token(self, tok):
        if isinstance(tok, Text):
            for word in tok.text.split():
                self.word(word)
        elif tok.tag == "i": self.style = "italic"
        elif tok.tag == "/i": self.style = "roman"
        elif tok.tag == "b": self.weight = "bold"
        elif tok.tag == "/b": self.weight = "normal"
        elif tok.tag == "small": self.size -= 2
        elif tok.tag == "/small": self.size += 2
        elif tok.tag == "big": self.size += 4
        elif tok.tag == "/big": self.size -= 4
        elif tok.tag == "br": self.flush()
        elif tok.tag == "/p": self.flush(); self.cursor_y += VSTEP

    def word(self, word):
        font = get_font(self.size, self.weight, self.style)
        w = font.measure(word)
        self.line.append((self.cursor_x, word, font))
        self.cursor_x += w + font.measure(" ")
        if self.cursor_x + w > WIDTH - HSTEP:
            self.flush()

    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([m["ascent"] for m in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))
        max_descent = max([m["descent"] for m in metrics])
        self.cursor_y = baseline + 1.25 * max_descent
        self.cursor_x = HSTEP
        self.line = []
```


### Notes on Text-of-Different-Sizes

- **Problem**: When mixing text sizes (e.g. `<small>a</small><big>A</big>`) naïvely, words are aligned along their tops. In good typography, all words are aligned along a shared **baseline**.
- **Solution**: Buffer all words in a line, then compute the baseline based on the tallest font's ascent (`max_ascent`). Place each word's y so its ascent sits on the baseline. Cursor_y for the next line is set using `max_descent`.
- **Result**: All text, regardless of size, aligns naturally, just like in professional typesetting.


### Font Caching
- Creating Font objects is slow. Use a global cache (`FONTS`) keyed by `(size, weight, style)` to reuse Font objects.
    ```python
    FONTS = {}
    def get_font(size, weight, style):
        key = (size, weight, style)
        if key not in FONTS:
            font = tkinter.font.Font(size=size, weight=weight, slant=style)
            label = tkinter.Label(font=font)
            FONTS[key] = (font, label)
        return FONTS[key][0]
    ```
- This speeds up layout and rendering on large pages.

## Example Usage

### Basic Usage
```bash
python browser.py https://browser.engineering/examples/example3-sizes.html
```