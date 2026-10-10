"""Tests for harness/tools/pakmod.py with FAKE repak and UAssetGUI scripts and temp folders.

No real tool, no real game folder, no real pak. The fake tools read and write a tiny pak format of their own
(a JSON file with base64 members). They prove the glue code, not the behavior of the real tools.
"""

import base64
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

HARNESS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HARNESS_DIR / "tools"))
import pakmod  # noqa: E402

UNINSTALL = HARNESS_DIR / "uninstall.ps1"
ASSET = "ManorLords/Content/NotStronghold/Data/DT_Items"
UASSET_BYTES = b"UASSET-DATA-0123456789"
UEXP_BYTES = b"UEXP-DATA-ABCDEF"
KEY = "TESTKEY0123456789abcdef"
KEY_ENV = "PAKMOD_TEST_AES_KEY"

FAKE_REPAK = textwrap.dedent('''
    import base64, hashlib, json, os, sys, time
    args = sys.argv[1:]
    key = None
    if args[:1] == ["--aes-key"]:
        key, args = args[1], args[2:]
    with open(os.environ["FAKE_LOG"], "a") as log:
        shown = ["***" if item == key else item for item in args]
        log.write(json.dumps({"tool": "repak", "key_seen": key is not None, "args": shown}) + "\\n")
    if args == ["--version"]:
        print("repak_cli 9.9.9-fake")
        sys.exit(0)
    mode = os.environ.get("FAKE_REPAK_MODE", "ok")
    if mode == "fail":
        print("failed, my arguments were: " + " ".join(sys.argv[1:]), file=sys.stderr)
        sys.exit(7)
    if mode == "sleep":
        time.sleep(30)
    command, options, positional = args[0], {}, []
    rest = iter(args[1:])
    for token in rest:
        if token in ("-s", "--mount-point", "--version"):
            options[token] = next(rest)
        else:
            positional.append(token)

    def load(path):
        pak = json.load(open(path))
        if pak.get("key") and pak["key"] != key:
            print("wrong or missing AES key", file=sys.stderr)
            sys.exit(1)
        return pak

    if command == "list":
        print("\\n".join(sorted(load(positional[0])["files"])))
    elif command == "hash-list":
        for name, data in sorted(load(positional[0])["files"].items()):
            print(hashlib.sha256(base64.b64decode(data)).hexdigest(), name)
    elif command == "info":
        pak = load(positional[0])
        print("mount point:", pak["mount"], "version:", pak.get("version"))
    elif command == "get":
        files = load(positional[0])["files"]
        if positional[1] not in files:
            print("file not found: " + positional[1], file=sys.stderr)
            sys.exit(1)
        sys.stdout.buffer.write(base64.b64decode(files[positional[1]]))
    elif command == "pack":
        folder = positional[0]
        names = sorted(
            os.path.relpath(os.path.join(root, f), folder).replace(os.sep, "/")
            for root, _, found in os.walk(folder) for f in found)
        if mode == "drop":
            names = names[:-1]
        files = {n: base64.b64encode(open(os.path.join(folder, n), "rb").read()).decode() for n in names}
        document = {"mount": options.get("--mount-point"), "version": options.get("--version"), "files": files}
        if mode != "nofile":
            json.dump(document, open(positional[1], "w"))
    else:
        sys.exit(2)
''')

FAKE_UASSETGUI = textwrap.dedent('''
    import base64, json, os, sys, time
    args = sys.argv[1:]
    with open(os.environ["FAKE_LOG"], "a") as log:
        log.write(json.dumps({"tool": "uassetgui", "args": args}) + "\\n")
    mode = os.environ.get("FAKE_UASSET_MODE", "ok")
    if mode == "fail":
        print("cannot parse the asset", file=sys.stderr)
        sys.exit(5)
    if mode == "sleep":
        time.sleep(30)
    command = args[0]
    if command == "tojson" and len(args) == 5:
        source, destination, engine, usmap = args[1:]
        exp = source[:-len(".uasset")] + ".uexp"
        document = {"engine": engine, "usmap": os.path.basename(usmap), "uasset": base64.b64encode(open(source, "rb").read()).decode(),
                    "uexp": base64.b64encode(open(exp, "rb").read()).decode() if os.path.exists(exp) else None}
        if mode != "nofile":
            open(destination, "w").write(json.dumps(document) if mode != "empty" else "")
    elif command == "fromjson" and len(args) == 4:
        source, destination, usmap = args[1:]
        document = json.load(open(source))
        uasset = base64.b64decode(document["uasset"])
        if os.environ.get("FAKE_UASSET_LOSSY"):
            uasset = uasset[:3] + b"?" + uasset[4:]
        open(destination, "wb").write(uasset)
        if document["uexp"]:
            open(destination[:-len(".uasset")] + ".uexp", "wb").write(base64.b64decode(document["uexp"]))
    else:
        print("bad arguments: " + repr(args), file=sys.stderr)
        sys.exit(2)
''')


