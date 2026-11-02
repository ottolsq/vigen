import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import export

FIXTURES = Path(__file__).parent / "fixtures"


class TestExport(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="vigen-export-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_exports_docs_and_manifest(self):
        rc = export.main(["x", str(FIXTURES / "good_project"), "--out", str(self.tmp / "out")])
        self.assertEqual(rc, 0)
        out = self.tmp / "out"
        for name in ("01_方案与剧本.md", "02_锚定表.md", "03_图片提示词.md",
                     "04_视频提示词.md", "05_语音台词表.md"):
            self.assertTrue((out / name).is_file(), name)
        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["asserts_approval"])
        self.assertEqual(len(manifest["files"]), 5)
        checks = (out / "checksums.sha256").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(checks), 5)
        # 清单里的 sha256 必须与实际文件一致
        for item in manifest["files"]:
            self.assertEqual(item["sha256"], export.sha256_of(out / item["path"]))
        # 隐藏状态与输入目录不打包
        self.assertFalse((out / ".short-drama").exists())

    def test_no_media(self):
        proj = self.tmp / "proj"
        shutil.copytree(FIXTURES / "good_project", proj)
        (proj / "assets").mkdir(exist_ok=True)
        (proj / "assets" / "ref.png").write_bytes(b"\x89PNG")
        rc = export.main(["x", str(proj), "--out", str(self.tmp / "out"),
                          "--no-media", "--episode", "EP001"])
        self.assertEqual(rc, 0)
        copied = [p for p in (self.tmp / "out").rglob("*") if p.is_file()]
        self.assertFalse(any(p.suffix == ".png" for p in copied))

    def test_out_inside_project_rejected(self):
        rc = export.main(["x", str(FIXTURES / "good_project"),
                          "--out", str(FIXTURES / "good_project" / "交付")])
        self.assertEqual(rc, 2)

    def test_non_empty_out_requires_overwrite(self):
        out = self.tmp / "out"
        out.mkdir()
        (out / "keep.txt").write_text("x", encoding="utf-8")
        rc = export.main(["x", str(FIXTURES / "good_project"), "--out", str(out)])
        self.assertEqual(rc, 2)
        rc = export.main(["x", str(FIXTURES / "good_project"), "--out", str(out), "--overwrite"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
