"""Tests for cheat_cli.cli — the main CLI dispatcher."""

import pytest

from cheat_cli.cli import build_parser, main


class TestBuildParser:
    def test_creates_parser(self):
        parser = build_parser()
        assert parser.prog == "cheat"

    def test_version_flag(self, capsys):
        parser = build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "cheat-cli" in captured.out

    def test_version_short_flag(self, capsys):
        parser = build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["-V"])
        assert exc_info.value.code == 0

    def test_help_flag(self, capsys):
        parser = build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--help"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "cheat" in captured.out.lower()

    def test_ls_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(["ls"])
        assert args.command == "ls"
        assert args.query is None

    def test_ls_with_query(self):
        parser = build_parser()
        args = parser.parse_args(["ls", "git"])
        assert args.command == "ls"
        assert args.query == "git"

    def test_search_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(["search", "docker"])
        assert args.command == "search"
        assert args.query == "docker"

    def test_add_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(["add"])
        assert args.command == "add"

    def test_rm_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(["rm", "git"])
        assert args.command == "rm"
        assert args.query == "git"

    def test_all_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(["all"])
        assert args.command == "all"

    def test_delete_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(["delete", "git"])
        assert args.command == "delete"
        assert args.query == "git"


class TestMain:
    def test_no_args_prints_help(self, capsys):
        exit_code = main([])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "cheat" in captured.out.lower()

    def test_unknown_command(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["foobar"])
        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "invalid choice" in captured.err.lower() or "unknown" in captured.err.lower()

    def test_ls_empty_storage(self, empty_csv, monkeypatch, capsys):
        monkeypatch.setattr("cheat_cli.cli.load_entries", list)
        exit_code = main(["ls"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "No results found" in captured.out

    def test_ls_with_data(self, sample_csv, monkeypatch, capsys):
        from cheat_cli.core.storage import load_entries
        monkeypatch.setattr("cheat_cli.cli.load_entries", lambda: load_entries(sample_csv))
        exit_code = main(["ls"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "git" in captured.out

    def test_ls_with_query(self, sample_csv, monkeypatch, capsys):
        from cheat_cli.core.search import search_entries
        from cheat_cli.core.storage import load_entries

        entries = load_entries(sample_csv)
        monkeypatch.setattr(
            "cheat_cli.cli.load_entries",
            lambda: search_entries(entries, "docker"),
        )
        exit_code = main(["ls", "docker"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "docker" in captured.out
        assert "git" not in captured.out

    def test_search_same_as_ls_query(self, sample_csv, monkeypatch, capsys):
        from cheat_cli.core.search import search_entries
        from cheat_cli.core.storage import load_entries

        entries = load_entries(sample_csv)
        monkeypatch.setattr(
            "cheat_cli.cli.load_entries",
            lambda: search_entries(entries, "git"),
        )
        exit_code = main(["search", "git"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "git" in captured.out

    def test_rm_no_match(self, sample_csv, monkeypatch, capsys):
        from cheat_cli.core.storage import load_entries
        monkeypatch.setattr("cheat_cli.cli.load_entries", lambda: load_entries(sample_csv))
        exit_code = main(["rm", "nonexistent"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "No match found" in captured.out

    def test_rm_cancelled(self, sample_csv, monkeypatch, capsys):
        from cheat_cli.core.storage import load_entries
        monkeypatch.setattr("cheat_cli.cli.load_entries", lambda: load_entries(sample_csv))
        monkeypatch.setattr("builtins.input", lambda _: "no")
        exit_code = main(["rm", "docker"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Cancelled" in captured.out

    def test_all_deprecated(self, sample_csv, monkeypatch, capsys):
        from cheat_cli.core.storage import load_entries
        monkeypatch.setattr("cheat_cli.cli.load_entries", lambda: load_entries(sample_csv))
        exit_code = main(["all"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "deprecated" in captured.err.lower()

    def test_delete_deprecated(self, sample_csv, monkeypatch, capsys):
        from cheat_cli.core.storage import load_entries
        monkeypatch.setattr("cheat_cli.cli.load_entries", lambda: load_entries(sample_csv))
        monkeypatch.setattr("builtins.input", lambda _: "no")
        exit_code = main(["delete", "docker"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "deprecated" in captured.err.lower()

    def test_delete_missing_query(self, capsys):
        exit_code = main(["delete"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "missing required argument" in captured.err.lower()
