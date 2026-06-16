# 中国金融数据 API 实测记录

> 最后更新: 2026-05-04 (v1.4 — 腾讯 K 线与 market 状态确认可用；DuckDuckGo 新闻降级)
> 测试环境: 海外服务器 (IP: 日本东京 64.83.44.51)

---

## 测试结论速查

| API / 数据源 | 协议 | 状态 | 备注 |
|-------------|------|------|------|
| 新浪 hq.sinajs.cn | HTTPS | ✅ | GBK编码，需 iconv |
| 腾讯 qt.gtimg.cn | HTTPS | ✅ | GBK编码 |
| 腾讯 fqkline / kline | HTTPS | ✅ | 历史日 K + `market` 状态可用 |
| Yahoo Finance | HTTPS | ✅ | 美股/VIX 正常，A股不支持 |
| AKShare (东方财富后端) | HTTPS | ❌ | push2.eastmoney.com → 502 |
| AKShare (新浪后端) | HTTPS | ✅ | stock_zh_index_daily_em 正常 |
| 东方财富 push2 API | HTTPS | ❌ | TLS握手成功，nginx 502 |
| 东方财富 datacenter-web | HTTPS | ❌ | 同502 |
| 东方财富网页 (浏览器) | Browser | 🐢 | 部分页面可用 |
| DuckDuckGo 新闻搜索 | HTTPS | ❌ | 触发 bot challenge，不再推荐 |
| Google News RSS | HTTPS | ✅ | 中文新闻可直接解析 |
| 同花顺概念板块 (10jqka.com.cn) | Browser | ❌ | 海外封 IP（64.83.44.51 → Nginx forbidden） |
| 雪球 (xueqiu.com) | Browser | ✅ | 海外可访问，但行业排行 API 需登录；申万行业分类可浏览无排行数据 |
| 雪球行情首页 (xueqiu.com/hq) | Browser | ✅ | 三大指数 + 科创50 + 热股榜可正常提取 |
| AKShare 板块函数 (push2后端) | HTTPS | ⚠️ | 与东方财富 API 同后端，海外大概率 502 |
| 新浪 hq.sinajs.cn（浏览器 fetch） | Browser | ❌ | 直接导航返回 Forbidden；带 Referer fetch 受 CORS 限制 |
| 新浪财经首页 (finance.sina.com.cn) | Browser | ✅ | 首页含三大指数实时数据，可用 snapshot 提取 |

---

## 东方财富 API 被墙详情

### 测试命令
```bash
curl -sv --connect-timeout 5 \
  "https://push2.eastmoney.com/api/qt/stock/get?secid=1.000001&fields=f43,f170"
```

### 测试结果
```
DNS 解析: 120.79.191.232 (阿里云杭州)
TLS 握手: ✅ 成功 (TLS 1.3 → 降级 1.2)
HTTP 响应: 502 Bad Gateway
nginx 版本: 1.26.2
```

**结论**: CDN 层面的 Geo-blocking。DNS 解析到国内阿里云 IP，TLS 连接成功，但 nginx 拒绝转发请求到上游应用服务器。非中国 IP 一律 502。

### 尝试过的绕过方法（均失败）
- HTTP 协议（不用 HTTPS）→ 同样 502
- 修改 User-Agent 伪装国内浏览器 → 同样 502
- 添加 Referer → 同样 502
- AKShare 库 → 底层 HTTP 请求同样 502

---

## 浏览器抓取东方财富网页实测

### ✅ 可用的页面
- `https://data.eastmoney.com/hsgt/index.html` — 北向资金 + 涨跌家数
  - 表格数据可通过 `browser_console` 执行 `document.querySelectorAll('table tbody tr')` 提取
  - 数据包含 11 列：类型/板块/状态/净买额/成交总额/资金余额/上涨数/持平数/下跌数/相关指数/涨跌幅
  - 加载时间: 5-15 秒

### ❌ 不可用的页面
- `https://data.eastmoney.com/bkzj/hy.html` — 板块排行
  - 页面加载成功，但数据表格使用 **Canvas 渲染**
  - JS `document.querySelectorAll` 只能提取到表头（2行），无法获取数据行
  - 页面脚本中搜索不到板块数据 JSON

### ❌ 同花顺概念板块 — 海外封 IP（2026-05-02 验证）
- `https://q.10jqka.com.cn/gn/` — 返回 **Nginx forbidden** + 来源 IP `64.83.44.51`
- 同花顺对非中国 IP 实施 Geo-block，海外不可用

