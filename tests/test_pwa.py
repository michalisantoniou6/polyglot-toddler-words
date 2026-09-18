import json
import re
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
SERVICE_WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
MANIFEST = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"{path} is not a PNG")
    return struct.unpack(">II", data[16:24])


class ProgressiveWebAppTests(unittest.TestCase):
    def test_page_exposes_installable_app_metadata(self) -> None:
        self.assertIn('<link rel="manifest" href="manifest.webmanifest">', HTML)
        self.assertIn('<meta name="theme-color" content="#3182ce">', HTML)
        self.assertIn('<meta name="apple-mobile-web-app-capable" content="yes">', HTML)
        self.assertIn('<link rel="apple-touch-icon" href="icons/icon-180.png">', HTML)

    def test_manifest_has_installable_github_pages_safe_configuration(self) -> None:
        self.assertEqual("Toddler Arcade", MANIFEST["name"])
        self.assertEqual("./", MANIFEST["id"])
        self.assertEqual("./", MANIFEST["start_url"])
        self.assertEqual("./", MANIFEST["scope"])
        self.assertEqual("standalone", MANIFEST["display"])
        self.assertEqual({"192x192", "512x512"}, {icon["sizes"] for icon in MANIFEST["icons"]})
        self.assertTrue(any(icon.get("purpose") == "maskable" for icon in MANIFEST["icons"]))

    def test_icons_have_the_dimensions_declared_by_the_manifest(self) -> None:
        self.assertEqual((180, 180), png_dimensions(ROOT / "icons/icon-180.png"))
        self.assertEqual((192, 192), png_dimensions(ROOT / "icons/icon-192.png"))
        self.assertEqual((512, 512), png_dimensions(ROOT / "icons/icon-512.png"))
        self.assertEqual((512, 512), png_dimensions(ROOT / "icons/icon-maskable-512.png"))

    def test_service_worker_is_registered_only_on_supported_web_origins(self) -> None:
        self.assertIn("'serviceWorker' in navigator", HTML)
        self.assertIn("location.protocol === 'https:'", HTML)
        self.assertIn("navigator.serviceWorker.register('./service-worker.js')", HTML)
        self.assertIn("await registration.update()", HTML)

    def test_complete_game_shell_is_precached_for_offline_play(self) -> None:
        for path in (
            "./index.html",
            "./manifest.webmanifest",
            "./icons/icon-192.png",
            "./icons/icon-512.png",
            "./assets/santa-ho-ho-ho.mp3?v=2",
        ):
            self.assertIn(f"'{path}'", SERVICE_WORKER)
        self.assertIn("cache.addAll(APP_SHELL)", SERVICE_WORKER)
        self.assertIn("request.mode === 'navigate'", SERVICE_WORKER)
        self.assertIn("networkFirstNavigation(request)", SERVICE_WORKER)
        self.assertRegex(SERVICE_WORKER, re.compile(r"catch \(error\).*cache\.match", re.S))


if __name__ == "__main__":
    unittest.main()
