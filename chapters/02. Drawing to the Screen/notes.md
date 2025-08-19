# Chapter 2 – Drawing to the Screen

## Overview

In this chapter, we transition from a command-line browser to a graphical user interface. We build a visual browser window using Tkinter that can display text, handle line wrapping, and provide scrolling functionality. This establishes the foundation for all future visual rendering features.

---

## Key Concepts

### Tkinter Graphics Framework

- Tkinter provides Python's standard GUI toolkit with a Canvas widget for drawing operations.

**Coordinate System:**
- Origin (0,0) at top-left corner
- X increases rightward, Y increases downward
- All measurements in pixels

**Drawing Operations:**
```python
canvas.create_text(x, y, text="Hello")     # Draw text at position
canvas.create_rectangle(x1, y1, x2, y2)   # Draw rectangle
canvas.create_image(x, y, image=img)      # Draw image/emoji
canvas.delete("all")                       # Clear canvas
```

---

### Display List Architecture

Instead of drawing text immediately, we compute a display list that separates layout calculation from rendering.

**Display List Structure:**
```python
display_list = [(kind, x, y, c), ...]
# Text: ("text", 13, 18, 'H')
# Emoji: ("emoji", 26, 18, PhotoImage_object)
```

**Benefits:**
- Separation of concerns: layout logic independent of drawing
- Efficient re-rendering: can redraw same content without recalculation
- Scrolling support: easy to offset positions during rendering
- Mixed content: supports both text and images seamlessly

---

### Typography and Spacing

Fixed-width character layout using consistent spacing constants:
```python
WIDTH, HEIGHT = 800, 600         # Window dimensions
HSTEP, VSTEP = 13, 18            # Character spacing: horizontal, vertical
SCROLL_STEP = 100                # Pixels per scroll action
SCROLLBAR_WIDTH = 15             # Scrollbar thickness
EMOJI_OFFSET_Y = 3               # Vertical alignment for emoji
```

**Character Positioning:**
- Each character occupies 13 pixels horizontally
- Each line occupies 18 pixels vertically
- Provides uniform, predictable text layout

---

### Text Layout Engine

Implements basic text flow with automatic line wrapping and newline support:
```python
def layout(text, rtl):
    display_list = []
    if rtl:
        cursor_x = WIDTH - HSTEP - SCROLLBAR_WIDTH
        step = -HSTEP
    else:
        cursor_x = HSTEP
        step = +HSTEP
    cursor_y = VSTEP

    for c in text:
        if c == "\n":
            # Reset cursor to appropriate side
            cursor_x = WIDTH - HSTEP - SCROLLBAR_WIDTH if rtl else HSTEP
            cursor_y += VSTEP
        else:
            display_list.append(("text", cursor_x, cursor_y, c))
            cursor_x += step
```

**Layout Rules:**
- Start at appropriate margin based on text direction
- Advance cursor horizontally for each character
- Handle explicit newlines with line breaks
- Wrap to next line when approaching edge
- Support both left-to-right (LTR) and right-to-left (RTL) text flow

---

### HTML Lexing

Extract plain text from HTML by filtering out markup tags:
```python
def lex(body):
    text_only = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            text_only += c
    return decode_entities(text_only)
```
- Track whether currently inside or outside HTML tags
- Accumulate only characters outside of tags
- Decode HTML entities for proper display

---

### Viewport and Scrolling

Implement scrollable content larger than the visible window with bounds checking:
```python
def draw(self):
    self.canvas.delete("content")
    for kind, x, y, c in self.display_list:
        # Viewport clipping
        if y > self.scroll + HEIGHT: continue     # Below visible area
        if y + VSTEP < self.scroll: continue      # Above visible area

        if kind == "emoji":
            self.canvas.create_image(x, y - self.scroll + EMOJI_OFFSET_Y, 
                                   image=c, anchor="nw", tags="content")
        else:
            self.canvas.create_text(x, y - self.scroll, 
                                  text=c, anchor="nw", tags="content")
```

**Scrolling Implementation:**
- `self.scroll`: tracks current vertical offset
- Viewport clipping: only render visible characters
- Coordinate translation: subtract scroll offset when drawing
- Bounds checking: prevent scrolling past document edges
- Multi-platform support: keyboard arrows, mouse wheel, touchpad

**Event Handling:**
```python
self.window.bind("<Down>", self.scroll_down)
self.window.bind("<Up>", self.scroll_up)
# Linux mouse wheel
self.canvas.bind('<Button-4>', self.scroll_up)
self.canvas.bind('<Button-5>', self.scroll_down)
# Windows/macOS mouse wheel (with platform differences)
self.canvas.bind('<MouseWheel>', self.mouse_wheel)
```

---

### Window Resizing Support

Handle dynamic window resizing with automatic reflow:
```python
def on_resize(self, e):
    global WIDTH, HEIGHT
    WIDTH = e.width
    HEIGHT = e.height
    # Recalculate layout for new window size
    self.display_list, self.page_height = layout(self.text, self.rtl)
    self.draw()

# Enable resizable window
self.canvas.pack(fill="both", expand=True)
self.canvas.bind('<Configure>', self.on_resize)
```

**Resizing Features:**
- Automatic text reflow on window size change
- Proportional scrollbar adjustment
- Maintained scroll position when possible

---

### Visual Scrollbar

