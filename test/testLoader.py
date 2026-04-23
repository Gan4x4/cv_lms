import os
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from loader import _download_csv, clear_runtime_cache, load_topics
from tree import tree


class DummyResponse:
    def __init__(self, body):
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class LoaderCacheTestCase(unittest.TestCase):

    def test_download_uses_cache_bust_and_writes_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = os.path.join(temp_dir, "topics.csv")
            response = DummyResponse(b"a,b\n1,2\n")

            with patch("loader.request.urlopen", return_value=response) as urlopen:
                result = _download_csv("https://example.com/topics.csv?gid=1&format=csv", destination)

            request_obj = urlopen.call_args[0][0]
            headers = {key.lower(): value for key, value in request_obj.header_items()}
            self.assertIn("_cache_bust=", request_obj.full_url)
            self.assertEqual("no-cache", headers["cache-control"])
            self.assertEqual("no-cache", headers["pragma"])
            self.assertEqual(destination, result["filename"])
            self.assertFalse(result["connection_failed"])

            with open(destination, "rb") as file:
                self.assertEqual(b"a,b\n1,2\n", file.read())

    def test_connect_failure_uses_existing_cache_and_marks_warning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = os.path.join(temp_dir, "topics.csv")

            with open(destination, "wb") as file:
                file.write(b"cached\n")

            with patch("loader.request.urlopen", side_effect=OSError("network down")):
                result = _download_csv("https://example.com/topics.csv", destination)

            self.assertEqual(destination, result["filename"])
            self.assertTrue(result["connection_failed"])

            with open(destination, "rb") as file:
                self.assertEqual(b"cached\n", file.read())


class TopicsFromQuestionsTestCase(unittest.TestCase):

    def test_load_topics_uses_question_topics_subtopics_and_link_columns(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            questions_path = os.path.join(temp_dir, "questions.csv")
            config_path = os.path.join(temp_dir, "config.ini")

            rows = [
                ["", "Раздел", "Подраздел", "Вопросы", "Ответы", "Link1", "Link2", "Note"],
                ["", "Topic A", "", "", "", "https://topic.example", "", ""],
                ["", "", "Subtopic A", "", "", "https://subtopic.example", "", ""],
                ["", "", "", "Question", "Answer", "https://question.example", "", "comment"],
                ["", "", "", "Question 2", "Answer 2", "https://question.example", "", "duplicate"],
                ["", "Topic B", "", "", "", "", "", ""],
                ["", "", "Subtopic B", "", "", "", "", ""],
                ["", "Topic C", "", "", "", "", "", ""],
                ["", "", "", "", "", "https://topic-row-1.example", "https://topic-row-2.example", ""],
            ]
            pd.DataFrame(rows).to_csv(questions_path, header=False, index=False)

            with open(config_path, "w", encoding="utf-8") as file:
                file.write(
                    "[questions]\n"
                    "type = local\n"
                    f"path = {questions_path}\n"
                )

            data, _ = load_topics(config_path)
            topics = tree(data)

            self.assertEqual(["Topic A", "Topic B", "Topic C"], list(topics.keys()))
            self.assertIn("https://topic.example", topics["Topic A"])
            self.assertIn("Subtopic A", topics["Topic A"])
            self.assertEqual(
                ["https://subtopic.example", "https://question.example"],
                list(topics["Topic A"]["Subtopic A"].keys()),
            )
            self.assertEqual({}, topics["Topic B"]["Subtopic B"])
            self.assertEqual(
                ["https://topic-row-1.example", "https://topic-row-2.example"],
                list(topics["Topic C"].keys()),
            )

    def test_clear_runtime_cache_keeps_unconfigured_backup_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = os.path.join(temp_dir, "cache")
            generated_dir = os.path.join(temp_dir, "generated")
            os.makedirs(cache_dir)
            os.makedirs(generated_dir)

            questions_cache = os.path.join(cache_dir, "questions.csv")
            backup = os.path.join(cache_dir, "topics_backup.csv")
            generated = os.path.join(generated_dir, "topics.html")
            config_path = os.path.join(temp_dir, "config.ini")

            for path in (questions_cache, backup, generated):
                with open(path, "w", encoding="utf-8") as file:
                    file.write("data")

            with open(config_path, "w", encoding="utf-8") as file:
                file.write(
                    "[app]\n"
                    f"topics_output = {generated}\n"
                    "questions_output = unused\n"
                    "\n"
                    "[questions]\n"
                    "type = remote\n"
                    "url = https://example.com/questions.csv\n"
                    f"cache_path = {questions_cache}\n"
                )

            clear_runtime_cache(config_path)

            self.assertFalse(os.path.exists(questions_cache))
            self.assertTrue(os.path.exists(backup))
            self.assertFalse(os.path.exists(generated))


if __name__ == '__main__':
    unittest.main()