def encode_files(files):
    return {name: base64.b64encode(data).decode() for name, data in files.items()}


class PakTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.work = self.tmp / "work"
        self.work.mkdir()
        self.game = self.tmp / "game"
        self.paks = self.game / "ManorLords" / "Content" / "Paks"
        self.paks.mkdir(parents=True)
        self.log = self.tmp / "fake.log"
        self.repak = self.tmp / "fake_repak.py"
        self.repak.write_text(FAKE_REPAK, encoding="utf-8")
        self.uassetgui = self.tmp / "fake_uassetgui.py"
        self.uassetgui.write_text(FAKE_UASSETGUI, encoding="utf-8")
        self.usmap = self.tmp / "game.usmap"
        self.usmap.write_bytes(b"usmap")
        self.config_path = self.tmp / "pakmod.local.json"
        self.write_config()
        env = mock.patch.dict(os.environ, {"FAKE_LOG": str(self.log), "FAKE_REPAK_MODE": "ok", "FAKE_UASSET_MODE": "ok"})
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("FAKE_UASSET_LOSSY", None)
        os.environ.pop(KEY_ENV, None)

    def write_config(self, pin=True, **overrides):
        config = {
            "repak": {"path": str(self.repak), "sha256": pakmod.sha256_of(self.repak) if pin else ""},
            "uassetgui": {"path": str(self.uassetgui), "sha256": pakmod.sha256_of(self.uassetgui) if pin else ""},
            "usmap": str(self.usmap),
            "engine_version": "5.5",
            "work_dir": str(self.work),
        }
        config.update(overrides)
        self.config_path.write_text(json.dumps(config), encoding="utf-8")

    def config(self):
        return pakmod.load_config(self.config_path)

    def make_game_pak(self, name="pakchunk0-WindowsNoEditor.pak", files=None, key=None):
        files = files if files is not None else {
            ASSET + ".uasset": UASSET_BYTES, ASSET + ".uexp": UEXP_BYTES, "ManorLords/Content/Other/Thing.uasset": b"other"}
        document = {"mount": "../../../", "files": encode_files(files)}
        if key:
            document["key"] = key
        path = self.paks / name
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def make_assets(self, name="demo", content=b"x"):
        path = self.work / name / "ManorLords" / "Content" / "Data" / "DT_Items.uasset"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = pakmod.main(["--config", str(self.config_path), "--game-dir", str(self.game), *argv])
        return code, out.getvalue(), err.getvalue()

    def log_entries(self, tool=None, command=None):
        if not self.log.exists():
            return []
        entries = [json.loads(line) for line in self.log.read_text().splitlines()]
        return [e for e in entries if (tool is None or e["tool"] == tool) and (command is None or command in e["args"][:1])]

    def build_and_install(self, name="demo"):
        self.make_assets(name)
        pakmod.build(self.config(), name)
        return pakmod.install(self.work, self.game, name)

    @property
    def mods(self):
        return pakmod.mods_dir_of(self.game)


