import os
import tempfile
import unittest
from pathlib import Path

from src.dotpaw.dotpaw import env, load, get, multi, save


class DotPawParsingTests(unittest.TestCase):
    def test_parse_set_without_forced_type(self):
        config = load("test.paw", use_env_overrides=False)

        self.assertIsInstance(config["list"]["values"], list)
        self.assertIsInstance(config["set"]["values"], set)
        self.assertIsInstance(config["dict"]["values"], dict)
        self.assertIsInstance(config["tuple"]["values"], tuple)
        self.assertEqual(config["list"]["values"], [1, 2, 3])
        self.assertEqual(config["set"]["values"], {1, 2, 3})
        self.assertEqual(config["dict"]["values"], {'1': 'a', '2': 'b', '3': 'c'})
        self.assertEqual(config["tuple"]["values"], (1, 2, 3))

    def test_parse_nested_values(self):
        config = load("test.paw", use_env_overrides=False)

        self.assertEqual(get("app.name", config), "MyWebsite")
        self.assertEqual(get("app.debug", config), True)
        self.assertEqual(get("app.port", config), 8080)
        self.assertEqual(get("db.host", config), "localhost")
        self.assertEqual(get("db.port", config), 5432)

    def test_parse_explicit_container_types(self):
        paw_text = """\
list.values: [1, 2, 3] [list]
set.values: {1, 2, 3} [set]
tuple.values: (1, 2, 3) [tuple]
dict.values: {'a': 1, 'b': 2} [dict]
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "explicit.paw"
            path.write_text(paw_text)
            config = load(str(path), use_env_overrides=False)

        self.assertEqual(config["list"]["values"], [1, 2, 3])
        self.assertEqual(config["set"]["values"], {1, 2, 3})
        self.assertEqual(config["tuple"]["values"], (1, 2, 3))
        self.assertEqual(config["dict"]["values"], {"a": 1, "b": 2})

    def test_env_override_uses_path_based_key(self):
        paw_text = "app.debug: false [bool]\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "override.paw"
            path.write_text(paw_text)
            os.environ["APP_DEBUG"] = "true"
            try:
                config = load(str(path), use_env_overrides=True)
            finally:
                del os.environ["APP_DEBUG"]

        self.assertEqual(config["app"]["debug"], True)

    def test_multi_merges_multiple_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path1 = Path(temp_dir) / "base.paw"
            path2 = Path(temp_dir) / "override.paw"
            path1.write_text("app.name: Base\napp.port: 8000 [int]\n")
            path2.write_text("app.port: 9000 [int]\ndb.host: localhost\n")
            config = multi([str(path1), str(path2)], use_env_overrides=False)

        self.assertEqual(config["app"]["name"], "Base")
        self.assertEqual(config["app"]["port"], 9000)
        self.assertEqual(config["db"]["host"], "localhost")

    def test_save_writes_nested_keys(self):
        nested = {
            "app": {"name": "SavedApp", "port": 8001},
            "db": {"host": "127.0.0.1", "ports": [5432, 5433]},
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "saved.paw"
            save(str(path), nested)
            contents = path.read_text()

        self.assertIn("app.name: SavedApp", contents)
        self.assertIn("db.ports: 5432, 5433", contents)

    def test_get_returns_default_for_missing_value(self):
        self.assertEqual(get("missing.key", {}, default="fallback"), "fallback")

    def test_env_function_exports_to_environment(self):
        paw_text = "service.name: example\nservice.port: 1234 [int]\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "export.paw"
            path.write_text(paw_text)
            env(str(path))

            self.assertEqual(os.environ.get("SERVICE_NAME"), "example")
            self.assertEqual(os.environ.get("SERVICE_PORT"), "1234")

            del os.environ["SERVICE_NAME"]
            del os.environ["SERVICE_PORT"]


if __name__ == "__main__":
    unittest.main()
