# 演示单元 —— 不碰任何真实系统的自检单元
#
# 它的作用：在动金蝶/OA 之前，先把"运行 → 分步 → 截图 → 断言"这条流水线跑通。
# 换句话说，它是"操作台本身的最小单元"——操作台不通，后面写什么单元都无从验证。

from core.config import STATIC_DIR

UNIT = {
    "key": "demo_form",
    "cn_name": "演示：本地表单",
    "order": 0,
    "env": "local",
    "desc": "打开本地演示页 → 填三个字段 → 提交 → 断言页面回显正确（不碰真实系统）",
    "inputs": [
        {"key": "supplier_name", "label": "供应商名称", "required": True,
         "example": "贵阳示例商贸有限公司"},
        {"key": "credit_code", "label": "统一社会信用代码", "required": False,
         "example": "91520000MA000000XX"},
        {"key": "contact", "label": "联系人", "required": False, "example": "张三"},
    ],
    "steps": [
        {"key": "open", "cn_name": "打开本地演示页"},
        {"key": "fill", "cn_name": "填写三个字段"},
        {"key": "submit", "cn_name": "点击提交并断言回显"},
    ],
}


def run(ctx):
    url = (STATIC_DIR / "demo_form.html").as_uri()

    with ctx.step("open"):
        ctx.page.goto(url)
        ctx.log(f"已打开 {url}")

    with ctx.step("fill"):
        ctx.page.fill("#supplier-name", ctx.inputs.get("supplier_name", ""))
        ctx.page.fill("#credit-code", ctx.inputs.get("credit_code", ""))
        ctx.page.fill("#contact", ctx.inputs.get("contact", ""))
        ctx.snap("filled")          # 主动截一张：证明字段真的填进去了

    with ctx.step("submit"):
        ctx.page.click("#submit")
        result = (ctx.page.text_content("#result") or "").strip()
        expect = ctx.inputs.get("supplier_name", "")
        # 断言：页面上必须回显出我们填的供应商名——这一步是"系统判定"的那一半
        assert expect in result, f"断言失败：页面显示「{result}」，没有包含「{expect}」"
        ctx.snap("submitted")
        ctx.log(f"页面回显：{result}")