class ConfigAndCheckTests(PakTestCase):
    def test_valid_config_loads_with_defaults(self):
        config = self.config()
        self.assertEqual(config["work_dir"], self.work)
        self.assertEqual(config["pak_version"], "V11")
        self.assertEqual(config["mount_point"], "../../../")

    def test_each_problem_is_reported(self):
        self.write_config(usmap="", work_dir=str(self.tmp / "nodir"), aes_key_env="not a name")
        text = " ".join(pakmod.config_problems(self.config_path))
        self.assertIn("'usmap' is missing", text)
        self.assertIn("work_dir is not a folder", text)
        self.assertIn("NAME of an environment variable", text)

    def test_a_pasted_key_in_aes_key_env_is_refused_without_echo(self):
        self.write_config(aes_key_env="0x" + "ab" * 32)
        problems = " ".join(pakmod.config_problems(self.config_path))
        self.assertIn("NAME of an environment variable", problems)
        self.assertNotIn("ab" * 32, problems)

    def test_missing_and_broken_config(self):
        self.assertIn("config file missing", pakmod.config_problems(self.tmp / "none.json")[0])
        self.config_path.write_text("{", encoding="utf-8")
        with self.assertRaises(pakmod.PakModError):
            pakmod.load_config(self.config_path)

    def test_check_ok_prints_hashes_status_and_the_repak_version(self):
        code, out, _ = self.run_main("check")
        self.assertEqual(code, 0, out)
        self.assertIn("repak: ok, sha256 matches. Version: repak_cli 9.9.9-fake", out)
        self.assertIn("uassetgui: ok", out)
        self.assertIn("unknown", out)  # UAssetGUI has no known version flag

    def test_hash_mismatch_refuses_with_exit_code_3_and_names_the_tool(self):
        self.uassetgui.write_text(FAKE_UASSETGUI + "\n# changed\n", encoding="utf-8")
        code, _, err = self.run_main("check")
        self.assertEqual(code, 3)
        self.assertIn("uassetgui does not match", err)

    def test_a_tool_with_a_wrong_hash_is_never_run(self):
        self.make_game_pak()
        self.repak.write_text(FAKE_REPAK + "\n# changed\n", encoding="utf-8")
        code, _, err = self.run_main("find", "DT_Items")
        self.assertEqual(code, 3)
        self.assertIn("repak does not match", err)
        self.assertEqual(self.log_entries("repak"), [])

    def test_missing_tool_is_reported(self):
        self.repak.unlink()
        code, out, _ = self.run_main("check")
        self.assertEqual(code, 1)
        self.assertIn("repak not found", out)

    def test_unpinned_tool_is_reported_and_pin_writes_the_hashes(self):
        self.write_config(pin=False)
        code, out, _ = self.run_main("check")
        self.assertEqual(code, 1)
        self.assertIn("no pinned hash", out)
        code, out, _ = self.run_main("check", "--pin")
        self.assertEqual(code, 0, out)
        self.assertIn(pakmod.sha256_of(self.repak), out)
        saved = json.loads(self.config_path.read_text())
        self.assertEqual(saved["repak"]["sha256"], pakmod.sha256_of(self.repak))
        self.assertEqual(saved["uassetgui"]["sha256"], pakmod.sha256_of(self.uassetgui))
        self.assertEqual(saved["engine_version"], "5.5")

    def test_pin_dry_run_does_not_write(self):
        self.write_config(pin=False)
        before = self.config_path.read_text()
        self.run_main("--dry-run", "check", "--pin")
        self.assertEqual(self.config_path.read_text(), before)

    def test_check_reports_a_missing_usmap_and_a_missing_paks_folder(self):
        self.usmap.unlink()
        shutil.rmtree(self.paks)
        code, out, _ = self.run_main("check")
        self.assertEqual(code, 1)
        self.assertIn("usmap file not found", out)
        self.assertIn("Paks folder not found", out)


class GuardTests(PakTestCase):
    def test_bad_names_are_refused(self):
        for name in ["", "..", "a/b", "a\\b", "x" * 41, "a b", "C:\\x", "../evil", "a.b"]:
            with self.subTest(name=name), self.assertRaises(pakmod.PakModError):
                pakmod.check_name(name)

    def test_good_names_pass_and_reserved_folder_names_do_not(self):
        for name in ["a", "Demo_1-x", "x" * 40]:
            self.assertEqual(pakmod.check_mod_name(name), name)
        with self.assertRaises(pakmod.PakModError):
            pakmod.check_mod_name("out")

    def test_path_outside_work_dir_is_refused(self):
        with self.assertRaises(pakmod.PakModError):
            pakmod.require_inside(self.tmp / "other", self.work, "x")
        with self.assertRaises(pakmod.PakModError):
            pakmod.require_inside(self.work / ".." / "other", self.work, "x")

    def test_symlink_in_assets_is_refused(self):
        self.make_assets()
        link = self.work / "demo" / "link.uasset"
        try:
            link.symlink_to(self.log)
        except OSError:
            self.skipTest("symlinks need a privilege on this system")
        with self.assertRaises(pakmod.PakModError):
            pakmod.build(self.config(), "demo")

    def test_missing_or_empty_asset_folder_is_refused(self):
        with self.assertRaises(pakmod.PakModError):
            pakmod.build(self.config(), "demo")
        (self.work / "demo").mkdir()
        with self.assertRaises(pakmod.PakModError):
            pakmod.build(self.config(), "demo")

    def test_asset_paths_with_traversal_or_absolute_parts_are_refused(self):
        self.make_game_pak()
        for bad in ["../x", "a/../b", "/abs/path", "C:/x/y", "\\\\server\\share\\x", "a//b", ""]:
            with self.subTest(path=bad):
                code, _, err = self.run_main("extract", bad)
                self.assertEqual(code, 1)
                self.assertIn("bad asset path", err)
        self.assertEqual(self.log_entries("repak"), [])

    def test_tojson_refuses_a_file_outside_the_work_folder(self):
        code, _, err = self.run_main("tojson", str(self.usmap))
        self.assertEqual(code, 1)
        self.assertIn("outside", err)


