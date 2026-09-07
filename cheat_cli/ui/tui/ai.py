"""AI suggestion screens for cheat-cli TUI."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, LoadingIndicator, Static

from ...ai.models import AICommandSuggestion, AIContext
from ...ai.provider import ProviderError
from ...ai.registry import get_provider
from ...runner import run_command
from ...safety import classify_command
from ..clipboard import ClipboardError, copy_to_clipboard
from .app import ConfirmScreen, ResultScreen


class AIRequestScreen(Screen):
    """Screen for entering AI command requests."""

    CSS = """
    #ai-container {
        width: 70;
        max-width: 90%;
        height: auto;
        border: solid $accent;
        padding: 1 2;
        margin: 2 4;
        background: $surface;
    }
    #ai-title {
        padding: 0 0 1 0;
    }
    #ai-error {
        color: $error;
        padding: 0 0 1 0;
        display: none;
    }
    #ai-error.visible {
        display: block;
    }
    #ai-hint {
        padding: 1 0 0 0;
        color: $text-muted;
    }
    """

    BINDINGS = [  # noqa: RUF012
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, provider_name: str = "") -> None:
        super().__init__()
        self.provider_name = provider_name
        self.result: str | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="ai-container"):
            yield Static("AI Command Suggestions", id="ai-title")
            yield Static("", id="ai-error")
            yield Input(placeholder="Describe what you want to do...", id="ai-input")
            provider_info = f"Provider: {self.provider_name or 'default'}"
            yield Static(
                f"[dim]{provider_info}[/dim]\n"
                f"[dim]Enter to submit, Esc to cancel[/dim]",
                id="ai-hint",
            )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#ai-input", Input).focus()

    def _show_error(self, message: str) -> None:
        error_widget = self.query_one("#ai-error", Static)
        error_widget.update(message)
        error_widget.add_class("visible")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "ai-input":
            self.action_submit()

    def action_submit(self) -> None:
        request = self.query_one("#ai-input", Input).value.strip()
        if not request:
            self._show_error("Please enter a request")
            return
        self.result = request
        self.dismiss(self.result)

    def action_cancel(self) -> None:
        self.result = None
        self.dismiss(None)


class AISuggestionsScreen(Screen):
    """Screen displaying AI command suggestions."""

    CSS = """
    #ai-suggestions-container {
        width: 100%;
        height: 1fr;
        padding: 1 2;
    }
    #ai-suggestions-header {
        height: auto;
        padding: 0 0 1 0;
    }
    #ai-suggestions-scroll {
        height: 1fr;
        border: solid $accent;
    }
    #ai-suggestions-list {
        width: 100%;
    }
    .suggestion-item {
        padding: 1 0;
        border-bottom: solid $surface;
    }
    .suggestion-command {
        color: $accent;
        text-style: bold;
    }
    .suggestion-description {
        color: $text;
    }
    .suggestion-tool {
        color: $text-muted;
    }
    #ai-suggestions-footer {
        height: auto;
        padding: 1 0 0 0;
        color: $text-muted;
    }
    #ai-suggestions-error {
        color: $error;
        padding: 1 0;
    }
    #ai-suggestions-loading {
        height: 3;
        padding: 1 0;
    }
    """

    BINDINGS = [  # noqa: RUF012
        Binding("escape", "cancel", "Back", show=False),
        Binding("y", "copy_command", "Copy", show=False),
        Binding("c", "copy_command", "Copy", show=False),
        Binding("r", "run_command", "Run", show=False),
        Binding("enter", "copy_command", "Copy", show=False),
        Binding("q", "cancel", "Back", show=False),
    ]

    def __init__(
        self,
        request: str,
        provider_name: str = "",
    ) -> None:
        super().__init__()
        self.request = request
        self.provider_name = provider_name
        self.suggestions: list[AICommandSuggestion] = []
        self.selected_index: int = 0
        self._loading = True
        self._error: str | None = None
        self._clipboard_feedback: str | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="ai-suggestions-container"):
            yield Static(
                f"[b]AI Suggestions[/b] — {self.request}",
                id="ai-suggestions-header",
            )
            yield LoadingIndicator(id="ai-suggestions-loading")
            yield Static("", id="ai-suggestions-error")
            with VerticalScroll(id="ai-suggestions-scroll"):
                yield Static("", id="ai-suggestions-list")
            yield Static(
                "[y] Copy    [r] Run    [Esc] Back",
                id="ai-suggestions-footer",
            )
        yield Footer()

    def on_mount(self) -> None:
        self._fetch_suggestions()

    def _fetch_suggestions(self) -> None:
        """Fetch suggestions from AI provider."""
        from .app import run_after_delay

        self._loading = True
        self._update_display()

        def do_fetch() -> None:
            try:
                provider = get_provider(self.provider_name or None)
                context = AIContext.detect()
                suggestions = provider.suggest_commands(self.request, context)
                self.suggestions = suggestions
                self._loading = False
                self._error = None
            except ProviderError as e:
                self._loading = False
                self._error = str(e)
            except (OSError, ValueError) as e:
                self._loading = False
                self._error = f"Unexpected error: {e}"

            self._update_display()

        run_after_delay(0.1, do_fetch)

    def _update_display(self) -> None:
        """Update the display based on current state."""
        try:
            loading = self.query_one("#ai-suggestions-loading", LoadingIndicator)
            error = self.query_one("#ai-suggestions-error", Static)
            list_widget = self.query_one("#ai-suggestions-list", Static)
            scroll = self.query_one("#ai-suggestions-scroll", VerticalScroll)
        except (IndexError, KeyError):
            return

        if self._loading:
            loading.display = True
            error.display = False
            list_widget.update("")
            return

        loading.display = False

        if self._error:
            error.update(self._error)
            error.display = True
            list_widget.update("")
            return

        error.display = False

        if not self.suggestions:
            list_widget.update("[dim]No suggestions returned.[/dim]")
            return

        lines = []
        for i, s in enumerate(self.suggestions):
            marker = "→" if i == self.selected_index else " "
            tags_str = f" [{', '.join(s.tags)}]" if s.tags else ""
            lines.append(
                f"  {marker} [b]{i + 1}.[/b] {s.tool} — {s.description}{tags_str}\n"
                f"       {s.command}"
            )
        list_widget.update("\n\n".join(lines))

        # Scroll to keep selected item visible
        if self.suggestions:
            item_height = 3  # lines per item approximately
            scroll_offset = self.selected_index * item_height
            scroll.scroll_home(animate=False)
            scroll.scroll_down(scroll_offset, animate=False)

    def _selected_suggestion(self) -> AICommandSuggestion | None:
        """Get the currently selected suggestion."""
        if 0 <= self.selected_index < len(self.suggestions):
            return self.suggestions[self.selected_index]
        return None

    def action_copy_command(self) -> None:
        """Copy the selected suggestion's command to clipboard."""
        suggestion = self._selected_suggestion()
        if suggestion is None:
            return
        try:
            copy_to_clipboard(suggestion.command)
            self._clipboard_feedback = f"Copied: {suggestion.command}"
            self._update_footer()
            self.set_timer(1.5, self._clear_clipboard_feedback)
        except ClipboardError:
            self._clipboard_feedback = "Could not copy command"
            self._update_footer()
            self.set_timer(1.5, self._clear_clipboard_feedback)

    def _clear_clipboard_feedback(self) -> None:
        self._clipboard_feedback = None
        self._update_footer()

    def _update_footer(self) -> None:
        footer = self.query_one("#ai-suggestions-footer", Static)
        if self._clipboard_feedback:
            footer.update(self._clipboard_feedback)
        else:
            footer.update("[y] Copy    [r] Run    [Esc] Back")

    def action_run_command(self) -> None:
        """Run the selected suggestion through the safety classifier."""
        suggestion = self._selected_suggestion()
        if suggestion is None:
            return
        risk_matches = classify_command(suggestion.command)
        if risk_matches:
            self.app.push_screen(
                ConfirmScreen(suggestion.command, risk_matches),
                callback=self._on_confirm_result,
            )
        else:
            self._execute_command(suggestion.command)

    def _on_confirm_result(self, confirmed: bool) -> None:
        if confirmed:
            suggestion = self._selected_suggestion()
            if suggestion is not None:
                self._execute_command(suggestion.command)

    def _execute_command(self, command: str) -> None:
        result = run_command(command)
        self.app.push_screen(ResultScreen(result))

    def action_cancel(self) -> None:
        self.dismiss()
