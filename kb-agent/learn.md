## 学习记录

#### 日期：2026年8月11日

- 如果我是用pycharm来创建项目的话，是不是创建好了就可以直接引入这些依赖包

- `requirements.txt`对每个python项目都是通用的吗？

- 可是如果是我写的话，我只会写fastapi，另外一个我不知道是干什么的？

- `uvicorn`很常用吗？

- 我看项目里面没有`/docs`路径，怎么会显示一个标准的接口文档？

- 如果要是我设置了路由把它占用了，会出现什么情况？

- `router`对象的`tags`设置有什么作用？

- `from pydantic import BaseModel`这是什么依赖包，用的模块有什么作用？

- 今天是第二天了，我忘记了这个项目该怎么启动？
  
  - 这是不是弄一个属于这个项目的`README.md`文档，并把项目怎么启动的方法写在里面比较好？

- 这句语言怎么理解？`matched = [t for t in FAKE_TEMPLATES if any(word in t["name"] for word in req.description)]`

- 这句话怎么理解？`db: Session = Depends(get_db),           # ← 注入数据库连接`
  
  - 相当于`db: Session = Depends(get_db)`这句话里，db是什么类型？
  - 等于号和后面的内容怎么理解？
  - 那这个Depends在这里是什么作用？
  - 那为什么我这里不直接写`db: Session = get_db()`

- 进入函数以后，这句话又是什么意思？`query = db.query(Policy)`，这个`Policy`怎么理解？

- 这些引入的东西是干什么用的？from sqlalchemy import String, Text  
  from sqlalchemy.orm import Mapped, mapped_column  
  from core.database import Base

- 创建方法仔细讲一下`create_policy`

- 这个`database`里的内容仔细讲一讲吧
  
  - 为什么这里需要三个斜杠来表示文件名称

- 你是怎么排查出是版本不兼容的问题的？另外我现在的开发环境是使用pycharm，我怎么查看kb_agent.db文件

- 这个种子数据是独立运行的吗？一般来说，该怎么创建一些有效果的测试数据，我们这样做是好的吗？

- 像这样的语法是什么意思？`question: str | None = None`


