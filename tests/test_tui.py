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