class FindTests(PakTestCase):
    def test_find_is_case_insensitive_and_names_the_pak(self):
        self.make_game_pak()
        self.make_game_pak("pakchunk1.pak", {"ManorLords/Content/Foo/dt_items_extra.uasset": b"1"})
        code, out, _ = self.run_main("find", "DT_ITEMS")
        self.assertEqual(code, 0)
        self.assertIn(f"pakchunk0-WindowsNoEditor.pak  {ASSET}.uasset", out)
        self.assertIn("pakchunk1.pak  ManorLords/Content/Foo/dt_items_extra.uasset", out)
        self.assertIn("3 matches in 2 paks", out)

    def test_second_find_uses_the_cache(self):
        self.make_game_pak()
        self.run_main("find", "DT_")
        self.assertEqual(len(self.log_entries("repak", "list")), 1)
        self.run_main("find", "Thing")
        self.assertEqual(len(self.log_entries("repak", "list")), 1)

    def test_changed_pak_refreshes_the_cache(self):
        pak = self.make_game_pak()
        self.run_main("find", "DT_")
        self.make_game_pak(files={"ManorLords/Content/New/DT_New.uasset": b"n"})
        code, out, _ = self.run_main("find", "DT_New")
        self.assertIn("DT_New", out)
        self.assertEqual(len(self.log_entries("repak", "list")), 2)
        self.assertTrue((self.work / ".index-cache" / (pak.name + ".json")).is_file())

    def test_the_mods_folder_is_not_searched(self):
        self.make_game_pak()
        self.mods.mkdir()
        (self.mods / "x_P.pak").write_text(json.dumps({"mount": "", "files": encode_files({"Only/Here.uasset": b"1"})}))
        _, out, _ = self.run_main("find", "Here")
        self.assertIn("0 matches", out)

    def test_find_shows_at_most_50_matches(self):
        self.make_game_pak(files={f"ManorLords/Content/Many/Item{i:03d}.uasset": b"1" for i in range(60)})
        _, out, _ = self.run_main("find", "Many")
        self.assertEqual(sum(1 for line in out.splitlines() if "Many/Item" in line), 50)
        self.assertIn("60 matches", out)

    def test_dry_run_runs_no_tool_and_writes_no_cache(self):
        self.make_game_pak()
        self.run_main("--dry-run", "find", "DT_")
        self.assertEqual(self.log_entries(), [])
        self.assertFalse((self.work / ".index-cache").exists())


class ExtractTests(PakTestCase):
    def test_extract_writes_uasset_and_uexp_in_the_internal_layout(self):
        self.make_game_pak()
        code, out, _ = self.run_main("extract", ASSET)
        self.assertEqual(code, 0, out)
        base = self.work / "extracted" / ASSET
        self.assertEqual(base.with_suffix(".uasset").read_bytes(), UASSET_BYTES)
        self.assertEqual(base.with_suffix(".uexp").read_bytes(), UEXP_BYTES)
        self.assertFalse(base.with_suffix(".ubulk").exists())

    def test_extract_takes_optional_ubulk(self):
        self.make_game_pak(files={ASSET + ".uasset": b"a", ASSET + ".uexp": b"e", ASSET + ".ubulk": b"\x00\xffbulk"})
        self.run_main("extract", ASSET + ".uasset")
        self.assertEqual((self.work / "extracted" / (ASSET + ".ubulk")).read_bytes(), b"\x00\xffbulk")

    def test_extract_of_a_missing_asset_is_an_error(self):
        self.make_game_pak()
        code, _, err = self.run_main("extract", "ManorLords/Content/Nope/Missing")
        self.assertEqual(code, 1)
        self.assertIn("asset not found in any game pak", err)

    def test_extract_dry_run_writes_nothing(self):
        self.make_game_pak()
        self.run_main("--dry-run", "extract", ASSET)
        self.assertFalse((self.work / "extracted").exists())
        self.assertEqual(self.log_entries(), [])

    def test_extract_from_an_encrypted_pak_uses_the_key_from_the_environment(self):
        self.make_game_pak(key=KEY)
        self.write_config(aes_key_env=KEY_ENV)
        os.environ[KEY_ENV] = KEY
        code, _, _ = self.run_main("extract", ASSET)
        self.assertEqual(code, 0)
        self.assertTrue(all(e["key_seen"] for e in self.log_entries("repak")))

    def test_missing_key_variable_is_a_clear_error(self):
        self.make_game_pak(key=KEY)
        self.write_config(aes_key_env=KEY_ENV)
        code, _, err = self.run_main("extract", ASSET)
        self.assertEqual(code, 1)
        self.assertIn(KEY_ENV, err)


