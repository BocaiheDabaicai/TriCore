# 单元注册表 —— 扫描 units/ 目录，把每个单元模块的声明收成一张表
#
# 加一个新单元 = 在 units/ 下加一个文件（里面声明 UNIT 字典 + run(ctx) 函数），别的代码一律不用改。
# 这和集群里"调度器只认统一协议"是同一个思路：把"单元长什么样"固定下来，加单元就不动框架。

import importlib
import pkgutil
from dataclasses import dataclass

from core.config import ROOT


@dataclass
class Unit:
    key: str                 # 唯一标识（接口路径、数据库里的 unit_key）
    cn_name: str             # 中文名（界面上显示）
    order: int               # 叠加次序（1、2、3…），界面上按它排
    env: str                 # 操作的是哪个系统：kingdee / oa / local
    desc: str                # 一句话说明这个单元干什么
    inputs: list[dict]       # 需要哪些输入字段：[{key, label, required, example}]
    steps: list[dict]        # 步骤声明：[{key, cn_name}]，顺序必须与代码里 ctx.step() 一致
    run: object              # 单元的执行函数 run(ctx)
    module: str              # 模块名（排查用）

    def to_dict(self, verified: bool = False, last_run: dict | None = None) -> dict:
        """给接口用的形状：不含 run（函数没法序列化）"""
        return {
            "key": self.key, "cn_name": self.cn_name, "order": self.order,
            "env": self.env, "desc": self.desc, "inputs": self.inputs,
            "steps": self.steps, "verified": verified, "last_run": last_run,
        }


_units: dict[str, Unit] = {}


def load_units(force: bool = False) -> dict[str, Unit]:
    """扫描并加载所有单元（进程内缓存；改了单元代码要重启服务）"""
    if _units and not force:
        return _units

    import units as units_pkg  # 延迟导入：避免 import 顺序问题

    loaded: dict[str, Unit] = {}
    for info in pkgutil.iter_modules(units_pkg.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"units.{info.name}")
        declared = getattr(module, "UNIT", None)
        run = getattr(module, "run", None)
        if not isinstance(declared, dict) or not callable(run):
            # 不是单元模块（比如共用的工具文件），跳过
            continue

        for field in ("key", "cn_name", "order", "env", "steps"):
            if field not in declared:
                raise ValueError(f"单元模块 units/{info.name}.py 缺少声明字段：{field}")
        if declared["key"] in loaded:
            raise ValueError(f"单元 key 重复：{declared['key']}")
        for s in declared["steps"]:
            if "key" not in s or "cn_name" not in s:
                raise ValueError(f"单元 {declared['key']} 的 steps 每项必须有 key 和 cn_name")

        loaded[declared["key"]] = Unit(
            key=declared["key"],
            cn_name=declared["cn_name"],
            order=declared.get("order", 99),
            env=declared.get("env", "local"),
            desc=declared.get("desc", ""),
            inputs=declared.get("inputs", []),
            steps=declared["steps"],
            run=run,
            module=f"units.{info.name}",
        )

    _units.clear()
    _units.update(loaded)
    return _units


def get_unit(key: str) -> Unit | None:
    return load_units().get(key)


def units_dir():
    return ROOT / "units"
