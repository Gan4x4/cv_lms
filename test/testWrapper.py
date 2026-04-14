import unittest

from wrapper import make_url_clickable


class WrapperTestCase(unittest.TestCase):

    def test_keeps_bare_formula_text_unchanged(self):
        text = (
            "Без неё сеть эквивалентна одной линейной модели: "
            "x=(W_1x)W_2 = xW https://example.com/demo"
        )

        rendered = make_url_clickable(text)

        self.assertIn("x=(W_1x)W_2 = xW", rendered)
        self.assertIn('<a href="https://example.com/demo" target="_blank">https://example.com/demo</a>', rendered)

    def test_keeps_existing_math_delimiters_unchanged(self):
        rendered = make_url_clickable("Количество запусков будет равно не k, $k^2$")

        self.assertEqual("Количество запусков будет равно не k, $k^2$", rendered)

    def test_keeps_unclosed_dollar_unchanged(self):
        rendered = make_url_clickable("Формула начинается так: $x=(W_1x)W_2")

        self.assertEqual("Формула начинается так: $x=(W_1x)W_2", rendered)

    def test_does_not_wrap_url_fragments_with_underscores(self):
        rendered = make_url_clickable("Ссылка https://example.com/foo_bar?q=x_y")

        self.assertNotIn("$foo_bar$", rendered)
        self.assertNotIn("$x_y$", rendered)
        self.assertIn('href="https://example.com/foo_bar?q=x_y"', rendered)


if __name__ == '__main__':
    unittest.main()