class AesKeySecrecyTests(PakTestCase):
    def test_the_key_never_appears_in_output_dry_run_errors_or_files(self):
        self.make_game_pak(key=KEY)
        self.write_config(aes_key_env=KEY_ENV)
        os.environ[KEY_ENV] = KEY
        outputs = [self.run_main("check"), self.run_main("find", "DT_"), self.run_main("extract", ASSET)]
        self.make_assets()
        outputs.append(self.run_main("--dry-run", "build", "demo"))
        os.environ["FAKE_REPAK_MODE"] = "fail"
        shutil.rmtree(self.work / ".index-cache")
        failing = self.run_main("find", "DT_")
        self.assertEqual(failing[0], 1)
        self.assertIn("failed, my arguments were", failing[2])  # the tool did echo the key to its stderr
        outputs.append(failing)
        for code, out, err in outputs:
            self.assertNotIn(KEY, out)
            self.assertNotIn(KEY, err)
        for path in [self.config_path, self.log, *self.work.rglob("*")]:
            if path.is_file():
                self.assertNotIn(KEY, path.read_text(errors="replace"), str(path))

    def test_dry_run_shows_the_command_with_a_masked_key(self):
        self.write_config(aes_key_env=KEY_ENV)
        os.environ[KEY_ENV] = KEY
        self.make_assets()
        _, out, _ = self.run_main("--dry-run", "build", "demo")
        self.assertIn("--aes-key", out)
        self.assertIn("***", out)


