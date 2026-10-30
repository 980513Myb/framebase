import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from app.services.log_service import summarize_log_file


class LogSummaryTests(unittest.TestCase):
    def write_log(self, content):
        temp_dir = tempfile.TemporaryDirectory()
        path = Path(temp_dir.name) / "app.log"
        path.write_text(content, encoding="utf-8")
        self.addCleanup(temp_dir.cleanup)
        return path

    def test_summary_classifies_and_filters_runtime_logs(self):
        path = self.write_log(
            "\n".join((
                "2026-08-03 10:00:00,000 - INFO - [System] service started",
                "2026-08-03 10:01:00,000 - INFO - [Engine] GIF 完成",
                "2026-08-03 10:02:00,000 - WARNING - [Webhook] payload missing path",
                "2026-08-03 10:03:00,000 - ERROR - [Notify] 企微通知失败",
                "2026-08-03 10:04:00,000 - EmbyClient - DEBUG - request completed",
            ))
        )

        summary = summarize_log_file(path, limit=50)

        self.assertEqual(summary["scoped_total"], 5)
        self.assertEqual(summary["shown"], 5)
        self.assertEqual(summary["categories"], {
            "system": 1,
            "cover": 1,
            "webhook": 1,
            "notify": 1,
            "emby": 1,
        })
        self.assertEqual(summary["levels"]["WARNING"], 1)
        self.assertEqual(summary["levels"]["ERROR"], 1)
        self.assertEqual(summary["entries"][1]["message"], "[Engine] GIF 完成")

        filtered = summarize_log_file(path, limit=50, category="webhook", level="WARNING")
        self.assertEqual(filtered["shown"], 1)
        self.assertEqual(filtered["entries"][0]["category"], "webhook")

    def test_summary_supports_time_range_and_missing_file(self):
        path = self.write_log(
            "\n".join((
                "2026-08-01 10:00:00,000 - INFO - old entry",
                "2026-08-03 11:00:00,000 - ERROR - current error",
            ))
        )

        summary = summarize_log_file(
            path,
            limit=50,
            hours=24,
            now=datetime(2026, 8, 3, 12, 0, 0),
        )
        self.assertEqual(summary["scoped_total"], 1)
        self.assertEqual(summary["last_issue"]["message"], "current error")

        missing = summarize_log_file(path.parent / "missing.log")
        self.assertEqual(missing["shown"], 0)
        self.assertEqual(missing["entries"], [])


if __name__ == "__main__":
    unittest.main()
