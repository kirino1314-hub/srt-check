# SRT Check

Early trial 0.1.0: review SRT files before burning or delivering subtitles. Python 3.10+; standard library only. No API key, GPU, FFmpeg, network calls, or automatic subtitle edits.

[繁體中文](README.md) · [MIT license](LICENSE) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)

## Run

Use GitHub's Code → Download ZIP and extract the entire folder first. Run from the extracted directory. Install Python from [python.org](https://www.python.org/downloads/) if needed. On Windows, `py -3` can replace `python` in these commands.

```sh
python srt_check.py examples/clean.srt --strict
python srt_check.py examples/review-needed.srt
python srt_check.py "captions.srt" --duration 120.5
python srt_check.py "captions.srt" --json --output report.json
python -I -m unittest discover -s tests -t . -v
```

No dependency installation needed. On Windows, `Run-Demo.cmd` runs the original examples or accepts dropped SRT files. It finds a local Python runtime and does not download software.

The clean example has 2 cues and no findings. The review-needed example intentionally has 4 cues, 1 error and 3 warnings, so exit 1 is expected. Do not run the launcher inside a ZIP preview.

## Rules and limitations

Errors cover empty files/text, malformed indices/timestamps, probable missing separators, non-positive durations, and cues beyond the user-supplied media duration. Warnings cover numbering/order, overlapping intervals (including nested overlaps), reading speed, line count, and estimated width. Overlap may be intentional and requires human review.

Defaults `--max-cps 15 --max-width 42 --max-lines 2` are adjustable heuristics, not a universal subtitle standard. CPS counts NFC-normalized non-whitespace code points excluding marks/control characters, after removing common b/i/u/font tags and decoding entities. Punctuation counts. Width counts Unicode Wide/Fullwidth as 2 and other ordinary characters as 1; marks/control characters count as 0. This is not font measurement or full emoji grapheme handling.

Supports ordinary numbered, blank-line-separated SRT with comma milliseconds, UTF-8/BOM and LF/CRLF. Use `--encoding` explicitly for other encodings. VTT, ASS, and SRT coordinate extensions are outside this prototype. It does not assess translation accuracy, missing speech, or audio/video synchronization. Optional `--duration` is in seconds and accepts exactly one input file.

Exit codes: 0 means no errors (warnings can remain); 1 means errors, or warnings with `--strict`; 2 means argument or file I/O failure. `--output` exclusively creates a new JSON file and refuses existing paths, including the input itself. Reports contain basenames, SHA-256, thresholds and issue locations, not subtitle text.

## Feedback

Use this repository's Issues → New issue to report a bug or trial feedback. Include tool/Python/OS versions, command, expected/actual result and a minimal synthetic SRT sample. Examples and tests are original synthetic material.

20 tests passed locally on Windows / Python 3.12.14, including the real CMD launcher, Unicode/spaced paths, multiple inputs, and interpreter fallback. Desktop drag-and-drop was not visually tested. A GitHub Actions matrix is provided for Windows, Ubuntu and macOS on Python 3.10 and 3.12; check actual Actions runs before treating those environments as verified. External adoption has not yet been established.
