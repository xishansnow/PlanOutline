# 基于 DGGS 的研究规划：核心方法、领域共性基础与应用验证

本文为研究规划总览，各论文的详细方案见独立文档（目前已建立板块一：[板块一/](板块一/) 与板块八的 8-1：[板块八/](板块八/)）。

研究主体为四个核心方法板块与三个领域共性基础板块：板块一评估并演进轴对齐剖分网格（以 GeoSOT 为核心案例），板块二夯实 DGGS 计算基础，板块三刻画空间不确定性，板块四构建全球位置编码与网格基础模型；板块五、六、七分别把核心方法落到低空空域、地球系统模式与海量时空数据组织三个领域的共性基础问题上。应用层分为无人智能装备、地球系统模式与时空大数据三组，分别验证板块五、六、七，只提供验证场景。板块一与板块二宜最先推进。此外设探索性板块八，研究 DGGS 能否改善世界坐标系下三维重建与视图合成的精度、分块融合与结果组织，先做 8-1 的基准，通过判定关口后再推进其余。

## 总体架构

![总体架构：核心方法与领域共性基础板块 35 篇（另有探索性板块八 3 篇，图中以虚线框表示），应用层三组 20 篇](figures/总体架构图.svg)

左侧四个核心方法板块中，板块一从轴对齐剖分的高层视角审视剖分本身，其余三个提供网格计算、不确定性与学习能力；中间三个领域共性基础板块把它们转化为低空空域、地球系统模式与时空数据组织的共性问题，右侧三组应用分别对其验证。高亮为建议优先推进的论文，各组应用所验证的方法成果见应用层 A、B、C 三组表的“验证的方法成果”列。

## 板块一：轴对齐剖分网格的适用性评估与演进

本板块站在轴对齐剖分网格的高层视角设置：研究对象是边界沿坐标轴方向、按层级逐级细分的一类离散全球网格，以经纬度上轴对齐的狭义网格为主（GeoSOT、Geohash、WorldCRS84Quad、GNOSIS Global Grid、北斗网格位置码、WebMercatorQuad、Open Location Code），以投影平面上轴对齐的广义网格与六边形网格为对照。GeoSOT 是 GB/T 40087-2021、北斗网格位置码（GB/T 39409-2020）与北斗剖分时间码（GB/T 42578-2023）的共同技术基础，是本板块的核心案例与演进对象。

立场是没有最好的 DGGS，只有最适用的 DGGS：网格的每项特性在某些需求下是代价，在另一些需求下是优势，评估的目的是弄清什么需求适合什么网格。1-1 在轴对齐剖分的层面完成评估，给出应用画像、指标体系与适用域；1-2 至 1-4 针对评估中识别的共性代价，提出对一类轴对齐网格通用的方法，以 GeoSOT 为实现主线；1-5 针对 GeoSOT 的个性代价形成标准修订建议；1-6 研究网格之间的转换与互操作，使适用域不同的网格可以并存。以上均以保持标准兼容的方式扩大适用域。与板块二的分工是：板块二在现有剖分上构建计算能力，本板块评估并改进剖分本身，其评估结论为其余各板块提供设计约束。基本原则是核心编码不变，以扩展单元、派生视图、附加层等方式演进，必要时形成标准修订建议。1-1 宜优先推进。

### 1.1 特性清单

| 特性（代价侧） | 表现 | 影响 | 优势（适用的需求） | 应对（规避 / 补偿 / 改进） |
| --- | --- | --- | --- | --- |
| 非等面积与形状畸变 | 网格面积随纬度按余弦收缩，高纬度网格狭长 | 统计须面积加权；图神经网络节点不均匀；相对等面积网格处于劣势 | 区域尺度内几乎无影响；单元边界与经纬度格网一致 | 区域尺度可规避；跨区域统计按面积加权；1-3 |
| 两极奇异 | 经线在极点汇聚，近极网格退化；GeoSOT 与北斗网格位置码均在南北纬 88°～90° 合并网格（GB/T 40087-2021、GB/T 39409-2020），Geohash 不作处理 | 极区邻接关系复杂，全球连续计算需特殊处理 | 应用范围在 88° 以内时不涉及 | 应用限于 88° 以内即可规避；1-4 |
| 扩展剖分的代价 | 经度扩展到 512°，度到分、分到秒各扩展到 64 | 编码空间大量无效；Z 序在无效区域跳变；出现部分有效网格 | 键值存储不受影响；换得度、分、秒的整数层级 | 稀疏存储可规避；1-5 |
| 层级过渡处尺寸不一致 | 例如 1° 剖分到 32′ 时第二个子网格仅 28′ 有效 | 同层网格不等价，误差分析与规范形式需额外处理 | 与度分秒表示的数据与图幅整数对齐 | 选用单元完整有效的层级；1-5 |
| 边界问题 | 跨越粗层级边界的小对象，最小包围网格骤然变大，工程上只能退而用中心点编码 | 小对象被过粗表达，查询精度与效率下降 | 点对象与层级前缀查询不受影响 | 以尺寸相称层级的至多 2×2 多单元覆盖补偿；1-2 |
| Z 序局部性一般 | 多尺度 Hilbert 曲线的空间连续性比 Z 序高 15% 到 30% | 作为索引键时聚簇性能非最优 | 前缀包含关系直接对应层级包含 | 点查询与前缀查询影响小；大窗口拆分区间；2-5、2-6 |
| 维度不协调 | 高度维、时间维与水平维的剖分规则和层级不对齐 | 四维编码缺乏统一的层级对应 | — | 系统内固定层级配比；1-5 |
| 编码形式多样 | 四进制字符码、二进制整数、混合进制字符码并存 | 跨系统互操作需反复转换 | — | 系统内只用一种主码；1-5 |

各特性的适用域与逐项应对见 [1-1 文档 4.6 节](板块一/1-1_剖分几何质量定量诊断.md)。

### 1.2 研究内容

#### 1.2.1 轴对齐剖分网格的适用性评估（1-1）

详细方案：[板块一/1-1_剖分几何质量定量诊断.md](板块一/1-1_剖分几何质量定量诊断.md)

基本立场是没有最好的 DGGS，只有最适用的 DGGS。研究对象从 GeoSOT 扩展为轴对齐剖分网格这一类：以经纬度上轴对齐的 GeoSOT、Geohash、WorldCRS84Quad、GNOSIS Global Grid、北斗网格位置码、WebMercatorQuad、Open Location Code 为主要对象，以在投影平面上轴对齐的 HEALPix、S2 等为对照，GeoSOT 作为重点案例。以坐标变换、根区域、各轴细分比、整数对齐、极区处理、编码顺序六项设计参数刻画这类网格，把各项特性归因到参数上，标明其在何种需求下是代价、何种需求下是优势，区分轴对齐固有的共性特性（面积、形状、极区）与具体设计带来的个性特性（如 GeoSOT 的无效编码与层级过渡）。以应用画像刻画需求，建立覆盖单元几何、邻接拓扑、层级结构、编码与键空间、对象表达、数据对齐的 10 项核心指标，与 2-5 的聚簇指标互补，由需求推出各网格的适用域；在低空、全球气候与城市大数据三类场景下，以只改变一个设计参数的对照网格检验指标预测的适用性排序是否与任务中的实际排序一致 [^b1-1][^b1-2]。

关键问题：指标能否预测任务中的适用性排序，以及特性如何归因到设计参数。

#### 1.2.2 有范围对象的表达与扩展单元（1-2）

详细方案：[板块一/1-2_边界问题与扩展单元.md](板块一/1-2_边界问题与扩展单元.md)

借鉴 XZ 序与松散四叉树的思想 [^b1-3]，为每个网格定义向外扩展的“扩展单元”，使跨边界的小对象能以与其尺寸相称的层级表达；扩展信息以附加位承载，不改变标准编码。边界问题是所有层级网格的共性，方法对层级轴对齐网格通用，以 GeoSOT 为实现主线，另选 Geohash、Open Location Code 验证。

关键问题：扩展单元引入重叠后，规范形式与集合运算（2-1）如何保持唯一与封闭。

#### 1.2.3 等面积派生视图与守恒重映射（1-3）

详细方案：[板块一/1-3_等面积派生视图.md](板块一/1-3_等面积派生视图.md)

在经纬度轴对齐网格（以 GeoSOT 为实现主线）之上构建等面积派生视图，例如基于等积纬度变换的派生网格，或按面积均衡原则聚合的网格组，并给出与 GeoSOT 网格的精确对应关系；服务于统计、图神经网络（2-4）、不确定性（板块三）与地球系统模式（板块六）。

关键问题：派生视图与原网格的边界不重合时，对应关系与守恒如何保证。

#### 1.2.4 极区剖分与衔接（1-4）

详细方案：[板块一/1-4_极区剖分与衔接.md](板块一/1-4_极区剖分与衔接.md)

以标准现行的 88°～90° 合并规则为基线，评估其适用边界，补全极区与常规区之间的邻接与层级衔接规则，并提出渐进经向合并与方位等积极冠两类改进方案。极区奇异是狭义轴对齐网格的共性，方案以经纬度边界为前提，以 GeoSOT 为实现主线，并与 GNOSIS 的变宽行对照。

关键问题：在保持编码兼容的前提下，使极区邻接计算（2-2）与常规区统一。

#### 1.2.5 编码空间与层级过渡的规范化（1-5）

详细方案：[板块一/1-5_编码空间与层级过渡规范化.md](板块一/1-5_编码空间与层级过渡规范化.md)

系统处理无效编码与部分有效网格，规范层级过渡处的尺寸不一致；以二进制整数作为统一主码，字符码作为派生表达，形成标准修订建议。存储排序的评估并入 2-5、2-6（见 2.2.6）。

关键问题：任何修订都须向后兼容既有数据与终端。

#### 1.2.6 轴对齐网格间的转换与互操作（1-6）

详细方案：[板块一/1-6_轴对齐网格间的转换与互操作.md](板块一/1-6_轴对齐网格间的转换与互操作.md)

狭义轴对齐网格的单元边界都是经线与纬线，网格间单元的交叠面积有闭式解，不需要多边形裁剪。在此基础上研究网格之间的层级对应、守恒重映射，并按 OGC API – DGGS 的 DGGRS 定义描述 GeoSOT 这类网格，列出无法直接表达之处，作为注册与标准修订的依据。与 2-1、2-2 的分工是：后者处理单一网格内的运算，本方向处理网格之间的关系。

