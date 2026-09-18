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
            "game-letters",
            "game-shapes",
            "game-counting",
            "game-body",
            "game-runner",
            "game-music",
            "game-beat",
            "game-dance",
            "game-bells",
        ):
            self.assertIn(f'id="{game_id}"', HTML)

    def test_learning_lab_games_are_in_the_game_picker(self) -> None:
        for game, nav_id in (
            ("letters", "navLetters"),
            ("shapes", "navShapes"),
            ("counting", "navCounting"),
            ("body", "navBody"),
            ("runner", "navRunner"),
        ):
            self.assertIn(f"switchGame('{game}', this)", HTML)
            self.assertIn(f'id="{nav_id}"', HTML)
            self.assertIn(f"gameId === '{game}'", HTML)

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

    def test_letter_garden_is_spoken_multilingual_and_icon_led(self) -> None:
        letter_source = HTML[HTML.index("const letterSets = {"):HTML.index("const learningColors = [")]
        self.assertGreaterEqual(letter_source.count("{letter:"), 24)
        for language in ("en:", "es:", "fr:", "el:"):
            self.assertIn(language, letter_source)
        self.assertIn("letterSets.enUS = letterSets.en.map", HTML)
        self.assertIn("letterSets.esES = letterSets.es.map", HTML)
        self.assertIn("speakSingle(languageSettings[language].code, phrase", HTML)
        self.assertIn("letterLanguageIndex = (letterLanguageIndex + 1)", HTML)

    def test_color_and_shape_hunt_is_adaptive_and_auto_advances(self) -> None:
        self.assertIn("const learningColors = [", HTML)
        self.assertIn("const learningShapes = [", HTML)
        self.assertIn("shapeSuccesses < 3 ? 2 : (shapeSuccesses < 7 ? 3 : 4)", HTML)
        self.assertIn("if (roundId === shapeRoundId) startShapeRound();", HTML)
        self.assertIn("shapePrompt:(color,shape)", HTML)

    def test_count_and_match_stays_within_one_to_five_and_auto_advances(self) -> None:
        self.assertIn("const target = 1 + Math.floor(Math.random() * 5)", HTML)
        self.assertIn("const candidate = 1 + Math.floor(Math.random() * 5)", HTML)
        self.assertIn("if (roundId === countingRoundId) startCountingRound();", HTML)
        self.assertIn("numbers[target - 1][language]", HTML)
        choice_height = re.search(r"\.number-choice\s*\{\s*min-height:\s*(\d+)px;", HTML)
        self.assertIsNotNone(choice_height)
        self.assertGreaterEqual(int(choice_height.group(1)), 44)

    def test_body_explorer_is_multilingual_and_teaches_related_parts(self) -> None:
        body_source = HTML[HTML.index("const bodyParts = {"):HTML.index("const spainSpanishNames = {")]
        self.assertEqual(13, len(re.findall(r"^\s{12}\w+:\s+\{", body_source, re.M)))
        for phrase in (
            "Hand · Fingers",
            "Mano · Dedos",
            "Main · Doigts",
            "Χέρι · Δάχτυλα",
            "Foot · Toes",
            "Pie · Dedos del pie",
            "Pied · Orteils",
            "Πατούσα · Δάχτυλα των ποδιών",
        ):
            self.assertIn(phrase, body_source)
        self.assertIn("part.enUS = part.en", HTML)
        self.assertIn("part.esES = part.es", HTML)

    def test_body_explorer_zoom_feedback_is_touch_friendly_and_resets(self) -> None:
        minimum_width = re.search(r"\.body-hotspot\s*\{.*?min-width:\s*(\d+)px;", HTML, re.S)
        minimum_height = re.search(r"\.body-hotspot\s*\{.*?min-height:\s*(\d+)px;", HTML, re.S)
        self.assertIsNotNone(minimum_width)
        self.assertIsNotNone(minimum_height)
        self.assertGreaterEqual(int(minimum_width.group(1)), 44)
        self.assertGreaterEqual(int(minimum_height.group(1)), 44)
        self.assertIn("bodyFigure.style.transformOrigin = `${part.x}% ${part.y}%`", HTML)
        self.assertIn("bodyStage.classList.add('focused')", HTML)
        self.assertIn("bodyLanguageIndex = (bodyLanguageIndex + 1)", HTML)
        self.assertRegex(HTML, re.compile(r"bodyFocusTimer\s*=\s*setTimeout\(\(\)\s*=>\s*\{.*?\},\s*2400\);", re.S))

    def test_surprise_game_button_never_reselects_the_current_game(self) -> None:
        self.assertIn('id="randomGameButton"', HTML)
        self.assertIn("const choices = tabs.filter(tab => tab !== currentTab)", HTML)
        self.assertIn("switchGame(gameId, nextTab)", HTML)
        self.assertIn("randomGame:'Surprise game'", HTML)
        random_button = re.search(r"\.random-game-button\s*\{.*?width:\s*(\d+)px;.*?height:\s*(\d+)px;", HTML, re.S)
        self.assertIsNotNone(random_button)
        self.assertGreaterEqual(int(random_button.group(1)), 44)
        self.assertGreaterEqual(int(random_button.group(2)), 44)

    def test_play_timer_has_quick_choices_and_survives_refresh(self) -> None:
        for minutes in (5, 10, 15, 20):
            self.assertIn(f"setPlayTimer({minutes})", HTML)
        self.assertIn("setPlayTimer(0)", HTML)
        self.assertIn("localStorage.setItem(playTimerStorageKey", HTML)
        self.assertIn("localStorage.getItem(playTimerStorageKey)", HTML)
        self.assertIn("pauseActivePlay();\n                showTimeUpOverlay();", HTML)
        for phrase in ("Play timer", "Tiempo de juego", "Temps de jeu", "Χρόνος παιχνιδιού"):
            self.assertIn(phrase, HTML)

    def test_broccoli_bounce_uses_hold_to_fly_and_restarts_after_a_crash(self) -> None:
        for phrase in (
            "runnerStage.addEventListener('pointerdown', startRunnerFlight)",
            "runnerStage.addEventListener('pointerup', stopRunnerFlight)",
            "runnerStage.addEventListener('pointercancel', stopRunnerFlight)",
            "requestAnimationFrame(runnerFrame)",
            "runnerThrusting = true",
            "runnerThrusting = false",
            "runnerCharacter.classList.add('flying')",
            "runnerCharacter.classList.add('bumped')",
            "resetRunnerRound();\n                startRunnerGame();",
        ):
            self.assertIn(phrase, HTML)
        self.assertRegex(HTML, re.compile(r"runnerRestartTimer\s*=\s*setTimeout\(\(\)\s*=>\s*\{.*?\},\s*1900\);", re.S))

    def test_broccoli_bounce_rewards_food_and_treats_rocks_as_obstacles(self) -> None:
        self.assertIn("runnerObject.innerHTML = `<span>${type === 'food' ? '🥦' : '🪨'}</span>`", HTML)
        self.assertIn("runnerScore++;", HTML)
        self.assertIn("document.getElementById('runnerCelebrationText').textContent = `🥦 +1`", HTML)
        self.assertIn("if (runnerObject.dataset.type === 'food') collectRunnerFood();", HTML)
        self.assertIn("else crashRunner();", HTML)
        self.assertIn("const speed = Math.min(180, 104 + runnerDistance * .36)", HTML)
        for phrase in ("Broccoli! One point!", "¡Brócoli! ¡Un punto!", "Brocoli ! Un point !", "Μπρόκολο! Ένας πόντος!"):
            self.assertIn(phrase, HTML)

    def test_broccoli_bounce_difficulty_unlocks_gradually_by_distance(self) -> None:
        self.assertIn("if (runnerDistance < 40) return 'food'", HTML)
        self.assertIn("runnerDistance < 100 ? .2 : (runnerDistance < 170 ? .32 : .42)", HTML)
        self.assertIn("const canFly = type === 'rock' && runnerDistance >= 110", HTML)
        self.assertIn("const lastTwoWereRocks", HTML)
        self.assertIn("runnerDistance += speed * elapsedSeconds / 18", HTML)
        self.assertIn("runnerAltitude === 0 && !runnerThrusting", HTML)

    def test_runner_localization_uses_natural_child_facing_instructions(self) -> None:
        for phrase in (
            "Catch the Broccoli",
            "Atrapa el brócoli",
            "Attrape le brocoli",
            "Πιάσε το μπρόκολο",
            "Mantén presionado para volar",
            "Maintiens appuyé pour voler",
            "Κράτα πατημένο για να πετάξεις",
        ):
            self.assertIn(phrase, HTML)
        for awkward_phrase in ("Salta por el brócoli", "Bondis vers le brocoli", "Πήδα στο μπρόκολο"):
            self.assertNotIn(awkward_phrase, HTML)
        self.assertIn("translate the child-facing intent into natural everyday speech", HTML)

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
