#import "@preview/touying:0.7.4": *
#import themes.stargazer: *

#let zh-serif = ("Noto Serif SC", "Noto Serif CJK SC", "STSong", "SimSun")
#let zh-sans = ("Noto Sans SC", "Noto Sans CJK SC", "Microsoft YaHei")
#let accent = rgb("#315c98")
#let warm = rgb("#c86f2e")
#let green = rgb("#3f7f5f")

#show: stargazer-theme.with(
  aspect-ratio: "16-9",
  progress-bar: true,
  config-colors(
    primary: accent,
    primary-light: rgb("#e8f0fb"),
    primary-dark: rgb("#173f6f"),
  ),
  config-info(
    title: [替换为项目标题],
    subtitle: [用一句话说明项目解决了什么问题],
    author: [替换为作者],
    date: datetime.today(),
    institution: [替换为机构],
    short-title: [项目简称],
    logo: [PDF],
  ),
)

#set text(font: zh-serif, lang: "zh", size: 20pt)
#show heading: set text(font: zh-sans, weight: "semibold")
#show strong: set text(font: zh-sans, weight: "bold")

#let note-card(title, body, color: accent) = block(
  fill: color.lighten(88%),
  stroke: (left: 3pt + color),
  inset: 12pt,
  radius: 4pt,
  width: 100%,
)[
  #text(font: zh-sans, weight: "bold", fill: color.darken(20%))[#title]
  #v(4pt)
  #text(size: 0.82em)[#body]
]

#title-slide(extra: [项目交流稿 · 请替换全部示例内容])

#focus-slide[
  #text(font: zh-sans, size: 1.35em, weight: "bold")[
    这个项目真正想回答的问题是什么？
  ]

  #v(1em)
  用一句清楚的话替换这里，不要写成宽泛口号。
]

#slide(title: [为什么值得做])[
  #grid(
    columns: (1fr, 1fr, 1fr),
    gutter: 12pt,
    note-card([问题], [现有流程、工具或研究存在什么具体缺口？], color: accent),
    note-card([影响], [这个缺口会让谁浪费时间、承担风险或得出错误结论？], color: warm),
    note-card([目标], [本项目希望把哪一个关键指标或体验改善到什么程度？], color: green),
  )

  #v(1em)
  #tblock(title: [边界])[
    明确本次不解决什么，避免把小项目包装成无所不包的大方案。
  ]
]

#slide(title: [方法只保留关键步骤])[
  #grid(
    columns: (1fr, 1fr, 1fr),
    gutter: 14pt,
    note-card([01  输入], [数据、用户请求、样本或系统状态。], color: accent),
    note-card([02  处理], [最重要的方法、模型或工程流程。], color: green),
    note-card([03  输出], [指标、报告、工具结果或可交互产品。], color: warm),
  )

  #v(1em)
  只保留听众理解结论所需的流程。完整参数、环境和代码放在报告与仓库中。
]

#slide(title: [最重要的结果])[
  #grid(
    columns: (0.72fr, 1.28fr),
    gutter: 20pt,
    [
      #text(font: zh-sans, size: 2.2em, weight: "bold", fill: accent)[XX.X%]
      #v(0.25em)
      #text(font: zh-sans, weight: "bold")[替换为关键指标]
      #v(0.6em)
      用一到两句话解释这个数字意味着什么，以及它和基准相比是否真的重要。
    ],
    [
      #image("../paper/figures/stance-profiles.svg", width: 100%)
      #align(center)[#text(size: 0.65em, fill: gray)[替换为项目真实图表]]
    ],
  )
]

#slide(title: [怎样理解这个结果])[
  #grid(
    columns: (1fr, 1fr),
    gutter: 18pt,
    [
      #tblock(title: [支持证据])[
        - 与合理基准比较，而不是只展示绝对数字；
        - 报告样本量和评测条件；
        - 保留失败案例和反例。
      ]
    ],
    [
      #tblock(title: [不能过度解读])[
        - 哪些结论只在当前样本成立；
        - 哪些变量尚未控制；
        - 哪些结果需要更多数据验证。
      ]
    ],
  )
]

#slide(title: [下一步只做最有价值的验证])[
  #grid(
    columns: (1fr, 1fr, 1fr),
    gutter: 12pt,
    note-card([短期], [补齐最关键的样本、测试或可用性问题。], color: accent),
    note-card([中期], [加入更强基准、稳健性检验或真实用户反馈。], color: green),
    note-card([里程碑], [结果稳定后，再考虑主页、Release、DOI 或正式汇报。], color: warm),
  )
]

#ending-slide(title: [讨论])[
  当前最值得质疑的假设是什么？
]

