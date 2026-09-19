import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
LANGUAGES = (ROOT / "languages.js").read_text(encoding="utf-8")


class ExpandedLanguageRegressionTests(unittest.TestCase):
    def test_first_language_wave_is_available_everywhere(self) -> None:
        self.assertIn(
            "['en', 'enUS', 'el', 'es', 'esES', 'fr', 'de', 'it', 'tr', 'ptBR', 'nl', 'pl']",
            HTML,
        )
        for language, code, flag in (
            ("de", "de-DE", "🇩🇪"),
            ("it", "it-IT", "🇮🇹"),
            ("tr", "tr-TR", "🇹🇷"),
            ("ptBR", "pt-BR", "🇧🇷"),
            ("nl", "nl-NL", "🇳🇱"),
            ("pl", "pl-PL", "🇵🇱"),
        ):
            self.assertIn(f"data-language=\"{language}\"", HTML)
            self.assertIn(f"code:'{code}'", LANGUAGES)
            self.assertIn(flag, LANGUAGES)

    def test_language_packs_cover_every_learning_collection(self) -> None:
        for vector in (
            "pack.foods",
            "pack.trucks",
            "pack.animals",
            "pack.numbers",
            "pack.everyday",
            "pack.instruments",
            "pack.colors",
            "pack.shapes",
            "pack.runnerFoods",
        ):
            self.assertIn(vector, HTML)
        self.assertIn("letterSets[language] = pack.letters", HTML)
        self.assertIn("bodyParts[key][language] = pack.body[index]", HTML)
        self.assertIn("bellNoteLabels[language] = pack.bellNotes", HTML)

    def test_device_locale_can_preselect_each_new_language(self) -> None:
        for locale, language in (
            ("de", "de"),
            ("it", "it"),
            ("tr", "tr"),
            ("pt", "ptBR"),
            ("nl", "nl"),
            ("pl", "pl"),
        ):
            self.assertIn(f"if (locale.startsWith('{locale}')) return '{language}'", HTML)

    def test_new_languages_have_localized_child_facing_copy(self) -> None:
        for phrase in (
            "Füttere den Bären",
            "Dai da mangiare all’orsetto",
            "Ayıcığı besle",
            "Alimente o ursinho",
            "Voer het beertje",
            "Nakarm misia",
        ):
            self.assertIn(phrase, LANGUAGES)
        self.assertIn("Object.assign(window.extraLanguagePacks.pl", LANGUAGES)
        self.assertIn("window.extraLanguagePacks.pl.numbers.push", LANGUAGES)

    def test_dutch_letter_set_is_closed_before_its_interface_copy(self) -> None:
        dutch = LANGUAGES[LANGUAGES.index("nl: {") : LANGUAGES.index("pl: {")]
        self.assertIn("])\n            ,interface:{", dutch)


if __name__ == "__main__":
    unittest.main()
