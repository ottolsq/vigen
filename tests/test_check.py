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


class TestK2(unittest.TestCase):
    def test_good(self):
        p = check.Project(FIXTURES / "good_project")
        self.assertEqual(check.gate_k2(p, False), [])

    def test_over_model_cap(self):
        # bad_duration: 01 分镜表某镜 生成时长 18s > 15s 上限
        p = check.Project(FIXTURES / "bad_duration")
        f = check.gate_k2(p, False)
        self.assertTrue(any(x.gate == "K2" and "超模型上限" in x.message for x in f))

    def test_dialogue_longer_than_shot(self):
        # bad_duration: 05 某行 朗读时长 6s > 所在镜头时长 4s
        p = check.Project(FIXTURES / "bad_duration")
        f = check.gate_k2(p, False)
        self.assertTrue(any("台词朗读超镜头时长" in x.message for x in f))


class TestK3(unittest.TestCase):
    def test_good(self):
        p = check.Project(FIXTURES / "good_project")
        self.assertEqual(check.gate_k3(p, False), [])

    def test_missing_hex(self):
        # bad_anchor: 04 FORMAT 节缺 02 登记的色号 #1B2430
        p = check.Project(FIXTURES / "bad_anchor")
        f = check.gate_k3(p, False)
        self.assertTrue(any(x.gate == "K3" and "#1B2430" in x.message for x in f))

    def test_missing_character_anchor(self):
        # bad_anchor: 04 出现角色"林枫"但无 REF 绑定且锚定短语未逐字出现
        p = check.Project(FIXTURES / "bad_anchor")
        f = check.gate_k3(p, False)
        self.assertTrue(any("林枫" in x.message and "锚定短语缺失" in x.message for x in f))


class TestK4(unittest.TestCase):
    def test_good(self):
        self.assertEqual(check.gate_k4(check.Project(FIXTURES / "good_project"), False), [])

    def test_duplicate_and_dangling(self):
        f = check.gate_k4(check.Project(FIXTURES / "bad_shotid"), False)
        self.assertTrue(any("镜号重复" in x.message for x in f))
        self.assertTrue(any("引用了01分镜表不存在的镜号" in x.message for x in f))


class TestK9(unittest.TestCase):
    def test_good(self):
        self.assertEqual(check.gate_k9(check.Project(FIXTURES / "good_project"), False), [])

    def test_uncovered_plot_point(self):
        f = check.gate_k9(check.Project(FIXTURES / "bad_coverage"), False)
        self.assertTrue(any(x.gate == "K9" and "情节点" in x.message and "未覆盖" in x.message for x in f))


if __name__ == "__main__":
    unittest.main()