class ConvertTests(PakTestCase):
    def extract(self):
        self.make_game_pak()
        self.run_main("extract", ASSET)

    def test_tojson_writes_a_json_file_inside_the_work_folder(self):
        self.extract()
        code, out, _ = self.run_main("tojson", ASSET + ".uasset")
        self.assertEqual(code, 0, out)
        target = self.work / "json" / (ASSET + ".json")
        document = json.loads(target.read_text())
        self.assertEqual((document["engine"], document["usmap"]), ("5.5", "game.usmap"))
        self.assertEqual(self.log_entries("uassetgui")[0]["args"][0], "tojson")

    def test_fromjson_writes_the_asset_and_can_target_a_build_folder(self):
        self.extract()
        self.run_main("tojson", ASSET + ".uasset")
        code, out, _ = self.run_main("fromjson", ASSET + ".json", "--to", "demo")
        self.assertEqual(code, 0, out)
        target = self.work / "demo" / (ASSET + ".uasset")
        self.assertEqual(target.read_bytes(), UASSET_BYTES)

    def test_fromjson_default_target_is_the_fromjson_folder(self):
        self.extract()
        self.run_main("tojson", ASSET + ".uasset")
        self.run_main("fromjson", str(self.work / "json" / (ASSET + ".json")))
        self.assertTrue((self.work / "fromjson" / (ASSET + ".uasset")).is_file())

    def test_fromjson_refuses_a_reserved_target_name(self):
        self.extract()
        self.run_main("tojson", ASSET + ".uasset")
        code, _, err = self.run_main("fromjson", ASSET + ".json", "--to", "out")
        self.assertEqual(code, 1)
        self.assertIn("reserved", err)

    def test_tool_failure_is_reported_with_its_message(self):
        self.extract()
        os.environ["FAKE_UASSET_MODE"] = "fail"
        code, _, err = self.run_main("tojson", ASSET + ".uasset")
        self.assertEqual(code, 1)
        self.assertIn("exit code 5", err)
        self.assertIn("cannot parse the asset", err)

    def test_tool_timeout_is_reported(self):
        self.extract()
        os.environ["FAKE_UASSET_MODE"] = "sleep"
        with mock.patch.object(pakmod, "UASSETGUI_TIMEOUT_S", 1):
            code, _, err = self.run_main("tojson", ASSET + ".uasset")
        self.assertEqual(code, 1)
        self.assertIn("did not finish", err)

    def test_missing_or_empty_output_is_an_error(self):
        self.extract()
        for mode in ("nofile", "empty"):
            with self.subTest(mode=mode):
                os.environ["FAKE_UASSET_MODE"] = mode
                code, _, err = self.run_main("tojson", ASSET + ".uasset")
                self.assertEqual(code, 1)
                self.assertIn("wrote no usable file", err)

    def test_no_shell_and_a_time_limit_are_used(self):
        self.extract()
        with mock.patch.object(pakmod.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, b"", b"")) as run:
            pakmod.main(["--config", str(self.config_path), "tojson", ASSET + ".uasset"])
        self.assertIsInstance(run.call_args.args[0], list)
        self.assertFalse(run.call_args.kwargs["shell"])
        self.assertEqual(run.call_args.kwargs["timeout"], pakmod.UASSETGUI_TIMEOUT_S)

    def test_a_missing_usmap_is_an_error(self):
        self.extract()
        self.usmap.unlink()
        code, _, err = self.run_main("tojson", ASSET + ".uasset")
        self.assertEqual(code, 1)
        self.assertIn("usmap file not found", err)

    def test_a_template_in_the_config_replaces_the_default(self):
        self.extract()
        self.write_config(templates={"tojson": ["tojson", "{source}", "{destination}", "{engine_version}", "{usmap}", "--extra"]})
        os.environ["FAKE_UASSET_MODE"] = "ok"
        code, _, err = self.run_main("tojson", ASSET + ".uasset")
        self.assertEqual(code, 1)  # the fake rejects the extra argument: the template was used
        self.assertIn("bad arguments", err)

    def test_dry_run_changes_nothing(self):
        self.extract()
        before = self.log_entries()
        self.run_main("--dry-run", "tojson", ASSET + ".uasset")
        self.run_main("--dry-run", "roundtrip", ASSET)
        self.assertEqual(self.log_entries(), before)
        self.assertFalse((self.work / "json").exists())


class RoundtripTests(PakTestCase):
    def test_equal_roundtrip_extracts_first_if_needed(self):
        self.make_game_pak()
        code, out, _ = self.run_main("roundtrip", ASSET)
        self.assertEqual(code, 0, out)
        self.assertIn(".uasset: equal", out)
        self.assertIn(".uexp: equal", out)
        self.assertIn("roundtrip: equal", out)

    def test_lossy_roundtrip_reports_the_first_differing_offset_with_exit_code_0(self):
        self.make_game_pak()
        os.environ["FAKE_UASSET_LOSSY"] = "1"
        code, out, _ = self.run_main("roundtrip", ASSET)
        self.assertEqual(code, 0)
        self.assertIn(f".uasset: DIFFERENT, original {len(UASSET_BYTES)} bytes, new {len(UASSET_BYTES)} bytes, first difference at offset 3", out)
        self.assertIn(".uexp: equal", out)
        self.assertIn("roundtrip: different", out)

    def test_compare_files_reports_a_length_difference(self):
        a, b = self.tmp / "a", self.tmp / "b"
        a.write_bytes(b"abcd")
        b.write_bytes(b"ab")
        result = pakmod.compare_files(a, b)
        self.assertEqual((result["equal"], result["first_diff"]), (False, 2))


