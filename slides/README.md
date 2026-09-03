# 幻灯片（可选）

普通项目默认不生成幻灯片。需要快速讲解时，使用 `main.typ` 的 Touying
`stargazer` 模板：

```powershell
typst compile slides/main.typ slides/main.pdf --root .
```

正式导师汇报、答辩或演讲时，参考：

- `polished-sample.pdf`：8 页精美样稿；
- `polished-sample.pptx`：可打开的 PowerPoint 样稿；
- `polished-sample-preview.png`：整套缩略预览；
- `POLISHED_STYLE.md`：视觉和叙事规则。

简洁稿和精美稿都应复用 `paper/` 与 `results/` 中的真实图表和结论。