关键问题：不依赖多边形裁剪，如何精确且守恒地在不同轴对齐网格之间转换。

### 1.3 论文

| 编号 | 题目方向 | 服务 |
| --- | --- | --- |
| 1-1 | [轴对齐剖分网格的适用性评估：特性画像、适用域与选型依据](板块一/1-1_剖分几何质量定量诊断.md) | 2-5、板块五至七 |
| 1-2 | [层级轴对齐网格中有范围对象的表达：扩展单元与覆盖优化](板块一/1-2_边界问题与扩展单元.md) | 2-1、7-1 |
| 1-3 | [经纬度轴对齐网格的等面积派生视图与守恒重映射](板块一/1-3_等面积派生视图.md) | 2-4、板块三、板块六 |
| 1-4 | [经纬度轴对齐网格的极区剖分与全球衔接](板块一/1-4_极区剖分与衔接.md) | 2-2、板块六 |
| 1-5 | [GeoSOT 编码空间与层级过渡的规范化及标准修订建议](板块一/1-5_编码空间与层级过渡规范化.md) | 2-1 |
| 1-6 | [轴对齐剖分网格间的转换与互操作：层级对应、守恒重映射与 DGGRS 注册](板块一/1-6_轴对齐网格间的转换与互操作.md) | 7-1、板块六 |

### 1.4 定位与风险