Draw a proportional scrollbar indicating document position and scroll capability:
```python
def draw_scrollbar(self):
    self.canvas.delete("scrollbar")
    if self.page_height <= HEIGHT:
        return  # No scrollbar needed

    scrollbar_x = WIDTH - SCROLLBAR_WIDTH
    visible_ratio = HEIGHT / self.page_height
    scrollbar_height = max(20, int(HEIGHT * visible_ratio))

    max_scroll = self.page_height - HEIGHT
    scroll_ratio = self.scroll / max_scroll if max_scroll > 0 else 0
    scrollbar_y = int(scroll_ratio * (HEIGHT - scrollbar_height))

    self.canvas.create_rectangle(
        scrollbar_x, scrollbar_y,
        scrollbar_x + SCROLLBAR_WIDTH, scrollbar_y + scrollbar_height,
        fill="white", tags="scrollbar"
    )
```

**Scrollbar Features:**
- Proportional size indicating visible content ratio
- Position shows current location in document
- Hidden when entire document fits on screen
- Minimum height for usability

---

### Emoji Support

Advanced emoji rendering using OpenMoji image library:
```python
class EmojiManager:
    def __init__(self, emoji_dir="openmoji"):
        self.emoji_dir = emoji_dir
        self.cache = {}  # {filename: PhotoImage}

    def get_image(self, char):
        code_point = f"{ord(char):X}".upper()
        filename = os.path.join(self.emoji_dir, f"{code_point}.png")
        if not os.path.exists(filename):
            return None
        if filename not in self.cache:
            self.cache[filename] = tkinter.PhotoImage(file=filename)
        return self.cache[filename]

    def is_possible_emoji(self, char):
        return (0x1F600 <= ord(char) <= 0x1F64F) or (0x1F300 <= ord(char) <= 0x1F5FF)
```

**Emoji Features:**
- Unicode codepoint to filename mapping
- Image caching for performance
- Fallback to text rendering if image unavailable
- Support for standard emoji Unicode ranges
- Integration with existing layout engine

**Emoji Layout Integration:**
```python
elif emoji_manager.is_possible_emoji(c):
    img = emoji_manager.get_image(c)
    if img:
        display_list.append(("emoji", cursor_x, cursor_y, img))
    else:
        display_list.append(("text", cursor_x, cursor_y, c))
    cursor_x += step
```

---

### Right-to-Left (RTL) Text Support

Implement basic RTL text flow for languages like Arabic, Persian, and Hebrew:
```python
class Browser:
    def __init__(self, rtl=False):
        self.rtl = rtl  # RTL mode flag
        # ... other initialization

def layout(text, rtl):
    if rtl:
        cursor_x = WIDTH - HSTEP - SCROLLBAR_WIDTH  # Start from right
        step = -HSTEP  # Move leftward
    else:
        cursor_x = HSTEP  # Start from left
        step = +HSTEP  # Move rightward
```

**RTL Features:**
- Command-line flag activation: `--rtl`
- Text flows from right to left
- Line wrapping at left margin
- Proper cursor positioning
- Mixed LTR/RTL content handling

**Command-Line Interface:**
```python
parser = argparse.ArgumentParser(description="A browser CLI")
parser.add_argument('url', nargs='?', default=DEFAULT_FILE)
parser.add_argument('--rtl', action='store_true', help='Enable right-to-left text flow')
```

---

### Error Recovery System

Robust error handling with about:blank fallback:
```python
class URL:
    def __init__(self, url):
        try:
            if ":" not in url:
                self.scheme = "about"
                raise ValueError("Malformed URL: no scheme found")
            # ... normal URL parsing
        except Exception as e:
            print(f"Malformed URL '{url}': {e}. Treating as about:blank")
            self.scheme = "about"
            self.about_page = "blank"

    def request(self, redirects=0):
        elif self.scheme == "about":
            if self.about_page == "blank":
                return ""  # Empty page
            else:
                return f"About page: {self.about_page}"
```

**Error Recovery Features:**
- Malformed URL detection and recovery
- Special about:blank URL scheme
- Graceful degradation instead of crashes
- User-friendly error messages

---

## Implementation Architecture

**Processing Pipeline**
- HTTP Request: Download HTML content using enhanced URL class
- Error Handling: Graceful fallback to about:blank for malformed URLs
- Lexical Analysis: Strip HTML tags, decode entities
- Layout Calculation: Convert text to positioned display list (text + emoji)
- Rendering: Draw visible elements with viewport clipping
- Event Handling: Scroll, resize, mouse/keyboard interactions
- Visual Feedback: Scrollbar indication and bounds enforcement

---

## User Interaction

### Navigation Controls
- Keyboard: Up/Down arrow keys for scrolling
- Mouse Wheel: Platform-specific scroll wheel support
- Touchpad: Gesture support on supported platforms
- Visual: Scrollbar indicates position and scroll capability

### Window Management
- Resizable Window: Dynamic text reflow on size changes
- Responsive Layout: Automatic adjustment to new dimensions
- Proportional Elements: Scrollbar scales with content and viewport

### Text Direction Support
- LTR Mode: Standard left-to-right text flow (default)
- RTL Mode: Right-to-left text flow with `--rtl` flag
- Proper Margins: Text starts from appropriate screen edge
- Line Wrapping: Wraps at correct margin based on text direction

---

## Example Usage

### Basic Usage
```bash
python browser.py https://example.org/
```

### Advanced Features
```bash
python browser.py --rtl file:///path/to/arabic.html    # RTL text support
python browser.py about:blank                          # Error recovery demo
python browser.py data:text/html,<h1>😀 Emoji Test</h1>  # Emoji rendering
```

---

## OpenMoji Setup

- Download OpenMoji Emoji PNG files from project website
- Extract PNG files to `openmoji/` directory
- Files should be named by Unicode codepoint (e.g., `1F600.png`)
- Browser automatically detects and renders supported emoji
