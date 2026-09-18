import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
HTML = INDEX.read_text(encoding="utf-8")


def constant_number(name: str) -> float:
    match = re.search(rf"const\s+{re.escape(name)}\s*=\s*([\d.]+);", HTML)
    if match is None:
        raise AssertionError(f"Missing numeric constant: {name}")
    return float(match.group(1))


def array_source(name: str) -> str:
    match = re.search(rf"const\s+{re.escape(name)}\s*=\s*\[(.*?)\n\s*\];", HTML, re.S)
    if match is None:
        raise AssertionError(f"Missing array: {name}")
    return match.group(1)


class IdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name == "id" and value:
                self.ids.append(value)


class AppRegressionTests(unittest.TestCase):
    def test_document_has_unique_ids_and_core_games(self) -> None:
        parser = IdCollector()
        parser.feed(HTML)
        duplicates = sorted({element_id for element_id in parser.ids if parser.ids.count(element_id) > 1})
        self.assertEqual([], duplicates)
        for game_id in (
            "game-monster",
            "game-trucks",
            "game-balloons",
            "game-animals",
            "game-everyday",
            "game-music",
            "game-beat",
            "game-dance",
            "game-bells",
        ):
            self.assertIn(f'id="{game_id}"', HTML)

    def test_english_and_balloon_pop_are_the_defaults(self) -> None:
        self.assertRegex(HTML, r"let\s+currentLangMode\s*=\s*'en';")
        self.assertRegex(HTML, r'id="game-balloons"\s+class="game-view active"')
        self.assertIn("spawnBalloon(true);", HTML)

    def test_saved_profile_versions_are_loaded_after_refresh(self) -> None:
        self.assertIn("[1, 2].includes(savedProfile?.schemaVersion)", HTML)
        self.assertIn("return normalizedProfile;", HTML)
        self.assertIn("localStorage.setItem(appProfileStorageKey, JSON.stringify(appProfile))", HTML)
        self.assertIn("onboardingComplete: true", HTML)

    def test_profiles_affected_by_the_v2_loader_bug_are_recovered(self) -> None:
        self.assertIn("savedProfile.schemaVersion === 2", HTML)
        self.assertIn("!normalizedProfile.onboardingComplete && hasSavedNames", HTML)
        self.assertIn("normalizedProfile.onboardingComplete = true", HTML)

    def test_onboarding_language_states_are_clear_and_localized(self) -> None:
        for phrase in (
            "Which languages should your child hear?",
            "Ποιες γλώσσες θέλεις να ακούει το παιδί;",
            "¿Qué idiomas quieres que escuche tu peque?",
            "Quelles langues veux-tu que ton enfant entende ?",
            "languageMain:",
            "languageOn:",
            "languageOff:",
            "onboardingLanguageSummary",
        ):
            self.assertIn(phrase, HTML)
        self.assertIn("onboardingCopy.enUS = { ...onboardingCopy.en }", HTML)
        self.assertIn("onboardingCopy.esES = { ...onboardingCopy.es }", HTML)

    def test_primary_language_is_first_in_all_languages_mode(self) -> None:
        ordering_pattern = re.compile(
            r"allLanguageOrder\s*=\s*\[\s*"
            r"appProfile\.primaryLanguage,\s*"
            r"\.\.\.supportedLanguageOrder\.filter\(language\s*=>\s*"
            r"language\s*!==\s*appProfile\.primaryLanguage\s*&&\s*"
            r"enabledLanguages\.includes\(language\)\)\s*\];"
        )
        self.assertGreaterEqual(len(ordering_pattern.findall(HTML)), 2)

    def test_feed_santa_uses_four_rows_with_large_tap_targets(self) -> None:
        self.assertRegex(HTML, r"\.food-grid\s*\{\s*--food-row-count:\s*4;")
        self.assertIn("repeat(var(--food-row-count), minmax(70px, 1fr))", HTML)
        self.assertGreaterEqual(len(re.findall(r'\{ emoji: "', array_source("foods"))), 24)
        minimum_height = re.search(r"\.food-item\s*\{.*?min-height:\s*(\d+)px;", HTML, re.S)
        self.assertIsNotNone(minimum_height)
        self.assertGreaterEqual(int(minimum_height.group(1)), 44)

    def test_feed_santa_supports_both_dragging_and_tapping(self) -> None:
        for behavior in (
            "pointerdown",
            "pointermove",
            "pointerup",
            "isFoodNearSanta",
            "feedMonster(state.food)",
            "feedMonster(f)",
        ):
            self.assertIn(behavior, HTML)

    def test_santa_laugh_is_short_local_preloaded_audio(self) -> None:
        audio_path = ROOT / "assets" / "santa-ho-ho-ho.mp3"
        self.assertTrue(audio_path.is_file())
        audio = audio_path.read_bytes()
        self.assertGreater(len(audio), 20_000)
        self.assertLess(len(audio), 150_000)
        self.assertTrue(audio.startswith(b"ID3") or audio[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"))
        self.assertIn('href="assets/santa-ho-ho-ho.mp3?v=2" as="audio"', HTML)
        self.assertRegex(
            HTML,
            r"clip\('assets/santa-ho-ho-ho\.mp3\?v=2'.*?'CC0'.*?,\s*0,\s*2\.7\)",
        )
        self.assertIn("profileName === 'santaLaugh' ? 1 : 0.58", HTML)

    def test_dance_and_freeze_has_time_for_real_dancing(self) -> None:
        self.assertGreaterEqual(constant_number("danceMoveDurationMilliseconds"), 7_000)
        self.assertGreaterEqual(constant_number("danceFreezeDurationMilliseconds"), 1_800)
        self.assertLessEqual(constant_number("danceFreezeDurationMilliseconds"), 3_500)
        self.assertGreaterEqual(constant_number("danceLeaderDurationMilliseconds"), 5_000)
        self.assertIn("setTimeout(runDanceMove, danceFreezeDurationMilliseconds)", HTML)
        self.assertIn("}, danceMoveDurationMilliseconds);", HTML)

    def test_balloon_difficulty_progresses_to_twenty(self) -> None:
        levels = array_source("balloonLevels")
        maximums = [int(value) for value in re.findall(r"max:\s*(\d+)", levels)]
        spawn_times = [int(value) for value in re.findall(r"spawnMs:\s*(\d+)", levels)]
        travel_times = [float(value) for value in re.findall(r"minTravelSeconds:\s*([\d.]+)", levels)]
        self.assertEqual([5, 8, 10, 15, 20], maximums)
        self.assertEqual(sorted(spawn_times, reverse=True), spawn_times)
        self.assertEqual(sorted(travel_times, reverse=True), travel_times)
        self.assertIn("Math.min(45, balloonSuccessfulPops + 1)", HTML)

    def test_everyday_find_it_uses_articles_and_advances_automatically(self) -> None:
        everyday = array_source("everydayItems")
        self.assertIn("elPrompt:'το καλαμάκι'", everyday)
        self.assertIn("esPrompt:'el popote'", everyday)
        self.assertIn("frPrompt:'la paille'", everyday)
        self.assertIn("if (roundId === findRoundId) startFindRound();", HTML)
        self.assertNotIn('id="findNextButton"', HTML)

    def test_regional_spanish_vocabulary_stays_distinct(self) -> None:
        self.assertRegex(HTML, r'en:\s*"Pig",\s*es:\s*"Cochino"')
        self.assertIn("Pig:'Cerdo'", HTML)
        self.assertRegex(HTML, r"en:'Straw',\s*es:'Popote'")
        self.assertIn("Straw:'Pajita'", HTML)

    def test_browser_back_restores_the_previous_game_state(self) -> None:
        self.assertIn("history.pushState(nextState, '')", HTML)
        self.assertIn("window.addEventListener('popstate'", HTML)
        self.assertIn("applyNavigationState(event.state)", HTML)

    def test_spoken_text_strips_commas(self) -> None:
        self.assertIn("const speechText = text.replace(/,/g, '')", HTML)


if __name__ == "__main__":
    unittest.main()
