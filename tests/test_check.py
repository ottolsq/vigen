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


class TestK5(unittest.TestCase):
    def test_good(self):
        self.assertEqual(check.gate_k5(check.Project(FIXTURES / "good_project"), False), [])

    def test_over_quota_and_unannotated(self):
        f = check.gate_k5(check.Project(FIXTURES / "bad_peak"), False)
        self.assertTrue(any("慢镜超配额" in x.message for x in f))          # 3处>2
        self.assertTrue(any("强调手段无峰值标注" in x.message for x in f))  # 缺 ←峰值：

    def test_annotation_must_resolve(self):
        # bad_peak 中一处标注 ←峰值：交手账R9 但 01 交手账只有 R1-R2
        f = check.gate_k5(check.Project(FIXTURES / "bad_peak"), False)
        self.assertTrue(any("峰值来源无法解析" in x.message for x in f))


class TestK6(unittest.TestCase):
    def test_good(self):
        self.assertEqual(check.gate_k6(check.Project(FIXTURES / "good_project"), False), [])

    def test_chase_without_follow(self):
        f = check.gate_k6(check.Project(FIXTURES / "bad_camera"), False)
        self.assertTrue(any("追逐" in x.message and "跟拍族" in x.message for x in f))

    def test_motive_column_format(self):
        f = check.gate_k6(check.Project(FIXTURES / "bad_camera"), False)
        self.assertTrue(any("运镜动机列不合CT1" in x.message for x in f))


class TestK7(unittest.TestCase):
    def test_good(self):
        self.assertEqual(check.gate_k7(check.Project(FIXTURES / "good_project"), False), [])

    def test_segment_without_env_motion(self):
        f = check.gate_k7(check.Project(FIXTURES / "bad_env"), False)
        self.assertTrue(any(x.gate == "K7" and "环境动态" in x.message for x in f))


class TestK8(unittest.TestCase):
    def test_good(self):
        self.assertEqual(check.gate_k8(check.Project(FIXTURES / "good_project"), False), [])

    def test_missing_section(self):
        f = check.gate_k8(check.Project(FIXTURES / "bad_skeleton"), False)
        self.assertTrue(any("FACE LOCK" in x.message and "缺节" in x.message for x in f))


class TestK10(unittest.TestCase):
    def test_good(self):
        self.assertEqual(check.gate_k10(check.Project(FIXTURES / "good_project"), False), [])

    def test_pending_text_and_dangling_ref(self):
        f = check.gate_k10(check.Project(FIXTURES / "bad_plan"), False)
        self.assertTrue(any("待补参考图" in x.message for x in f))
        self.assertTrue(any("REF-X9" in x.message and "03中无法解析" in x.message for x in f))


class TestPartial(unittest.TestCase):
    def test_partial_skips_missing_docs(self):
        rc = check.main(["x", str(FIXTURES / "partial_project"), "--partial"])
        self.assertEqual(rc, 0)   # 只有01+02：K1/K2(05)/K5-K8(04)/K10 全部静默跳过



class TestRegressions(unittest.TestCase):
    """V3.0 评审的假阴性方向（每个 Critical 一条复现测试）。"""

    def test_k1_dialogue_on_performance_line(self):
        # C4：表演注与台词同行时，台词被改仍必须报（旧实现整行被黑名单跳过）
        f = check.gate_k1(check.Project(FIXTURES / "bad_dialogue_in_perf"), False)
        self.assertTrue(any("台词与01定稿不一致" in x.message and "钥匙归别人管" in x.message
                            for x in f))

    def test_k5_segment_heading_variant(self):
        # C2：段落标题是「## 段1a」时 K5 仍须执行（旧实现按 '## 段落' 切块 → 空转）
        f = check.gate_k5(check.Project(FIXTURES / "bad_seg_heading"), False)
        self.assertTrue(any("强调手段无峰值标注" in x.message for x in f))

    def test_k6_fixed_with_wrong_row(self):
        # I7：运镜列写固定、动机报 R3（非 R7）必须报
        f = check.gate_k6(check.Project(FIXTURES / "bad_fixed_motive"), False)
        self.assertTrue(any("运镜列写固定" in x.message for x in f))

    def test_k9_missing_status_column_no_crash(self):
        # C1：情节点表无「状态」列时报 Finding，不得抛异常
        f = check.gate_k9(check.Project(FIXTURES / "bad_plot_nostatus"), False)
        self.assertTrue(any("缺「状态」列" in x.message for x in f))

    def test_k10_same_plan_id_twice_allowed(self):
        # I12：E2 的正常形态是同一张缺图挂一个 PLAN、多段共用
        f = check.gate_k10(check.Project(FIXTURES / "bad_plan_dup"), False)
        self.assertFalse(any("PLAN-SCENE-A" in x.message for x in f))

    def test_k4_body_text_is_not_shot_reference(self):
        # I8：正文「高速甩镜360度」不是镜号引用
        f = check.gate_k4(check.Project(FIXTURES / "bad_shot_text"), False)
        self.assertFalse(any("镜360" in x.message for x in f))


