"""Browser view for cheat-cli TUI — displays entries in a DataTable."""

from __future__ import annotations

from textual.containers import Vertical
from textual.widgets import DataTable

from ...core.models import Entry


class EntryTable(Vertical):
    """Wraps a DataTable showing cheat entries with selection tracking."""

    DEFAULT_CSS = """
    EntryTable {
        height: 1fr;
    }
    DataTable {
        height: 1fr;
    }
    """

    def __init__(self, entries: list[Entry], **kwargs) -> None:
        super().__init__(**kwargs)
        self.entries = entries
        self.flat_index = 0

    def compose(self):
        table = DataTable(id="entry-table")
        table.add_columns("Tool", "Command", "Description", "Tags")
        for entry in self.entries:
            table.add_row(
                entry.tool, entry.command, entry.description, entry.tags,
            )
        yield table

    @property
    def entry_count(self) -> int:
        return len(self.entries)

    def _max_flat(self) -> int:
        return max(0, len(self.entries) - 1)

    def select(self, index: int) -> None:
        self.flat_index = max(0, min(index, self._max_flat()))
        self._update_cursor()

    def select_first(self) -> None:
        self.flat_index = 0
        self._update_cursor()

    def select_last(self) -> None:
        self.flat_index = self._max_flat()
        self._update_cursor()

    def move_down(self, step: int = 1) -> None:
        self.flat_index = min(self.flat_index + step, self._max_flat())
        self._update_cursor()

    def move_up(self, step: int = 1) -> None:
        self.flat_index = max(self.flat_index - step, 0)
        self._update_cursor()

    def selected_entry(self) -> Entry | None:
        if not self.entries:
            return None
        idx = max(0, min(self.flat_index, len(self.entries) - 1))
        return self.entries[idx]

    def update_entries(self, entries: list[Entry]) -> None:
        """Replace the displayed entries, preserving selection when possible."""
        old_index = self.flat_index
        self.entries = entries
        if self.entries:
            self.flat_index = min(old_index, self._max_flat())
        else:
            self.flat_index = 0
        table = self.query_one("#entry-table", DataTable)
        table.clear()
        for entry in self.entries:
            table.add_row(
                entry.tool, entry.command, entry.description, entry.tags,
            )
        if self.entries:
            table.cursor_type = "row"
            table.move_cursor(row=self.flat_index, animate=False)

    def _update_cursor(self) -> None:
        table = self.query_one("#entry-table", DataTable)
        if self.entries:
            table.cursor_type = "row"
            table.move_cursor(row=self.flat_index, animate=False)
