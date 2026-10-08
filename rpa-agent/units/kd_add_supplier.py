# 单元 ①：在金蝶里添加供应商（骨架，选择器待截图确认后填）
#
# 现状：只把"要哪些输入、分几步"声明出来，run() 直接报"尚未实现"。
# 为什么先摆骨架：操作台靠声明渲染界面（输入字段清单、步骤列表），
# 声明先落地，界面和留痕就能先验证；选择器等看清页面结构再补。
#
# ★ 待补的东西（等金蝶页面截图到位）：
#   1. SEL 里每个选择器（优先用 label 文本 / name 属性这类稳定特征，不用 nth-child 位置）
#   2. 输入字段清单（下面 inputs 是按业务描述猜的，要以真实页面为准）
#   3. 保存后的断言方式（回到列表页搜一下，确认这条供应商真的建出来了）

from core.config import KINGDEE_URL

# 选择器集中放这里：将来金蝶改版，只改这一块
SEL = {
    "供应商菜单": "",        # 例：金蝶里的"基础资料 → 供应商"入口
    "新增按钮": "",
    "供应商名称": "",
    "信用代码": "",
    "联系人": "",
    "联系电话": "",
    "保存按钮": "",
    "保存成功提示": "",
}

UNIT = {
    "key": "kd_add_supplier",
    "cn_name": "① 添加供应商",
    "order": 1,
    "env": "kingdee",
    "desc": "在金蝶「基础资料-供应商」里新建一条供应商（写生产系统，先人工核对）",
    # 字段清单是按业务描述拟的，等截图确认后改
    "inputs": [
        {"key": "supplier_name", "label": "供应商名称", "required": True, "example": ""},
        {"key": "credit_code", "label": "统一社会信用代码", "required": True, "example": ""},
        {"key": "contact", "label": "联系人", "required": False, "example": ""},
        {"key": "phone", "label": "联系电话", "required": False, "example": ""},
        {"key": "address", "label": "地址", "required": False, "example": ""},
    ],
    "steps": [
        {"key": "enter", "cn_name": "进入供应商列表"},
        {"key": "new", "cn_name": "点新增，打开录入表单"},
        {"key": "fill", "cn_name": "填写供应商字段"},
        {"key": "save", "cn_name": "保存"},
        {"key": "assert", "cn_name": "回列表确认已创建"},
    ],
}


def run(ctx):
    with ctx.step("enter"):
        if not KINGDEE_URL:
            raise RuntimeError("尚未配置 KINGDEE_URL（在 rpa-agent/.env 里填金蝶网址）")
        raise RuntimeError("单元尚未实现：等金蝶「供应商」相关页面截图到位后填选择器（见文件顶部待补清单）")
