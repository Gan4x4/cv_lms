import os
import tempfile
import unittest
from unittest.mock import patch

from loader import _download_csv


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


if __name__ == '__main__':
    unittest.main()
