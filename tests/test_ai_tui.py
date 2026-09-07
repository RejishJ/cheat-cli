"""Tests for cheat_cli.ui.tui.ai — AI TUI screens."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestAIRequestScreen:
    """Tests for AIRequestScreen."""

    async def test_screen_opens(self) -> None:
        from cheat_cli.ui.tui.ai import AIRequestScreen
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp

        app = CheatApp(service=MagicMock())
        async with app.run_test() as pilot:
            assert isinstance(app.screen, BrowserScreen)
            # Press 'i' to open AI screen
            await pilot.press("i")
            await pilot.pause()
            assert isinstance(app.screen, AIRequestScreen)

    async def test_submit_with_empty_request(self) -> None:
        from cheat_cli.ui.tui.ai import AIRequestScreen
        from cheat_cli.ui.tui.app import CheatApp

        app = CheatApp(service=MagicMock())
        async with app.run_test() as pilot:
            await pilot.press("i")
            await pilot.pause()
            assert isinstance(app.screen, AIRequestScreen)

            # Try to submit empty
            await pilot.press("enter")
            await pilot.pause()
            # Should still be on request screen
            assert isinstance(app.screen, AIRequestScreen)

    async def test_submit_with_request(self) -> None:
        from cheat_cli.ui.tui.ai import AIRequestScreen
        from cheat_cli.ui.tui.app import CheatApp

        with patch("cheat_cli.ui.tui.ai.get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.name = "mock"
            mock_provider.suggest_commands.return_value = []
            mock_get.return_value = mock_provider

            app = CheatApp(service=MagicMock())
            async with app.run_test() as pilot:
                await pilot.press("i")
                await pilot.pause()
                assert isinstance(app.screen, AIRequestScreen)

                # Type a request
                input_widget = app.screen.query_one("#ai-input")
                input_widget.value = "show git status"
                await pilot.press("enter")
                await pilot.pause()
                # Should dismiss (not on request screen anymore)
                assert not isinstance(app.screen, AIRequestScreen)

    async def test_cancel(self) -> None:
        from cheat_cli.ui.tui.ai import AIRequestScreen
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp

        app = CheatApp(service=MagicMock())
        async with app.run_test() as pilot:
            await pilot.press("i")
            await pilot.pause()
            assert isinstance(app.screen, AIRequestScreen)

            await pilot.press("escape")
            await pilot.pause()
            assert isinstance(app.screen, BrowserScreen)


class TestAISuggestionsScreen:
    """Tests for AISuggestionsScreen."""

    async def test_screen_opens_with_loading(self) -> None:
        from cheat_cli.ui.tui.ai import AIRequestScreen, AISuggestionsScreen
        from cheat_cli.ui.tui.app import CheatApp

        with patch("cheat_cli.ui.tui.ai.get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.name = "mock"
            mock_provider.suggest_commands.return_value = []
            mock_get.return_value = mock_provider

            app = CheatApp(service=MagicMock())
            async with app.run_test() as pilot:
                # Open AI request screen
                await pilot.press("i")
                await pilot.pause()
                assert isinstance(app.screen, AIRequestScreen)

                # Submit request
                input_widget = app.screen.query_one("#ai-input")
                input_widget.value = "test"
                await pilot.press("enter")
                await pilot.pause()

                # Should be on suggestions screen
                assert isinstance(app.screen, AISuggestionsScreen)

    async def test_escape_back(self) -> None:
        from cheat_cli.ui.tui.ai import AISuggestionsScreen
        from cheat_cli.ui.tui.app import BrowserScreen, CheatApp

        with patch("cheat_cli.ui.tui.ai.get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.name = "mock"
            mock_provider.suggest_commands.return_value = []
            mock_get.return_value = mock_provider

            app = CheatApp(service=MagicMock())
            async with app.run_test() as pilot:
                screen = AISuggestionsScreen("test")
                app.push_screen(screen)
                await pilot.pause()

                await pilot.press("escape")
                await pilot.pause()
                assert isinstance(app.screen, BrowserScreen)
