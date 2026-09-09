# Contributing / 參與方式

歡迎繁中或英文的問題回報、文件修正、自製測試案例與程式改善。
Bug reports, documentation improvements and focused pull requests are welcome in Traditional Chinese or English.

## Report a problem / 回報問題

1. Search existing issues first. / 先確認是否已有相同問題。
2. Include OS, Python and tool version (`python srt_check.py --version`).
3. Provide the command, expected result, actual result and a small synthetic SRT that reproduces it.
4. For a false warning, explain why the subtitle is intentional or which threshold fits the use case.

請勿附私人字幕、影片、憑證或不適合公開的檔案。JSON 報告含檔名，分享前也請檢查。
Do not attach private or copyrighted media, credentials, or sensitive subtitle text. Review filenames before sharing reports.

## Development / 開發

Python 3.10+ and its standard library are sufficient:

```sh
python -I -S -m unittest discover -s tests -t . -v
python srt_check.py examples/clean.srt --strict
```

Windows launcher tests run only on Windows and use disposable synthetic files. Keep input files read-only and preserve existing reports. Add a regression test for a reproducible bug; avoid unrelated refactors. Describe the behavior change and testing in the pull request. Code or examples contributed to this project must be material you can license under the repository's MIT license.

## Trial feedback / 試用回饋

Tell us whether installation worked, which checks were useful, and which warnings were confusing. A successful trial report is welcome even when no bug was found. Only real feedback is recorded; there is no need to star the repository to participate.