- 表述分寸：以“演进”而非“否定”立论，强调评估服务于标准体系的完善；优势与代价并重，缺陷只指对某类需求构成代价的特性。
- 兼容性：所有改进以附加层或派生视图实现，不破坏既有数据与终端。
- 国际对齐：OGC 抽象规范 Topic 21 第二版的修订内容含对轴对齐单元的支持，轴对齐专门部分为后续计划（[OGC 20-040r3](https://docs.ogc.org/as/20-040r3/20-040r3.html)），评估与演进成果可为 GeoSOT 注册为 DGGRS 提供依据。

延伸阅读：[^b1-1][^b1-2][^b1-3]

以上三条已据 Crossref 核对。

[^b1-1]: Kimerling A J, Sahr K, White D, Song L. Comparing geometrical properties of global grids. Cartography and Geographic Information Science, 1999, 26(4): 271-288. DOI: 10.1559/152304099782294186.
[^b1-2]: Sahr K, White D, Kimerling A J. Geodesic discrete global grid systems. Cartography and Geographic Information Science, 2003, 30(2): 121-134. DOI: 10.1559/152304003100011090.
[^b1-3]: Böhm C, Klump G, Kriegel H-P. XZ-ordering: a space-filling curve for objects with spatial extension. SSD 1999, LNCS 1651: 75-90. DOI: 10.1007/3-540-48482-5_7.

## 板块二：DGGS 本身的深入创新研究

目标是把 GeoSOT 从数据组织工具提升为可支撑实时决策的空间计算引擎，核心解决四维时空表达与编码关系的精确高效计算两个问题。

### 2.1 关键问题

包含与父子关系可由编码前缀直接判断，真正困难的是四类计算：

1. 邻接关系：Z 序曲线上相邻的编码空间上未必相邻，反之亦然。
2. 跨层级集合拓扑：由不同层级网格组成的多尺度集合之间的相交、包含、相接判断。
3. 边界特殊情况：两极、180° 经线、GeoSOT 扩展剖分空间中的无效编码区域。
4. 海量查询效率：如上万条四维航迹两两之间的重叠判断。

此外，GeoSOT 按经纬度剖分，网格实际尺寸随纬度变化，高度方向剖分规则也需明确。所有关系判断均要求精确，不接受近似结果。

### 2.2 研究方向

#### 2.2.1 四维时空网格模型与编码代数（2-1）

将航迹表达为“网格码 + 时间片”序列，以编码相同或父子包含判定时空重叠；分析判定复杂度与离散化带来的保守性；与 H3、S2、均匀体素、八叉树对比，突出标准化编码（GB/T 40087-2021）与多尺度一致性。

#### 2.2.2 编码关系精确算法（2-2）

针对邻接、跨层级集合拓扑与边界情况，设计与层级无关的位运算算法，并给出正确性证明。本节界定待求的编码关系与正确性标准，2.2.3 给出自动发现这些算法的方法，两者共同构成论文 2-2。

#### 2.2.3 学习化编码关系计算（2-2）

神经网络只做加速，最终判定始终由精确编码运算完成。四种范式如下：

| 范式 | 思路 | 精确性 | 成熟度 |
| --- | --- | --- | --- |
| AI 自动发现算法 | 大模型 + 进化搜索生成位运算程序，以几何暴力计算为真值裁判 | 精确且可验证 | 前沿，DGGS 上未见 |
| 学习化空间索引 | 模型学习编码分布替代索引树 | 可保证 | 较成熟，可迁移 |
| 学习化过滤 + 精确校验 | 网络筛候选，编码运算确认，后备结构保证零漏报（学习化布隆过滤器见 [^b2b-5][^b2b-6]） | 可保证 | 框架成熟，需适配 |
| 神经算法推理 [^b2b-4] / 网格嵌入 | 网络模仿算法或向量化网格 | 近似 | 探索性，仅用于相似度、语义检索 |

主线为 AI 自动发现算法，先例包括 AlphaDev（Nature, 2023）[^b2b-1]、FunSearch（Nature, 2024）[^b2b-2] 与 AlphaEvolve（2025）[^b2b-3]，其产出是可读、可测试、可证明正确的代码而非黑盒网络。学习化索引可借鉴 ZM 索引（[MDM 2019](https://vbn.aau.dk/da/publications/learned-index-for-spatial-queries)）、RSMI（[VLDB 2020](https://vbn.aau.dk/ws/files/391644098/p2341_qi.pdf)）与保证包含、相交查询精度的 GLIN（[GitHub](https://github.com/DataOceanLab/GLIN)），评测见 [arXiv 2606.19034](https://arxiv.org/pdf/2606.19034)；GeoSOT 编码与 Z 序同构，可直接迁移。

#### 2.2.4 高频更新的四维时空索引（2-3）

与 2-6（见 2.2.6）分工明确，2-6 决定数据在一维存储中如何排列，本方向在排列已定的前提下解决实时位置流带来的高频插入与更新。UTM 中无人机位置每秒更新，而插入与更新代价正是学习化索引的主要短板。

- 经典移动对象索引：TPR 树以参数化包围盒索引持续运动的对象 [^b2a-1]；Bx 树 [^b2a-2] 以空间填充曲线加 B+ 树、按时间分区组织移动对象，结构上与 GeoSOT 编码最接近，是首选基线。
- 可更新的学习化索引：ALEX 通过间隙数组与自适应结构支持插入 [^b2a-3]；LISA [^b2a-4] 与 RSMI 将学习化索引扩展到空间数据并支持更新（RSMI 见 [VLDB 2020](https://vbn.aau.dk/ws/files/391644098/p2341_qi.pdf)）。
- GeoSOT 切入点：利用编码前缀把更新局限在父网格子树内；按时间片滚动重训练，旧时间片冻结；位置抖动只在同一网格内时免更新，以层级选择控制更新频率。

延伸阅读：[^b2a-1][^b2a-2][^b2a-3][^b2a-4]

以上四条中，第 1、3、4 条已据 Crossref 核对；第 2 条（VLDB 2004）页码据 DBScholar 与维基百科，未取得出版社页面。

[^b2a-1]: Šaltenis S, Jensen C S, Leutenegger S T, López M A. Indexing the positions of continuously moving objects. Proceedings of the 2000 ACM SIGMOD International Conference on Management of Data, 2000: 331-342. DOI: 10.1145/342009.335427.
[^b2a-2]: Jensen C S, Lin D, Ooi B C. Query and update efficient B+-tree based indexing of moving objects. Proceedings of the 30th International Conference on Very Large Data Bases (VLDB), 2004: 768-779.
[^b2a-3]: Ding J, Minhas U F, Yu J, et al. ALEX: an updatable adaptive learned index. Proceedings of the 2020 ACM SIGMOD International Conference on Management of Data, 2020: 969-984. DOI: 10.1145/3318464.3389711.
[^b2a-4]: Li P, Lu H, Zheng Q, Yang L, Pan G. LISA: a learned index structure for spatial data. Proceedings of the 2020 ACM SIGMOD International Conference on Management of Data, 2020: 2119-2133. DOI: 10.1145/3318464.3389703.

#### 2.2.5 GeoSOT 多尺度剖分图神经网络（2-4）

以剖分单元为图节点，同层相邻网格连邻接边、父子网格连层级边，构成类似 GraphCast 多尺度网格的图结构。GraphCast 以细化 6 次的二十面体网格（40962 个节点）为基元，采用“编码—处理—解码”结构，并以各层级边的并集实现长程消息传递（[Lam 等](https://arxiv.org/pdf/2212.12794)）。GeoSOT 版本的关键问题与机会：

- 网格不均匀：高纬度网格变窄，需在边特征中写入真实球面距离与方向，或按纬度自适应选择层级使节点面积大致相当。
- 与经纬度数据对齐：剖分层级与度、分、秒网格对齐，经纬度格网输入可精确聚合到节点，有望简化学习式重采样，需实验验证。
- 自适应多分辨率图：活动密集处用细网格、空旷处用粗网格，适合低空“局部密集、整体稀疏”的场景，是相对 GraphCast 均匀网格的创新点。
- 编码作为层级位置编码：编码二进制位携带层级位置信息，前缀越长越精细。
- 高度维度：高度作为通道（同 GraphCast 气压层）与 GeoSOT-3D 三维构图两种方式对比。

构图依赖大量求邻居运算，可用上 2-2 的成果；最直接的应用是应用层的 A-7。

#### 2.2.6 编码聚簇性能评价与学习化排序（2-5、2-6）

网格编码的聚簇性能决定其作为空间索引的效率。经典理论多在平面方格上讨论，DGGS 研究多为“Hilbert 对比 Z 序”的个案实验，面向 DGGS 的系统评价体系与学习化改进仍属空白。独立存储键的决策依据（在何种数据规模与查询负载下值得引入，且不替换 OGC API – DGGS 要求的标准子单元顺序）也由本方向给出，原属 1-5 的此部分内容已并入。

- 经典理论：Moon 等将“聚簇数”定义为查询区域在曲线上被切分出的连续编码段数，给出 Hilbert 曲线的闭式解，并证明簇数取决于查询区域的表面积而非体积，Hilbert 优于 Z 序 [^b2-1]；Xu 与 Tirthapura 给出任意曲线聚簇数的首个非平凡下界 [^b2-2]，Onion 曲线进一步表明 Hilbert 可能远非最优 [^b2-3]，说明须结合查询负载评价。
- DGGS 与 GeoSOT：多尺度 Hilbert 曲线相对 Z 曲线的空间连续性提升 15%～30% [^b2-7]；HGST 将 Hilbert 与 GeoSOT 结合用于海量轨迹时空范围查询 [^b2-8]。
- 学习化曲线：QUILTS 按查询负载设计曲线 [^b2-9]；BMTree 以强化学习构建分段曲线，扩展版支持负载变化后的局部重训练 [^b2-10]；LMSFC 直接学习单调曲线 [^b2-11]；常数时间代价模型使学习过程无需实际执行查询 [^b2-12]。

| 层面 | 指标 | 参考 |
| --- | --- | --- |
| 几何局部性（与查询无关） | 膨胀比（最坏与平均）、连续性与跳变次数、包围盒质量 | [^b2-4][^b2-5][^b2-6] |
| 查询聚簇（与负载相关） | 编码段数、与下界之比、冗余覆盖率、跨层级聚簇 | [^b2-1][^b2-2][^b2-3] |
| 系统代价 | 数据块访问数、寻址次数、延迟、编码解码开销 | [^b2-12] |
| DGGS 特有 | 两极与 180° 经线处退化、无效编码空洞比例、以球面距离计算的局部性、三维与时空四维的维度权衡 | 待建立 |

- 编码不变、排序可学：GeoSOT 编码作为国家标准对外交换不变，另学一个仅用于物理存储的排序键，映射须廉价且可逆。
- 保持层级连续性：只学习每个父网格下子网格的排列顺序，则同一父网格的后代在新顺序中仍为连续一段，前缀范围查询能力完整保留；Hilbert 曲线是其特例，问题天然适合 BMTree 式树搜索与强化学习。
- 时空四维位交织：经度、纬度、高度、时间各维二进制位的交织顺序按负载学习，例如 UTM 查询时间窄、空间宽。
- 验证：以上述指标与代价模型为目标，在轨迹与 UTM 查询负载上与 GeoSOT 原生 Z 序、多尺度 Hilbert、HGST、BMTree、LMSFC 对比，并研究负载漂移下的增量更新。

延伸阅读：[^b2-1][^b2-2][^b2-3][^b2-4][^b2-5][^b2-6][^b2-7][^b2-8][^b2-9][^b2-10][^b2-11][^b2-12][^b2-13]

以上文献已据 Crossref、出版社页面与 arXiv 核对。

[^b2-1]: Moon B, Jagadish H V, Faloutsos C, Saltz J H. Analysis of the clustering properties of the Hilbert space-filling curve. IEEE TKDE, 2001, 13(1): 124-141.（[IEEE](https://ieeexplore.ieee.org/abstract/document/908985/keywords)，[技术报告](https://www.cs.arizona.edu/sites/default/files/TR99-10.pdf)）
[^b2-2]: Xu P, Tirthapura S. On the optimality of clustering properties of space filling curves. PODS 2012: 215-224；期刊扩展版：Optimality of clustering properties of space-filling curves. ACM TODS, 2014, 39(2): 10。（[PODS](https://www.ece.iastate.edu/snt/files/2015/10/pods12-clustering.pdf)，[TODS](https://www.ece.iastate.edu/snt/files/2016/02/Clustering-TODS.pdf)）
[^b2-3]: Xu P, Nguyen C, Tirthapura S. Onion curve: a space filling curve with near-optimal clustering. ICDE 2018.（[arXiv 1801.07399](https://arxiv.org/pdf/1801.07399v1)）
[^b2-4]: Gotsman C, Lindenbaum M. On the metric properties of discrete space-filling curves. IEEE Transactions on Image Processing, 1996, 5(5): 794-797.
[^b2-5]: Haverkort H, van Walderveen F. Locality and bounding-box quality of two-dimensional space-filling curves. Computational Geometry, 2010, 43(2): 131-147.（[arXiv 0806.4787](https://arxiv.org/pdf/0806.4787)）
[^b2-6]: Haverkort H. An inventory of three-dimensional Hilbert space-filling curves.（[arXiv 1109.2323](https://ar5iv.arxiv.org/html/1109.2323)，与 GeoSOT-3D 相关）
[^b2-7]: 翟卫欣, 陈波, 童晓冲, 程承旗. 多尺度空间填充曲线空间连续性研究. 北京大学学报（自然科学版）, 2018, 54(2): 331-335. DOI: 10.13209/j.0479-8023.2017.147.（[链接](https://xbna.pku.edu.cn/EN/Y2018/V54/I2/331)）
[^b2-8]: Liu H, Yan J, Wang J, Chen B, Chen M, Huang X. HGST: a Hilbert-GeoSOT spatio-temporal meshing and coding method for efficient spatio-temporal range query on massive trajectory data. ISPRS IJGI, 2023, 12(3): 113. DOI: 10.3390/ijgi12030113.（[MDPI](https://www.mdpi.com/2220-9964/12/3/113/notes)）
[^b2-9]: Nishimura S, Yokota H. QUILTS: multidimensional partitioning framework based on query-aware and skew-tolerant space-filling curves. SIGMOD 2017: 1525-1537.
[^b2-10]: Li J, Wang Z, Cong G, et al. Towards designing and learning piecewise space-filling curves. PVLDB, 2023, 16(9).（[VLDB](https://vldb.org/pvldb/volumes/16/paper/Towards%20Designing%20and%20Learning%20Piecewise%20Space-Filling%20Curves)，[扩展版](https://arxiv.org/pdf/2505.01697v1)）
[^b2-11]: Gao J, Cao X, Yao X, et al. LMSFC: a novel multidimensional index based on learned monotonic space filling curves. PVLDB, 2023, 16(10).（[VLDB](https://vldb.org/pvldb/volumes/16/paper/LMSFC%3A%20A%20Novel%20Multidimensional%20Index%20based%20on%20Learned%20Monotonic%20Space%20Filling%20Curves)）
[^b2-12]: Liu G, Kulik L, Jensen C S, Li T, Borovica-Gajic R, Qi J. Efficient cost modeling of space-filling curves. PVLDB, 2024, 17(13): 4773-4785.（[arXiv 2312.16355](https://arxiv.org/pdf/2312.16355)）
[^b2-13]: Chen X, Liu S, Yuan T, Ye T, Zeng K, Su H, Zheng K. Optimizing block skipping for high-dimensional data with learned adaptive curve（AdaCurve）. SIGMOD 2025. DOI: 10.1145/3709710.

### 2.3 论文

| 编号 | 题目方向 | 验证方式 |
| --- | --- | --- |
| 2-1 | GeoSOT 四维时空网格模型与基于编码的重叠判定 | 复杂度分析、保守性量化、与 H3/S2/八叉树对比 |
| 2-2 | 基于大模型进化搜索的 GeoSOT 编码关系算法自动发现 | 邻居查找与跨层级拓扑基准测试、穷举加形式化证明 |
| 2-3 | 面向高频更新的四维时空网格学习化索引 | 以 UTM 实时位置流评测插入、更新与查询吞吐，与 Bx-tree、LISA、ALEX 等对比 |
| 2-4 | 基于 GeoSOT 多尺度剖分图的地理图神经网络框架 | 区域风场短临预测上与二十面体、HEALPix 剖分图对比精度与效率 |
| 2-5 | DGGS 编码聚簇性能评价指标体系 | 以球面距离与 UTM、轨迹查询负载评测 Z 序、Hilbert、HGST 等编码 |
| 2-6 | 保持层级连续性的 GeoSOT 学习化编码排序 | 与原生 Z 序、多尺度 Hilbert、BMTree、LMSFC 对比，考察负载漂移；只优化静态排列，更新问题交由 2-3 |

## 板块三：DGGS 与空间不确定性

以 DGGS 层级作为精度表达，结合不确定性神经网络，统一刻画、传播与校准空间数据的不确定性，并服务于无人机的概率冲突检测与风险感知规划。

### 3.1 不确定性类型

| 类型 | 含义 | 无人机场景示例 | DGGS 切入点 |
| --- | --- | --- | --- |
| 位置 | 对象位置存在误差 | GNSS 定位误差 | 概率网格编码 |
| 属性 | 测量或插值误差（偶然不确定性） | 风速传感器误差、观测稀疏 | 逐网格均值与方差 |
| 尺度 | 结论随聚合尺度变化（可变面积单元问题） | 不同层级上风险统计不一致 | 跨层级一致性约束 |
| 模型 | 模型在缺乏数据处不可靠（认知不确定性） | 无观测区域的预测 | 网格化不确定性地图 |

### 3.2 DGGS 提供的结构

- 编码长度即精度声明：用第几级编码表达对象，本身隐含对其位置的确定程度，这是经纬度坐标不具备的语义。
- 概率网格编码：将不确定位置表示为某一层级上各网格的概率分布，作为介于确定性编码与连续分布之间的新数据原语。
- 跨层级传播：父网格分布应为子网格分布的聚合，为不确定性提供跨尺度一致性约束，也为定量研究可变面积单元问题提供规范框架。

### 3.3 不确定性神经网络方法

#### 3.3.1 逐网格异方差预测（3-2）

剖分图神经网络的每个节点同时输出均值与方差，以高斯负对数似然训练，刻画观测噪声等偶然不确定性 [^b3-1]。代价几乎为零，是其余方法的基础。证据深度学习可在单次前向中同时给出偶然与认知不确定性，可作为低成本替代 [^b3-4]。

关键问题：方差在训练数据稀疏处易被低估，不能代替认知不确定性，需与 3.3.2 结合；同时应检验方差是否满足跨层级一致性，即父网格的方差应与子网格协方差的聚合一致。

#### 3.3.2 集成与贝叶斯图神经网络（3-2）

深度集成以多个独立训练模型之间的分歧度量认知不确定性，实现简单且校准良好 [^b3-2]；MC Dropout 在推理时保留 dropout，以较低代价近似贝叶斯推断 [^b3-3]。在 GeoSOT 剖分图上可输出“模型在哪些网格缺乏把握”的地图，直接服务 A-9 主动采样与不确定性驱动的自适应剖分。

关键问题：集成成本随成员数线性增长；可只在细层级的局部网格上集成，或采用快照集成降低开销。

#### 3.3.3 剖分图生成式概率模型（3-3）

GenCast 以扩散模型在细化 6 次的二十面体网格上生成 15 天、0.25° 集合预报，精度首次超过 ECMWF 的 ENS [^b3-5]，说明“剖分图 + 扩散模型”路线可行。GeoSOT 版本在 2-4 的剖分图上做条件扩散，生成低空风场的集合成员；与 3.3.1 的逐点方差相比，集合成员保留了网格之间的空间相关结构，可直接用于 A-8 计算整条航迹的冲突概率。

关键问题：扩散采样步数多、推理慢，可借鉴天气集合预报的扩散蒸馏加速（[arXiv 2608.27728](https://arxiv.org/pdf/2608.27728)）。

#### 3.3.4 分层共形校准（3-2）

共形预测不依赖分布假设，给出“真值以至少 1−α 的概率落入区间”的有限样本保证 [^b3-6]；自适应共形推断可在分布漂移下维持长期覆盖率 [^b3-7]，已有研究将其用于 GenCast 分位数校准（[综述](https://www.emergentmind.com/topics/gencast)）。

关键问题：标准共形预测假设样本可交换，而空间数据存在自相关。可按 GeoSOT 层级与区域分组做分组共形校准，使覆盖率保证在每个层级、每个区域都成立；这一保证是 A-6 安全护盾给出漏检概率上限的依据。

延伸阅读：[^b3-1][^b3-2][^b3-3][^b3-4][^b3-5][^b3-6][^b3-7]

以上七条已据 arXiv 与 Crossref 核对。

[^b3-1]: Kendall A, Gal Y. What uncertainties do we need in Bayesian deep learning for computer vision? NeurIPS 2017.（[arXiv 1703.04977](https://arxiv.org/abs/1703.04977)）
[^b3-2]: Lakshminarayanan B, Pritzel A, Blundell C. Simple and scalable predictive uncertainty estimation using deep ensembles. NeurIPS 2017.（[arXiv 1612.01474](https://arxiv.org/abs/1612.01474)）
[^b3-3]: Gal Y, Ghahramani Z. Dropout as a Bayesian approximation: representing model uncertainty in deep learning. ICML 2016.（[arXiv 1506.02142](https://arxiv.org/abs/1506.02142)）
[^b3-4]: Amini A, Schwarting W, Soleimany A, Rus D. Deep evidential regression. NeurIPS 2020.（[arXiv 1910.02600](https://arxiv.org/abs/1910.02600)）
[^b3-5]: Price I, et al. Probabilistic weather forecasting with machine learning（GenCast）. Nature, 2025, 637(8044): 84-90.（[Nature](https://link.springer.com/10.1038/s41586-024-08252-9)，[arXiv 2312.15796](https://arxiv.org/html/2312.15796v2)）
[^b3-6]: Angelopoulos A N, Bates S. A gentle introduction to conformal prediction and distribution-free uncertainty quantification. 期刊版：Conformal prediction: a gentle introduction. Foundations and Trends in Machine Learning, 2023, 16(4): 494-591.（[arXiv 2107.07511](https://arxiv.org/abs/2107.07511)）
[^b3-7]: Gibbs I, Candès E. Adaptive conformal inference under distribution shift. NeurIPS 2021.（[arXiv 2106.00170](https://arxiv.org/abs/2106.00170)）

### 3.4 在应用层的落点

- 不确定性驱动的自适应剖分：不确定性高处细化网格，低处用粗网格。
- 无人机作为移动传感器：依不确定性地图优先飞往不确定性最高的网格采集数据（主动学习），形成降低环境不确定性的闭环。
- 概率冲突检测与风险感知规划：冲突概率即两个概率网格分布的重叠概率；安全间隔由校准后的不确定性决定，支撑 5-4 与 A-8；A-6 的安全护盾以共形区间校验，给出漏检概率上限。

### 3.5 论文

| 编号 | 题目方向 | 依托 | 应用层验证 |
| --- | --- | --- | --- |
| 3-1 | GeoSOT 概率网格编码与跨层级不确定性传播 | 2-1 | A-8 |
| 3-2 | 不确定性感知的剖分图神经网络与分层共形校准 | 2-4 | A-6、A-9 |
| 3-3 | 基于 GeoSOT 剖分图扩散模型的概率集合预报 | 2-4、3-2 | A-7（低空风场） |

### 3.6 难点

- 校准评估需要高质量真值数据。
- 集成与扩散模型计算成本高。
- 需以空管员可理解的方式呈现不确定性。

## 板块四：DGGS 全球位置编码与网格基础模型

位置编码决定 AI 模型如何理解地球上的位置，是网格基础模型的入口。本板块以 GeoSOT 层级编码构建全球位置编码器，再以此为基础构建网格基础模型，汇聚其他板块的成果。

### 4.1 全球位置编码的三条路线

| 路线 | 代表方法 | 优点 | 局限 |
| --- | --- | --- | --- |
| 连续函数编码 | Space2Vec、Sphere2Vec [^b4a-1]（多尺度正余弦）；球谐函数 + SIREN | 平滑，可泛化到任意坐标 | 正余弦编码假设矩形域，两极易出伪影；分辨率受最高频率限制，米级需极高阶 |
| 预训练编码器 | SatCLIP、GeoCLIP（与影像对比学习） | 携带地物语义，下游即插即用 | 分辨率受训练影像限制，局限于地表二维 |
| 离散网格编码 | H3、S2 单元 ID 嵌入表 | 可任意细分，与空间索引一致 | 单元间无泛化，词表随层级爆炸，单元边界处不连续 |

- 球谐函数在球面上原生定义，与 SIREN 组合后在多项任务上取得最优，尤其改善了以往方法表现不佳的极区（[Rußwurm 等，ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/073c8584ef86bee26fe9d639ec648e28-Abstract-Conference.html)）。
- SatCLIP 以卫星影像对比预训练得到通用位置嵌入，能编码空间上相距遥远但环境相似的地点；同一团队还提出以球面 Slepian 函数将表达能力集中于感兴趣区域，以较低代价提升分辨率（[作者主页](https://www.alphaxiv.org/@marc-russwurm)）。

### 4.2 GeoSOT 层级位置编码器

编码器以 GeoSOT 编码为骨架，遵循 GB/T 40087-2021，可精确反解并跨系统交换，由以下五个组件构成。

#### 4.2.1 多分辨率网格嵌入（4-1）

每个层级维护一张可学习特征表，位置的表示为其所在各层级网格特征的拼接或加和。思路与 Instant-NGP 的多分辨率哈希编码同构 [^b4-1]，区别在于 GeoSOT 编码前缀天然给出各层级索引，粗层级无需哈希即可精确定位。粗层级完整建表；细层级采用哈希表或只为有数据的网格建表，以控制 32 个层级带来的参数膨胀。

关键问题：参与编码的层级范围如何选取，使之与任务尺度匹配。

#### 4.2.2 网格内连续插值（4-1）

离散嵌入在网格边界处不连续，相邻但跨边界的两点表示差异很大。借鉴 Instant-NGP 的插值方式 [^b4-1]，以位置在网格内的相对坐标对相邻网格特征加权，得到连续可微的表示。

关键问题：依赖高效求邻居（2-2），并需正确处理 180° 经线与两极处的邻接。

#### 4.2.3 与连续函数编码融合（4-1）

球谐函数在球面上原生定义，与 SIREN 组合后在多项任务上取得最优，尤其改善了极区表现 [^b4-2]，但分辨率受最高阶数限制。可在粗尺度用球谐函数保证全球平滑与极区正确，细尺度用 GeoSOT 网格嵌入提供米级细节，两者拼接后输入下游网络。Space2Vec 等多尺度正余弦编码可作为对比基线 [^b4-3]。

关键问题：两种表示的尺度分界点如何确定，以及融合后是否仍保持极区优势。

#### 4.2.4 面向低空的四维扩展（4-2）

SatCLIP 以卫星影像对比预训练得到通用位置嵌入，能编码相距遥远但环境相似的地点 [^b4-4]；GeoCLIP 以照片与位置对齐用于图像定位 [^b4-5]。二者均限于地表二维。以 GeoSOT-3D 编码加时间片构成四维编码：高度维沿用网格嵌入，时间维以周期编码表达日变化与季节变化。

关键问题：高度与水平方向的分辨率需求差异大，各维层级如何配比。

#### 4.2.5 不确定位置编码（4-1、3-1）

位置以 3-1 的概率网格编码给出时，取各网格嵌入按概率加权的期望，使定位误差自然传入下游模型。误差越大，表示越接近粗层级，体现“编码长度即精度声明”。

关键问题：概率分布跨越多个网格时的计算开销，以及期望表示是否会抹平关键细节。

延伸阅读：[^b4-1][^b4-2][^b4-3][^b4-4][^b4-5]

以上五条已据 arXiv、Crossref 与 AAAI 官网核对。

[^b4-1]: Müller T, Evans A, Schied C, Keller A. Instant neural graphics primitives with a multiresolution hash encoding. ACM Transactions on Graphics, 2022, 41(4).（[arXiv 2201.05989](https://arxiv.org/abs/2201.05989)）
[^b4-2]: Rußwurm M, Klemmer K, Rolf E, Zbinden R, Tuia D. Geographic location encoding with spherical harmonics and sinusoidal representation networks. ICLR 2024.（[ICLR](https://proceedings.iclr.cc/paper_files/paper/2024/hash/073c8584ef86bee26fe9d639ec648e28-Abstract-Conference.html)）
[^b4-3]: Mai G, Janowicz K, Yan B, Zhu R, Cai L, Lao N. Multi-scale representation learning for spatial feature distributions using grid cells（Space2Vec）. ICLR 2020.（[arXiv 2003.00824](https://arxiv.org/abs/2003.00824)）
[^b4-4]: Klemmer K, Rolf E, Robinson C, Mackey L, Rußwurm M. SatCLIP: global, general-purpose location embeddings with satellite imagery. AAAI 2025, 39(4): 4347-4355.（[arXiv 2311.17179](https://arxiv.org/abs/2311.17179v3)）
[^b4-5]: Vivanco Cepeda V, Nayak G K, Shah M. GeoCLIP: CLIP-inspired alignment between locations and images for effective worldwide geo-localization. NeurIPS 2023.

### 4.3 GeoSOT 网格基础模型

ClimaX [^b4a-2]、Aurora [^b4a-3]、Prithvi WxC [^b4a-4] 等地球基础模型多基于经纬度切块或固定均匀网格，DGGS 原生的通用模型尚无成型代表；GraphCast 骨干已被迁移到季节性火灾预测等任务（[FireCastNet](https://arxiv.org/pdf/2502.01550)）。

| 通用层次 | 含义 | GeoSOT 的作用 |
| --- | --- | --- |
| 跨任务 | 预训练一次，微调服务风场、风险、流量、冲突概率预测 | 统一的节点与图结构 |
| 跨尺度 | 在任意或混合层级的自适应图上工作 | 层级自相似，弥合天气模型约 25 公里与低空米级之间三个数量级的尺度鸿沟 |
| 跨模态 | 气象、地形建筑、人口、通信覆盖、航迹统一建模 | 网格编码作为对齐各模态的公共坐标系 |

- 架构：各模态编码器 → 网格词元（以 4.2 的编码器作位置编码）→ 自适应多尺度图上的处理器（图神经网络或图 Transformer，见 2-4）→ 各任务解码头，输出概率分布而非单值（见板块三）。
- 预训练目标：遮蔽网格重建、下一时刻预测、跨层级一致性（父网格预测应与子网格预测的聚合一致），以及类 SatCLIP 的多模态对比学习。

### 4.4 推进路径

1. 完成 4-1 与 2-4，分别验证位置编码器与剖分图框架。
2. 在一个城市低空空域内，以同一模型处理风场、风险、流量等三四个任务，依托 5-5 的基准数据集验证。
3. 尝试跨区域、跨尺度预训练。

### 4.5 论文

| 编号 | 题目方向 | 依托 | 验证方式 |
| --- | --- | --- | --- |
| 4-1 | GeoSOT 多分辨率层级位置编码器 | 2-1、2-2 | 在公开任务上与球谐 + SIREN、Space2Vec、SatCLIP 对比，重点考察极区与高分辨率 |
| 4-2 | 面向低空的四维位置编码 | 4-1 | 低空风场与航迹任务 |
| 4-3 | 基于 GeoSOT 编码器的多模态对比预训练 | 4-1 | 下游迁移与少样本适配 |
| 4-4 | 基于网格词元的航迹基础模型 | 2-1、4-2 | 航迹预测、意图识别与“黑飞”检测（A-10） |
| 4-5 | 跨层级一致性自监督的网格基础模型 | 2-4、3-2、4-3 | 5-5 基准上的低空多任务 |

4-4 需注意固定网格词元化已受批评（[TrajTok](https://arxiv.org/pdf/2605.20134) 改用密度自适应六边形网格），离散化亦有几何代价（[Geometric Alignment Tax](https://arxiv.org/pdf/2604.04155)）；宜采用“网格码 + 网格内连续偏移”混合表达，并以编码前缀做由粗到细的分层生成。

### 4.6 难点

- 算力与数据：完整基础模型需大团队，宜从区域小模型起步。
- 价值论证：通用模型未必在单一任务胜过专用模型，应以迁移能力、数据效率与跨尺度能力证明价值。
- 公平对比：位置编码器需在统一任务与数据上与连续编码对比，避免只在网格友好的任务上验证。

正文所涉其他模型文献：[^b4a-1][^b4a-2][^b4a-3][^b4a-4]

以上四条已据原文核对：Sphere2Vec 为多尺度正余弦编码；ClimaX、Aurora 将经纬度格网切块为词元，Prithvi WxC 在 MERRA-2 经纬度格网上以 2×2 像素词元分窗注意力。

[^b4a-1]: Mai G, Xuan Y, Zuo W, He Y, Song J, Ermon S, Janowicz K, Lao N. Sphere2Vec: a general-purpose location representation learning over a spherical surface for large-scale geospatial predictions. ISPRS Journal of Photogrammetry and Remote Sensing, 2023, 202: 439-462.（[arXiv 2306.17624](https://arxiv.org/abs/2306.17624)）
[^b4a-2]: Nguyen T, Brandstetter J, Kapoor A, Gupta J K, Grover A. ClimaX: a foundation model for weather and climate. ICML 2023.（[arXiv 2301.10343](https://arxiv.org/abs/2301.10343)）
[^b4a-3]: Bodnar C, Bruinsma W P, Lucic A, et al. A foundation model for the Earth system（Aurora）. Nature, 2025, 641(8065): 1180-1187. DOI: 10.1038/s41586-025-09005-y.（[arXiv 2405.13063](https://arxiv.org/abs/2405.13063)）
[^b4a-4]: Schmude J, Roy S, Trojak W, Jakubik J, et al. Prithvi WxC: foundation model for weather and climate.（[arXiv 2409.13598](https://arxiv.org/abs/2409.13598)）

## 板块五：面向低空的 DGGS 空域基础

把 UTM/UAM 的共性需求抽象为 DGGS 问题，只回答空域、航迹、容量、间隔与数据如何在网格上表达与度量，不涉及具体规划算法；成果是应用层各篇的共同底座。5-1 宜优先推进。

### 5.1 现有工作

“网格建模 + 单机寻路改进”已较拥挤，多机、动态场景下的标准化网格表达与度量仍少。

- 空域建模：借鉴 DGGS 思想，用 GeoSOT-3D 构建低空航路并实现多层级海量数据查询（[PMC8046233](https://pmc.ncbi.nlm.nih.gov/articles/PMC8046233)）。
- 单机路径规划：基于 GeoSOT 的三维跳点搜索 GPJ3D-RP（[ISPRS 2025](https://isprs-archives.copernicus.org/articles/XLVIII-4-W14-2025/421/2025/)）；依托 GeoSOT-3D 电磁网格改进 A\*（[信息对抗技术 2025](https://castjournals.cast.org.cn/joweb/xxdkjs/EN/PDF/10.12399/j.issn.2097-163x.2025.05.007)）；程承旗团队的室内无人机网格路径规划（[2022](https://lowaltitudeeconomy.aero/zh/目录/白皮书/lae白皮书/基于网格优化的无人机室内路径规划算法复杂性)）。
- 风险评估：以北斗网格为基准的低空风险量化与航线规划（[secrss](https://www.secrss.com/articles/93336)）。
- 产业平台：中科星图低空云以 G-DGGS 与 GeoSOT 剖分双引擎为核心（[IT之家](https://www.ithome.com/0/825/798.htm)）。

### 5.2 GeoSOT 的价值

- 冲突判定变为编码运算（依托 2-1），可借助数据库索引批量判断。
- 多尺度对应分层规划：粗层级服务全局规划，细层级服务局部重规划，编码继承关系保证两层一致。
- 影响范围快速判定：环境变化表达为网格码集合，前缀匹配即可查出受影响对象。
- 多源数据标准化融合：障碍物、气象、通信覆盖、风险评估结果挂载到同一编码。

### 5.3 研究内容

#### 5.3.1 空域要素统一表达（5-1）

禁飞区、限制区、航路走廊、起降场保护区与临时管制区，统一表达为“网格码集合 + 有效时段 + 属性”，以多层级混合表达兼顾精度与数据量。

#### 5.3.2 四维航迹网格化与动力学一致性（5-2）

制定连续航迹到网格序列的转换规则，校核平滑后航迹与网格序列的一致性；网格层级随速度与定位精度自适应。

#### 5.3.3 空域容量与时空占用度量（5-3）

以网格时空单元定义占用、预约与容量，量化离散化保守性带来的容量损失，为战略冲突消解与 UAM 流量管理提供统一度量。

#### 5.3.4 网格化安全间隔与保护区（5-4）

确定性间隔以网格膨胀表达，概率间隔由 3-1 给出，并与法规间隔要求对照。

#### 5.3.5 低空多源数据融合与基准（5-5）

障碍物、气象、通信覆盖、人口与风险数据挂载到同一编码，构建低空多任务基准数据集，供板块四与应用层使用。

### 5.4 论文

| 编号 | 题目方向 | 依托 | 应用层验证 |
| --- | --- | --- | --- |
| 5-1 | 低空空域要素的 GeoSOT 统一时空表达模型 | 2-1 | A-1、A-4 |
| 5-2 | 四维航迹网格化与动力学一致性校核 | 2-1、2-2 | A-1、A-2 |
| 5-3 | 网格化空域容量与时空占用度量 | 2-1、2-3 | A-1、A-4 |
| 5-4 | 网格化安全间隔与保护区表达 | 2-1、3-1 | A-2、A-8 |
| 5-5 | 低空多源数据网格融合与多任务基准数据集 | 2-1 | 4-5、A-7 |

## 板块六：面向地球系统模式的 DGGS 基础

与板块五并列，把地球系统模式中与网格相关的共性需求抽象为 DGGS 问题：模式输出的组织与分析、分量间耦合重映射、跨尺度降尺度、观测同化接口，以及 AI 模拟器的网格基座。本板块不研究动力框架本身：GeoSOT 基于经纬度剖分，两极网格收缩会限制时间步长，不宜直接作为动力核心的计算网格，其定位是数据、耦合与 AI 层的公共剖分底座。6-1 宜优先推进。

### 6.1 现有工作

- 模式网格：新一代模式转向准均匀非结构网格。国内 GRIST 采用类二十面体 Voronoi 网格与六边形 C 网格，支持全球变分辨率（[GMD 2020](https://gmd.copernicus.org/articles/13/6325/2020/gmd-13-6325-2020-assets.html)，[框架介绍](https://cmalibrary.cn/amst/2024/202404/fmbd/202409/P020240927772890505636.pdf)）；国外 ICON 用二十面体网格 [^b6-4]、MPAS 用 Voronoi 网格 [^b6-5]、FV3 用立方球网格 [^b6-6]。
- 层级输出：DKRZ 将千米级 ICON 模拟输出写为 HEALPix 层级多分辨率数据，使分析时读取的数据量随分析范围而非模型规模变化（[easy.gems](https://easy.gems.dkrz.de/Processing/healpix)）；Hiopy 借助 YAC 耦合器在线生成层级时空聚合（[EGU 2026](https://meetingorganizer.copernicus.org/EGU26/EGU26-9822.html)）；nextGEMS 将输出统一到 HEALPix 网格，为 DestinE 气候数字孪生奠定基础（[DestinE](https://destine.ecmwf.int/news/pioneering-kilometre-scale-climate-simulations-the-nextgems-breakthroughs)）；Waterpark 将 ERA5、ICON、CMIP6 与观测统一重映射到 HEALPix 并存为 Zarr 金字塔（[Waterpark](https://waterpark.dkrz.de/storage_concepts/)）。
- 耦合器：国内 C-Coupler 系列由清华大学研发，C-Coupler3.0 指出千米级网格的全局管理内存开销大，需支持更高分辨率耦合（[GMD 2023](https://gmd.copernicus.org/articles/16/2833/2023/)）。
- 启示：HEALPix 已在 DKRZ、nextGEMS 等项目中成为高分辨率模式输出的层级网格，GeoSOT 在这一位置仍属空白，同时须正视 HEALPix 等面积的优势。

### 6.2 GeoSOT 的定位与价值

- 与经纬度格网对齐：剖分层级与度、分、秒网格对齐，而 CMIP、ERA5 等多为经纬度格网，有望以精确聚合替代插值，需实验验证。
- 层级聚合严格守恒：子网格精确划分父网格，父网格值即子网格的面积加权和，天然满足质量与能量守恒。
- 跨领域共用编码：模式输出与低空空域、遥感等数据共用国家标准编码，衔接板块五（如低空风场）。
- 劣势：非等面积，统计与重映射须面积加权；两极存在退化；须与 HEALPix 系统对比。

### 6.3 研究内容

#### 6.3.1 模式输出的 GeoSOT 层级组织（6-1）

将模式输出在线或离线写为 GeoSOT 多层级 Zarr 金字塔，数据块划分与编码排序结合 2-5、2-6 的成果，评测分析延迟、存储开销与跨层级一致性，并与 HEALPix 层级输出对比。

#### 6.3.2 分量耦合与守恒重映射（6-2）

以 GeoSOT 作为大气、海洋、陆面等分量之间的公共交换网格，或作为重映射权重的组织索引：利用编码快速求网格交叠（2-2），生成一阶与二阶守恒重映射权重 [^b6-2]；按编码前缀做分布式划分，降低千米级网格管理的内存开销，回应 C-Coupler3.0 提出的问题。以质量与能量守恒误差、权重生成时间与内存为评价指标。

#### 6.3.3 跨层级降尺度与物理一致性（6-3）

GeoSOT 层级天然构成粗细尺度配对。以 AI 模型由第 n 级预测第 n+k 级，约束子网格聚合等于父网格，与板块三的跨层级一致性呼应，并输出不确定性（3-3）。

#### 6.3.4 观测稀疏化与同化接口（6-4）

观测按网格码组织，在网格内做超级观测与稀疏化，观测误差按层级表达（3-1）；观测算子借助编码快速定位所在模式网格。无人机移动观测（A-9）可由此接入同化流程。

#### 6.3.5 AI 模拟器的剖分图基座（6-5）

以 2-4 剖分图承载 AI 天气与气候模拟器，与二十面体图（GraphCast、GenCast）及 HEALPix 对比。在物理与 AI 混合模型中 [^b6-3]，物理部分保留原生网格，AI 部分运行于 GeoSOT 图，两者经 6.3.2 的重映射衔接。

### 6.4 论文

| 编号 | 题目方向 | 依托 | 验证方式 |
| --- | --- | --- | --- |
| 6-1 | 地球系统模式输出的 GeoSOT 层级组织与分析就绪数据集 | 2-5、2-6 | 与 HEALPix 层级输出对比分析延迟与存储 |
| 6-2 | 基于 GeoSOT 的分量耦合守恒重映射 | 2-2 | 守恒误差、权重生成时间与内存 |
| 6-3 | 守恒约束的 GeoSOT 跨层级 AI 降尺度 | 3-1、3-3 | ERA5、CMIP6 降尺度精度与守恒性 |
| 6-4 | GeoSOT 网格化观测稀疏化与同化接口 | 3-1 | 同化试验中的观测利用率与分析误差 |
| 6-5 | 面向 AI 地球系统模拟器的 GeoSOT 剖分图基座 | 2-4、4-5 | 与二十面体、HEALPix 图在中期预报上对比 |

### 6.5 难点

- 领域壁垒：验证依赖模式运行资源，宜与模式研发团队合作。
- 先发优势：HEALPix 已有成熟工具链（如 CDO、healpy、easygems），须明确 GeoSOT 的增量价值。
- 非等面积：所有统计、聚合与重映射须面积加权。

延伸阅读：[^b6-1][^b6-2][^b6-3][^b6-4][^b6-5][^b6-6]

以上六条已据 Crossref 与出版社页面核对；[^b6-4]–[^b6-6] 分别为 6.1 中 ICON（二十面体三角形 C 网格）、MPAS（质心 Voronoi 网格）、FV3（立方球网格）网格描述的原始文献。

[^b6-1]: Górski K M, Hivon E, Banday A J, et al. HEALPix: a framework for high-resolution discretization and fast analysis of data distributed on the sphere. The Astrophysical Journal, 2005, 622(2): 759-771.
[^b6-2]: Jones P W. First- and second-order conservative remapping schemes for grids in spherical coordinates. Monthly Weather Review, 1999, 127(9): 2204-2210.
[^b6-3]: Kochkov D, et al. Neural general circulation models for weather and climate（NeuralGCM）. Nature, 2024, 632(8027): 1060-1066.
[^b6-4]: Zängl G, Reinert D, Rípodas P, Baldauf M. The ICON (ICOsahedral Non-hydrostatic) modelling framework of DWD and MPI-M: description of the non-hydrostatic dynamical core. Quarterly Journal of the Royal Meteorological Society, 2015, 141(687): 563-579. DOI: 10.1002/qj.2378.
[^b6-5]: Skamarock W C, Klemp J B, Duda M G, Fowler L D, Park S-H, Ringler T D. A multiscale nonhydrostatic atmospheric model using centroidal Voronoi tesselations and C-grid staggering. Monthly Weather Review, 2012, 140(9): 3090-3105. DOI: 10.1175/MWR-D-11-00215.1.
[^b6-6]: Putman W M, Lin S-J. Finite-volume transport on various cubed-sphere grids. Journal of Computational Physics, 2007, 227(1): 55-78.

## 板块七：海量时空数据组织与存储基础

与板块五、六并列，研究以 GeoSOT 为统一剖分框架的海量时空数据组织、存储与查询共性方法。与板块二的分工是：板块二研究编码本身的算法（关系计算、排序、索引），本板块研究数据系统层面的数据模型、分区、查询处理与存储格式，把板块二的成果落地为系统组件；6-1 可视为本板块方法在地球系统模式输出上的特例。7-1 宜优先推进。

### 7.1 现有工作

- 国际标准：OGC API – DGGS 第 1 部分已获批为正式 OGC 标准，与 ISO 19170-1:2021 一起补齐了 DGGS 互操作的关键环节（[OGC 公告](https://www.ogc.org/announcement/ogc-membership-approves-ogc-api-discrete-global-grid-systems-part-1-core-as-an-official-ogc-standard/)）；其 DGGRS 定义包括网格层级、单元标识参考系以及确定性的子单元顺序（[OGC API – DGGS](https://ogcapi.ogc.org/dggs/)）。因此 2-6 的学习化排序须作为独立的存储键，而不能替换标准规定的顺序。
- 时空大数据引擎：GeoMesa 以 Z2、Z3 与 XZ 空间填充曲线在分布式键值库上索引时空数据；Apache Sedona（原 GeoSpark）、京东 JUST 等面向分布式时空分析 [^b7-1]–[^b7-4]。
- GeoSOT 实践：HGST 结合 Hilbert 与 GeoSOT 实现海量轨迹时空范围查询（[IJGI 2023](https://www.mdpi.com/2220-9964/12/3/113/notes)）；G-SEED 基于 GeoSOT 构建林草数据时空编码框架（[arXiv 2506.18094](https://arxiv.org/pdf/2506.18094)）。
- 云原生格式：Zarr 金字塔、GeoParquet 等格式兴起，DKRZ 的 Waterpark 已把多源气候数据统一到 HEALPix 并存为 Zarr 金字塔（[Waterpark](https://waterpark.dkrz.de/storage_concepts/)）。

### 7.2 GeoSOT 的价值

- 编码即索引键：网格编码可直接作为分布式存储的行键与分区键。
- 多源异构统一：矢量、栅格、点云、轨迹与影像统一映射到网格编码，实现跨类型关联。
- 层级前缀天然支持多分辨率组织与按层级分区。
- 与 GB/T 40087-2021 及北斗网格位置码等国家标准衔接，便于跨部门共享。

### 7.3 研究内容

#### 7.3.1 多源异构时空数据统一数据模型（7-1）

制定矢量、栅格、点云、轨迹与影像的网格化表达规则：点落入单元，线与面以多层级网格集合覆盖（对接 2-1），栅格按层级对齐聚合；统一组织属性与时间维，并与 OGC API – DGGS 的数据访问接口对接。

关键问题：覆盖精度与网格数量之间的权衡，以及同一对象多层级表达的一致性。

#### 7.3.2 基于编码的分布式分区与负载均衡（7-2）

按编码前缀划分数据分区，天然保持空间邻近；针对城市、航线等热点区域的数据倾斜，按数据量自适应调整分区层级；结合 2-5 的聚簇评价与 2-6 的排序优化减少跨分区查询。

关键问题：分区重平衡时的数据迁移代价。

#### 7.3.3 编码连接的空间关联查询（7-3）

把空间连接与范围查询转化为编码集合的相等或前缀匹配，以过滤—精化框架保证结果精确（依托 2-2、2-3）；在分布式引擎中实现编码连接算子，并与几何连接对比效率。

关键问题：多层级覆盖带来的重复结果如何去重。

#### 7.3.4 多分辨率预聚合与网格数据立方体（7-4）

沿 GeoSOT 层级预先计算统计聚合，构成时空数据立方体，支持从全球到局部的交互式分析；父单元由子单元精确聚合，衔接板块三的跨层级一致性。

关键问题：预聚合的存储开销与查询加速之间的权衡，以及增量更新。

#### 7.3.5 利用网格局部性的压缩与云原生存储（7-5）

按编码顺序排列后，相邻数据的相关性强，可提升压缩率；研究 Zarr、GeoParquet 中的分块方式与编码排序（2-6）的配合，以及冷热数据分层。

关键问题：压缩率、随机访问与写入吞吐之间的平衡。

### 7.4 论文

| 编号 | 题目方向 | 依托 | 应用层验证 |
| --- | --- | --- | --- |
| 7-1 | 多源异构时空数据的 GeoSOT 统一数据模型 | 2-1 | C-1、C-3、C-4 |
| 7-2 | 基于 GeoSOT 编码的分布式分区与负载均衡 | 2-5、2-6 | C-2、C-4、C-5 |
| 7-3 | 编码连接的空间关联查询处理 | 2-2、2-3 | C-2 |
| 7-4 | GeoSOT 多分辨率预聚合与网格数据立方体 | 2-1、3-1 | C-1、C-3 |
| 7-5 | 利用网格局部性的时空数据压缩与云原生存储 | 2-6 | C-1 |

### 7.5 难点

- 与成熟引擎竞争：GeoMesa、Sedona 等已高度工程化，须以明确的效率或互操作优势立论。
- 可复现性：需公开数据与查询负载，便于他人复现对比。

延伸阅读：[^b7-1][^b7-2][^b7-3][^b7-4]

以上四条已据 Crossref 与 ICDE 官网核对。

[^b7-1]: Hughes J N, Annex A, Eichelberger C N, Fox A, Hulbert A, Ronquest M. GeoMesa: a distributed architecture for spatio-temporal fusion. Proceedings of SPIE, 2015, 9473: 94730F.
[^b7-2]: Böhm C, Klump G, Kriegel H-P. XZ-ordering: a space-filling curve for objects with spatial extension. SSD 1999, LNCS 1651: 75-90. DOI: 10.1007/3-540-48482-5_7.
[^b7-3]: Yu J, Wu J, Sarwat M. GeoSpark: a cluster computing framework for processing large-scale spatial data. ACM SIGSPATIAL 2015.
[^b7-4]: Li R, He H, Wang R, et al. JUST: JD urban spatio-temporal data engine. ICDE 2020.

## 板块八：世界坐标系下的三维重建与视图合成（探索性）

与板块五、六、七并列，但处于探索阶段：研究在前馈式大场景重建与生成中，DGGS 能否为块划分、坐标约定与结果组织提供一套统一做法，使结果直接落在 WGS84 等世界坐标系。前馈式方法一次前向推理输出场景表示，不做逐场景优化；近期面向地理空间的前馈工作多在小范围样本上，各自约定局部坐标并做尺度归一化 [^b8-1][^b8-2]，“把大量小块拼成一整片世界系结果”还缺系统比较。DGGS 不解决位姿与尺度估计，只可能在块划分、坐标约定、拼接与组织上起作用，因此本板块以一个判定关口控制规模：先做块拼接基准（8-1），关口通过后才做 8-2、8-3。

### 8.1 现有工作

按特点分类的技术方法摘要（面向不熟悉重建领域的读者，含术语表）见 [板块八/相关研究工作.md](板块八/相关研究工作.md)，下面只列与本板块最相关的几条。

- 地理空间的前馈式重建（2026 年预印本，未经同行评议）：Cross-View Splatter 融合带 GPS 的地面照片与卫星图，每个样本以首张地面图像定义局部系、范围固定 244 m，未讨论多块拼接 [^b8-1]；GeoRay 输出大地坐标系下的高度场（2.5D），以 256 像素窗口解码，窗口边界有接缝，块间存在高程基准的整块常数偏移，大范围镶嵌未描述，代码与权重已发布 [^b8-2]；AnyCity 从稀疏航拍单次前馈生成城市高斯，位姿由网络内部预测，未说明世界系，未声明发布 [^b8-3]；另有以卫星图像恢复度量尺度的工作，每次处理 250 m 见方的卫星图 [^b8-4]。信息取自 arXiv 全文的网页抓取摘要，坐标细节以原文与代码为准。
- 大场景神经辐射场与高斯泼溅（逐场景优化）：Mega-NeRF、Block-NeRF 按空间分块训练再拼接 [^b8-5][^b8-6]；HUG、CityGaussianV2 用块级与层级方法处理规模 [^b8-9][^b8-10]；常用表示有多分辨率哈希编码与 3D 高斯泼溅 [^b8-7][^b8-8]。
- DGGS 与重建的结合：本文的几轮检索没有发现把 DGGS 用于 NeRF、3DGS、多视图立体或前馈重建的工作，检索较浅，不能据此断言空白。

### 8.2 DGGS 的价值与边界

| 问题 | DGGS 是否有帮助 |
| --- | --- |
| 位姿与尺度估计、世界系配准 | 没有，须依赖 GNSS、IMU、控制点、卫星 RPC 或卫星图像参照 |
| 单精度数值范围（ECEF 量级约 6.4×10⁶ m，单精度间隔 0.5 m，按公式推算） | 有可能：每个单元自带局部坐标系，全局以编码寻址；但单块范围小，原点平移同样有效 |
| 块边界的接缝、块间尺度与高程基准的常数偏移 | 有可能：块边界即单元边界，相邻块共享地址，重叠带有统一定义 |
| 块尺度的归一化 | 有可能：以单元层级给出尺度，替代按批的数据相关归一化（需重新训练，属 8-2） |
| 多尺度与流式加载 | 有可能：层级编码对应层次细节 |
| 结果的落地与检索 | 有可能：产物以编码索引，进入板块七的数据组织 |
| 训练与测试的空间划分 | 有可能：以单元划分块级交叉验证，减少空间泄漏（属 8-2，待论证） |

代价：经纬度单元形状随纬度变化，体素与窗口各向异性（1-1 的评估对象）；缓解办法是“单元局部度量坐标系加全局编码”。对照基线是样本锚定局部系、归一化大地坐标加窗口解码、ECEF 双精度加原点平移，DGGS 的增量必须对它们证明。

### 8.3 研究内容

#### 8.3.1 前馈式大范围重建的坐标策略与块拼接基准（8-1）

固定前馈模型，在推理阶段比较样本锚定局部系、归一化大地坐标加窗口解码、网格单元局部系三种块策略，量化不同拼接范围与纬度下的世界系误差、接缝与块间常数偏移；详见 [8-1](板块八/8-1_前馈式大范围重建的坐标策略与块拼接基准.md)。

关键问题：在不重新训练模型的前提下，把块的坐标与拼接策略这一变量单独分离出来。

#### 8.3.2 单元局部系下的前馈模型训练与跨块一致性（8-2，关口通过后）

以单元局部系与单元边长尺度归一化训练前馈模型，并设计跨块重叠带的一致性解码；与按批归一化、窗口重叠融合对照；探索以编码为键的位置先验（须检验其是否损害跨区域泛化）；以单元划分训练与测试，考察空间泄漏。

关键问题：单元层级尺度归一化与按批归一化相比，在跨块一致性与跨区域泛化上是否有优势。

#### 8.3.3 跨块镶嵌与世界系结果的 DGGS 落地（8-3，关口通过后）

用重叠区估计并校正块间尺度与高程基准偏移；把高度场、高斯或点云按编码索引，导出为通用格式（如瓦片化的三维数据），并接入板块七的数据组织与 OGC API – DGGS 访问。

关键问题：块间偏移估计的可靠性，以及以编码组织的三维产物与通用瓦片格式相比的检索效率与互操作。

### 8.4 论文

| 编号 | 题目方向 | 依托 | 验证 |
| --- | --- | --- | --- |
| 8-1 | [前馈式大范围重建的坐标策略与块拼接基准](板块八/8-1_前馈式大范围重建的坐标策略与块拼接基准.md) | 1-1、2-1 | 合成数据、卫星或航拍数据 |
| 8-2 | 单元局部系下的前馈模型训练与跨块一致性（关口通过后） | 4-1、8-1 | 跨块一致性与跨区域泛化 |
| 8-3 | 跨块镶嵌与世界系结果的 DGGS 落地（关口通过后） | 7-1、8-1 | 与 5-5 数据集、通用瓦片格式对比 |

板块八暂不进入应用层 A、B、C 三组，验证使用合成数据、公开卫星或航拍数据与 5-5 的低空影像。

### 8.5 难点与判定关口

- 判定关口：8-1 的基准若显示在 10 km² 及以上范围，网格单元局部系相对归一化大地坐标加窗口解码，接缝或块间偏移没有达到事先设定的改善阈值（暂定相对 10%），则终止 8-2、8-3，仅以基准结论发表。
- 竞争与时效：该方向 2026 年内已有多篇预印本，须持续跟踪，且新颖性只能以“块拼接与坐标约定的系统比较”立论，不能声称首次把前馈方法用于世界系。
- 前馈模型的可得性：权重与代码是否公开决定能否固定模型。
- 位姿误差可能淹没策略差别：合成数据用真值位姿，真实数据固定束调整结果。

延伸阅读：[^b8-1][^b8-2][^b8-3][^b8-4][^b8-5][^b8-6][^b8-7][^b8-8][^b8-9][^b8-10]

以下条目已在线核对（arXiv、Crossref）。[^b8-1] 至 [^b8-4] 为 2026 年预印本，已核对 arXiv 页面的标题、作者与日期；Mega-NeRF 与 CityGaussianV2 的会议信息取自 arXiv 备注，HUG 仅有 arXiv 版本（备注称改进版已被 ICCV 接收），Block-NeRF 的发表信息未核对。

[^b8-1]: Turkulainen M, Krishnan A, Aleotti F, Sayed M, Garcia-Hernando G, Kannala J, Solin A, Brostow G, Turmukhambetov D. Cross-View Splatter: feed-forward view synthesis with georeferenced images. arXiv:2605.19656, 2026.（[arXiv](https://arxiv.org/abs/2605.19656)）
[^b8-2]: Dong Z, Wu W, Sun Y, Jiang H, Ma Y, Ren L, Liu T, Gu Y. GeoRay: gauge-aware feed-forward satellite 3D reconstruction in the geodetic frame. arXiv:2608.29680, 2026.（[arXiv](https://arxiv.org/abs/2608.29680)）
[^b8-3]: Wu D, Li Z, Hua T, Ren Y, Wei X, Qin R, Zhao W. Feed-forward Gaussian splatting from sparse aerial views（方法名 AnyCity）. arXiv:2605.19949, 2026.（[arXiv](https://arxiv.org/abs/2605.19949)）
[^b8-4]: Ze X, Luo Y, Chao M, Song Z, Lu J, Shi Y. Empowering feed-forward reconstruction models with metric scale via satellite images. arXiv:2606.08205, 2026.（[arXiv](https://arxiv.org/abs/2606.08205)）
[^b8-5]: Turki H, Ramanan D, Satyanarayanan M. Mega-NeRF: scalable construction of large-scale NeRFs for virtual fly-throughs. CVPR 2022（据 arXiv 备注）. arXiv:2112.10703.（[arXiv](https://arxiv.org/abs/2112.10703)）
[^b8-6]: Tancik M, Casser V, Yan X, Pradhan S, Mildenhall B, Srinivasan P P, Barron J T, Kretzschmar H. Block-NeRF: scalable large scene neural view synthesis. arXiv:2202.05263, 2022.（[arXiv](https://arxiv.org/abs/2202.05263)）
[^b8-7]: Müller T, Evans A, Schied C, Keller A. Instant neural graphics primitives with a multiresolution hash encoding. ACM Transactions on Graphics, 2022, 41(4). DOI: 10.1145/3528223.3530127.
[^b8-8]: Kerbl B, Kopanas G, Leimkühler T, Drettakis G. 3D Gaussian splatting for real-time radiance field rendering. ACM Transactions on Graphics, 2023, 42(4). DOI: 10.1145/3592433.
[^b8-9]: Su M, Wang Z, Au H, Li Y, Cao X, Pan C, Chen Y, Wang G. HUG: hierarchical urban Gaussian splatting with block-based reconstruction for large-scale aerial scenes. arXiv:2504.16606, 2025.（[arXiv](https://arxiv.org/abs/2504.16606)）
[^b8-10]: Liu Y, Luo C, Mao Z, Peng J, Zhang Z. CityGaussianV2: efficient and geometrically accurate reconstruction for large-scale scenes. ICLR 2025（据 arXiv 备注）. arXiv:2411.00771.（[arXiv](https://arxiv.org/abs/2411.00771)）

## 应用层：应用验证

应用层分为三组，分别验证三个领域共性基础板块：A 组无人智能装备应用验证板块五，B 组地球系统模式应用验证板块六，C 组时空大数据应用验证板块七。每篇以“验证哪些方法成果”定位；A-2 局部重规划为核心验证场景，与国内外研究现状综述直接衔接。

### A 无人智能装备应用（验证板块五）

| 编号 | 题目方向 | 验证的方法成果 |
| --- | --- | --- |
| A-1 | 基于时空网格预约的多机战略冲突消解 | 2-1、5-1、5-2、5-3 |
| A-2 | 基于网格编码的局部重规划（核心） | 2-1、2-2、5-2、5-4 |
| A-3 | 网格代价场下的任务动态重分配 | 2-3、5-3 |
| A-4 | UAM 走廊与垂直起降场流量管理 | 5-1、5-3 |
| A-5 | 学习型局部重规划决策 | 2-4、A-2 |
| A-6 | 神经提议与网格校验的冲突检测安全护盾 | 2-3、3-2 |
| A-7 | 预测式战术冲突消解（低空风场与冲突概率预测） | 2-4、3-3、5-5 |
| A-8 | 概率冲突检测与风险感知规划 | 3-1、5-4 |
| A-9 | 不确定性驱动的无人机主动采样 | 3-2 |
| A-10 | 空管大模型网格智能体与航迹异常检测 | 4-4、5-1 |

#### A 组说明

- 对比基线：《工程科学学报》2026 年提出“全局航路—局部重规划—机动控制”分层冲突消解（原文称“冲突解脱”），平均重规划时间 126 ms（[工程科学学报](https://cje.ustb.edu.cn/article/doi/10.13374/j.issn2095-9389.2026.03.20.003)），可作为 A-2 的非网格基线。
- A-10 可借鉴以 S2 网格为枢纽构建地理知识图谱的思路（[arXiv 2410.14808](https://arxiv.org/abs/2410.14808v1)），以 GeoSOT 关联法规限制、障碍物与运营人资质。
- 数据：真实无人机航迹较少，可用仿真数据，或用有人机 ADS-B 公开数据（如 OpenSky）预训练后迁移。

### B 地球系统模式应用（验证板块六）

| 编号 | 题目方向 | 验证的方法成果 |
| --- | --- | --- |
| B-1 | 千米级模拟输出的交互式分析平台 | 6-1、2-5、2-6 |
| B-2 | 区域气候降尺度与影响评估 | 6-3、3-3 |
| B-3 | 多分量耦合试验 | 6-2、2-2 |
| B-4 | 数据同化与预报试验（含无人机观测） | 6-4、3-1、A-9 |
| B-5 | AI 中期天气预报 | 6-5、2-4、3-3 |

#### B 组说明

- 数据：依托公开模式输出与再分析资料，如 nextGEMS、CMIP6、ERA5，降低对自行运行模式的依赖。
- 跨组联动：B-4 接入 A-9 的无人机移动观测，B-2、B-5 的低空风场产品可回馈 A-7。

### C 时空大数据应用（验证板块七）

| 编号 | 题目方向 | 验证的方法成果 |
| --- | --- | --- |
| C-1 | 遥感影像网格数据立方体 | 7-1、7-4、7-5 |
| C-2 | 城市交通轨迹大数据分析 | 7-2、7-3、2-3 |
| C-3 | 跨部门多源时空数据共享交换 | 7-1、7-4 |
| C-4 | 数字孪生城市时空底座 | 7-1、7-2、5-5 |
| C-5 | 实时位置流处理与查询 | 7-2、2-3 |

#### C 组说明

- C-3 以 OGC API – DGGS 作为对外接口，检验与国际标准的互操作。
- C-5 面向车辆、物联网等通用位置流，与 A 组的 UTM 场景区分。

## 共性风险与对策

| 风险 | 涉及板块 | 对策 |
| --- | --- | --- |
| 离散化保守性：网格判定放大实际安全间隔、降低空域容量 | 二、五 | 定量分析网格层级与容量损失的权衡（5-3），可作为贡献点 |
| 网格航迹不满足动力学：折线平滑后可能离开原网格 | 五 | 5-2 设计平滑后的网格一致性校核 |
| 审稿人质疑“为何用 GeoSOT”：国际上可能视其为八叉树 | 全部 | 与 H3、S2、均匀体素、八叉树对比，突出标准化编码与多尺度一致性 |
| 跨层级泛化：GeoSOT 有 32 个层级，学习模型可能只在训练层级有效 | 二、四 | 优先生成与层级无关的程序，或多层级联合训练 |
| 正确性证明：进化搜索所得程序需证明精确 | 二 | 有限层级穷举测试并辅以形式化证明 |
| 计算成本：进化搜索、集合预报与基础模型耗费算力 | 二、三、四 | 从单一关系或区域小模型起步 |
| 应用论文缺少方法贡献，被视为工程应用 | 应用层 | 每篇在应用层 A、B、C 组表中列明所验证的方法成果，并在文中阐明方法贡献 |
| 切香肠式发表 | 全部 | 共用仿真平台与 5-5 数据集，但每篇问题定义与贡献独立完整 |

AlphaDev、FunSearch、AlphaEvolve、神经算法推理、学习化布隆过滤器等文献：[^b2b-1][^b2b-2][^b2b-3][^b2b-4][^b2b-5][^b2b-6]

以上文献已据 Crossref 与 arXiv 核对。FunSearch 于 2023 年 12 月在线、2024 年 1 月刊出，采用刊出年；AlphaEvolve 目前只有 arXiv 版本；Mitzenmacher 2018 指 NeurIPS 论文，勿与 arXiv 1802.00884 混淆，其页码 464-473 仅见 mlanthology，未在 NeurIPS 官网核对。

[^b2b-1]: Mankowitz D J, Michi A, Zhernov A, et al. Faster sorting algorithms discovered using deep reinforcement learning. Nature, 2023, 618(7964): 257-263. DOI: 10.1038/s41586-023-06004-9.
[^b2b-2]: Romera-Paredes B, Barekatain M, Novikov A, et al. Mathematical discoveries from program search with large language models. Nature, 2024, 625(7995): 468-475. DOI: 10.1038/s41586-023-06924-6.
[^b2b-3]: Novikov A, Vũ N, Eisenberger M, et al. AlphaEvolve: a coding agent for scientific and algorithmic discovery. arXiv:2506.13131, 2025.（[arXiv](https://arxiv.org/abs/2506.13131)）
[^b2b-4]: Veličković P, Blundell C. Neural algorithmic reasoning. Patterns, 2021, 2(7): 100273. DOI: 10.1016/j.patter.2021.100273.
[^b2b-5]: Kraska T, Beutel A, Chi E H, et al. The case for learned index structures. Proceedings of the 2018 International Conference on Management of Data (SIGMOD), 2018: 489-504. DOI: 10.1145/3183713.3196909.
[^b2b-6]: Mitzenmacher M. A model for learned Bloom filters and optimizing by sandwiching. Advances in Neural Information Processing Systems 31 (NeurIPS 2018): 464-473.（[NeurIPS](https://proceedings.neurips.cc/paper/2018/hash/0f49c89d1e7298bb9930789c8ed59d48-Abstract.html)）

## 投稿方向

| 方向 | 主要对应板块 | 国内期刊 | 国际期刊 / 会议 |
| --- | --- | --- | --- |
| 地理信息 | 一、二、三、四、五 | 《测绘学报》《武汉大学学报（信息科学版）》《地球信息科学学报》 | ISPRS International Journal of Geo-Information；International Journal of Geographical Information Science |
| 计算机视觉与摄影测量 | 八 | 《测绘学报》《武汉大学学报（信息科学版）》 | CVPR；ICCV；ISPRS Journal of Photogrammetry and Remote Sensing |
| 空间数据库 | 二、七 | — | ACM SIGSPATIAL；GeoInformatica |
| 机器学习 | 三、四 | — | ICLR；NeurIPS；AAAI |
| 航空 | 五、应用层 | 《航空学报》 | Aerospace Science and Technology；Chinese Journal of Aeronautics |
| 交通管理 | 应用层 | — | Transportation Research Part C；IEEE Transactions on Intelligent Transportation Systems |
| UTM 会议 | 五、应用层 | — | AIAA Aviation；DASC；ICNS |
| 地球系统模式 | 六 | 《大气科学》《气象学报》 | Geoscientific Model Development；Journal of Advances in Modeling Earth Systems |

期刊定位与要求请以最新投稿指南为准。
