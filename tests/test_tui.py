"""Tests for cheat_cli.ui.tui — Textual TUI application."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from cheat_cli.cheat_service import CheatService
from cheat_cli.core.models import CSV_FIELDS


@pytest.fixture
def tui_service(tmp_path: Path) -> CheatService:
    """Create a CheatService with test data for TUI tests."""
    csv_path = tmp_path / "commands.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for tool, cmd, desc, tags in [
            ("git", "git status", "Show working tree status", "repo state"),
            ("git", "git log --oneline", "Compact log", "history"),
            ("git", "git diff", "Show unstaged changes", "diff"),
            ("docker", "docker ps", "List containers", "containers"),
            ("docker", "docker images", "List images", "images"),
            ("kubectl", "kubectl get pods", "List pods", "k8s"),
            ("python", "python -m pytest", "Run tests", "testing"),
            ("python", "python -m ruff check .", "Lint code", "linting"),
        ]:
            writer.writerow({"tool": tool, "command": cmd, "description": desc, "tags": tags})
    return CheatService(csv_path=csv_path)


@pytest.fixture
def empty_tui_service(tmp_path: Path) -> CheatService:
    """Create a CheatService with no entries."""
    csv_path = tmp_path / "empty.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
    return CheatService(csv_path=csv_path)


@pytest.fixture
def single_entry_service(tmp_path: Path) -> CheatService:
    """Create a CheatService with exactly one entry."""
    csv_path = tmp_path / "single.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerow({
            "tool": "git", "command": "git status",
            "description": "Show status", "tags": "repo",
        })
    return CheatService(csv_path=csv_path)


def _create_risky_csv(
    tmp_path: Path,
    filename: str,
    commands: list[tuple[str, str, str, str]],
) -> CheatService:
    """Create a CSV with risky commands for testing."""
    csv_path = tmp_path / filename
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for tool, cmd, desc, tags in commands:
            writer.writerow({"tool": tool, "command": cmd, "description": desc, "tags": tags})
    return CheatService(csv_path=csv_path)


class TestTuiStartup:
    async def test_app_starts(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        app = CheatApp(service=tui_service)
        async with app.run_test():
            assert app.screen is not None

    async def test_entries_loaded(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test():
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 8

    async def test_empty_data_works(self, empty_tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        app = CheatApp(service=empty_tui_service)
        async with app.run_test():
            assert app.screen is not None


class TestTuiNavigation:
    async def test_j_moves_down(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.flat_index == 0
            await pilot.press("j")
            assert entry_table.flat_index == 1

    async def test_k_moves_up(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            entry_table = app.screen.query_one(EntryTable)
            await pilot.press("j")
            await pilot.press("j")
            assert entry_table.flat_index == 2
            await pilot.press("k")
            assert entry_table.flat_index == 1

    async def test_arrow_down_works(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            entry_table = app.screen.query_one(EntryTable)
            await pilot.press("down")
            assert entry_table.flat_index == 1

    async def test_arrow_up_works(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            entry_table = app.screen.query_one(EntryTable)
            await pilot.press("down")
            await pilot.press("down")
            await pilot.press("up")
            assert entry_table.flat_index == 1

    async def test_g_moves_to_first(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            entry_table = app.screen.query_one(EntryTable)
            await pilot.press("j")
            await pilot.press("j")
            await pilot.press("j")
            assert entry_table.flat_index == 3
            await pilot.press("g")
            assert entry_table.flat_index == 0

    async def test_G_moves_to_last(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            entry_table = app.screen.query_one(EntryTable)
            await pilot.press("G")
            assert entry_table.flat_index == 7

    async def test_selection_stays_at_zero(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            entry_table = app.screen.query_one(EntryTable)
            await pilot.press("k")
            assert entry_table.flat_index == 0
            await pilot.press("k")
            assert entry_table.flat_index == 0

    async def test_selection_stays_at_last(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            entry_table = app.screen.query_one(EntryTable)
            last = entry_table.entry_count - 1
            await pilot.press("G")
            assert entry_table.flat_index == last
            await pilot.press("j")
            assert entry_table.flat_index == last


class TestTuiPagination:
    async def test_ctrl_d_pages_down(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.flat_index == 0
            await pilot.press("ctrl+d")
            assert entry_table.flat_index == 7

    async def test_ctrl_u_pages_up(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            entry_table = app.screen.query_one(EntryTable)
            await pilot.press("G")
            assert entry_table.flat_index == 7
            await pilot.press("ctrl+u")
            assert entry_table.flat_index == 0


class TestTuiDetails:
    async def test_enter_opens_details(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp, DetailScreen
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("enter")
            assert isinstance(app.screen, DetailScreen)

    async def test_detail_shows_entry(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp, DetailScreen
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("enter")
            detail = app.screen
            assert isinstance(detail, DetailScreen)
            assert detail.entry.tool == "git"
            assert detail.entry.command == "git status"

    async def test_esc_returns_to_browser(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, DetailScreen
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("enter")
            assert isinstance(app.screen, DetailScreen)
            await pilot.press("escape")
            assert isinstance(app.screen, BrowserScreen)

    async def test_detail_shows_selected_not_first(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp, DetailScreen
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("j")
            await pilot.press("j")
            await pilot.press("enter")
            detail = app.screen
            assert isinstance(detail, DetailScreen)
            assert detail.entry.command == "git diff"


class TestTuiQuery:
    async def test_initial_query_filters(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service, query="docker")
        async with app.run_test():
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 2

    async def test_no_match_query(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service, query="nonexistent")
        async with app.run_test():
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 0

    async def test_empty_query_shows_all(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service, query="")
        async with app.run_test():
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 8


class TestTuiQuit:
    async def test_q_exits(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("q")
            assert app._running is False or app.is_running is False

    async def test_escape_exits_from_browser(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("escape")
            assert app._running is False or app.is_running is False

    async def test_single_entry_navigation(self, single_entry_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=single_entry_service)
        async with app.run_test() as pilot:
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 1
            assert entry_table.flat_index == 0
            await pilot.press("j")
            assert entry_table.flat_index == 0
            await pilot.press("k")
            assert entry_table.flat_index == 0
            await pilot.press("G")
            assert entry_table.flat_index == 0
            await pilot.press("g")
            assert entry_table.flat_index == 0


class TestTuiSearchActivation:
    async def test_slash_enters_search_mode(self, tui_service: CheatService):
        from textual.widgets import Input

        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            screen = app.screen
            assert isinstance(screen, BrowserScreen)
            search_input = screen.query_one("#search-input", Input)
            assert not search_input.has_class("active")
            await pilot.press("slash")
            assert search_input.has_class("active")
            assert screen.search_active

    async def test_search_input_receives_focus(self, tui_service: CheatService):
        from textual.widgets import Input

        from cheat_cli.ui.tui.app import CheatApp
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            search_input = app.screen.query_one("#search-input", Input)
            assert search_input.has_focus

    async def test_slash_starts_search_empty(self, tui_service: CheatService):
        from textual.widgets import Input

        from cheat_cli.ui.tui.app import CheatApp
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            search_input = app.screen.query_one("#search-input", Input)
            assert search_input.has_class("active")
            assert search_input.value == ""


class TestTuiSearchFiltering:
    async def test_typing_filters_results(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 8
            await pilot.press("slash")
            await pilot.press("d", "o", "c", "k", "e", "r")
            assert entry_table.entry_count == 2

    async def test_single_char_filter(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("g")
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 7

    async def test_filter_by_command(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("p", "o", "d", "s")
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 1
            assert entry_table.entries[0].command == "kubectl get pods"

    async def test_filter_by_description(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("l", "i", "n", "t")
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 1
            assert entry_table.entries[0].command == "python -m ruff check ."

    async def test_filter_by_tags(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("h", "i", "s", "t", "o", "r", "y")
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 1
            assert entry_table.entries[0].command == "git log --oneline"

    async def test_filter_case_insensitive(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("D", "O", "C", "K", "E", "R")
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 2

    async def test_filter_no_match(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("z", "z", "z")
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 0


class TestTuiSearchConfirm:
    async def test_enter_confirms_search(self, tui_service: CheatService):
        from textual.widgets import Input

        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("d", "o", "c", "k", "e", "r")
            screen = app.screen
            assert isinstance(screen, BrowserScreen)
            assert screen.search_active
            await pilot.press("enter")
            assert not screen.search_active
            search_input = screen.query_one("#search-input", Input)
            assert not search_input.has_class("active")
            assert screen.active_query == "docker"

    async def test_filtered_results_remain_after_confirm(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("d", "o", "c", "k", "e", "r")
            await pilot.press("enter")
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 2

    async def test_navigation_works_after_confirm(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("d", "o", "c", "k", "e", "r")
            await pilot.press("enter")
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.flat_index == 0
            await pilot.press("j")
            assert entry_table.flat_index == 1
            await pilot.press("k")
            assert entry_table.flat_index == 0


class TestTuiSearchEscape:
    async def test_esc_exits_search_editing(self, tui_service: CheatService):
        from textual.widgets import Input

        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("d", "o", "c", "k")
            screen = app.screen
            assert isinstance(screen, BrowserScreen)
            assert screen.search_active
            await pilot.press("escape")
            assert not screen.search_active
            search_input = screen.query_one("#search-input", Input)
            assert not search_input.has_class("active")
            assert search_input.value == ""

    async def test_esc_clears_applied_filter(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            # Apply a filter first
            await pilot.press("slash")
            await pilot.press("d", "o", "c", "k", "e", "r")
            await pilot.press("enter")
            screen = app.screen
            assert isinstance(screen, BrowserScreen)
            assert screen.active_query == "docker"
            # Now Esc should clear the filter
            await pilot.press("escape")
            assert screen.active_query == ""

    async def test_full_list_restored_after_clear(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("d", "o", "c", "k", "e", "r")
            await pilot.press("enter")
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 2
            await pilot.press("escape")
            assert entry_table.entry_count == 8

    async def test_esc_cancel_preserves_previous_query(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            # Apply docker filter
            await pilot.press("slash")
            await pilot.press("d", "o", "c", "k", "e", "r")
            await pilot.press("enter")
            screen = app.screen
            assert screen.active_query == "docker"
            # Enter search again, type something else, then Esc
            await pilot.press("slash")
            await pilot.press("g", "i", "t")
            await pilot.press("escape")
            # Should restore the docker filter
            assert screen.active_query == "docker"

    async def test_esc_cancel_preserves_entry_count(self, tui_service: CheatService):
        """Regression: stale Input.Changed must not overwrite filter after Esc."""
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            # Apply docker filter and confirm
            await pilot.press("slash")
            await pilot.press("d", "o", "c", "k", "e", "r")
            await pilot.press("enter")
            screen = app.screen
            entry_table = app.screen.query_one(EntryTable)
            assert screen.active_query == "docker"
            assert entry_table.entry_count == 2
            # Enter search again, type something, then Esc
            await pilot.press("slash")
            await pilot.press("g", "i", "t")
            await pilot.press("escape")
            # active_query must still be docker
            assert screen.active_query == "docker"
            # Displayed entries must still be the docker-filtered set (not all)
            assert entry_table.entry_count == 2


class TestTuiSearchNavigation:
    async def test_j_k_on_filtered_results(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("d", "o", "c", "k", "e", "r")
            await pilot.press("enter")
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 2
            await pilot.press("j")
            assert entry_table.flat_index == 1
            await pilot.press("k")
            assert entry_table.flat_index == 0

    async def test_arrows_on_filtered_results(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("d", "o", "c", "k", "e", "r")
            await pilot.press("enter")
            entry_table = app.screen.query_one(EntryTable)
            await pilot.press("down")
            assert entry_table.flat_index == 1
            await pilot.press("up")
            assert entry_table.flat_index == 0

    async def test_g_G_on_filtered_results(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("d", "o", "c", "k", "e", "r")
            await pilot.press("enter")
            entry_table = app.screen.query_one(EntryTable)
            await pilot.press("G")
            assert entry_table.flat_index == 1
            await pilot.press("g")
            assert entry_table.flat_index == 0

    async def test_ctrl_d_u_on_filtered_results(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("d", "o", "c", "k", "e", "r")
            await pilot.press("enter")
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.flat_index == 0
            await pilot.press("ctrl+d")
            assert entry_table.flat_index == 1
            await pilot.press("ctrl+u")
            assert entry_table.flat_index == 0


class TestTuiSearchDetails:
    async def test_enter_opens_selected_filtered_entry(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp, DetailScreen
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("d", "o", "c", "k", "e", "r")
            await pilot.press("enter")
            await pilot.press("j")
            await pilot.press("enter")
            detail = app.screen
            assert isinstance(detail, DetailScreen)
            assert detail.entry.command == "docker images"

    async def test_detail_shows_correct_filtered_entry(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp, DetailScreen
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("p", "y", "t", "h", "o", "n")
            await pilot.press("enter")
            await pilot.press("j")
            await pilot.press("enter")
            detail = app.screen
            assert isinstance(detail, DetailScreen)
            assert detail.entry.tool == "python"
            assert "ruff" in detail.entry.command

    async def test_esc_returns_to_browser_from_filtered(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, DetailScreen
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("d", "o", "c", "k", "e", "r")
            await pilot.press("enter")
            await pilot.press("enter")
            assert isinstance(app.screen, DetailScreen)
            await pilot.press("escape")
            assert isinstance(app.screen, BrowserScreen)


class TestTuiSearchEmpty:
    async def test_no_match_query_stable(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("z", "z", "z")
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 0
            assert entry_table.flat_index == 0

    async def test_navigation_safe_on_empty(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("z", "z", "z")
            await pilot.press("enter")
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.flat_index == 0
            await pilot.press("j")
            assert entry_table.flat_index == 0
            await pilot.press("k")
            assert entry_table.flat_index == 0
            await pilot.press("G")
            assert entry_table.flat_index == 0
            await pilot.press("g")
            assert entry_table.flat_index == 0

    async def test_enter_no_op_on_empty(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("z", "z", "z")
            await pilot.press("enter")
            assert isinstance(app.screen, BrowserScreen)

    async def test_clearing_query_restores_results(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("z", "z", "z")
            await pilot.press("enter")
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 0
            await pilot.press("escape")
            assert entry_table.entry_count == 8

    async def test_empty_data_search(self, empty_tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=empty_tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("a", "n", "y", "t", "h", "i", "n", "g")
            await pilot.press("enter")
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 0
            await pilot.press("escape")
            assert entry_table.entry_count == 0


class TestTuiSearchInitialQuery:
    async def test_initial_query_displays_filtered(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service, query="docker")
        async with app.run_test():
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 2

    async def test_initial_query_allows_continued_editing(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service, query="docker")
        async with app.run_test() as pilot:
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 2
            await pilot.press("slash")
            await pilot.press("g", "i", "t")
            assert entry_table.entry_count == 3

    async def test_initial_query_can_be_cleared(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service, query="docker")
        async with app.run_test() as pilot:
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 2
            await pilot.press("escape")
            assert entry_table.entry_count == 8


class TestTuiSearchSelectionCorrectness:
    async def test_filter_clamps_selection(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            entry_table = app.screen.query_one(EntryTable)
            # Move to position 7 (last)
            await pilot.press("G")
            assert entry_table.flat_index == 7
            # Filter to docker (2 entries) — selection clamps to last valid index
            await pilot.press("slash")
            await pilot.press("d", "o", "c", "k", "e", "r")
            await pilot.press("enter")
            assert entry_table.entry_count == 2
            assert entry_table.flat_index == 1

    async def test_widening_filter_restores_selection(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            # Start with docker filter
            await pilot.press("slash")
            await pilot.press("d", "o", "c", "k", "e", "r")
            await pilot.press("enter")
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 2
            await pilot.press("j")
            assert entry_table.flat_index == 1
            # Clear filter — selection preserved at index 1
            await pilot.press("escape")
            assert entry_table.entry_count == 8
            assert entry_table.flat_index == 1

    async def test_selection_at_zero_on_empty_filter(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            entry_table = app.screen.query_one(EntryTable)
            await pilot.press("G")
            assert entry_table.flat_index == 7
            await pilot.press("slash")
            await pilot.press("z", "z", "z")
            await pilot.press("enter")
            assert entry_table.flat_index == 0


class TestTuiHelp:
    async def test_question_mark_opens_help(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp, HelpScreen
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("question_mark")
            assert isinstance(app.screen, HelpScreen)

    async def test_help_displays_key_descriptions(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp, HelpScreen
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("question_mark")
            help_screen = app.screen
            assert isinstance(help_screen, HelpScreen)
            help_text = help_screen.query_one("#help-container").render()
            text = str(help_text)
            assert "Move down" in text
            assert "Move up" in text
            assert "Search" in text
            assert "Open details" in text
            assert "Quit" in text
            assert "Show this help" in text

    async def test_esc_closes_help(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, HelpScreen
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("question_mark")
            assert isinstance(app.screen, HelpScreen)
            await pilot.press("escape")
            assert isinstance(app.screen, BrowserScreen)

    async def test_browser_state_intact_after_help(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            entry_table = app.screen.query_one(EntryTable)
            await pilot.press("j")
            await pilot.press("j")
            assert entry_table.flat_index == 2
            await pilot.press("question_mark")
            await pilot.press("escape")
            assert entry_table.flat_index == 2
            assert entry_table.entry_count == 8


class TestTuiStatusFeedback:
    async def test_entry_count_displays(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        app = CheatApp(service=tui_service)
        async with app.run_test():
            status = app.screen.query_one("#status-bar").render()
            text = str(status)
            assert "8" in text

    async def test_filter_shows_match_count(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("d", "o", "c", "k", "e", "r")
            await pilot.press("enter")
            status = app.screen.query_one("#status-bar").render()
            text = str(status)
            assert "2" in text

    async def test_no_results_message_shown(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("z", "z", "z")
            no_results = app.screen.query_one("#no-results")
            assert no_results.has_class("visible")

    async def test_no_results_hidden_when_matches_exist(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            await pilot.press("d", "o", "c", "k", "e", "r")
            no_results = app.screen.query_one("#no-results")
            assert not no_results.has_class("visible")

    async def test_help_hint_in_status(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        app = CheatApp(service=tui_service)
        async with app.run_test():
            status = app.screen.query_one("#status-bar").render()
            text = str(status)
            assert "Help" in text


class TestTuiTags:
    async def test_tags_appear_in_table(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test():
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 8
            table = entry_table.query_one("#entry-table")
            assert table.row_count == 8

    async def test_tags_column_exists(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        async with app.run_test():
            entry_table = app.screen.query_one(EntryTable)
            table = entry_table.query_one("#entry-table")
            assert table.columns is not None
            assert len(list(table.columns)) == 4


class TestTuiCopyCommand:
    async def test_y_copies_selected_command(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp
        app = CheatApp(service=tui_service)
        copied: list[str] = []
        async with app.run_test() as pilot:
            screen = app.screen
            assert isinstance(screen, BrowserScreen)
            screen._clipboard_fn = lambda text: copied.append(text)
            await pilot.press("y")
            assert copied == ["git status"]

    async def test_y_copies_different_selected_command(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp
        app = CheatApp(service=tui_service)
        copied: list[str] = []
        async with app.run_test() as pilot:
            screen = app.screen
            assert isinstance(screen, BrowserScreen)
            screen._clipboard_fn = lambda text: copied.append(text)
            await pilot.press("j")
            await pilot.press("j")
            await pilot.press("y")
            assert copied == ["git diff"]

    async def test_y_after_filtering(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp
        app = CheatApp(service=tui_service)
        copied: list[str] = []
        async with app.run_test() as pilot:
            screen = app.screen
            assert isinstance(screen, BrowserScreen)
            screen._clipboard_fn = lambda text: copied.append(text)
            await pilot.press("slash")
            await pilot.press("d", "o", "c", "k", "e", "r")
            await pilot.press("enter")
            await pilot.press("y")
            assert copied == ["docker ps"]

    async def test_y_with_zero_results(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp
        from cheat_cli.ui.tui.browser import EntryTable
        app = CheatApp(service=tui_service)
        copied: list[str] = []
        async with app.run_test() as pilot:
            screen = app.screen
            assert isinstance(screen, BrowserScreen)
            screen._clipboard_fn = lambda text: copied.append(text)
            await pilot.press("slash")
            await pilot.press("z", "z", "z")
            entry_table = app.screen.query_one(EntryTable)
            assert entry_table.entry_count == 0
            await pilot.press("y")
            assert copied == []

    async def test_y_with_no_entries(self, empty_tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp
        app = CheatApp(service=empty_tui_service)
        copied: list[str] = []
        async with app.run_test() as pilot:
            screen = app.screen
            assert isinstance(screen, BrowserScreen)
            screen._clipboard_fn = lambda text: copied.append(text)
            await pilot.press("y")
            assert copied == []

    async def test_y_shows_success_feedback(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            screen = app.screen
            assert isinstance(screen, BrowserScreen)
            screen._clipboard_fn = lambda text: None
            await pilot.press("y")
            assert screen._clipboard_feedback == "Copied: git status"

    async def test_y_shows_failure_feedback(self, tui_service: CheatService):
        from cheat_cli.ui.clipboard import ClipboardError
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp
        app = CheatApp(service=tui_service)

        def failing_clipboard(text: str) -> None:
            raise ClipboardError("no clipboard")

        async with app.run_test() as pilot:
            screen = app.screen
            assert isinstance(screen, BrowserScreen)
            screen._clipboard_fn = failing_clipboard
            await pilot.press("y")
            assert screen._clipboard_feedback == "Could not copy command"

    async def test_feedback_clears_after_timer(self, tui_service: CheatService):
        import asyncio

        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            screen = app.screen
            assert isinstance(screen, BrowserScreen)
            screen._clipboard_fn = lambda text: None
            await pilot.press("y")
            assert screen._clipboard_feedback == "Copied: git status"
            await asyncio.sleep(2.0)
            assert screen._clipboard_feedback is None


class TestTuiRunCommand:
    async def test_r_opens_result_for_safe_command(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, ResultScreen
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            screen = app.screen
            assert isinstance(screen, BrowserScreen)
            await pilot.press("r")
            await pilot.pause()
            assert isinstance(app.screen, ResultScreen)
            assert app.screen.result.command == "git status"
            assert app.screen.result.success is True

    async def test_r_shows_result_output(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp, ResultScreen
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("r")
            await pilot.pause()
            assert isinstance(app.screen, ResultScreen)
            assert app.screen.result.stdout is not None

    async def test_r_esc_returns_to_browser(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, ResultScreen
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("r")
            await pilot.pause()
            assert isinstance(app.screen, ResultScreen)
            await pilot.press("escape")
            await pilot.pause()
            assert isinstance(app.screen, BrowserScreen)

    async def test_r_q_returns_to_browser(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, ResultScreen
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("r")
            await pilot.pause()
            assert isinstance(app.screen, ResultScreen)
            await pilot.press("q")
            await pilot.pause()
            assert isinstance(app.screen, BrowserScreen)

    async def test_r_no_entries_noop(self, empty_tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp
        app = CheatApp(service=empty_tui_service)
        async with app.run_test() as pilot:
            screen = app.screen
            assert isinstance(screen, BrowserScreen)
            await pilot.press("r")
            await pilot.pause()
            assert isinstance(app.screen, BrowserScreen)

    async def test_r_risky_shows_confirm(self, tmp_path):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, ConfirmScreen

        service = _create_risky_csv(
            tmp_path, "risky.csv",
            [("system", "sudo rm -rf /tmp/test", "Remove temp files", "dangerous")],
        )
        app = CheatApp(service=service)
        async with app.run_test() as pilot:
            screen = app.screen
            assert isinstance(screen, BrowserScreen)
            await pilot.press("r")
            await pilot.pause()
            assert isinstance(app.screen, ConfirmScreen)
            assert "sudo rm -rf /tmp/test" in app.screen.command

    async def test_r_risky_confirm_y_shows_result(self, tmp_path):
        from cheat_cli.ui.tui.app import CheatApp, ConfirmScreen, ResultScreen

        service = _create_risky_csv(
            tmp_path, "risky.csv",
            [("system", "pip uninstall nonexistent_pkg_xyz", "Uninstall nonexistent package", "test")],
        )
        app = CheatApp(service=service)
        async with app.run_test() as pilot:
            await pilot.press("r")
            await pilot.pause()
            assert isinstance(app.screen, ConfirmScreen)
            assert "pip uninstall nonexistent_pkg_xyz" in app.screen.command
            await pilot.press("y")
            await pilot.pause()
            assert isinstance(app.screen, ResultScreen)

    async def test_r_risky_n_cancels(self, tmp_path):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, ConfirmScreen

        service = _create_risky_csv(
            tmp_path, "risky.csv",
            [("system", "sudo rm -rf /tmp/test", "Remove temp files", "dangerous")],
        )
        app = CheatApp(service=service)
        async with app.run_test() as pilot:
            await pilot.press("r")
            await pilot.pause()
            assert isinstance(app.screen, ConfirmScreen)
            await pilot.press("n")
            await pilot.pause()
            assert isinstance(app.screen, BrowserScreen)

    async def test_r_risky_esc_cancels(self, tmp_path):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, ConfirmScreen

        service = _create_risky_csv(
            tmp_path, "risky.csv",
            [("system", "sudo rm -rf /tmp/test", "Remove temp files", "dangerous")],
        )
        app = CheatApp(service=service)
        async with app.run_test() as pilot:
            await pilot.press("r")
            await pilot.pause()
            assert isinstance(app.screen, ConfirmScreen)
            await pilot.press("escape")
            await pilot.pause()
            assert isinstance(app.screen, BrowserScreen)

    async def test_r_selection_preserved_after_cancel(self, tmp_path):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, ConfirmScreen
        from cheat_cli.ui.tui.browser import EntryTable

        commands = [("tool", f"cmd{i}", f"Command {i}", "test") for i in range(5)]
        commands.append(("system", "sudo rm -rf /tmp/test", "Remove temp files", "dangerous"))
        service = _create_risky_csv(tmp_path, "risky.csv", commands)
        app = CheatApp(service=service)
        async with app.run_test() as pilot:
            screen = app.screen
            assert isinstance(screen, BrowserScreen)
            table = screen.query_one(EntryTable)
            table.select(5)
            await pilot.press("r")
            await pilot.pause()
            assert isinstance(app.screen, ConfirmScreen)
            await pilot.press("n")
            await pilot.pause()
            assert isinstance(app.screen, BrowserScreen)
            assert table.flat_index == 5

    async def test_r_risky_confirm_shows_command(self, tmp_path):
        from cheat_cli.ui.tui.app import CheatApp, ConfirmScreen

        service = _create_risky_csv(
            tmp_path, "risky.csv",
            [("system", "shutdown -h now", "Shutdown system", "system")],
        )
        app = CheatApp(service=service)
        async with app.run_test() as pilot:
            await pilot.press("r")
            await pilot.pause()
            assert isinstance(app.screen, ConfirmScreen)
            assert "shutdown -h now" in app.screen.command
            assert len(app.screen.risk_matches) >= 1

    async def test_r_risky_confirm_shows_risk_descriptions(self, tmp_path):
        from cheat_cli.ui.tui.app import CheatApp, ConfirmScreen

        service = _create_risky_csv(
            tmp_path, "risky.csv",
            [("system", "sudo rm -rf /tmp", "Remove temp", "dangerous")],
        )
        app = CheatApp(service=service)
        async with app.run_test() as pilot:
            await pilot.press("r")
            await pilot.pause()
            assert isinstance(app.screen, ConfirmScreen)
            descriptions = [m.description for m in app.screen.risk_matches]
            assert any("sudo" in d.lower() or "privilege" in d.lower() for d in descriptions)

    async def test_r_with_zero_search_results(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            screen = app.screen
            assert isinstance(screen, BrowserScreen)
            await pilot.press("slash")
            await pilot.press("z", "z", "z", "z", "z")
            await pilot.press("enter")
            await pilot.pause()
            assert len(screen.entries) == 0
            await pilot.press("r")
            await pilot.pause()
            assert isinstance(app.screen, BrowserScreen)

    async def test_r_mocked_execution(self, tui_service: CheatService):
        from cheat_cli.runner import RunResult
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, ResultScreen

        app = CheatApp(service=tui_service)

        async with app.run_test() as pilot:
            screen = app.screen
            assert isinstance(screen, BrowserScreen)

            mock_result = RunResult(
                command="git status",
                stdout="On branch main\nnothing to commit",
                stderr="",
                return_code=0,
            )
            executed_commands: list[str] = []

            def mock_execute(command: str) -> None:
                executed_commands.append(command)
                screen.app.push_screen(ResultScreen(mock_result))

            screen._execute_command = mock_execute
            await pilot.press("r")
            await pilot.pause()
            assert executed_commands == ["git status"]
            assert isinstance(app.screen, ResultScreen)
            assert app.screen.result.stdout == "On branch main\nnothing to commit"

    async def test_r_mocked_risky_execution(self, tmp_path):
        from unittest.mock import patch

        from cheat_cli.runner import RunResult
        from cheat_cli.ui.tui.app import (
            BrowserScreen,
            CheatApp,
            ConfirmScreen,
            ResultScreen,
        )

        service = _create_risky_csv(
            tmp_path, "risky.csv",
            [("system", "sudo rm -rf /tmp/test", "Remove temp", "dangerous")],
        )
        app = CheatApp(service=service)

        mock_result = RunResult(
            command="sudo rm -rf /tmp/test",
            stdout="",
            stderr="",
            return_code=0,
        )

        async with app.run_test() as pilot:
            screen = app.screen
            assert isinstance(screen, BrowserScreen)

            with patch(
                "cheat_cli.ui.tui.app.run_command", return_value=mock_result
            ) as mock_run:
                await pilot.press("r")
                await pilot.pause()
                assert isinstance(app.screen, ConfirmScreen)
                await pilot.press("y")
                await pilot.pause()
                mock_run.assert_called_once_with("sudo rm -rf /tmp/test")
                assert isinstance(app.screen, ResultScreen)

    async def test_r_result_shows_exit_code_zero(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp, ResultScreen
        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("r")
            await pilot.pause()
            assert isinstance(app.screen, ResultScreen)
            assert app.screen.result.return_code == 0

    async def test_r_result_shows_exit_code_nonzero(self, tui_service: CheatService):
        from cheat_cli.runner import RunResult
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, ResultScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            screen = app.screen
            assert isinstance(screen, BrowserScreen)

            mock_result = RunResult(
                command="false",
                stdout="",
                stderr="",
                return_code=1,
            )

            def mock_execute(command: str) -> None:
                app.push_screen(ResultScreen(mock_result))

            screen._execute_command = mock_execute
            await pilot.press("r")
            await pilot.pause()
            assert isinstance(app.screen, ResultScreen)
            assert app.screen.result.return_code == 1

    async def test_r_result_shows_timeout(self, tui_service: CheatService):
        from cheat_cli.runner import RunResult
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, ResultScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            screen = app.screen
            assert isinstance(screen, BrowserScreen)

            mock_result = RunResult(
                command="sleep 10",
                timed_out=True,
                error="Command timed out after 30s",
            )

            def mock_execute(command: str) -> None:
                app.push_screen(ResultScreen(mock_result))

            screen._execute_command = mock_execute
            await pilot.press("r")
            await pilot.pause()
            assert isinstance(app.screen, ResultScreen)
            assert app.screen.result.timed_out is True
            assert "Timed out" in app.screen.result.status_label

    async def test_r_result_shows_error(self, tui_service: CheatService):
        from cheat_cli.runner import RunResult
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, ResultScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            screen = app.screen
            assert isinstance(screen, BrowserScreen)

            mock_result = RunResult(
                command="bad_cmd",
                error="Command not found: [Errno 2] No such file",
            )

            def mock_execute(command: str) -> None:
                app.push_screen(ResultScreen(mock_result))

            screen._execute_command = mock_execute
            await pilot.press("r")
            await pilot.pause()
            assert isinstance(app.screen, ResultScreen)
            assert "Error" in app.screen.result.status_label

    async def test_r_result_shows_stderr(self, tui_service: CheatService):
        from cheat_cli.runner import RunResult
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, ResultScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            screen = app.screen
            assert isinstance(screen, BrowserScreen)

            mock_result = RunResult(
                command="echo err >&2",
                stdout="",
                stderr="some error output",
                return_code=0,
            )

            def mock_execute(command: str) -> None:
                app.push_screen(ResultScreen(mock_result))

            screen._execute_command = mock_execute
            await pilot.press("r")
            await pilot.pause()
            assert isinstance(app.screen, ResultScreen)
            assert "some error output" in str(app.screen.result.stderr)

    async def test_r_no_auto_execution(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            screen = app.screen
            assert isinstance(screen, BrowserScreen)
            await pilot.pause()
            assert isinstance(app.screen, BrowserScreen)


class TestTuiAdd:
    async def test_a_opens_editor(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, EditorScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            await pilot.press("a")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)

    async def test_editor_title_add(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp, EditorScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("a")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)
            assert app.screen.editor_title == "Add Command"

    async def test_editor_starts_empty(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp, EditorScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("a")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)
            tool_input = app.screen.query_one("#tool-input")
            command_input = app.screen.query_one("#command-input")
            assert tool_input.value == ""
            assert command_input.value == ""

    async def test_add_valid_entry(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, EditorScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            initial_count = len(app.service.list_entries())
            await pilot.press("a")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)

            # Fill fields
            tool_input = app.screen.query_one("#tool-input")
            command_input = app.screen.query_one("#command-input")
            desc_input = app.screen.query_one("#description-input")
            tags_input = app.screen.query_one("#tags-input")
            tool_input.value = "kubectl"
            command_input.value = "kubectl get svc"
            desc_input.value = "List services"
            tags_input.value = "k8s networking"

            # Save
            await pilot.press("ctrl+s")
            await pilot.pause()
            assert isinstance(app.screen, BrowserScreen)

            # Verify entry was added
            entries = app.service.list_entries()
            assert len(entries) == initial_count + 1
            assert entries[-1].command == "kubectl get svc"
            assert entries[-1].tool == "kubectl"

    async def test_add_empty_tool_rejected(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp, EditorScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("a")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)

            command_input = app.screen.query_one("#command-input")
            command_input.value = "some command"

            await pilot.press("ctrl+s")
            await pilot.pause()
            # Should still be on editor with error
            assert isinstance(app.screen, EditorScreen)

    async def test_add_empty_command_rejected(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp, EditorScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("a")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)

            tool_input = app.screen.query_one("#tool-input")
            tool_input.value = "some tool"

            await pilot.press("ctrl+s")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)

    async def test_add_cancel_no_entry(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, EditorScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            initial_count = len(app.service.list_entries())
            await pilot.press("a")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)

            await pilot.press("escape")
            await pilot.pause()
            assert isinstance(app.screen, BrowserScreen)
            assert len(app.service.list_entries()) == initial_count

    async def test_new_entry_appears_in_browser(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, EditorScreen
        from cheat_cli.ui.tui.browser import EntryTable

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            await pilot.press("a")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)

            tool_input = app.screen.query_one("#tool-input")
            command_input = app.screen.query_one("#command-input")
            tool_input.value = "tmux"
            command_input.value = "tmux new -s work"

            await pilot.press("ctrl+s")
            await pilot.pause()
            assert isinstance(app.screen, BrowserScreen)

            table = app.screen.query_one(EntryTable)
            assert table.entry_count == len(app.service.list_entries())

    async def test_add_persists_after_reload(self, tmp_path):
        import csv

        from cheat_cli.cheat_service import CheatService
        from cheat_cli.core.models import CSV_FIELDS
        from cheat_cli.ui.tui.app import CheatApp, EditorScreen

        csv_path = tmp_path / "cmds.csv"
        with open(csv_path, "w", newline="") as f:  # noqa: ASYNC230
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerow({"tool": "git", "command": "git status", "description": "Show status", "tags": "repo"})

        service = CheatService(csv_path=csv_path)
        app = CheatApp(service=service)
        async with app.run_test() as pilot:
            await pilot.press("a")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)

            tool_input = app.screen.query_one("#tool-input")
            command_input = app.screen.query_one("#command-input")
            tool_input.value = "python"
            command_input.value = "python -m pytest"

            await pilot.press("ctrl+s")
            await pilot.pause()

        # Reload and verify
        service2 = CheatService(csv_path=csv_path)
        entries = service2.list_entries()
        assert len(entries) == 2
        assert entries[1].command == "python -m pytest"


class TestTuiEdit:
    async def test_e_opens_editor(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, EditorScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            await pilot.press("e")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)

    async def test_editor_title_edit(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, EditorScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            await pilot.press("e")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)
            assert app.screen.editor_title == "Edit Command"

    async def test_editor_prepopulated(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, EditorScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            await pilot.press("e")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)

            tool_input = app.screen.query_one("#tool-input")
            command_input = app.screen.query_one("#command-input")
            tags_input = app.screen.query_one("#tags-input")
            assert tool_input.value == "git"
            assert command_input.value == "git status"
            assert tags_input.value == "repo state"

    async def test_edit_valid_change(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, EditorScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            await pilot.press("e")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)

            desc_input = app.screen.query_one("#description-input")
            desc_input.value = "Updated description"

            await pilot.press("ctrl+s")
            await pilot.pause()
            assert isinstance(app.screen, BrowserScreen)

            entries = app.service.list_entries()
            assert entries[0].description == "Updated description"
            assert entries[0].command == "git status"

    async def test_edit_empty_tool_rejected(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, EditorScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            await pilot.press("e")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)

            tool_input = app.screen.query_one("#tool-input")
            tool_input.value = ""

            await pilot.press("ctrl+s")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)

    async def test_edit_empty_command_rejected(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, EditorScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            await pilot.press("e")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)

            command_input = app.screen.query_one("#command-input")
            command_input.value = ""

            await pilot.press("ctrl+s")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)

    async def test_edit_cancel_no_change(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, EditorScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            original = app.service.list_entries()[0]

            await pilot.press("e")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)

            desc_input = app.screen.query_one("#description-input")
            desc_input.value = "Should not persist"

            await pilot.press("escape")
            await pilot.pause()
            assert isinstance(app.screen, BrowserScreen)

            entries = app.service.list_entries()
            assert entries[0].description == original.description

    async def test_edit_old_value_replaced(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, EditorScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            await pilot.press("e")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)

            command_input = app.screen.query_one("#command-input")
            command_input.value = "git status --porcelain"

            await pilot.press("ctrl+s")
            await pilot.pause()

            entries = app.service.list_entries()
            assert entries[0].command == "git status --porcelain"
            assert all(e.command != "git status" for e in entries)

    async def test_edit_unrelated_entries_unchanged(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, EditorScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            entries_before = app.service.list_entries()
            second_cmd = entries_before[1].command

            await pilot.press("e")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)

            desc_input = app.screen.query_one("#description-input")
            desc_input.value = "Changed"

            await pilot.press("ctrl+s")
            await pilot.pause()

            entries_after = app.service.list_entries()
            assert entries_after[1].command == second_cmd

    async def test_edit_persists_after_reload(self, tmp_path):
        import csv

        from cheat_cli.cheat_service import CheatService
        from cheat_cli.core.models import CSV_FIELDS
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, EditorScreen

        csv_path = tmp_path / "cmds.csv"
        with open(csv_path, "w", newline="") as f:  # noqa: ASYNC230
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerow({"tool": "git", "command": "git status", "description": "Show status", "tags": "repo"})

        service = CheatService(csv_path=csv_path)
        app = CheatApp(service=service)
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            await pilot.press("e")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)

            desc_input = app.screen.query_one("#description-input")
            desc_input.value = "Persisted edit"

            await pilot.press("ctrl+s")
            await pilot.pause()

        service2 = CheatService(csv_path=csv_path)
        entries = service2.list_entries()
        assert entries[0].description == "Persisted edit"


class TestTuiDelete:
    async def test_d_opens_confirm(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, DeleteConfirmScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            await pilot.press("d")
            await pilot.pause()
            assert isinstance(app.screen, DeleteConfirmScreen)

    async def test_confirm_shows_command(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, DeleteConfirmScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            await pilot.press("d")
            await pilot.pause()
            assert isinstance(app.screen, DeleteConfirmScreen)
            assert app.screen.entry.command == "git status"

    async def test_confirm_n_cancels(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, DeleteConfirmScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            initial_count = len(app.service.list_entries())
            await pilot.press("d")
            await pilot.pause()
            assert isinstance(app.screen, DeleteConfirmScreen)

            await pilot.press("n")
            await pilot.pause()
            assert isinstance(app.screen, BrowserScreen)
            assert len(app.service.list_entries()) == initial_count

    async def test_confirm_esc_cancels(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, DeleteConfirmScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            initial_count = len(app.service.list_entries())
            await pilot.press("d")
            await pilot.pause()
            assert isinstance(app.screen, DeleteConfirmScreen)

            await pilot.press("escape")
            await pilot.pause()
            assert isinstance(app.screen, BrowserScreen)
            assert len(app.service.list_entries()) == initial_count

    async def test_confirm_y_deletes(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, DeleteConfirmScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            initial_count = len(app.service.list_entries())
            await pilot.press("d")
            await pilot.pause()
            assert isinstance(app.screen, DeleteConfirmScreen)

            await pilot.press("y")
            await pilot.pause()
            assert isinstance(app.screen, BrowserScreen)
            assert len(app.service.list_entries()) == initial_count - 1

    async def test_deletes_correct_entry(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, DeleteConfirmScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            entries_before = app.service.list_entries()
            deleted_cmd = entries_before[0].command

            await pilot.press("d")
            await pilot.pause()
            assert isinstance(app.screen, DeleteConfirmScreen)

            await pilot.press("y")
            await pilot.pause()

            entries_after = app.service.list_entries()
            assert all(e.command != deleted_cmd for e in entries_after)

    async def test_delete_last_entry(self, tmp_path):
        import csv

        from cheat_cli.cheat_service import CheatService
        from cheat_cli.core.models import CSV_FIELDS
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, DeleteConfirmScreen

        csv_path = tmp_path / "single.csv"
        with open(csv_path, "w", newline="") as f:  # noqa: ASYNC230
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerow({"tool": "git", "command": "git status", "description": "Show status", "tags": "repo"})

        service = CheatService(csv_path=csv_path)
        app = CheatApp(service=service)
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            await pilot.press("d")
            await pilot.pause()
            assert isinstance(app.screen, DeleteConfirmScreen)

            await pilot.press("y")
            await pilot.pause()
            assert isinstance(app.screen, BrowserScreen)
            assert len(app.service.list_entries()) == 0

    async def test_unrelated_entries_remain(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import CheatApp

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            entries_before = app.service.list_entries()
            other_cmds = {e.command for e in entries_before[1:]}

            await pilot.press("d")
            await pilot.press("y")
            await pilot.pause()

            entries_after = app.service.list_entries()
            assert {e.command for e in entries_after} == other_cmds

    async def test_delete_persists_after_reload(self, tmp_path):
        import csv

        from cheat_cli.cheat_service import CheatService
        from cheat_cli.core.models import CSV_FIELDS
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp

        csv_path = tmp_path / "cmds.csv"
        with open(csv_path, "w", newline="") as f:  # noqa: ASYNC230
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerow({"tool": "git", "command": "git status", "description": "Show status", "tags": "repo"})
            writer.writerow({"tool": "docker", "command": "docker ps", "description": "List", "tags": "containers"})

        service = CheatService(csv_path=csv_path)
        app = CheatApp(service=service)
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            await pilot.press("d")
            await pilot.press("y")
            await pilot.pause()

        service2 = CheatService(csv_path=csv_path)
        entries = service2.list_entries()
        assert len(entries) == 1
        assert entries[0].command == "docker ps"


class TestTuiEditDeleteState:
    async def test_edit_while_filtered(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, EditorScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            # Filter to docker entries
            await pilot.press("slash")
            await pilot.pause()
            await pilot.press("d", "o", "c", "k", "e", "r")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            assert len(app.screen.entries) == 2

            # Edit the selected docker entry
            await pilot.press("e")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)

            desc_input = app.screen.query_one("#description-input")
            desc_input.value = "Edited filtered"
            await pilot.press("ctrl+s")
            await pilot.pause()

            assert isinstance(app.screen, BrowserScreen)
            # Filter should be preserved
            assert len(app.screen.entries) == 2

    async def test_delete_while_filtered(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, DeleteConfirmScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            await pilot.press("slash")
            await pilot.pause()
            await pilot.press("g", "i", "t")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            assert len(app.screen.entries) == 3  # git status, git log, git diff

            await pilot.press("d")
            await pilot.pause()
            assert isinstance(app.screen, DeleteConfirmScreen)

            await pilot.press("y")
            await pilot.pause()
            assert isinstance(app.screen, BrowserScreen)
            # Filter should be preserved, but one git entry removed
            assert len(app.screen.entries) == 2

    async def test_selection_after_delete(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            # Move to second entry
            await pilot.press("j")
            await pilot.pause()

            await pilot.press("d")
            await pilot.press("y")
            await pilot.pause()

            assert isinstance(app.screen, BrowserScreen)
            # Should still be able to navigate
            await pilot.press("j")
            await pilot.pause()

    async def test_selection_after_edit(self, tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, EditorScreen

        app = CheatApp(service=tui_service)
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            await pilot.press("j")
            await pilot.pause()

            await pilot.press("e")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)

            desc_input = app.screen.query_one("#description-input")
            desc_input.value = "Edited"
            await pilot.press("ctrl+s")
            await pilot.pause()

            assert isinstance(app.screen, BrowserScreen)
            # Should still be navigable
            await pilot.press("j")
            await pilot.pause()

    async def test_empty_state_add(self, empty_tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp, EditorScreen

        app = CheatApp(service=empty_tui_service)
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            await pilot.press("a")
            await pilot.pause()
            assert isinstance(app.screen, EditorScreen)

            tool_input = app.screen.query_one("#tool-input")
            command_input = app.screen.query_one("#command-input")
            tool_input.value = "git"
            command_input.value = "git init"

            await pilot.press("ctrl+s")
            await pilot.pause()
            assert isinstance(app.screen, BrowserScreen)
            assert len(app.service.list_entries()) == 1

    async def test_empty_state_no_edit_or_delete(self, empty_tui_service: CheatService):
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp

        app = CheatApp(service=empty_tui_service)
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            # e and d should be no-ops when no entry is selected
            await pilot.press("e")
            await pilot.pause()
            assert isinstance(app.screen, BrowserScreen)
            await pilot.press("d")
            await pilot.pause()
            assert isinstance(app.screen, BrowserScreen)
