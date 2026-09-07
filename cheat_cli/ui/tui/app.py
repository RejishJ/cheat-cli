"""Main Textual TUI application for cheat-cli."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.events import Key
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Static

from ...cheat_service import CheatService
from ...runner import RunResult, run_command
from ...safety import classify_command
from ..clipboard import ClipboardError, copy_to_clipboard
from .browser import EntryTable

if TYPE_CHECKING:
    from ...core.models import Entry


class SearchInput(Input):
    """Input that stops printable key events from reaching Screen priority bindings.

    Printable chars and backspace are handled by Input and stopped.
    Enter/escape are NOT handled by Input — they bubble to BrowserScreen.on_key
    for synchronous processing (avoids async message delay of Input.Submitted).
    """

    can_focus = False

    async def _on_key(self, event: Key) -> None:
        if event.is_printable or event.key == "backspace":
            await super()._on_key(event)
            event.stop()


_HELP_TEXT = """\
[b]cheat-cli — Keyboard Shortcuts[/b]

[j] / [down]     Move down
[k] / [up]       Move up
[ctrl+d]         Page down
[ctrl+u]         Page up
[g]              First entry
[G]              Last entry

[/]              Search
[enter]          Open details
[a]              Add command
[e]              Edit command
[d]              Delete command
[y]              Copy command
[r]              Run command
[escape]         Close search / clear filter / go back
[?]              Show this help
[q]              Quit
"""


class HelpScreen(Screen):
    """Modal help overlay showing keyboard shortcuts."""

    CSS = """
    #help-container {
        width: 60;
        max-width: 90%;
        height: auto;
        border: solid $accent;
        padding: 1 2;
        margin: 2 4;
        background: $surface;
    }
    """

    BINDINGS = [  # noqa: RUF012
        Binding("escape", "dismiss", "Close", show=False),
        Binding("q", "dismiss", "Close", show=False),
        Binding("question_mark", "dismiss", "Close", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(_HELP_TEXT, id="help-container")
        yield Footer()

    def action_dismiss(self) -> None:
        self.dismiss()


class DetailScreen(Screen):
    """Screen displaying details of a single entry."""

    CSS = """
    #detail-container {
        width: 80%;
        max-width: 80;
        height: auto;
        border: solid $accent;
        padding: 1 2;
        margin: 2 4;
    }
    """

    BINDINGS = [  # noqa: RUF012
        Binding("escape", "pop_screen", "Back", show=False),
        Binding("q", "quit", "Quit", show=False),
    ]

    def __init__(self, entry: Entry) -> None:
        super().__init__()
        self.entry = entry

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            f"[b]Tool:[/b]       {self.entry.tool}\n"
            f"[b]Command:[/b]     {self.entry.command}\n"
            f"[b]Description:[/b] {self.entry.description}\n"
            f"[b]Tags:[/b]        {self.entry.tags}",
            id="detail-container",
        )
        yield Footer()

    def action_pop_screen(self) -> None:
        self.dismiss()


class ConfirmScreen(Screen):
    """Modal confirmation screen for risky command execution."""

    CSS = """
    #confirm-container {
        width: 70;
        max-width: 90%;
        height: auto;
        border: solid $warning;
        padding: 1 2;
        margin: 2 4;
        background: $surface;
    }
    #confirm-command {
        padding: 0 0 1 0;
    }
    #confirm-warning {
        color: $warning;
        padding: 0 0 1 0;
    }
    #confirm-actions {
        padding: 1 0 0 0;
    }
    """

    BINDINGS = [  # noqa: RUF012
        Binding("y", "confirm", "Yes", show=False),
        Binding("n", "cancel", "No", show=False),
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, command: str, risk_matches: list) -> None:
        super().__init__()
        self.command = command
        self.risk_matches = risk_matches
        self.confirmed = False

    def compose(self) -> ComposeResult:
        yield Header()
        risk_lines = "\n".join(f"  - {m.description}" for m in self.risk_matches)
        yield Static(
            f"[b]Command:[/b]\n{self.command}\n\n"
            f"[b]Warning:[/b]\n"
            f"This command may modify or delete data.\n"
            f"Matched patterns:\n{risk_lines}\n\n"
            f"[b]Run this command?[/b]",
            id="confirm-container",
        )
        yield Static("[y] Yes    [n] No    [Esc] Cancel", id="confirm-actions")
        yield Footer()

    def action_confirm(self) -> None:
        self.confirmed = True
        self.dismiss(self.confirmed)

    def action_cancel(self) -> None:
        self.confirmed = False
        self.dismiss(self.confirmed)


class ResultScreen(Screen):
    """Screen displaying command execution results."""

    CSS = """
    #result-container {
        width: 100%;
        height: 1fr;
        padding: 1 2;
    }
    #result-header {
        height: auto;
        padding: 0 0 1 0;
    }
    #result-scroll {
        height: 1fr;
        border: solid $accent;
    }
    #result-output {
        width: 100%;
    }
    #result-status {
        height: 1;
        dock: bottom;
        background: $surface;
        color: $text-muted;
        padding: 0 1;
    }
    """

    BINDINGS = [  # noqa: RUF012
        Binding("escape", "dismiss", "Back", show=False),
        Binding("q", "dismiss", "Back", show=False),
    ]

    def __init__(self, result: RunResult) -> None:
        super().__init__()
        self.result = result

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="result-container"):
            yield Static(
                f"[b]Command:[/b] {self.result.command}",
                id="result-header",
            )
            with VerticalScroll(id="result-scroll"):
                output_parts = []
                if self.result.stdout:
                    output_parts.append(f"[b]Output:[/b]\n{self.result.stdout.rstrip()}")
                if self.result.stderr:
                    output_parts.append(f"[b]Errors:[/b]\n{self.result.stderr.rstrip()}")
                if self.result.error:
                    output_parts.append(f"[b]Error:[/b] {self.result.error}")
                if not output_parts:
                    output_parts.append("[dim]No output[/dim]")
                yield Static("\n\n".join(output_parts), id="result-output")
            status_color = "green" if self.result.success else "red"
            yield Static(
                f"[{status_color}]{self.result.status_label}[/]",
                id="result-status",
            )
        yield Footer()

    def action_dismiss(self) -> None:
        self.dismiss()


class EditorScreen(Screen):
    """Screen for adding or editing a command entry."""

    CSS = """
    #editor-container {
        width: 70;
        max-width: 90%;
        height: auto;
        border: solid $accent;
        padding: 1 2;
        margin: 2 4;
        background: $surface;
    }
    #editor-title {
        padding: 0 0 1 0;
    }
    #editor-error {
        color: $error;
        padding: 0 0 1 0;
        display: none;
    }
    #editor-error.visible {
        display: block;
    }
    .field-row {
        height: auto;
        padding: 0 0 1 0;
    }
    .field-label {
        width: 14;
    }
    #editor-actions {
        padding: 1 0 0 0;
    }
    """

    BINDINGS = [  # noqa: RUF012
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("ctrl+s", "save", "Save", show=False),
    ]

    def __init__(
        self,
        title: str,
        tool: str = "",
        command: str = "",
        description: str = "",
        tags: str = "",
    ) -> None:
        super().__init__()
        self.editor_title = title
        self.initial_tool = tool
        self.initial_command = command
        self.initial_description = description
        self.initial_tags = tags
        self.result: tuple[str, str, str, str] | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="editor-container"):
            yield Static(self.editor_title, id="editor-title")
            yield Static("", id="editor-error")
            with Vertical(id="editor-fields"):
                with Vertical(classes="field-row"):
                    yield Static("Tool:", classes="field-label")
                    yield Input(
                        value=self.initial_tool, id="tool-input", placeholder="Tool name"
                    )
                with Vertical(classes="field-row"):
                    yield Static("Command:", classes="field-label")
                    yield Input(
                        value=self.initial_command,
                        id="command-input",
                        placeholder="Command to cheat",
                    )
                with Vertical(classes="field-row"):
                    yield Static("Description:", classes="field-label")
                    yield Input(
                        value=self.initial_description,
                        id="description-input",
                        placeholder="What it does",
                    )
                with Vertical(classes="field-row"):
                    yield Static("Tags:", classes="field-label")
                    yield Input(
                        value=self.initial_tags,
                        id="tags-input",
                        placeholder="Space-separated tags",
                    )
            yield Static("[ctrl+s] Save    [Esc] Cancel", id="editor-actions")
        yield Footer()

    def _show_error(self, message: str) -> None:
        error_widget = self.query_one("#editor-error", Static)
        error_widget.update(message)
        error_widget.add_class("visible")

    def action_save(self) -> None:
        tool = self.query_one("#tool-input", Input).value.strip()
        command = self.query_one("#command-input", Input).value.strip()
        description = self.query_one("#description-input", Input).value.strip()
        tags = self.query_one("#tags-input", Input).value.strip()

        errors: list[str] = []
        if not tool:
            errors.append("Tool cannot be empty")
        if not command:
            errors.append("Command cannot be empty")

        if errors:
            self._show_error("; ".join(errors))
            return

        self.result = (tool, command, description, tags)
        self.dismiss(self.result)

    def action_cancel(self) -> None:
        self.result = None
        self.dismiss(None)


class DeleteConfirmScreen(Screen):
    """Modal confirmation screen for deleting a command entry."""

    CSS = """
    #delete-container {
        width: 60;
        max-width: 90%;
        height: auto;
        border: solid $warning;
        padding: 1 2;
        margin: 2 4;
        background: $surface;
    }
    #delete-command {
        padding: 0 0 1 0;
    }
    #delete-warning {
        color: $warning;
        padding: 0 0 1 0;
    }
    #delete-actions {
        padding: 1 0 0 0;
    }
    """

    BINDINGS = [  # noqa: RUF012
        Binding("y", "confirm", "Yes", show=False),
        Binding("n", "cancel", "No", show=False),
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, entry: Entry) -> None:
        super().__init__()
        self.entry = entry
        self.confirmed = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            f"[b]Delete Command?[/b]\n\n"
            f"{self.entry.command}\n\n"
            f"[dim]Tool: {self.entry.tool}  |  "
            f"Tags: {self.entry.tags or '(none)'}[/dim]",
            id="delete-container",
        )
        yield Static("[y] Yes    [n] No    [Esc] Cancel", id="delete-actions")
        yield Footer()

    def action_confirm(self) -> None:
        self.confirmed = True
        self.dismiss(self.confirmed)

    def action_cancel(self) -> None:
        self.confirmed = False
        self.dismiss(self.confirmed)


_BROWSER_NAV_ACTIONS = frozenset({
    "cursor_down", "cursor_up", "cursor_first", "cursor_last",
    "page_down", "page_up", "quit",
    "add_entry", "edit_entry", "delete_entry",
})


class BrowserScreen(Screen):
    """Main browser screen showing entry list with interactive search."""

    CSS = """
    #search-input {
        dock: top;
        height: 1;
        display: none;
    }
    #search-input.active {
        display: block;
    }
    #status-bar {
        height: 1;
        dock: bottom;
        background: $surface;
        color: $text-muted;
        padding: 0 1;
    }
    #no-results {
        height: 1;
        dock: bottom;
        padding: 0 1;
        color: $text-muted;
        display: none;
    }
    #no-results.visible {
        display: block;
    }
    """

    BINDINGS = [  # noqa: RUF012
        Binding("j", "cursor_down", "Down", show=False, priority=True),
        Binding("k", "cursor_up", "Up", show=False, priority=True),
        Binding("down", "cursor_down", "Down", show=False, priority=True),
        Binding("up", "cursor_up", "Up", show=False, priority=True),
        Binding("ctrl+d", "page_down", "Page Down", show=False, priority=True),
        Binding("ctrl+u", "page_up", "Page Up", show=False, priority=True),
        Binding("g", "cursor_first", "First", show=False, priority=True),
        Binding("G", "cursor_last", "Last", show=False, priority=True),
        Binding("a", "add_entry", "Add", show=False, priority=True),
        Binding("e", "edit_entry", "Edit", show=False, priority=True),
        Binding("d", "delete_entry", "Delete", show=False, priority=True),
        Binding("y", "copy_command", "Copy", show=False, priority=True),
        Binding("r", "run_command", "Run", show=False, priority=True),
        Binding("q", "quit", "Quit", show=False, priority=True),
        Binding("escape", "cancel_or_quit", "Quit", show=False, priority=True),
        Binding("question_mark", "show_help", "Help", show=False, priority=True),
    ]

    _clipboard_fn = staticmethod(copy_to_clipboard)

    def __init__(self, entries: list[Entry], query: str = "") -> None:
        super().__init__()
        self.all_entries = entries
        self.entries = list(entries)
        self.active_query = query
        self.search_active = False
        self._clipboard_feedback: str | None = None
        self._editing_entry: Entry | None = None
        self._delete_target: Entry | None = None

    def check_action(self, action: str, params: tuple) -> bool | None:
        return not (self.search_active and action in _BROWSER_NAV_ACTIONS)

    def compose(self) -> ComposeResult:
        yield Header()
        title = "cheat-cli" + (f" — {self.active_query}" if self.active_query else "")
        yield Static(title, id="title-bar")
        yield SearchInput(placeholder="Search...", id="search-input")
        yield Vertical(EntryTable(self.entries, id="entry-list"))
        yield Static(self._status_hint(), id="status-bar")
        yield Static("No matching commands", id="no-results")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#entry-list", EntryTable)
        table.focus()
        if self.active_query:
            self._apply_filter(self.active_query)

    async def on_key(self, event: Key) -> None:
        if event.character == "/":
            if not self.search_active:
                event.stop()
                self.action_start_search()
        elif event.key == "enter":
            event.stop()
            if self.search_active:
                self._confirm_search()
            else:
                self.action_open_detail()

    def _status_hint(self) -> str:
        if self._clipboard_feedback:
            return self._clipboard_feedback
        total = len(self.all_entries)
        shown = len(self.entries)
        count = f"{shown}/{total}" if self.active_query else str(total)
        base = "j/k Navigate  Enter Details  a Add  e Edit  d Delete  y Copy  r Run  ? Help  q Quit"
        if self.search_active:
            return f"Search ({count})  |  Enter Confirm  Esc Cancel  |  {base}"
        if self.active_query:
            return f"Filter: {self.active_query} ({count})  |  / Search  Esc Clear  |  {base}"
        return f"{count} commands  |  / Search  |  {base}"

    def _update_status(self) -> None:
        self.query_one("#status-bar", Static).update(self._status_hint())
        no_results = self.query_one("#no-results", Static)
        if self.entries is not None and len(self.entries) == 0:
            no_results.add_class("visible")
        else:
            no_results.remove_class("visible")

    def _apply_filter(self, query: str) -> None:
        if query:
            self.entries = self.app.service.search_filtered(self.all_entries, query)
        else:
            self.entries = list(self.all_entries)
        self.query_one(EntryTable).update_entries(self.entries)
        self._update_status()

    def action_start_search(self) -> None:
        search_input = self.query_one("#search-input", SearchInput)
        search_input.value = ""
        search_input.add_class("active")
        search_input.can_focus = True
        search_input.focus()
        self.search_active = True
        self._update_status()

    def _exit_search(self) -> None:
        search_input = self.query_one("#search-input", SearchInput)
        search_input.remove_class("active")
        search_input.can_focus = False
        search_input.blur()
        self.search_active = False
        self.query_one(EntryTable).focus()
        self._update_status()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-input" and self.search_active:
            self._apply_filter(event.value)

    def _confirm_search(self) -> None:
        search_input = self.query_one("#search-input", SearchInput)
        self.active_query = search_input.value
        self._exit_search()

    def action_cancel_or_quit(self) -> None:
        if self.search_active:
            search_input = self.query_one("#search-input", SearchInput)
            search_input.value = ""
            self._exit_search()
            self._apply_filter(self.active_query)
        elif self.active_query:
            self.active_query = ""
            self._apply_filter("")
            self._update_status()
        else:
            self.app.exit()

    def action_show_help(self) -> None:
        self.app.push_screen(HelpScreen())

    def action_copy_command(self) -> None:
        """Copy the selected entry's command to the clipboard."""
        entry = self.query_one(EntryTable).selected_entry()
        if entry is None:
            return
        try:
            self._clipboard_fn(entry.command)
            self._clipboard_feedback = f"Copied: {entry.command}"
        except ClipboardError:
            self._clipboard_feedback = "Could not copy command"
        self._update_status()
        self.set_timer(1.5, self._clear_clipboard_feedback)

    def _clear_clipboard_feedback(self) -> None:
        self._clipboard_feedback = None
        self._update_status()

    def action_run_command(self) -> None:
        """Execute the selected entry's command."""
        entry = self.query_one(EntryTable).selected_entry()
        if entry is None:
            return
        risk_matches = classify_command(entry.command)
        if risk_matches:
            self.app.push_screen(
                ConfirmScreen(entry.command, risk_matches),
                callback=self._on_confirm_result,
            )
        else:
            self._execute_command(entry.command)

    def _on_confirm_result(self, confirmed: bool) -> None:
        """Handle confirmation screen result."""
        if confirmed:
            entry = self.query_one(EntryTable).selected_entry()
            if entry is not None:
                self._execute_command(entry.command)

    def _execute_command(self, command: str) -> None:
        """Run the command and display results."""
        result = run_command(command)
        self.app.push_screen(ResultScreen(result))

    def action_cursor_down(self) -> None:
        self.query_one(EntryTable).move_down()

    def action_cursor_up(self) -> None:
        self.query_one(EntryTable).move_up()

    def action_page_down(self) -> None:
        self.query_one(EntryTable).move_down(step=10)

    def action_page_up(self) -> None:
        self.query_one(EntryTable).move_up(step=10)

    def action_cursor_first(self) -> None:
        self.query_one(EntryTable).select_first()

    def action_cursor_last(self) -> None:
        self.query_one(EntryTable).select_last()

    def action_open_detail(self) -> None:
        entry = self.query_one(EntryTable).selected_entry()
        if entry is not None:
            self.app.push_screen(DetailScreen(entry))

    def action_add_entry(self) -> None:
        """Open the editor to add a new command."""
        self.app.push_screen(
            EditorScreen("Add Command"),
            callback=self._on_add_result,
        )

    def _on_add_result(self, result: tuple[str, str, str, str] | None) -> None:
        if result is None:
            return
        tool, command, description, tags = result
        try:
            self.app.service.add_entry(tool, command, description, tags)
            self._refresh_entries()
            # Select the newly added entry (now last in the list)
            table = self.query_one(EntryTable)
            table.select_last()
            self._feedback(f"Added: {command}")
        except ValueError as e:
            self._feedback(str(e))

    def action_edit_entry(self) -> None:
        """Open the editor to edit the selected command."""
        entry = self.query_one(EntryTable).selected_entry()
        if entry is None:
            return
        self._editing_entry = entry
        self.app.push_screen(
            EditorScreen(
                "Edit Command",
                tool=entry.tool,
                command=entry.command,
                description=entry.description,
                tags=entry.tags,
            ),
            callback=self._on_edit_result,
        )

    def _on_edit_result(self, result: tuple[str, str, str, str] | None) -> None:
        if result is None:
            return
        tool, command, description, tags = result
        original = getattr(self, "_editing_entry", None)
        if original is None:
            return
        try:
            self.app.service.update_entry(original, tool, command, description, tags)
            self._refresh_entries()
            self._feedback(f"Updated: {command}")
        except ValueError as e:
            self._feedback(str(e))

    def action_delete_entry(self) -> None:
        """Open confirmation to delete the selected command."""
        entry = self.query_one(EntryTable).selected_entry()
        if entry is None:
            return
        self._delete_target = entry
        self.app.push_screen(
            DeleteConfirmScreen(entry),
            callback=self._on_delete_result,
        )

    def _on_delete_result(self, confirmed: bool) -> None:
        if not confirmed:
            return
        target = getattr(self, "_delete_target", None)
        if target is None:
            return
        self.app.service.delete_entry(target)
        self._refresh_entries()
        self._feedback(f"Deleted: {target.command}")

    def _refresh_entries(self) -> None:
        """Reload entries from the service, preserving filter if active."""
        self.all_entries = self.app.service.list_entries()
        if self.active_query:
            self._apply_filter(self.active_query)
        else:
            self.entries = list(self.all_entries)
            self.query_one(EntryTable).update_entries(self.entries)
        self._update_status()

    def _feedback(self, message: str) -> None:
        """Show a short-lived feedback message in the status bar."""
        self._clipboard_feedback = message
        self._update_status()
        self.set_timer(1.5, self._clear_clipboard_feedback)

    def action_quit(self) -> None:
        self.app.exit()


class CheatApp(App):
    """Main TUI application for cheat-cli."""

    TITLE = "cheat-cli"

    def __init__(
        self,
        service: CheatService,
        query: str = "",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.service = service
        self.initial_query = query

    def on_mount(self) -> None:
        entries = self.service.list_entries()
        self.push_screen(BrowserScreen(entries, self.initial_query))


def run_tui(service: CheatService, query: str = "") -> None:
    """Launch the TUI with the given service and optional initial query."""
    app = CheatApp(service=service, query=query)
    app.run()
