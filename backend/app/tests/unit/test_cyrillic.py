# -*- coding: utf-8 -*-
"""
CYRILLIC TESTS
Unit testovi za utils/cyrillic.py.

Pokretanje:
    pytest tests/unit/test_cyrillic.py -v
"""

from app.utils.cyrillic import (
    cyrillic_to_latin,
    latin_to_cyrillic,
    transliterate_text,
    CYRILLIC_TO_LATIN,
    LATIN_TO_CYRILLIC,
)


class TestCyrillicToLatin:
    def test_empty_string(self):
        assert cyrillic_to_latin("") == ""

    def test_none_input(self):
        assert cyrillic_to_latin(None) is None

    def test_basic_serbian_cyrillic(self):
        text = "АБВГДЂЕЖЗИЈКЛЉМНЊОПРСТЋУФХЦЧЏШ"
        expected = "ABVGDĐEŽZIJKLLJMNNJOPRSTĆUFHCČDŽŠ"
        assert cyrillic_to_latin(text) == expected

    def test_lowercase_serbian_cyrillic(self):
        text = "абвгдђежзијклљмнњопрстћуфхцчџш"
        expected = "abvgdđežzijklljmnnjoprstćufhcčdžš"
        assert cyrillic_to_latin(text) == expected

    def test_russian_characters(self):
        text = "ъыьэюяЪЫЬЭЮЯ"
        expected = "yejujaYEJUJA"
        assert cyrillic_to_latin(text) == expected

    def test_mixed_cyrillic_and_latin(self):
        text = "ABCабвDEF"
        expected = "ABCabvDEF"
        assert cyrillic_to_latin(text) == expected

    def test_non_cyrillic_preserved(self):
        text = "Hello 123! @#$"
        assert cyrillic_to_latin(text) == text

    def test_unicode_outside_range(self):
        text = "\u4e16\u754c"  # Chinese: 世界
        assert cyrillic_to_latin(text) == text

    def test_dj_mapping_consistency(self):
        assert cyrillic_to_latin("ђ") == "đ"
        assert cyrillic_to_latin("Ђ") == "Đ"

    def test_lj_nj_dz_multi_char(self):
        assert cyrillic_to_latin("љ") == "lj"
        assert cyrillic_to_latin("Њ") == "NJ"
        assert cyrillic_to_latin("џ") == "dž"
        assert cyrillic_to_latin("Џ") == "DŽ"

    def test_old_slavic_characters(self):
        assert cyrillic_to_latin("і") == "i"
        assert cyrillic_to_latin("ї") == "ji"
        assert cyrillic_to_latin("є") == "je"
        assert cyrillic_to_latin("І") == "I"
        assert cyrillic_to_latin("Ї") == "YI"
        assert cyrillic_to_latin("Є") == "JE"

    def test_yo_mapping(self):
        assert cyrillic_to_latin("Ё") == "Ë"
        assert cyrillic_to_latin("ё") == "ё"

    def test_known_phrase(self):
        text = "Здраво Свете"
        expected = "Zdravo Svete"
        assert cyrillic_to_latin(text) == expected

    def test_soft_sign_and_hard_sign_removed(self):
        assert cyrillic_to_latin("ъьЪЬ") == ""
        assert cyrillic_to_latin("мъ") == "m"


class TestLatinToCyrillic:
    def test_empty_string(self):
        assert latin_to_cyrillic("") == ""

    def test_none_input(self):
        assert latin_to_cyrillic(None) is None

    def test_single_char_mappings(self):
        for latin_char, cyrillic_char in LATIN_TO_CYRILLIC.items():
            if len(latin_char) != 1:
                continue
            assert latin_to_cyrillic(latin_char) == cyrillic_char

    def test_non_latin_preserved(self):
        text = "123!@#"
        assert latin_to_cyrillic(text) == text

    def test_lowercase_conversion(self):
        assert latin_to_cyrillic("abc") == "абц"

    def test_uppercase_conversion(self):
        assert latin_to_cyrillic("ABC") == "АБЦ"

    def test_mixed_text(self):
        result = latin_to_cyrillic("abc123")
        assert "а" in result
        assert "123" in result

    def test_dict_symmetry_single_char(self):
        known_duplicates = {"Ђ", "Ѓ", "ђ", "ѓ", "Ѐ", "Ё", "е", "и", "Е", "И", "Й"}
        for cyrillic_char, latin_char in CYRILLIC_TO_LATIN.items():
            if not latin_char or len(latin_char) != 1:
                continue
            if cyrillic_char in known_duplicates:
                continue
            reversed_char = LATIN_TO_CYRILLIC.get(latin_char)
            if reversed_char:
                assert cyrillic_char == reversed_char, (
                    f"Symmetry broken: {cyrillic_char}->{latin_char}->{reversed_char}"
                )


class TestTransliterateText:
    def test_empty_string(self):
        assert transliterate_text("") == ""

    def test_none_input(self):
        assert transliterate_text(None) is None

    def test_cyrillic_to_latin(self):
        text = "Здраво Свете"
        expected = "Zdravo Svete"
        assert transliterate_text(text) == expected

    def test_latin_to_cyrillic_fallback(self):
        text = "Zdravo Svete"
        result = transliterate_text(text)
        assert result != text

    def test_mixed_text_prefers_cyrillic(self):
        text = "ABCздравоDEF"
        result = transliterate_text(text)
        assert "здраво" not in result
        assert "zdravo" in result.lower()

    def test_no_alpha_text(self):
        text = "123!@#"
        assert transliterate_text(text) == "123!@#"

    def test_single_cyrillic_char(self):
        assert transliterate_text("а") == "a"
        assert transliterate_text("б") == "b"

    def test_detection_edge_case(self):
        text_cyr_start = "Ћирилица"
        result = transliterate_text(text_cyr_start)
        assert "Ћ" not in result
        assert "Ć" in result or "ć" in result.lower()
