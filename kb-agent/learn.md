## 学习记录

> 你先熟悉一下项目，这个项目是从0开始一点一点建设起来的，通过AI和自我学习思考构建成现在的状况，我也是一个小白，目前也正在学习中，回答上可以讲得简洁、精炼一点，不用过于照顾我
> 
> 好的今天先结束吧，记得更新相关的文档内容，learn.md的内容不用更新

#### 日期：2026年8月25日

- 这样的话语是什么意思？`yield delta`

- 这个函数我实在是看不懂，请你帮我讲解一下`split_chunks`

- 我感觉到头晕，我就先看一看、跑一跑了，代码是在不好瞬间理解

- 项目写到这里，我觉得就比较好了，我目前觉得这应该是一个项目集合体的形式，除了企业知识问答，应该还有企业项目文档审查、企业数据分析、企业通知助手这一系列的Agent，然后汇总到一个叫做企业AI助手的问答体上，由这个AI助手来决定问题应该使用哪个Agent进行回答，甚至是结合几个Agent进行回答

- 我觉得还是将项目根目录下，除了`.claude,.git,kb-agent`之外的其它项目专门放进一个遗弃的文件夹下，并用文件注明，存在仅为纪念早期AI开发意义，并在根目录下为其它的Agent先创建文件夹和`README.md`文档，同时在根目录下为这个集群的项目创建一个新的`README.md`文件夹，并说明这个项目，以及将更新日志也迁移过来，然后接下来我们来讨论这个企业AI助手该怎么做？你觉得如何？

- 这份框架和建议先记录好，然后把 ai-assistant文件夹也先建好，并说明等Agent长大之后再拆分出去使用，另外我谈谈我的想法，你看看怎么样，我觉得应该是多个Agent服务，提供统一的智能问答接口，接入一个统一的AI助手服务上进行使用，然后有一个支持的前端界面属于这个AI助手服务，我想的是最终通过前端界面来实现我的整个AI项目

- 我这里有一个疑问，这样设计架构相比于全部杂糅在一起有什么好处？

- 其实目前我更想把雏形的AI助手服务和前端界面先做出来，后面再做其他Agent的时候，再接上去就可以了，这样可以有阶段性成果出来，能够先给企业带来一些帮助，你看看怎么样？

- 服务的技术栈还是保持一致，前端使用vite新版本来实现，先把这个接下来做的事情记录下来，然后也是从最小单位开始，带着我一步一步构建

#### 日期：2026年8月24日

- 在这一步里，我现在对于文件上传有一个新的想法，我们分了制度管理、文档问答、流程助手，可实际上我觉得比较好的一个应用方案就是，我们不再主动去区分它属于什么内容，而是提供一个统一的上传接口，分析并识别它，将它的内容进行保存，走出现在学习AI项目阶段的属于什么分类，就用什么上传接口，你看看怎么样？

- 我觉得可以不用当下的接口和数据库结构，本身我在学习过程中，就是在探索一个较好的运行方式，我觉得可以建一种新表，支持各种分类类型，统一到一处，连同上传的接口，也放在同一个新分组下面，你觉得怎么样？

- 我现在上传了一个文档，现在好像出了点问题，这个文件似乎只传了部分内容，你看一看

- 你发现的这个问题很好，你觉得像表格这样的东西，我需不需要统一用一个表存，另外文件上传这里，我为项目配置的是deepseek-flash模型，你觉得改成deepseek-v4-flash-vision-exp怎么样？我目前是确定这个项目是做企业知识问答用的

- 我提一个问题，构建新表是为什么才会去构建？

- 另外一个问题是，这个上传的文件，没有分类，分类列显示的是未分类，按道理来说，通过`classify_upload`，应该就会给这个文件一个分类，但实际上没有，我无法确定是不是AI没有工作？

- 等一下，这里的分类优化工作，我觉得不要局限于之前的分类，我觉得就由AI去判断和决定这个文件属于什么分类

- 不好意思，是我把category和kind弄错了，这里kind是AI自动识别得到的，只是我想在category没有提交指定内容的时候，也自动生成一个合适的category名称

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
