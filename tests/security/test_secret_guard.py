"""비밀값을 출력하지 않고 실제 Git 인덱스와 바이너리 검사를 검증합니다."""

from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile
import unittest


GUARD = Path(__file__).resolve().parents[2] / "scripts" / "check-secrets.py"
CONFIG = GUARD.parent.parent / ".gitleaks.toml"
FAKE_KEY = ("AI" + "za" + "A" * 35).encode("ascii")


class SecretGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="secret-guard-")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "github" / "main"
        self.repo.mkdir(parents=True)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Security Test")
        self.git("config", "user.email", "security-test@example.invalid")
        self.git("config", "core.hooksPath", str(self.repo / "no-hooks"))

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, check=True,
                              capture_output=True).stdout

    def add(self, name, data=b"safe\n"):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        self.git("add", "--", name)

    def guard(self, *args):
        return subprocess.run([sys.executable, str(GUARD), *args], cwd=self.repo,
                              capture_output=True, check=False)

    def test_clean_staged_file_passes(self):
        self.add("notes.md")
        self.assertEqual(self.guard("--staged").returncode, 0)

    def test_binary_secret_is_blocked_without_printing_it(self):
        self.add("renamed.dat", b"\x00\xffbefore" + FAKE_KEY + b"\x00after")
        result = self.guard("--staged")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"renamed.dat", result.stdout)
        self.assertNotIn(FAKE_KEY, result.stdout + result.stderr)

    def test_clean_working_file_does_not_hide_staged_secret(self):
        self.add("notes.txt", FAKE_KEY)
        (self.repo / "notes.txt").write_bytes(b"safe\n")
        self.assertEqual(self.guard("--staged").returncode, 1)

    def test_profile_with_no_key_is_blocked(self):
        self.add("analysis/chrome-tmp-new/Default/Preferences")
        self.assertEqual(self.guard("--staged").returncode, 1)

    def test_renamed_profile_database_is_blocked(self):
        self.add("analysis/renamed/Default/shared_proto_db/000003.log")
        self.assertEqual(self.guard("--staged").returncode, 1)

    def test_missing_revision_fails_closed(self):
        self.assertEqual(self.guard("--ref", "does-not-exist").returncode, 2)

    def test_snapshot_cleanup_does_not_claim_history_is_clean(self):
        self.add("old.log", b"\x00" + FAKE_KEY)
        self.git("commit", "-qm", "synthetic fixture")
        old = self.git("rev-parse", "HEAD").decode().strip()
        self.git("rm", "-q", "old.log")
        self.add("notes.md")
        self.git("commit", "-qm", "remove fixture")
        self.assertEqual(self.guard().returncode, 0)
        self.assertEqual(self.guard("--ref", old).returncode, 1)

    def gitleaks(self):
        return subprocess.run(
            ["gitleaks", "git", ".", "--pre-commit", "--staged", "--config", str(CONFIG),
             "--redact=100", "--no-banner", "--ignore-gitleaks-allow"],
            cwd=self.repo, capture_output=True, check=False,
        )

    def test_ctf_hash_exception_is_limited_to_exact_path(self):
        digest = hashlib.sha256(b"synthetic security test fixture").hexdigest()
        line = ('ADMIN_PASSWORD_SHA256: "' + digest + '"\n').encode()
        self.add("web/Neon Skies/challenge/public/docker-compose.yml", line)
        self.assertEqual(self.gitleaks().returncode, 0)
        self.add("unrelated.yml", line)
        self.assertEqual(self.gitleaks().returncode, 1)

    def test_ctf_hash_exception_does_not_allow_other_keys(self):
        fixture = hashlib.sha256(b"synthetic unrelated API fixture").hexdigest()
        line = ('api_key: "' + fixture + '"\n').encode()
        self.add("web/Neon Skies/challenge/public/docker-compose.yml", line)
        self.assertEqual(self.gitleaks().returncode, 1)


if __name__ == "__main__":
    unittest.main()