class BuildTests(PakTestCase):
    def test_build_packs_the_folder_with_the_mount_point_and_version(self):
        self.make_assets()
        output = pakmod.build(self.config(), "demo")
        self.assertEqual(output, self.work / "out" / "demo_P.pak")
        pak = json.loads(output.read_text())
        self.assertEqual((pak["mount"], pak["version"]), ("../../../", "V11"))
        self.assertEqual(list(pak["files"]), ["ManorLords/Content/Data/DT_Items.uasset"])

    def test_pak_version_and_mount_point_come_from_the_config(self):
        self.write_config(pak_version="V9", mount_point="../")
        self.make_assets()
        pak = json.loads(pakmod.build(self.config(), "demo").read_text())
        self.assertEqual((pak["mount"], pak["version"]), ("../", "V9"))

    def test_output_always_has_the_priority_suffix(self):
        self.make_assets("abc")
        self.assertTrue(pakmod.build(self.config(), "abc").name.endswith("_P.pak"))

    def test_build_verifies_the_pak_with_list(self):
        self.make_assets()
        pakmod.build(self.config(), "demo")
        self.assertEqual(len(self.log_entries("repak", "list")), 1)

    def test_a_pak_that_misses_a_file_is_reported_with_exit_code_4(self):
        self.make_assets("demo", b"a")
        extra = self.work / "demo" / "ManorLords" / "Content" / "Data" / "Zzz.uasset"
        extra.write_bytes(b"b")
        os.environ["FAKE_REPAK_MODE"] = "drop"
        code, _, err = self.run_main("build", "demo")
        self.assertEqual(code, 4)
        self.assertIn("missing in the pak: ManorLords/Content/Data/Zzz.uasset", err)

    def test_pack_failure_timeout_and_missing_output(self):
        self.make_assets()
        for mode, text in (("fail", "exit code 7"), ("nofile", "wrote no pak")):
            with self.subTest(mode=mode):
                os.environ["FAKE_REPAK_MODE"] = mode
                code, _, err = self.run_main("build", "demo")
                self.assertEqual(code, 1)
                self.assertIn(text, err)
        os.environ["FAKE_REPAK_MODE"] = "sleep"
        with mock.patch.object(pakmod, "PACK_TIMEOUT_S", 1):
            self.assertIn("did not finish", self.run_main("build", "demo")[2])

    def test_dry_run_changes_nothing(self):
        self.make_assets()
        self.run_main("--dry-run", "build", "demo")
        self.assertFalse((self.work / "out").exists())
        self.assertEqual(self.log_entries(), [])


class InstallRemoveTests(PakTestCase):
    def test_install_copies_and_records_the_hash(self):
        target = self.build_and_install()
        self.assertEqual(target, self.mods / "demo_P.pak")
        manifest = json.loads((self.mods / pakmod.MANIFEST_NAME).read_text())
        self.assertEqual(manifest["files"], {"demo_P.pak": pakmod.sha256_of(target)})
        self.assertTrue(manifest["created_dir"])

    def test_install_dry_run_changes_nothing(self):
        self.make_assets()
        pakmod.build(self.config(), "demo")
        pakmod.install(self.work, self.game, "demo", dry_run=True)
        self.assertFalse(self.mods.exists())

    def test_install_before_build_is_refused(self):
        with self.assertRaisesRegex(pakmod.PakModError, "not built"):
            pakmod.install(self.work, self.game, "demo")

    def test_install_refuses_to_overwrite_a_foreign_pak(self):
        self.make_assets()
        pakmod.build(self.config(), "demo")
        self.mods.mkdir(parents=True)
        foreign = self.mods / "demo_P.pak"
        foreign.write_bytes(b"user file")
        with self.assertRaisesRegex(pakmod.PakModError, "not in the harness manifest"):
            pakmod.install(self.work, self.game, "demo")
        self.assertEqual(foreign.read_bytes(), b"user file")

    def test_install_can_replace_its_own_pak(self):
        self.build_and_install()
        self.make_assets(content=b"changed")
        pakmod.build(self.config(), "demo")
        target = pakmod.install(self.work, self.game, "demo")
        self.assertEqual(pakmod.read_manifest(self.mods)["files"]["demo_P.pak"], pakmod.sha256_of(target))

    def test_remove_deletes_only_manifest_files_and_the_empty_folder(self):
        self.build_and_install()
        self.assertEqual(pakmod.remove(self.game, ["demo"]), 0)
        self.assertFalse(self.mods.exists())

    def test_remove_keeps_other_files_and_a_folder_the_user_made(self):
        self.mods.mkdir(parents=True)
        other = self.mods / "other_P.pak"
        other.write_bytes(b"user")
        self.build_and_install()
        pakmod.remove(self.game, None)
        self.assertEqual(other.read_bytes(), b"user")
        self.assertEqual(sorted(p.name for p in self.mods.iterdir()), ["other_P.pak"])

    def test_remove_all_with_two_paks(self):
        self.build_and_install("one")
        self.build_and_install("two")
        pakmod.remove(self.game, None)
        self.assertFalse(self.mods.exists())

    def test_remove_refuses_a_name_that_is_not_in_the_manifest(self):
        self.mods.mkdir(parents=True)
        other = self.mods / "other_P.pak"
        other.write_bytes(b"user")
        with self.assertRaisesRegex(pakmod.PakModError, "not in the harness manifest"):
            pakmod.remove(self.game, ["other"])
        self.assertTrue(other.exists())

    def test_remove_skips_a_changed_file(self):
        target = self.build_and_install()
        target.write_bytes(b"edited by hand")
        self.assertEqual(pakmod.remove(self.game, ["demo"]), 1)
        self.assertTrue(target.exists())
        self.assertIn("demo_P.pak", pakmod.read_manifest(self.mods)["files"])

    def test_remove_refuses_a_manifest_entry_with_a_path(self):
        self.mods.mkdir(parents=True)
        victim = self.tmp / "victim.pak"
        victim.write_bytes(b"keep")
        manifest = {"version": 1, "created_dir": False, "files": {"../../victim.pak": pakmod.sha256_of(victim)}}
        pakmod.write_manifest(self.mods, manifest)
        with self.assertRaises(pakmod.PakModError):
            pakmod.remove(self.game, None)
        self.assertTrue(victim.exists())

    def test_remove_dry_run_changes_nothing(self):
        target = self.build_and_install()
        pakmod.remove(self.game, None, dry_run=True)
        self.assertTrue(target.exists())
        self.assertIn("demo_P.pak", pakmod.read_manifest(self.mods)["files"])

    def test_remove_command_needs_name_or_all(self):
        self.assertEqual(self.run_main("remove")[0], 1)

    def test_list_reports_the_state(self):
        target = self.build_and_install()
        self.assertIn(" ok ", pakmod.list_paks(self.game)[0])
        target.write_bytes(b"other")
        self.assertIn("CHANGED", pakmod.list_paks(self.game)[0])

    def test_broken_manifest_stops_the_command(self):
        self.mods.mkdir(parents=True)
        (self.mods / pakmod.MANIFEST_NAME).write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(pakmod.PakModError, "manifest is broken"):
            pakmod.list_paks(self.game)


