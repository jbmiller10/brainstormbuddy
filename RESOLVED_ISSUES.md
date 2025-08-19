# Resolved Issues

## TUI Display Issue - Empty Borders Without Content

### Problem Description
When launching the Brainstorm Buddy TUI application (`uv run python -m app.tui.app`), the app would display only empty borders for the three-pane layout without any content inside the panes. The file tree, session viewer, and context panel were rendering their borders but not their actual content.

### Root Cause
The issue occurred when widgets were defined as separate classes in individual files and instantiated during the `compose()` method. The widgets' `on_mount()` methods, which were responsible for populating content, were not being executed properly when the widgets were yielded from external classes.

### Solution
We resolved the issue by:

1. **Defining widget classes inline** within the main screen module (`app/tui/views/main_screen.py`)
2. **Using proper `on_mount()` lifecycle methods** to populate widget content after the widgets are mounted to the DOM
3. **Ensuring widgets write their content during the composition phase** when necessary

The working implementation:
- Creates `SessionViewer(RichLog)` and `FileTreeWidget(Tree)` classes directly in `main_screen.py`
- Populates tree structure and writes welcome messages in their respective `on_mount()` methods
- Uses `VerticalScroll` container with `Static` widgets for the context panel

### Prevention Guidelines

To avoid similar issues in the future:

1. **Test widget composition early**: When creating custom widgets, test them in isolation first before integrating into the main layout

2. **Use inline widget creation for initial content**: When widgets need content during composition, create and populate them inline rather than relying solely on `on_mount()`

3. **Understand Textual's lifecycle**:
   - `compose()` - Widget structure is created
   - `on_mount()` - Widget is added to the DOM and can be populated
   - Content written during composition may not always persist

4. **Prefer simpler approaches first**: Start with inline widget creation and only extract to separate classes when complexity warrants it

5. **Verify rendering at each step**: Run the app frequently during development to catch rendering issues early

6. **Use proper CSS selectors**: Ensure CSS IDs and classes match between widget definitions and stylesheets

### Testing Verification
After the fix:
- ✅ Linting passes (`uv run ruff check .`)
- ✅ Formatting applied (`uv run ruff format .`)
- ✅ Type checking passes (`uv run mypy . --strict`)
- ✅ App displays three-pane layout with content correctly

### Related Files Modified
- `app/tui/views/main_screen.py` - Main fix implementing inline widget classes
- `app/tui/widgets/session_viewer.py` - Original widget that wasn't rendering properly

### Commands for Testing
```bash
# Run the TUI app
uv run python -m app.tui.app

# Run quality checks
uv run ruff check .
uv run ruff format .
uv run mypy . --strict
uv run pytest -q
```

---

## TUI Black Screen Issue - Complete App Not Rendering

### Problem Description
When launching the Brainstorm Buddy TUI app (`uv run python -m app.tui.app`), users saw only a black terminal screen with escape codes but no visible interface - no header, no widgets, no content.

### Root Cause
The issue was caused by incorrect widget composition in the Textual app structure. The main app (`BrainstormBuddyApp`) was yielding a `Screen` object (`MainScreen`) from its `compose()` method, which doesn't work correctly in Textual. Screens should be pushed/popped, not yielded from the app's compose method.

### Solution
Fixed by restructuring the app to compose widgets directly:

1. **Removed the Screen layer** - Changed `BrainstormBuddyApp` to compose widgets directly instead of yielding `MainScreen`
2. **Added proper CSS** - Added `DEFAULT_CSS` with styling for Screen, Header, and Horizontal containers
3. **Direct widget composition** - App now yields: Header → Horizontal(widgets) → Footer → CommandPalette

### Files Modified
- `app/tui/app.py` - Restructured to compose widgets directly
- `app/tui/widgets/file_tree.py` - Set folders to expand by default for better visibility

### Prevention Guidelines

1. **Understand Textual's composition model**:
   - Apps compose widgets directly in their `compose()` method
   - Screens are for modal/navigation, not primary composition
   - Use `push_screen()` for screens, not `yield`

2. **Follow Textual patterns**:
   ```python
   # ❌ WRONG
   class App(App):
       def compose(self):
           yield SomeScreen()

   # ✅ CORRECT
   class App(App):
       def compose(self):
           yield Header()
           yield ContentWidget()
           yield Footer()
   ```

3. **Test incrementally**: Build and test TUI apps widget by widget

4. **Include CSS for layouts**: Always define CSS for container widgets

### Testing Verification
After the fix:
- ✅ App displays header with title "Brainstorm Buddy"
- ✅ Three-pane layout renders correctly
- ✅ All widgets show their content
- ✅ Linting and type checking pass
