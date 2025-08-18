# Chapter 2 – Drawing to the Screen

## Overview
In this chapter, we transition from a command-line browser to a graphical user interface. We build a visual browser window using Tkinter that can display text, handle line wrapping, and provide scrolling functionality. This establishes the foundation for all future visual rendering features.

## Key Concepts

### Tkinter Graphics Framework
Tkinter provides Python's standard GUI toolkit with a Canvas widget for drawing operations.

**Coordinate System:**
- Origin (0,0) at top-left corner
- X increases rightward, Y increases downward
- All measurements in pixels

**Drawing Operations:**
```python
canvas.create_text(x, y, text="Hello")     # Draw text at position
canvas.create_rectangle(x1, y1, x2, y2)   # Draw rectangle
canvas.delete("all")                       # Clear canvas
```

### Display List Architecture
Instead of drawing text immediately, we compute a display list that separates layout calculation from rendering.

**Display List Structure:**
```python
display_list = [(x, y, character), ...]
# Example: [(13, 18, 'H'), (26, 18, 'e'), (39, 18, 'l'), (52, 18, 'l'), (65, 18, 'o')]
```

**Benefits:**
- **Separation of concerns:** layout logic independent of drawing
- **Efficient re-rendering:** can redraw same content without recalculation
- **Scrolling support:** easy to offset positions during rendering

### Typography and Spacing
Fixed-width character layout using consistent spacing constants:

```python
WIDTH, HEIGHT = 800, 600    # Window dimensions
HSTEP, VSTEP = 13, 18      # Character spacing: horizontal, vertical
```

**Character Positioning:**
- Each character occupies 13 pixels horizontally
- Each line occupies 18 pixels vertically
- Provides uniform, predictable text layout

### Text Layout Engine
Implements basic text flow with automatic line wrapping:

```python
def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        if cursor_x >= WIDTH - HSTEP:  # Line wrap condition
            cursor_x = HSTEP           # Reset to left margin
            cursor_y += VSTEP          # Move to next line
```

**Layout Rules:**
- Start at top-left with margin (HSTEP, VSTEP)
- Advance cursor horizontally for each character
- Wrap to next line when approaching right edge
- Characters are positioned individually for maximum flexibility

### HTML Lexing
Extract plain text from HTML by filtering out markup tags:

```python
def lex(body):
    text = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            text += c
    return text
```
- Track whether currently inside or outside HTML tags
- Accumulate only characters outside of tags

### Viewport and Scrolling
Implement scrollable content larger than the visible window:

```python
SCROLL_STEP = 100  # Pixels to scroll per action

def draw(self):
    self.canvas.delete("all")
    for x, y, c in self.display_list:
        # Viewport clipping
        if y > self.scroll + HEIGHT: continue     # Below visible area
        if y + VSTEP < self.scroll: continue      # Above visible area
        self.canvas.create_text(x, y - self.scroll, text=c)
```

**Scrolling Implementation:**
- `self.scroll`: tracks current vertical offset
- **Viewport clipping:** only render visible characters
- **Coordinate translation:** subtract scroll offset when drawing
- **Keyboard bindings:** Up/Down arrows for navigation

**Event Handling:**
```python
self.window.bind("<Down>", self.scroll_down)
self.window.bind("<Up>", self.scroll_up)

def scroll_down(self, e):
    self.scroll += SCROLL_STEP
    self.draw()
```

## Implementation Architecture

### Browser Class Structure
```python
class Browser:
    def __init__(self)        # Initialize Tkinter window, canvas, scroll state
    def load(url)            # Download → lex → layout → draw pipeline
    def draw(self)           # Render display list with viewport clipping
    def scroll_up/down(e)    # Handle scroll events, redraw
```

### Processing Pipeline
1. **HTTP Request:** Download HTML content using URL class
2. **Lexical Analysis:** Strip HTML tags to extract plain text
3. **Layout Calculation:** Convert text to positioned character list
4. **Rendering:** Draw visible characters to canvas
5. **Event Handling:** Respond to scroll commands and redraw

## User Interaction

### Keyboard Navigation
```python
self.window.bind("<Down>", self.scroll_down)   # Scroll down
self.window.bind("<Up>", self.scroll_up)       # Scroll up
```

### Scrolling Behavior
- Fixed scroll increment (100 pixels)
- Prevents scrolling above document start

## Example Usage

```bash
python browser.py https://example.org/
```

Opens an 800x600 pixel window displaying the webpage content with scrollable text layout.