@unittest.skipUnless(shutil.which("powershell"), "needs Windows PowerShell")
class UninstallIntegrationTests(PakTestCase):
    def setUp(self):
        super().setUp()
        mods = self.game / "ManorLords" / "Binaries" / "Win64" / "ue4ss" / "Mods"
        mods.mkdir(parents=True)
        (mods / "mods.txt").write_text("Keybinds : 1\n", encoding="utf-8")

    def uninstall(self, *flags):
        command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(UNINSTALL), "-GameDir", str(self.game), *flags]
        return subprocess.run(command, capture_output=True, text=True, timeout=120)

    def test_remove_deletes_the_harness_pak_and_keeps_others(self):
        self.mods.mkdir(parents=True)
        other = self.mods / "other_P.pak"
        other.write_bytes(b"user")
        self.build_and_install()
        done = self.uninstall("-Remove")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertFalse((self.mods / "demo_P.pak").exists())
        self.assertFalse((self.mods / pakmod.MANIFEST_NAME).exists())
        self.assertEqual(other.read_bytes(), b"user")

    def test_remove_deletes_the_folder_that_the_harness_made(self):
        self.build_and_install()
        self.assertEqual(self.uninstall("-Remove").returncode, 0)
        self.assertFalse(self.mods.exists())

    def test_dry_run_and_default_mode_keep_the_pak(self):
        target = self.build_and_install()
        self.assertEqual(self.uninstall("-Remove", "-DryRun").returncode, 0)
        self.assertEqual(self.uninstall().returncode, 0)
        self.assertTrue(target.exists())
        self.assertTrue((self.mods / pakmod.MANIFEST_NAME).exists())

    def test_changed_pak_is_kept(self):
        target = self.build_and_install()
        target.write_bytes(b"edited")
        self.assertEqual(self.uninstall("-Remove").returncode, 0)
        self.assertTrue(target.exists())
        self.assertTrue((self.mods / pakmod.MANIFEST_NAME).exists())

    def test_manifest_entry_with_a_path_is_refused(self):
        self.mods.mkdir(parents=True)
        victim = self.tmp / "victim.pak"
        victim.write_bytes(b"keep")
        manifest = {"version": 1, "created_dir": False, "files": {"..\\..\\..\\..\\victim.pak": pakmod.sha256_of(victim)}}
        pakmod.write_manifest(self.mods, manifest)
        done = self.uninstall("-Remove")
        self.assertNotEqual(done.returncode, 0)
        self.assertTrue(victim.exists())

    def test_no_pak_manifest_is_fine(self):
        self.assertEqual(self.uninstall("-Remove").returncode, 0)


if __name__ == "__main__":
    unittest.main()
