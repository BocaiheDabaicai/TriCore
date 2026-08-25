# 教学用观察脚本：把 split_chunks 的三个阶段拆开，打印每一步的中间结果
# 用法：.venv/Scripts/python debug_split_chunks.py
# 看完删掉即可，和项目代码无关

from core.database import SessionLocal
from models.knowledge import Knowledge

db = SessionLocal()
item = db.query(Knowledge).filter(Knowledge.id == 24).first()
text = item.content
db.close()

chunk_size = 400
overlap = 50

print("========== 阶段一：拆行 ==========")
text = text.strip()
lines = [seg.strip() for seg in text.split("\n") if seg.strip()]
print(f"总行数：{len(lines)}")
for i, line in enumerate(lines[:8]):
    print(f"  行{i:2d}: {line[:50]}")

print("\n========== 阶段二：打标签（是不是表格行） ==========")
is_row = [" | " in line for line in lines]   # 第一遍：含 | 的就是表格行
for idx in range(len(lines)):                # 第二遍：短行且紧邻表格行 → 传染
    if is_row[idx]:
        continue
    short = len(lines[idx]) < 40
    prev_row = idx > 0 and is_row[idx - 1]
    next_row = idx + 1 < len(lines) and is_row[idx + 1]
    is_row[idx] = short and (prev_row or next_row)

# 只看表格行分布（True 的行）
for i, flag in enumerate(is_row):
    if flag:
        print(f"  行{i:2d} [表格行]: {lines[i][:50]}")

print("\n========== 阶段三：合并单元 ==========")
units = []
i = 0
while i < len(lines):
    if is_row[i]:
        rows = []
        while i < len(lines) and is_row[i]:
            rows.append(lines[i])
            i += 1
        units.append(("\n".join(rows), True))
    else:
        units.append((lines[i], False))
        i += 1
print(f"单元总数：{len(units)}")
for j, (unit, is_table) in enumerate(units):
    kind = "表格单元" if is_table else "普通单元"
    print(f"  单元{j:2d} [{kind}] 长度{len(unit):4d}: {unit[:40]}")

print("\n========== 阶段四：装块 ==========")
chunks = []
current = ""
for unit, is_table in units:
    if is_table and current:            # 规则1：表格要独立成块，先封箱
        chunks.append(current)
        current = ""
    if current and len(current) + 1 + len(unit) > chunk_size:   # 规则2：装不下就封箱
        chunks.append(current)
        current = ""
    current = f"{current}\n{unit}" if current else unit
    while len(current) > chunk_size:    # 规则3：超长硬切，带 50 字重叠
        chunks.append(current[:chunk_size])
        current = current[chunk_size - overlap:]
if current:
    chunks.append(current)

print(f"最终块数：{len(chunks)}")
for j, c in enumerate(chunks):
    print(f"  块{j:2d} 长度{len(c):4d}: {c[:50]}")
