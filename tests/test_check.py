import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check

FIXTURES = Path(__file__).parent / "fixtures"


class TestK1(unittest.TestCase):
    def test_good_project_passes(self):
        p = check.Project(FIXTURES / "good_project")
        self.assertEqual(check.gate_k1(p, partial=False), [])

    def test_changed_dialogue_fails(self):
        p = check.Project(FIXTURES / "bad_dialogue")
        findings = check.gate_k1(p, partial=False)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].gate, "K1")
        self.assertEqual(findings[0].file, "04_视频提示词.md")
        self.assertIn("台词与01定稿不一致", findings[0].message)

    def test_action_line_with_fullwidth_colon_not_dialogue(self):
        # SCR-18 歧义陷阱：动作行不得进入台词集合（否则 good_project 会误报）
        p = check.Project(FIXTURES / "good_project")
        lines = p.doc("01")
        self.assertFalse(check._is_dialogue_line("第二格：一只手把杯子推过去。"))


if __name__ == "__main__":
    unittest.main()