class TestCLI(unittest.TestCase):
    def test_unknown_gate_returns_usage_error(self):
        # C5：写错门名不得静默返回「全部通过」
        self.assertEqual(check.main(["x", str(FIXTURES / "bad_dialogue"), "--gate", "K05"]), 2)
        self.assertEqual(check.main(["x", str(FIXTURES / "bad_dialogue"), "--gate", "bogus"]), 2)

    def test_gate_filter_runs_only_selected(self):
        rc = check.main(["x", str(FIXTURES / "bad_dialogue"), "--gate", "K1", "--partial"])
        self.assertEqual(rc, 1)
        rc = check.main(["x", str(FIXTURES / "bad_dialogue"), "--gate", "K5", "--partial"])
        self.assertEqual(rc, 0)

    def test_full_stricter_than_partial(self):
        # I1：全量要求 01-05 齐备，partial 只查已有文档
        proj = str(FIXTURES / "partial_project")
        self.assertEqual(check.main(["x", proj, "--partial"]), 0)
        self.assertEqual(check.main(["x", proj]), 1)


class TestParsers(unittest.TestCase):
    """解析层单元测试（C2/I3/I4/I5/I9 的根因）。"""

    def setUp(self):
        import vigen_md
        self.md = vigen_md

    def test_blocks_split_on_any_level2_heading(self):
        lines = ["# t", "## 段1a（生成 8s）", "a", "## 镜头2（生成 5s）", "b"]
        got = self.md.blocks(lines)
        self.assertEqual([g[0][1] for g in got], ["## 段1a（生成 8s）", "## 镜头2（生成 5s）"])

    def test_shot_blocks_timecode_variants(self):
        for sep in ("–", "-", "—", "~"):
            lines = ["## 段1", "0.0s%s4.0s｜镜头1｜a" % sep, "body"]
            self.assertEqual(len(self.md.shot_blocks(lines)), 1, sep)

    def test_shot_blocks_skeleton_b_heading(self):
        lines = ["## 镜头1（0:00-0:04，生成 5s）", "body"]
        self.assertEqual(len(self.md.shot_blocks(lines)), 1)

    def test_table_rows_preserve_empty_cells_and_alias(self):
        lines = ["| 镜号 | 生成时长 | 运镜动机（CT1） |", "| --- | --- | --- |",
                 "| 1 |  | pressure(R3)：x |"]
        rows = self.md.table_rows(lines, ("镜号", "生成时长"))
        self.assertIsNotNone(rows)
        self.assertEqual(self.md.cell(rows[0], "生成时长"), "")
        self.assertEqual(self.md.cell(rows[0], "运镜动机", "动机"), "pressure(R3)：x")

    def test_dialogue_quote_structural_cue(self):
        lines = ["画面：他开口（语气：低）：\"台词A。\" 表演：核心是\"不是台词\"",
                 "镜头语言：从\"观察\"转成\"咬合\""]
        got = [t for _, t in self.md.dialogue_quotes(lines)]
        self.assertIn("台词A。", got)
        self.assertNotIn("不是台词", got)
        self.assertNotIn("观察", got)

    def test_cap_takes_range_upper_bound(self):
        # I4：3s-15s 应解析为 15，而不是 3
        lines = ["| 用途 | 模型 | 备注 |", "| --- | --- | --- |", "| 视频 | happyhorse | 4s-15s |"]
        rows = self.md.table_rows(lines, ("用途", "模型"))
        self.assertEqual(self.md.cell(rows[0], "备注"), "4s-15s")


if __name__ == "__main__":
    unittest.main()
