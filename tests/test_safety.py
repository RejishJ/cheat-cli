"""Tests for cheat_cli.safety — deterministic command safety classifier."""

from __future__ import annotations

from cheat_cli.safety import RiskMatch, classify_command, is_risky_command


class TestRiskyCommands:
    def test_rm_rf(self) -> None:
        assert is_risky_command("rm -rf /var/log")

    def test_rm_recursive(self) -> None:
        assert is_risky_command("rm -r temp/")

    def test_rm_force(self) -> None:
        assert is_risky_command("rm -f old_file.txt")

    def test_del_recursive_windows(self) -> None:
        assert is_risky_command("del /s /q C:\\temp")

    def test_rmdir_recursive_windows(self) -> None:
        assert is_risky_command("rmdir /s /q C:\\temp")

    def test_format_disk(self) -> None:
        assert is_risky_command("format D:")

    def test_diskpart(self) -> None:
        assert is_risky_command("diskpart /s script.txt")

    def test_mkfs(self) -> None:
        assert is_risky_command("mkfs.ext4 /dev/sda1")

    def test_dd(self) -> None:
        assert is_risky_command("dd if=image.iso of=/dev/sdb")

    def test_shutdown(self) -> None:
        assert is_risky_command("shutdown -h now")

    def test_reboot(self) -> None:
        assert is_risky_command("reboot")

    def test_init_0(self) -> None:
        assert is_risky_command("init 0")

    def test_init_6(self) -> None:
        assert is_risky_command("init 6")

    def test_sudo(self) -> None:
        assert is_risky_command("sudo apt update")

    def test_sudo_rm(self) -> None:
        assert is_risky_command("sudo rm -rf /tmp/*")

    def test_chmod_recursive(self) -> None:
        assert is_risky_command("chmod -R 777 /var/www")

    def test_chown_recursive(self) -> None:
        assert is_risky_command("chown -R user:group /opt")

    def test_git_reset_hard(self) -> None:
        assert is_risky_command("git reset --hard HEAD~1")

    def test_git_reset_hard_full_hash(self) -> None:
        assert is_risky_command("git reset --hard abc123")

    def test_git_clean_fd(self) -> None:
        assert is_risky_command("git clean -fd")

    def test_git_clean_fd_with_directory(self) -> None:
        assert is_risky_command("git clean -fd src/")

    def test_git_push_force(self) -> None:
        assert is_risky_command("git push --force origin main")

    def test_git_push_force_short_flag(self) -> None:
        assert is_risky_command("git push -f origin main")

    def test_docker_system_prune(self) -> None:
        assert is_risky_command("docker system prune -a")

    def test_docker_rm(self) -> None:
        assert is_risky_command("docker rm container1")

    def test_docker_rmi(self) -> None:
        assert is_risky_command("docker rmi image:latest")

    def test_pip_uninstall(self) -> None:
        assert is_risky_command("pip uninstall numpy")

    def test_npm_uninstall(self) -> None:
        assert is_risky_command("npm uninstall lodash")

    def test_iptables(self) -> None:
        assert is_risky_command("iptables -F")

    def test_systemctl_stop(self) -> None:
        assert is_risky_command("systemctl stop nginx")

    def test_service_disable(self) -> None:
        assert is_risky_command("service mysql disable")


class TestNonRiskyCommands:
    def test_git_status(self) -> None:
        assert not is_risky_command("git status")

    def test_git_log(self) -> None:
        assert not is_risky_command("git log --oneline")

    def test_git_diff(self) -> None:
        assert not is_risky_command("git diff")

    def test_docker_ps(self) -> None:
        assert not is_risky_command("docker ps")

    def test_docker_images(self) -> None:
        assert not is_risky_command("docker images")

    def test_kubectl_get(self) -> None:
        assert not is_risky_command("kubectl get pods")

    def test_python_pytest(self) -> None:
        assert not is_risky_command("python -m pytest")

    def test_python_ruff(self) -> None:
        assert not is_risky_command("python -m ruff check .")

    def test_ls(self) -> None:
        assert not is_risky_command("ls -la")

    def test_cat(self) -> None:
        assert not is_risky_command("cat file.txt")

    def test_echo(self) -> None:
        assert not is_risky_command("echo hello")

    def test_empty_command(self) -> None:
        assert not is_risky_command("")

    def test_whitespace_command(self) -> None:
        assert not is_risky_command("   ")

    def test_pip_install(self) -> None:
        assert not is_risky_command("pip install requests")

    def test_npm_install(self) -> None:
        assert not is_risky_command("npm install express")

    def test_systemctl_start(self) -> None:
        assert not is_risky_command("systemctl start nginx")

    def test_chmod_not_recursive(self) -> None:
        assert not is_risky_command("chmod 755 file.sh")

    def test_chown_not_recursive(self) -> None:
        assert not is_risky_command("chown user:group file.txt")


class TestClassifyCommand:
    def test_returns_risk_matches(self) -> None:
        matches = classify_command("rm -rf /tmp")
        assert len(matches) >= 1
        assert all(isinstance(m, RiskMatch) for m in matches)

    def test_multiple_risky_patterns(self) -> None:
        matches = classify_command("sudo rm -rf /var/log")
        assert len(matches) >= 2

    def test_no_matches_for_safe_command(self) -> None:
        matches = classify_command("git status")
        assert len(matches) == 0

    def test_case_insensitive(self) -> None:
        assert is_risky_command("RM -rf /tmp")
        assert is_risky_command("SUDO apt update")
        assert is_risky_command("Git Reset --hard HEAD")

    def test_risky_pattern_has_description(self) -> None:
        matches = classify_command("rm -rf /tmp")
        assert all(m.description for m in matches)

    def test_risky_pattern_has_pattern(self) -> None:
        matches = classify_command("rm -rf /tmp")
        assert all(m.pattern for m in matches)


class TestSafetyDoesNotExecute:
    """Verify the classifier does not execute any commands."""

    def test_classify_is_pure(self) -> None:
        """classify_command should only do string matching."""
        import unittest.mock

        with unittest.mock.patch("subprocess.run") as mock_run:
            classify_command("rm -rf /tmp")
            classify_command("sudo shutdown")
            mock_run.assert_not_called()

    def test_is_risky_is_pure(self) -> None:
        """is_risky_command should only do string matching."""
        import unittest.mock

        with unittest.mock.patch("subprocess.run") as mock_run:
            is_risky_command("rm -rf /tmp")
            is_risky_command("git status")
            mock_run.assert_not_called()
