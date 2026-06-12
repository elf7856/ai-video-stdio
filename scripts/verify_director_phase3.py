"""
Phase 3 离线验证：bible-aware 视频 prompt

不打真实 LLM。截获 conversion_prompt 文本，验证 bible 上下文被正确注入：
1. scene_context 出现在模板里
2. characters_in_shot 出现在模板里
3. transition=continuous 时附带 "Begin where the previous shot ended" + 上一镜头摘要
4. transition=cut（或缺省）时不带承接指令
5. transition=match_cut 时带 "echoes the previous shot" 指令
6. 不传任何上下文（向后兼容）也不会报错

跑法：
    python scripts/verify_director_phase3.py
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def run_one(transition, scene_ctx=None, chars=None, prev_summary=None):
    """调用一次 convert_image_to_video_prompt，捕获模板内容"""
    from app.services.video_generation.agents.prompt_evaluator_agent import (
        PromptEvaluatorAgent,
    )

    evaluator = PromptEvaluatorAgent()

    captured = {}

    def fake_call(messages, temperature=0.5, **kw):
        captured["text"] = messages[0]["content"]
        return {"content": "fake video prompt output"}

    evaluator.llm.call = fake_call

    await evaluator.convert_image_to_video_prompt(
        image_prompt="A cat walks down the alley",
        duration=6.0,
        visual_style_guide={"color_palette": "warm tones", "lighting_style": "soft"},
        has_reference_image=True,
        scene_context=scene_ctx,
        characters_in_shot=chars,
        previous_shot_summary=prev_summary,
        transition=transition,
    )
    return captured["text"]


async def test_continuous_includes_previous():
    text = await run_one(
        transition="continuous",
        scene_ctx={"location": "rooftop", "time_of_day": "dusk", "mood": "tense"},
        chars=["Whiskers"],
        prev_summary="The cat leaps across rooftops in slow motion",
    )
    assert "CONTINUOUS" in text or "continuous" in text.lower(), "continuous 标识未出现"
    assert "Begin where the previous shot ended" in text, "缺承接指令"
    assert "The cat leaps across rooftops" in text, "上一镜头摘要未注入"
    assert "rooftop" in text, "scene_context location 未注入"
    assert "dusk" in text, "scene_context time 未注入"
    assert "Whiskers" in text, "characters_in_shot 未注入"
    print("✅ continuous：scene/characters/前镜头摘要全部注入")


async def test_match_cut_uses_echo():
    text = await run_one(
        transition="match_cut",
        prev_summary="A cup of coffee tilts and pours",
    )
    assert "MATCH CUT" in text or "match_cut" in text.lower(), "match_cut 标识未出现"
    assert "echoes the previous shot" in text or "visually rhymes" in text, "缺 echo 指令"
    assert "A cup of coffee tilts" in text, "上一镜头摘要未注入"
    print("✅ match_cut：echo 指令 + 上一镜头摘要注入")


async def test_cut_is_independent():
    text = await run_one(
        transition="cut",
        scene_ctx={"location": "street", "time_of_day": "day", "mood": "calm"},
        prev_summary="Some previous shot text",
    )
    # cut 时不应该出现承接指令
    assert "Begin where the previous shot ended" not in text, "cut 不应承接"
    assert "echoes the previous shot" not in text, "cut 不应 echo"
    assert "independent shot" in text or "CUT" in text, "应有 cut 标识"
    # cut 时不应注入上一镜头摘要（避免误导 LLM）
    assert "Some previous shot text" not in text, "cut 不应注入上一镜头摘要"
    print("✅ cut：独立镜头，不承接")


async def test_no_context_backward_compat():
    text = await run_one(transition=None)
    # 没有 transition → 默认走 cut 分支
    assert "independent shot" in text or "CUT" in text, "缺省应走 cut"
    # 不应崩
    assert "fake video prompt output" not in text, "捕获错误"
    print("✅ 无上下文调用：向后兼容，等同于 cut")


async def test_empty_chars_handled():
    """characters_in_shot=None 不应炸，也不应注入空名单"""
    text = await run_one(transition="cut", chars=None)
    assert "Characters present" not in text, "空角色不应渲染 characters_block"
    text2 = await run_one(transition="cut", chars=[])
    assert "Characters present" not in text2, "空 list 也不应渲染 characters_block"
    print("✅ 空 characters_in_shot 处理正确")


async def main():
    print("=" * 60)
    print("Phase 3 离线验证（bible-aware video prompt）")
    print("=" * 60)
    await test_continuous_includes_previous()
    await test_match_cut_uses_echo()
    await test_cut_is_independent()
    await test_no_context_backward_compat()
    await test_empty_chars_handled()
    print()
    print("=" * 60)
    print("✅ 全部通过 — Phase 3 OK")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
