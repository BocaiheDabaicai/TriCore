## 学习记录

> 你先熟悉一下项目，这个项目是从0开始一点一点建设起来的，通过AI和自我学习思考构建成现在的状况

#### 日期：2026年8月20日

- 现在新版的deepseek v4 pro收费很贵，和新的deepseek v4 flash相比起来提升大不大，和旧版本的deepseek v4 pro相比又如何，我好判断是否切换模型

- 你讲解一下这个配置是什么意思？

```powershell
$env:ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
$env:ANTHROPIC_AUTH_TOKEN="<你的 DeepSeek API Key>"
$env:ANTHROPIC_MODEL="deepseek-v4-pro[1m]"
$env:ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-v4-pro[1m]"
$env:ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-v4-pro[1m]"
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL="deepseek-v4-flash"
$env:CLAUDE_CODE_SUBAGENT_MODEL="deepseek-v4-flash"
$env:CLAUDE_CODE_EFFORT_LEVEL="max"
$env:CLAUDE_CODE_AUTO_COMPACT_WINDOW="786432"
```

- 我想说的是你claude，我给你的配置，使用现在最新的deepseek v4 flash和pro区别大吗？按照上面这样配置来说，还是全部换成deepseek v4 flash

- 基准测试就不做了吧？这是必要的吗？

- JSON格式与BLOB格式相比起来，做数据的存储有什么优缺点？

- 服务层是什么意思？怎么忽然我这个项目有了层级了？

- 这句话是什么意思？`current = f"{current}\n{p}" if current else p`

- 这两个方法我不理解，你讲一讲`split_chunks`,`add_chunks`

#### 日期：2026年8月19日

- null

#### 日期：2026年8月14日

- 如果先删除模板，再删除步骤，会出现什么问题？

- 这句话是什么意思？`client.chat.completions`

- 另外，我觉得很奇怪，为什么core、models、services文件夹下都要放一个`__init__.py`文件，而且内容都是空

- 这个next函数时起到什么作用？`chosen = next((t for t in templates if t.name == picked_name), None)`

- 这句话是什么意思？`matched = [{"type": t, "id": cid, "title": title, "content": content} 
  for _, t, cid, title, content in top]`

- 用单字匹配累加分的方式来寻找符合的`policy`和`document`不是太好，这样的问题人为使用代码控制，估计仍然会有偏差，有没有可能使用其他的什么AI大模型来对数据进行相关度排序，替代这一块代码？

- 流程助手、制度问答、文档问答，以及之后可能会新加的分组内容，我想集中成一个专门的问答接口来进行使用，你觉得怎么样？

- 这里有一个问题，如果之后的制度、文档等等内容越来越多，甚至总数到达了几万条，这会不会影响结果生成的效率？
  
  - 做之前，我还有一个问题，是不是传统的其他大型电商平台、外卖、抖音、小红书之类的平台，为了保证几毫秒的服务响应速度，用的也是向量库？【答案：核心思路：能提前算好的提前算，能缓存的缓存，扛不住的就拆开并行。】
  
  - 我还有另外一个问题，CDN就近请求可以省略网络请求的时间；网关和负载均衡保证了服务被接收和处理；数据库的构建、向量库和向量检索库的构建、设计提供了更快速地需求数据构建能力；那redis缓存是干什么作用的？

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
