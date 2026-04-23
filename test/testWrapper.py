import unittest

from wrapper import Wrapper, classify_url_label, label_from_url, make_url_clickable


class WrapperTestCase(unittest.TestCase):

    def test_keeps_bare_formula_text_unchanged(self):
        text = (
            "Без неё сеть эквивалентна одной линейной модели: "
            "x=(W_1x)W_2 = xW https://example.com/demo"
        )

        rendered = make_url_clickable(text)

        self.assertIn("x=(W_1x)W_2 = xW", rendered)
        self.assertIn('href="https://example.com/demo"', rendered)
        self.assertIn('title="https://example.com/demo"', rendered)
        self.assertIn(">demo</a>", rendered)

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

    def test_classifies_colab_links_as_ipynb(self):
        label = classify_url_label(
            "https://colab.research.google.com/drive/1AM6PIIvcI4m-D0NxIUwgnn55F7E8gkZH#scrollTo=PnIVfL0uxflo"
        )

        self.assertEqual("Colab", label)

    def test_classifies_google_slides_as_pptx(self):
        label = classify_url_label(
            "https://docs.google.com/presentation/d/1MCgXRalQYN4XMinNhaM49ZpEc39TnBxIwYJjiL2F5kU/edit"
        )

        self.assertEqual("pptx", label)

    def test_renders_short_label_for_known_link_types(self):
        rendered = make_url_clickable(
            "Материал https://github.com/Gan4x4/cv/blob/main/Neural_network/Multilayer_perceptron.ipynb"
        )

        self.assertIn(">Colab</a>", rendered)
        self.assertNotIn(">https://github.com/Gan4x4/cv/blob/main/Neural_network/Multilayer_perceptron.ipynb</a>", rendered)

    def test_uses_meaningful_filename_when_available(self):
        label = label_from_url(
            "https://education.yandex.ru/handbook/ml/article/reshayushchiye-derevya"
        )

        self.assertEqual("reshayushchiye-derevya", label)

    def test_falls_back_to_type_for_opaque_colab_links(self):
        label = label_from_url(
            "https://colab.research.google.com/drive/1AM6PIIvcI4m-D0NxIUwgnn55F7E8gkZH#scrollTo=PnIVfL0uxflo"
        )

        self.assertEqual("Colab", label)

    def test_uses_last_meaningful_path_part_for_github_tree(self):
        label = label_from_url(
            "https://github.com/Gan4x4/cv/tree/main/Decision_trees"
        )

        self.assertEqual("Decision_trees", label)

    def test_groups_sibling_link_leaves_into_one_row(self):
        wrapper = Wrapper()
        rendered = wrapper.flatten(
            {
                "https://example.com/a.ipynb": {},
                "https://example.com/b.pdf": {},
                "Question text": {},
            }
        )

        self.assertEqual(1, rendered.count('class="filter-leaf filter-link-row"'))
        self.assertIn("Colab", rendered)
        self.assertIn(">b</a>", rendered)
        self.assertIn("Question text", rendered)

    def test_wrap_groups_link_children_into_one_row(self):
        wrapper = Wrapper()
        rendered = wrapper.wrap(
            {
                "Parent": {
                    "https://example.com/a.ipynb": {},
                    "https://example.com/b.pdf": {},
                    "https://example.com/c": {},
                }
            }
        )

        self.assertEqual(1, rendered.count('class="filter-leaf filter-link-row"'))
        self.assertIn("Colab", rendered)
        self.assertIn(">b</a>", rendered)
        self.assertIn(">c</a>", rendered)


if __name__ == '__main__':
    unittest.main()