### ⚠️ 雪球 — 海外可用但板块数据受限（2026-05-02 验证）
- `https://xueqiu.com/hq` — ✅ 海外可访问，三大指数+科创50+热股榜正常
- 申万行业分类可浏览（`xueqiu.com/hq#exchange=CN`），但为纯分类列表，**无涨跌幅排行**
- 行业排行 API（`stock.xueqiu.com/v5/stock/screener/quote/list.json`）返回 `400016` 需登录
- 个股排行（创业板涨幅/跌幅等）可正常提取，但非板块维度

### ⚠️ 不稳定的页面
- `https://data.eastmoney.com/zjlx/` — 资金流向
  - 部分数据 JS 动态加载
  - 首次加载可能只有表头，需要等待 JS 渲染
  - 实际数据提取成功率不高

---

## 新浪 API 详细说明

### 指数行情
```
GET https://hq.sinajs.cn/list=sh000001,sz399001,sz399006
Headers: Referer: https://finance.sina.com.cn
Encoding: GBK

返回格式: var hq_str_sh000001="名称,当前价,昨收,今开,最高,最低,...,成交量(手),成交额(元),...";
```

字段索引（从 0 开始）:
- 0: 名称
- 1: 当前价
- 2: 昨收
- 3: 今开
- 4: 最高
- 5: 最低
- 8: 成交量（手）
- 9: 成交额（元）

### 人民币汇率
```
GET https://hq.sinajs.cn/list=USDCNY,USDCNH
Headers: Referer: https://finance.sina.com.cn
```

---

## 腾讯 API 详细说明

### 指数行情
```
GET https://qt.gtimg.cn/q=sh000001,sz399001
Encoding: GBK

返回格式: v_sh000001="1~名称~代码~今开~昨收~当前价~成交量~...";
```

字段分隔符为 `~`。

### 历史 K 线 + 市场状态
```
GET https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh000001,day,,,30,qfq
GET https://web.ifzq.gtimg.cn/appstock/app/kline/kline?param=sh000001,day,,,30
```

特点：
- 返回近 N 日日 K（日期/开/收/高/低/量）
- `qt.market` 字段内含市场状态，例如：
  - `SH_close_劳动节休市`
  - `SZ_close_劳动节休市`
  - `CYB_close_劳动节休市`
- 适合用于：
  1. 历史轨迹复盘
  2. 节假日/收盘后/午休的状态确认

注意：
- `market` 状态优先级高于本地时钟判断
- 可作为 AKShare 缺失时的零依赖替代路径

### 板块数据（格式不标准）
```
GET https://qt.gtimg.cn/q=pt01801053,pt01801040,...
```
⚠️ 涨跌幅百分比数值异常（如 28267%），可能是字段索引错误或编码问题。需要进一步验证。

---

## 测试用 SSH 服务器

- **IP**: 150.158.111.110（实际出网 IP: 64.83.44.51）
- **位置**: 日本东京
- **用户**: ubuntu
- **系统**: Ubuntu 24.04 (6.8.0-48)
- **无代理**: 未配置 clash/v2ray/proxychains
- **结论**: 非中国 IP，东方财富 API 不可用

---

## 结论与建议

1. **海外服务器做 A 股分析的最佳方案**：新浪财经首页（指数）+ 浏览器抓取东方财富（北向资金 + 板块持股流）+ 雪球（交叉验证指数 + 热股榜）
2. **完整六维分析需要国内服务器**：部署在阿里云/腾讯云国内节点，东方财富 API 全通，同花顺/雪球 API 均可正常调用，AKShare 板块函数可用
3. **板块排行是最大缺口**：同花顺封海外 IP，雪球板块 API 需登录，东方财富 Canvas 渲染不可抓。目前板块数据唯一可用来源是东方财富网页的「板块持股流」表（涨跌+资金流，非纯涨幅排行）
4. **新浪 API（hq.sinajs.cn）**：curl CLI 可用（需 iconv GBK），浏览器端受 CORS 限制不可用；新浪财经首页（finance.sina.com.cn）可替代提取指数数据
5. **腾讯 fqkline/kline 是关键补位源**：零依赖即可获取历史日 K 和市场状态，适合作为海外环境下 A 股历史轨迹主路径
6. **AKShare 在新浪后端模式下可用**：`stock_zh_index_daily_em` 等函数走新浪接口，不受 Geo-block 影响；板块函数（`stock_board_*_em`）仍走东方财富后端，海外不可用
