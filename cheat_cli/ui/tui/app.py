"""Main Textual TUI application for cheat-cli."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.events import Key
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Static

from ...cheat_service import CheatService
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
        self.app.pop_screen()


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
        self.app.pop_screen()


_BROWSER_NAV_ACTIONS = frozenset({
    "cursor_down", "cursor_up", "cursor_first", "cursor_last",
    "page_down", "page_up", "quit",
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
        Binding("q", "quit", "Quit", show=False, priority=True),
        Binding("escape", "cancel_or_quit", "Quit", show=False, priority=True),
        Binding("question_mark", "show_help", "Help", show=False, priority=True),
    ]

    def __init__(self, entries: list[Entry], query: str = "") -> None:
        super().__init__()
        self.all_entries = entries
        self.entries = list(entries)
        self.active_query = query
        self.search_active = False

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
        total = len(self.all_entries)
        shown = len(self.entries)
        count = f"{shown}/{total}" if self.active_query else str(total)
        base = "j/k Navigate  Enter Details  ? Help  q Quit"
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
