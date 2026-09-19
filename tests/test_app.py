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

    def test_us_english_and_age_three_balloon_game_are_the_defaults(self) -> None:
        self.assertIn('<html lang="en-US" translate="no"', HTML)
        self.assertRegex(HTML, r"let\s+currentLangMode\s*=\s*'enUS';")
        self.assertIn("return 'enUS';", HTML)
        self.assertIn("primaryLanguage: preferredFirstRunLanguage()", HTML)
        self.assertIn('<option value="enUS" selected>', HTML)
        self.assertRegex(HTML, r'class="lang-pill active"[^>]+data-language="enUS"')
        self.assertRegex(HTML, r'id="game-balloons"\s+class="game-view active"')
        self.assertRegex(HTML, r'class="nav-tab active"[^>]+aria-selected="true"[^>]+switchGame\(\'balloons\', this\)')
        self.assertIn('<span id="collapsedGameIcon" aria-hidden="true">🎈</span>', HTML)
        self.assertIn("spawnBalloon(true);", HTML)

    def test_first_run_uses_device_locale_without_skipping_onboarding(self) -> None:
        self.assertIn("function preferredFirstRunLanguage()", HTML)
        self.assertIn("navigator.languages", HTML)
        self.assertIn("locale === 'es-mx'", HTML)
        self.assertIn("locale.startsWith('en-gb')", HTML)
        self.assertIn("window.applyInstalledOnboardingLanguage = language =>", HTML)
        self.assertIn("onboardingComplete: false", HTML)
        self.assertIn("primaryLanguage: language", HTML)
        self.assertIn("persistAppProfile();", HTML)
        self.assertIn("openOnboarding(false);", HTML)

    def test_saved_profile_versions_are_loaded_after_refresh(self) -> None:
        self.assertIn("[1, 2, 3, 4, 5].includes(savedProfile?.schemaVersion)", HTML)
        self.assertIn("schemaVersion: 5", HTML)
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
            "addLanguage:",
            "localeHint:",
            "onboardingLanguageSummary",
        ):
            self.assertIn(phrase, HTML)
        self.assertIn("onboardingCopy.enUS = { ...onboardingCopy.en }", HTML)
        self.assertIn("onboardingCopy.esES = { ...onboardingCopy.es }", HTML)

    def test_onboarding_language_picker_scales_without_long_card_lists(self) -> None:
        self.assertIn('id="onboardingPrimarySelect"', HTML)
        self.assertIn('id="onboardingAddLanguageSelect"', HTML)
        self.assertIn('id="onboardingSelectedLanguages"', HTML)
        self.assertIn("function renderOnboardingLanguagePicker(copy)", HTML)
        self.assertIn("function populateOnboardingPrimaryOptions()", HTML)
        self.assertIn("supportedLanguageOrder.forEach(language =>", HTML)
        self.assertIn("populateOnboardingPrimaryOptions();", HTML)
        self.assertIn("function addOnboardingLanguage(language)", HTML)
        self.assertIn("function removeOnboardingLanguage(language)", HTML)
        self.assertNotIn('data-primary-language=', HTML)
        self.assertNotIn('data-enabled-language=', HTML)

    def test_new_profiles_begin_with_only_the_locale_matched_primary_language(self) -> None:
        self.assertGreaterEqual(HTML.count("enabledLanguages: [preferredFirstRunLanguage()]"), 2)

    def test_onboarding_collects_age_and_chooses_an_age_based_first_game(self) -> None:
        for age in (2, 3, 4, 5):
            self.assertIn(f'data-child-age="{age}"', HTML)
            self.assertIn(f"chooseOnboardingAge({age})", HTML)
        self.assertIn("const childAge = [2, 3, 4, 5].includes", HTML)
        self.assertIn("childAge,", HTML)
        self.assertIn("const defaultGamesByAge = Object.freeze({ 2:'animals', 3:'balloons', 4:'runner', 5:'runner' })", HTML)
        self.assertIn("activateDefaultGameForAge();", HTML)
        self.assertIn("How old is your child?", HTML)
        self.assertIn("Πόσο χρονών είναι το παιδί;", HTML)
        self.assertIn("¿Cuántos años tiene tu peque?", HTML)
        self.assertIn("Quel âge a ton enfant ?", HTML)
        self.assertIn("onboardingStep4", HTML)
        self.assertIn("onboardingStep < 4", HTML)
        self.assertIn("childAgeConfirmed: true", HTML)
        self.assertIn("openOnboarding(false, 3, true)", HTML)
        self.assertIn("if (onboardingAgeOnly)", HTML)

    def test_every_game_has_an_age_tier_and_dice_prioritizes_the_exact_age(self) -> None:
        age_map = HTML[HTML.index("const gameMinimumAges") : HTML.index("const defaultGamesByAge")]
        for game in (
            "monster", "trucks", "balloons", "animals", "everyday", "letters", "shapes",
            "counting", "body", "runner", "icecream", "birthday", "cooking", "music",
            "beat", "dance", "bells",
        ):
            self.assertRegex(age_map, rf"\b{game}:[2345]\b")
        self.assertIn("minimumAge <= appProfile.childAge", HTML)
        self.assertIn("minimumAge === appProfile.childAge ? 4 : 1", HTML)
        self.assertIn("ageAppropriateChoices.length ? ageAppropriateChoices", HTML)

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
        self.assertIn("profileName === 'santaLaugh' || profileName === 'runnerOuch' ? 1 : 0.58", HTML)

    def test_boutique_mascots_replace_prominent_generic_emoji(self) -> None:
        for asset in ("toddler-arcade-bear.png", "toddler-arcade-santa.png"):
            path = ROOT / "assets" / asset
            self.assertTrue(path.is_file())
            self.assertGreater(path.stat().st_size, 100_000)
            self.assertIn(f'href="assets/{asset}" as="image"', HTML)

        self.assertIn("/* Boutique storybook system:", HTML)
        self.assertIn('id="monsterAvatar" type="button" onclick="tickleMonster()" aria-label="Santa Claus"><img src="assets/toddler-arcade-santa.png"', HTML)
        self.assertIn('<image href="assets/toddler-arcade-bear.png"', HTML)
        self.assertIn('class="runner-character" id="runnerCharacter" aria-hidden="true"><span class="runner-bear-emoji">🧸</span>', HTML)
        self.assertIn('function setDanceCharacterVisual(character, symbol)', HTML)

    def test_body_explorer_invitation_is_visual_instead_of_reading_dependent(self) -> None:
        self.assertIn('id="bodyTapHint" aria-hidden="true">👆</div>', HTML)
        self.assertIn("document.getElementById('bodyTapHint').textContent = '👆';", HTML)
        self.assertNotIn('👆 Tap the character', HTML)

    def test_dance_and_freeze_has_time_for_real_dancing(self) -> None:
        self.assertGreaterEqual(constant_number("danceMoveDurationMilliseconds"), 7_000)
        self.assertGreaterEqual(constant_number("danceFreezeDurationMilliseconds"), 4_500)
        self.assertLessEqual(constant_number("danceFreezeDurationMilliseconds"), 6_000)
        self.assertGreaterEqual(constant_number("danceLeaderDurationMilliseconds"), 5_000)
        self.assertIn("setTimeout(runDanceMove, danceFreezeDurationMilliseconds)", HTML)
        self.assertIn("}, danceMoveDurationMilliseconds);", HTML)

    def test_dance_and_freeze_uses_short_toddler_friendly_cues(self) -> None:
        dance_source = HTML[HTML.index("const danceMoves = ["):HTML.index("// --- Game 9: Santa's Bells ---")]
        for greek_cue in ("Χόρεψε!", "Παλαμάκια!", "Τρέξε γύρω γύρω!", "Πήδα!", "Στριφογύρισε!", "Χέρια ψηλά!", "Πάγωσε!", "Η σειρά σου!"):
            self.assertIn(greek_cue, dance_source)
        for verbose_cue in ("Freeze like a star", "Freeze tall like a tree", "Freeze tiny like a mouse", "Πάγωσε σαν", "Δείξε μας μια κίνηση", "Slowly", "Fast"):
            self.assertNotIn(verbose_cue, dance_source)
        self.assertIn("const cue = move[danceRoundLanguage];", dance_source)

    def test_letter_garden_is_spoken_multilingual_and_icon_led(self) -> None:
        letter_source = HTML[HTML.index("const letterSets = {"):HTML.index("const learningColors = [")]
        expected_counts = {"en": 26, "es": 27, "fr": 26, "el": 24}
        boundaries = {"en": "es", "es": "fr", "fr": "el"}
        for language, expected_count in expected_counts.items():
            if language == "el":
                source = letter_source[letter_source.index("            el: ["):letter_source.index("            ]\n        };")]
            else:
                next_language = boundaries[language]
                source = letter_source[letter_source.index(f"            {language}: ["):letter_source.index(f"            {next_language}: [")]
            self.assertEqual(expected_count, source.count("{letter:"), language)
        for language in ("en:", "es:", "fr:", "el:"):
            self.assertIn(language, letter_source)
        self.assertIn("{letter:'Ñ', name:'Eñe'", letter_source)
        self.assertIn("{letter:'Ω', name:'Ωμέγα'", letter_source)
        self.assertIn("letterSets.enUS = letterSets.en.map", HTML)
        self.assertIn("letterSets.esES = letterSets.es.map", HTML)
        self.assertIn("speakSingle(languageSettings[language].code, phrase", HTML)
        self.assertIn("letterLanguageIndex = (letterLanguageIndex + 1)", HTML)
        self.assertIn("body.controls-collapsed #game-letters", HTML)
        self.assertRegex(HTML, re.compile(r"#letterPrompt\s*\{.*?clip-path:inset\(50%\)", re.S))
        self.assertIn("#game-letters .letter-grid { padding-top:0; }", HTML)

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
        self.assertIn("function positionBodyHotspots()", HTML)
        self.assertIn("const [x,y,width,height] = button.dataset.bodyRegion.split(' ').map(Number)", HTML)
        self.assertIn("bodyFigure.style.transformOrigin = `${focus.focusX}px ${focus.focusY}px`", HTML)
        self.assertIn("new ResizeObserver", HTML)
        self.assertIn("bodyStage.classList.add('focused')", HTML)
        self.assertIn("bodyLanguageIndex = (bodyLanguageIndex + 1)", HTML)
        self.assertRegex(HTML, re.compile(r"bodyFocusTimer\s*=\s*setTimeout\(\(\)\s*=>\s*\{.*?\},\s*2400\);", re.S))

    def test_body_explorer_face_targets_match_the_drawing(self) -> None:
        body_markup = HTML[HTML.index('<div class="body-stage" id="bodyStage"'):HTML.index('<!-- 10. BROCCOLI BOUNCE -->')]
        self.assertEqual(2, body_markup.count('data-body-part="ears"'))
        for part, region in {
            "eyes": "140 100 120 48",
            "nose": "174 132 52 43",
            "mouth": "154 158 92 45",
        }.items():
            self.assertIn(f'data-body-part="{part}" data-body-region="{region}"', body_markup)
        self.assertNotIn('data-body-part="ears" type="button" style="left:24%;top:12%;width:52%;height:15%"', body_markup)

    def test_surprise_game_button_never_reselects_the_current_game(self) -> None:
        self.assertIn('id="randomGameButton"', HTML)
        self.assertIn("const ageAppropriateChoices = tabs.filter", HTML)
        self.assertIn("const weightedChoices = choices.flatMap", HTML)
        self.assertIn("switchGame(gameId, nextTab)", HTML)
        self.assertIn("randomGame:'Surprise game'", HTML)
        random_button = re.search(r"\.random-game-button\s*\{.*?width:\s*(\d+)px;.*?height:\s*(\d+)px;", HTML, re.S)
        self.assertIsNotNone(random_button)
        self.assertGreaterEqual(int(random_button.group(1)), 44)
        self.assertGreaterEqual(int(random_button.group(2)), 44)

    def test_one_dice_button_uses_the_adult_selected_language_mode(self) -> None:
        self.assertIn('id="randomGameButton"', HTML)
        self.assertIn('onclick="playConfiguredDiceGame()"', HTML)
        self.assertNotIn('id="randomLanguageGameButton"', HTML)
        for mode in ("single", "multilingual", "random"):
            self.assertIn(f'name="diceMode" value="{mode}"', HTML)
        self.assertIn("function playConfiguredDiceGame()", HTML)
        self.assertIn("appProfile.diceMode === 'multilingual'", HTML)
        self.assertIn("setLanguage('all')", HTML)
        self.assertIn("appProfile.diceMode === 'random'", HTML)
        self.assertIn("setLanguage(appProfile.primaryLanguage)", HTML)
        self.assertIn("diceMode: document.querySelector", HTML)

    def test_name_step_is_optional_and_anonymous_copy_stays_natural(self) -> None:
        self.assertIn('id="onboardingSkipName"', HTML)
        self.assertIn("function skipOnboardingNames()", HTML)
        self.assertIn("finishOnboarding(true)", HTML)
        self.assertIn("const hasAnyNames = onboardingDraft.greekNames.length > 0", HTML)
        self.assertIn("Object.fromEntries(supportedLanguageOrder.map(language => [language,'']))", HTML)
        self.assertIn("name ? `🎤 Your turn ${name}!` : '🎤 Your turn!'", HTML)

    def test_timer_is_only_in_parent_settings(self) -> None:
        settings = HTML[HTML.index('id="settingsModal"'):HTML.index('<!-- Header & Language Mode Selector -->')]
        quick_controls = HTML[HTML.index('<div class="quick-play-controls"'):HTML.index('<div class="play-timer-modal"')]
        self.assertIn('id="playTimerButton"', settings)
        self.assertNotIn('id="playTimerButton"', quick_controls)
        self.assertIn("timerOpenedFromSettings", HTML)

    def test_jingle_bells_has_a_santa_sleigh_cta_and_pages_invite_taps(self) -> None:
        self.assertIn('class="game-action-button jingle-sleigh-button"', HTML)
        self.assertIn('class="jingle-sleigh-art" src="assets/santa-sleigh.png"', HTML)
        self.assertIn('class="jingle-button-label visually-hidden" id="jingleButtonLabel"', HTML)
        sleigh = ROOT / "assets/santa-sleigh.png"
        self.assertTrue(sleigh.is_file())
        self.assertTrue(sleigh.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(6, sleigh.read_bytes()[25])
        self.assertIn("function inviteActiveGameClickables()", HTML)
        self.assertIn("button:not(:disabled), [data-tap-invite]", HTML)
        self.assertNotIn("button:not(:disabled), [role=\"button\"], [data-tap-invite]", HTML)
        self.assertNotIn('runner-rotate-phone', HTML)
        self.assertNotIn('@keyframes runnerRotatePhone', HTML)
        self.assertIn("prefers-reduced-motion: reduce", HTML)
        self.assertIn("randomLanguageGame:'Juego e idioma sorpresa'", HTML)
        self.assertIn("randomLanguageGame:'Παιχνίδι και γλώσσα έκπληξη'", HTML)

    def test_toddler_play_pages_hide_noninteractive_titles(self) -> None:
        for element_id in ("everydayTitle", "beatTitle", "danceTitle", "bellsTitle"):
            self.assertRegex(HTML, rf'class="learning-title visually-hidden" id="{element_id}"')
        for element_id in ("everydayPrompt", "beatPrompt", "danceTogetherNote", "bellsPrompt"):
            self.assertRegex(HTML, rf'class="[^"]*visually-hidden[^"]*" id="{element_id}"')
        self.assertIn("#game-bells .bell-keyboard { flex:1; min-height:42svh; }", HTML)

    def test_game_picker_gives_the_teddy_bear_label_breathing_room(self) -> None:
        self.assertRegex(HTML, re.compile(r"\.controls-panel \.game-picker\s*\{.*?padding:\s*16px 14px 14px;", re.S))
        self.assertRegex(HTML, re.compile(r"\.controls-panel #gamePickerLabel\s*\{.*?padding:\s*2px 6px;", re.S))

    def test_play_timer_has_quick_choices_and_survives_refresh(self) -> None:
        for minutes in (5, 10, 15, 20):
            self.assertIn(f"setPlayTimer({minutes})", HTML)
        self.assertIn("setPlayTimer(0)", HTML)
        self.assertIn("localStorage.setItem(playTimerStorageKey", HTML)
        self.assertIn("localStorage.getItem(playTimerStorageKey)", HTML)
        self.assertIn("pauseActivePlay();\n                showTimeUpOverlay();", HTML)
        for phrase in ("Play timer", "Tiempo de juego", "Temps de jeu", "Χρόνος παιχνιδιού"):
            self.assertIn(phrase, HTML)

    def test_feed_the_bear_uses_short_repeatable_boosts_and_never_stops_after_a_crash(self) -> None:
        for phrase in (
            "runnerStage.addEventListener('pointerdown', startRunnerFlight)",
            "runnerStage.addEventListener('pointerup', stopRunnerFlight)",
            "runnerStage.addEventListener('pointercancel', stopRunnerFlight)",
            "requestAnimationFrame(runnerFrame)",
            "runnerThrusting = true",
            "runnerThrusting = false",
            "runnerCharacter.classList.add('flying')",
            "animateRunnerCrash(reaction);",
            "scheduleRunnerObject(260);",
        ):
            self.assertIn(phrase, HTML)
        crash_source = HTML[HTML.index("function crashRunner()") : HTML.index("function startRunnerFlight")]
        self.assertNotIn("runnerRunning = false", crash_source)
        self.assertNotIn("cancelAnimationFrame", crash_source)
        self.assertNotIn("runnerCrashed", crash_source)
        self.assertNotIn("setTimeout", crash_source)
        self.assertIn("scheduleRunnerObject(260);", crash_source)
        frame_source = HTML[HTML.index("function runnerFrame") : HTML.index("function playRunnerChime")]
        self.assertIn("if (!runnerRunning) return", frame_source)
        self.assertIn("if (runnerRunning) runnerAnimationFrame = requestAnimationFrame(runnerFrame)", frame_source)
        self.assertIn("const runnerBoostDurationMilliseconds = 950", HTML)
        self.assertIn("if (!runnerRunning || runnerPointerHeld) return", HTML)
        self.assertIn("runnerBoostRemainingMilliseconds = runnerBoostDurationMilliseconds", HTML)
        self.assertIn("runnerBoostRemainingMilliseconds - elapsedSeconds * 1000", frame_source)
        self.assertIn("if (runnerBoostRemainingMilliseconds === 0) runnerThrusting = false", frame_source)
        stop_source = HTML[HTML.index("function stopRunnerFlight") : HTML.index("function showRunnerTutorial")]
        self.assertIn("runnerPointerHeld = false", stop_source)
        self.assertIn("runnerBoostRemainingMilliseconds = 0", stop_source)

    def test_runner_stays_one_consistent_size(self) -> None:
        for removed_mechanic in (
            "runnerFoodsPerGrowthStep",
            "runnerMaximumHeightRatio",
            "runnerMinimumScale",
            "runnerGrowthLevel",
            "growRunner",
            "shrinkRunner",
            ".runner-character.growing",
        ):
            self.assertNotIn(removed_mechanic, HTML)
        self.assertIn("const altitudeCeiling = Math.max(0, runnerStage.clientHeight * .80 - runnerBaseCharacterHeight - 12)", HTML)
        self.assertIn(".runner-bear-emoji { display:block;font-size:5.8rem", HTML)

    def test_broccoli_bounce_rewards_food_and_treats_rocks_as_obstacles(self) -> None:
        self.assertIn("runnerObject.innerHTML = `<span>${type === 'food' ? activeRunnerFood.emoji : '🪨'}</span>`", HTML)
        self.assertIn("runnerScore++;", HTML)
        self.assertIn("document.getElementById('runnerCelebrationText').textContent = `${activeRunnerFood.emoji} ⭐ ${runnerScore}`", HTML)
        self.assertIn("if (runnerObject.dataset.type === 'food') collectRunnerFood();", HTML)
        self.assertIn("else crashRunner();", HTML)
        self.assertIn("const speed = Math.min(155, 76 + runnerDistance * .24)", HTML)
        self.assertIn("const foodName = activeRunnerFood[runnerDisplayLanguage]", HTML)
        self.assertIn("{ volume: .38 }", HTML)

    def test_runner_rotates_through_fruits_and_vegetables_and_tallies_catches(self) -> None:
        food_source = array_source("runnerFoods")
        self.assertEqual(24, food_source.count("{emoji:"))
        for emoji in ("🥦", "🍅", "🥕", "🍎", "🍌", "🍓", "🍊", "🌽", "🍐", "🍇", "🍉", "🍍", "🥑", "🍒", "🍋", "🥔", "🍑", "🥭", "🫑", "🥒", "🍆", "🍠", "🥝", "🫐"):
            self.assertIn(emoji, food_source)
        self.assertIn("runnerFoods[runnerFoodIndex++ % runnerFoods.length]", HTML)
        self.assertIn("runnerScore++", HTML)
        self.assertNotIn("runnerScore++", HTML[HTML.index("else if (runnerObject.getBoundingClientRect().right"):HTML.index("function playRunnerChime")])
        self.assertIn("score === 1 ? 'One point'", HTML)
        self.assertIn("runnerCaught:(food,score)=>`${food}! ${greekPointScore(score)}!`", HTML)

    def test_greek_runner_scores_use_masculine_number_forms(self) -> None:
        self.assertIn("'τρεις'", HTML)
        self.assertIn("'τέσσερις'", HTML)
        self.assertIn("'δεκατρείς'", HTML)
        self.assertIn("'δεκατέσσερις'", HTML)
        self.assertIn("return 'Ένας πόντος'", HTML)
        self.assertIn("πέντε', 'έξι', 'επτά'", HTML)
        self.assertNotIn("`${score} πόντοι`", HTML)

    def test_feed_the_bear_difficulty_and_food_heights_progress_gradually(self) -> None:
        self.assertIn("if (runnerDistance < 60) return 'food'", HTML)
        self.assertIn("runnerDistance < 130 ? .10 : (runnerDistance < 220 ? .18 : .28)", HTML)
        self.assertIn("const canFly = type === 'rock' && runnerDistance >= 170", HTML)
        self.assertIn("const lastWasRock", HTML)
        self.assertIn("Math.max(580, 980 - runnerDistance * 1.6)", HTML)
        self.assertIn("runnerDistance += speed * elapsedSeconds / 18", HTML)
        self.assertIn("runnerAltitude === 0 && !runnerThrusting", HTML)
        self.assertIn("const runnerFoodAltitudeRatios = [0, .18, .38, .08, .48, .27]", HTML)
        self.assertIn("runnerFoodLaneIndex++ % runnerFoodAltitudeRatios.length", HTML)
        self.assertIn("stageHeight * foodAltitudeRatio", HTML)

    def test_runner_uses_four_fun_crash_reactions_and_recovers(self) -> None:
        self.assertIn("['crash-bandage', 'crash-dizzy', 'crash-tumble', 'crash-wobble']", HTML)
        for animation in (
            "@keyframes runnerCrashBandage",
            "@keyframes runnerCrashDizzy",
            "@keyframes runnerCrashTumble",
            "@keyframes runnerCrashWobble",
        ):
            self.assertIn(animation, HTML)
        self.assertIn(".runner-character.crash-bandage::after { content:'🩹'", HTML)
        self.assertIn("const runnerOuchAudioPool = Array.from({ length: 4 }", HTML)
        self.assertIn("playRunnerOuch();", HTML)
        self.assertIn("assets/runner-ouch.mp3?v=2", HTML)
        self.assertIn("'Ow.wav', 'balloonhead', 'CC0'", HTML)
        self.assertIn("profileName === 'santaLaugh' || profileName === 'runnerOuch' ? 1 : 0.58", HTML)
        self.assertGreater((ROOT / "assets" / "runner-ouch.mp3").stat().st_size, 15_000)
        self.assertIn("runnerCrashReactionIndex++ % runnerCrashReactions.length", HTML)
        self.assertIn("document.getElementById('runnerCrashText').textContent = phrase", HTML)
        self.assertIn("playRunnerCrashHaptics();", HTML)
        self.assertIn("window.AndroidHaptics.crash();", HTML)
        self.assertIn("navigator.vibrate([70, 45, 90])", HTML)
        self.assertIn('id="runnerImpactStars"', HTML)
        self.assertIn("stars.classList.add('active')", HTML)

    def test_ice_cream_maker_is_one_tap_guided_and_has_no_failure_state(self) -> None:
        self.assertIn('id="game-icecream"', HTML)
        self.assertIn("function chooseIceCreamFlavor(index)", HTML)
        self.assertIn("function addIceCreamTopping(index)", HTML)
        self.assertIn("iceCreamScoopCount >= 3", HTML)
        self.assertIn("iceCreamToppingChoices", HTML)
        self.assertIn("@keyframes iceCreamPour", HTML)
        self.assertNotIn("iceCreamWrong", HTML)

    def test_ice_cream_uses_full_screen_decorative_toppings_without_a_finish_button(self) -> None:
        self.assertIn("#game-icecream,\n        #game-cooking { width:100%;max-width:none;height:100svh", HTML)
        self.assertIn('class="ice-cream-result" id="iceCreamResult" role="button"', HTML)
        self.assertNotIn('id="iceCreamFinish"', HTML)
        self.assertIn("iceCreamToppingCount >= 3", HTML)
        self.assertIn("setTimeout(() => finishIceCream(true), 720)", HTML)
        for topping_kind in ("sprinkle", "berry", "banana", "nut", "chocolate", "cherry"):
            self.assertIn(f"kind:'{topping_kind}'", HTML)
            self.assertIn(f".ice-cream-topping.{topping_kind}", HTML)
        self.assertNotIn("piece.textContent = topping.emoji", HTML)

    def test_birthday_candles_use_a_private_reliable_countdown_and_tap_fallback(self) -> None:
        birthday_source = HTML[HTML.index("let birthdayTimers") : HTML.index("const cookingMeals")]
        self.assertIn("function startBirthdayRound()", birthday_source)
        self.assertIn("birthdayStagePressed()", birthday_source)
        self.assertIn("extinguishBirthdayCandle", birthday_source)
        self.assertIn("3 2 1", birthday_source)
        self.assertNotIn("getUserMedia", birthday_source)
        self.assertNotIn("MediaRecorder", birthday_source)
        self.assertNotIn('id="birthdayStart"', HTML)
        self.assertIn('id="birthdayStage" role="button" tabindex="0" data-tap-invite', HTML)

    def test_little_chef_guides_choice_counting_chopping_and_stirring(self) -> None:
        self.assertIn('id="game-cooking"', HTML)
        self.assertIn("for (let onion = 0; onion < 5; onion++)", HTML)
        self.assertIn("function addCookingOnion(button)", HTML)
        self.assertIn("beginCookingIngredientDrag(event, button)", HTML)
        self.assertIn("moveCookingIngredientDrag", HTML)
        self.assertIn("finishCookingIngredientDrag", HTML)
        self.assertIn("function chopIngredient()", HTML)
        self.assertIn("function stirCookingPot()", HTML)
        self.assertIn("cookingChopCount < 3", HTML)
        self.assertIn("cookingCountWords", HTML)

    def test_little_chef_speaks_each_instruction_and_requires_the_main_ingredient(self) -> None:
        self.assertIn("if (gameId === 'cooking') prepareCookingGame(true)", HTML)
        self.assertIn("`${meal.names[language] || meal.names.en}. ${interfaceText[language].cookingAddOnions}`", HTML)
        self.assertIn("cookingAddOnions:'Add five onions. Tap each onion to put it on the chopping board.'", HTML)
        self.assertIn("cookingAddOnions:'Βάλε πέντε κρεμμυδάκια στο ξύλο κοπής. Πάτησε κάθε κρεμμυδάκι.'", HTML)
        self.assertIn('id="cookingMainIngredient"', HTML)
        self.assertIn("cookingStep = 'addMain'", HTML)
        self.assertIn("function addCookingMainIngredient()", HTML)
        self.assertIn("document.getElementById('cookingPotFood').textContent = meal.emoji", HTML)
        self.assertIn("names:{en:'Carrots',enUS:'Carrots'", HTML)
        chop_source = HTML[HTML.index("function chopIngredient()") : HTML.index("function addCookingMainIngredient()")]
        self.assertNotIn("cookingStep = 'stir'", chop_source)

    def test_little_chef_uses_voice_only_reminders_on_a_bounded_idle_schedule(self) -> None:
        self.assertIn(".cooking-game > .creative-prompt { width:1px;height:1px", HTML)
        self.assertIn("for (let reminder = 1; reminder <= 3; reminder++)", HTML)
        self.assertIn("reminder * 10_000", HTML)
        self.assertIn("scheduleCookingReminders(language, interfaceText[language].cookingAddOnions)", HTML)

    def test_little_chef_animates_onion_bits_and_supports_hold_to_stir(self) -> None:
        self.assertIn("function launchCookingOnionBits()", HTML)
        self.assertIn("className = 'cooking-onion-bit'", HTML)
        self.assertIn("@keyframes onionBitToPot", HTML)
        self.assertIn("cookingPot.addEventListener('pointerdown', beginCookingStir)", HTML)
        self.assertIn("setInterval(advanceCookingStir, 230)", HTML)
        self.assertIn("cookingStirCount < 8", HTML)
        self.assertIn("@keyframes spoonTurn", HTML)
        self.assertIn(".cooking-pot.stirring .cooking-spoon", HTML)

    def test_little_chef_uses_the_full_screen_and_objects_instead_of_action_buttons(self) -> None:
        self.assertIn("#game-cooking { width:100%;max-width:none;height:100svh", HTML)
        self.assertIn("grid-template-columns:repeat(5,minmax(0,1fr))", HTML)
        self.assertIn('class="cooking-pot" id="cookingPot" role="button"', HTML)
        self.assertIn('class="cooking-finished-plate" id="cookingFinishedPlate" role="button"', HTML)
        self.assertNotIn('id="cookingAction"', HTML)
        self.assertNotIn('id="cookingNext"', HTML)
        self.assertIn("cookingPot').classList.add('ready-to-stir')", HTML)

    def test_runner_speaks_food_before_a_quieter_score(self) -> None:
        self.assertIn("speakSingle(languageSettings[runnerDisplayLanguage].code, foodName, () =>", HTML)
        self.assertIn("runnerScorePhrases[runnerDisplayLanguage](runnerScore)", HTML)
        self.assertIn("{ volume: .38 }", HTML)
        self.assertIn("{ volume: 1 }", HTML)
        self.assertIn("utterance.volume = volume", HTML)

    def test_runner_starts_in_any_orientation_and_expands_in_landscape(self) -> None:
        self.assertNotIn("runner-rotate-overlay", HTML)
        self.assertNotIn("runnerIsLandscape", HTML)
        self.assertNotIn("if (!runnerIsLandscape()) return", HTML)
        self.assertIn("@media (orientation:landscape)", HTML)
        self.assertIn("body.controls-collapsed #game-runner { width:100%;max-width:none;padding:2px; }", HTML)
        self.assertIn('id="runnerTutorial"', HTML)
        self.assertIn("@keyframes runnerTutorialFly", HTML)
        self.assertIn("@keyframes runnerTutorialPress", HTML)
        self.assertIn("runnerTutorialSeen = true", HTML)

    def test_runner_localization_uses_natural_child_facing_instructions(self) -> None:
        for phrase in (
            "Feed the Bear",
            "Dale de comer al osito",
            "Nourris l’ourson",
            "Τάισε το αρκουδάκι",
            "Presiona para volar",
            "Appuie pour voler",
            "Πάτησε για να πετάξει",
        ):
            self.assertIn(phrase, HTML)
        self.assertIn('<span class="nav-icon">🧸</span>', HTML)
        for old_title in ("Catch the Broccoli", "Atrapa el brócoli", "Attrape le brocoli", "Πιάσε το μπρόκολο"):
            self.assertNotIn(old_title, HTML)
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
        self.assertRegex(HTML, r'en:\s*"Pig",\s*es:\s*"Cochinito"')
        self.assertIn("Pig:'Cerdito'", HTML)
        self.assertRegex(HTML, r"en:'Straw',\s*es:'Popote'")
        self.assertIn("Straw:'Pajita'", HTML)

    def test_animals_use_natural_greek_and_spanish_diminutives(self) -> None:
        self.assertRegex(HTML, r'en:\s*"Monkey",\s*es:\s*"Monito",\s*fr:\s*"Singe",\s*el:\s*"Μαϊμουδάκι"')
        for phrase in ("Perrito", "Gatito", "Osito", "Σκυλάκι", "Γατούλα", "Αρκουδάκι"):
            self.assertIn(phrase, HTML)
        self.assertNotIn('el: "Πίθηκος"', HTML)

    def test_music_studio_has_more_instruments_and_its_own_touch_scroller(self) -> None:
        instrument_source = array_source("instruments")
        self.assertEqual(13, instrument_source.count("{ emoji:"))
        for kind in ("violin", "saxophone", "flute", "accordion", "banjo"):
            self.assertIn(f"kind:'{kind}'", instrument_source)
            self.assertIn(f"kind === '{kind}'", HTML)
        scroller = HTML[HTML.index("body.controls-collapsed #game-music"):HTML.index("#game-music .learning-game")]
        self.assertIn("overflow-y:auto", scroller)
        self.assertIn("touch-action:pan-y", scroller)

    def test_browser_back_restores_the_previous_game_state(self) -> None:
        self.assertIn("history.pushState(nextState, '')", HTML)
        self.assertIn("window.addEventListener('popstate'", HTML)
        self.assertIn("applyNavigationState(event.state)", HTML)

    def test_spoken_text_strips_commas(self) -> None:
        self.assertIn("const speechText = text.replace(/,/g, '')", HTML)

    def test_toddler_play_is_voice_first_without_reading_required(self) -> None:
        for element_id in (
            "balloonStatus",
            "monsterSpeech",
            "findQuestion",
            "letterPromptText",
            "shapePromptText",
            "countingPromptText",
            "bodyPromptText",
            "iceCreamPrompt",
            "birthdayPrompt",
        ):
            self.assertIn(f"#{element_id}", HTML)
        hidden_prompt_layer = HTML[HTML.index("#balloonStatus,") : HTML.index("#letterPrompt {")]
        self.assertIn("clip-path:inset(50%)", hidden_prompt_layer)
        self.assertIn("overflow:hidden !important", hidden_prompt_layer)
        self.assertIn("speakSingle(languageSettings[language].code, instruction)", HTML)

    def test_toddler_guidance_is_bounded_and_stops_after_interaction(self) -> None:
        guidance_source = HTML[HTML.index("let toddlerGuidanceTimers") : HTML.index("function navigationState")]
        self.assertIn("for (let reminder = 1; reminder <= 3; reminder++)", guidance_source)
        self.assertIn("reminder * 10_000", guidance_source)
        self.assertIn("document.addEventListener('pointerdown'", guidance_source)
        self.assertIn("if (activeGame) clearToddlerGuidance()", guidance_source)
        self.assertNotIn("monster: ()", guidance_source)
        self.assertIn("clearToddlerGuidance();\n            cancelRepeatSequence();", HTML)

    def test_toddler_targets_and_press_feedback_follow_mobile_guidance(self) -> None:
        self.assertIn("button { min-width:48px;min-height:48px; }", HTML)
        self.assertIn("button:disabled { cursor:default; }", HTML)
        self.assertIn(".tap-invite", HTML)
        self.assertIn("@media (prefers-reduced-motion:reduce)", HTML)
        self.assertIn("transition-duration:.01ms !important", HTML)

    def test_bottom_controls_do_not_cover_guided_game_choices(self) -> None:
        self.assertRegex(
            HTML,
            re.compile(
                r"\.ice-cream-flavors,\s*\.ice-cream-topping-buttons\s*\{\s*bottom:max\(86px",
                re.S,
            ),
        )
        self.assertRegex(
            HTML,
            re.compile(r"\.cooking-pot\s*\{\s*margin-bottom:max\(92px", re.S),
        )
        self.assertRegex(
            HTML,
            re.compile(r"\.birthday-game\s*\{.*?padding:8px 8px max\(82px", re.S),
        )


if __name__ == "__main__":
    unittest.main()
