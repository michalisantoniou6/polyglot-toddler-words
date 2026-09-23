import re
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

    def test_new_languages_localize_the_age_range_setting(self) -> None:
        for phrase in (
            "Jüngere Altersgruppen einbeziehen",
            "Includi fasce di età più giovani",
            "Daha küçük yaş gruplarını dahil et",
            "Incluir faixas etárias menores",
            "Jongere leeftijdsgroepen meenemen",
            "Uwzględnij młodsze grupy wiekowe",
        ):
            self.assertIn(phrase, LANGUAGES)

    def test_new_languages_localize_the_child_lock_confirmation(self) -> None:
        self.assertEqual(6, LANGUAGES.count("childLockToast:"))
        self.assertEqual(6, LANGUAGES.count("childLockTutorial:"))
        for phrase in (
            "Gesperrt. Nach oben wischen und halten",
            "Bloccato. Scorri verso l’alto",
            "Kilitlendi. Çıkmak için yukarı",
            "Bloqueado. Deslize para cima",
            "Vergrendeld. Veeg omhoog",
            "Zablokowano. Przesuń w górę",
        ):
            self.assertIn(phrase, LANGUAGES)

    def test_vehicle_words_are_short_and_catalog_subtypes_are_removed(self) -> None:
        vehicle_vectors = re.findall(r"trucks:\[([^\]]+)\]", LANGUAGES)
        self.assertEqual(6, len(vehicle_vectors))
        for vector in vehicle_vectors:
            labels = re.findall(r"'([^']*)'", vector)
            self.assertEqual(22, len(labels))
            self.assertTrue(all(len(label.split()) <= 3 for label in labels))
        for catalog_term in (
            "Kompaktlader", "Baggerlader", "Minipala", "Terna", "Mini yükleyici",
            "Kazıcı yükleyici", "Minicarregadeira", "Retroescavadeira",
            "Schranklader", "Graaflaadmachine", "Miniładowarka", "Koparko-ładowarka",
        ):
            self.assertNotIn(catalog_term, LANGUAGES)

    def test_dutch_letter_set_is_closed_before_its_interface_copy(self) -> None:
        dutch = LANGUAGES[LANGUAGES.index("nl: {") : LANGUAGES.index("pl: {")]
        self.assertIn("])\n            ,interface:{", dutch)


if __name__ == "__main__":
    unittest.main()
