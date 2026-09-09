import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from srt_check import check_text, main


def cue(number=1, start="00:00:01,000", end="00:00:04,000", text="你好"):
    return f"{number}\n{start} --> {end}\n{text}"


class SubtitleTests(unittest.TestCase):
    def codes(self, text, **options):
        return [i["code"] for i in check_text(text, **options)["issues"]]

    def test_bom_crlf_numeric_dialogue(self):
        result = check_text("\ufeff" + cue(text="11").replace("\n", "\r\n"))
        self.assertEqual((result["cue_count"], result["errors"], result["warnings"]), (1, 0, 0))

    def test_invalid_minute_and_malformed_block_are_reported(self):
        codes = self.codes(cue(start="00:60:00,000") + "\n\nnot a cue")
        self.assertEqual(codes, ["INVALID_TIMESTAMP", "INVALID_INDEX"])

    def test_zero_and_negative_duration(self):
        for end in ("00:00:01,000", "00:00:00,000"):
            with self.subTest(end=end):
                self.assertIn("INVALID_DURATION", self.codes(cue(end=end)))

    def test_nested_overlap_and_unsorted_input(self):
        text = "\n\n".join([cue(1, end="00:00:10,000"),
                              cue(2, "00:00:05,000", "00:00:06,000"),
                              cue(3, "00:00:03,000", "00:00:04,000")])
        codes = self.codes(text)
        self.assertEqual(codes.count("OVERLAP"), 2)
        self.assertIn("OUT_OF_ORDER", codes)

    def test_touching_intervals_do_not_overlap(self):
        self.assertNotIn("OVERLAP", self.codes(cue() + "\n\n" +
                           cue(2, "00:00:04,000", "00:00:07,000")))

    def test_empty_and_format_only_text(self):
        self.assertIn("EMPTY_FILE", self.codes("  \n"))
        self.assertIn("EMPTY_TEXT", self.codes(cue(text="")))
        self.assertIn("EMPTY_TEXT", self.codes(cue(text="<i> </i>")))

    def test_missing_separator(self):
        self.assertIn("MISSING_SEPARATOR", self.codes(cue() + "\n" + cue(2)))

    def test_configurable_speed_and_cjk_width(self):
        text = cue(text="<b>你好世界</b>")
        self.assertIn("READING_SPEED", self.codes(text, max_cps=1))
        self.assertIn("LINE_WIDTH", self.codes(text, max_width=7))
        self.assertNotIn("LINE_WIDTH", self.codes(text, max_width=8))
        self.assertNotIn("READING_SPEED", self.codes(cue(text="e\u0301"), max_cps=0.34))

    def test_line_count_and_media_boundary(self):
        text = cue(text="一\n二\n三")
        self.assertIn("LINE_COUNT", self.codes(text))
        self.assertIn("BEYOND_MEDIA", self.codes(text, duration=3.999))
        self.assertNotIn("BEYOND_MEDIA", self.codes(text, duration=4))

    def test_sequence_warning(self):
        self.assertIn("INDEX_SEQUENCE", self.codes(cue(9)))

    def test_large_finite_duration_does_not_overflow(self):
        self.assertEqual(check_text(cue(), duration=1e308)["errors"], 0)

    def test_submillisecond_media_boundary_is_not_rounded_up(self):
        self.assertIn("BEYOND_MEDIA", self.codes(cue(), duration=3.9999))

    def test_invalid_thresholds(self):
        for options in ({"max_cps": float("nan")}, {"duration": float("inf")},
                        {"max_width": 0}, {"max_lines": -1}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                check_text(cue(), **options)

    def test_cli_never_overwrites_and_reports_json(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "字幕.srt"
            report = Path(directory) / "report.json"
            source.write_text(cue(), encoding="utf-8")
            original = source.read_bytes()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main([str(source), "--output", str(report)]), 0)
                first_report = report.read_bytes()
                self.assertEqual(main([str(source), "--output", str(source)]), 2)
                self.assertEqual(main([str(source), "--output", str(report)]), 2)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(report.read_bytes(), first_report)
            self.assertEqual(json.loads(first_report)["files"][0]["cue_count"], 1)

    def test_cli_strict_missing_file_and_encoding(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "demo.srt"
            source.write_bytes(cue(2).encode("utf-16"))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(source)]), 2)
                self.assertEqual(main([str(source), "--encoding", "utf-16"]), 0)
                self.assertEqual(main([str(source), "--encoding", "utf-16", "--strict"]), 1)
                self.assertEqual(main([str(source.with_name("absent.srt"))]), 2)


if __name__ == "__main__":
    unittest.main()
