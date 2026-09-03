# Publish Checklist

This project is meant for lightweight research notes: more formal than a blog post, less formal than a conference paper.

## Default rule

The default project output is deliberately minimal:

1. A GitHub repository with code, data notes, figures, and results.
2. A simple PDF report from `paper/main.typ`.

There are two distinct modes:

- Local-only request: build code and PDF, with no external write.
- Upload/publish request: publish the cleaned project to a public GitHub repository
  and sync the PDF, project record, generated detail page, and public code link to
  `3099404236.github.io`. Use private GitHub or skip the homepage only when the user
  explicitly asks for that exception.

Do not create slides, Zenodo DOI records, polished presentation assets, or
discussion posts unless they are actually needed. Add those only as optional
upgrades after the basic repository and PDF are working.

## One-time setup

1. Create a repository from this template.
2. Confirm GitHub Actions are enabled.
3. Use public visibility by default for a publish request; use private only when
   explicitly requested.

Optional setup:

- Enable **Discussions** if you want feedback inside GitHub.
- Connect Zenodo only if this project may later need a DOI.
- GitHub Pages synchronization is part of the default publish flow when a PDF exists.

## Default per-project workflow

1. Put code in `code/`, data notes or small data files in `data/`, and outputs in `results/`.
2. Edit `paper/main.typ`.
3. Edit `paper/refs.bib` if references are needed.
4. Edit `README.md` with the abstract and reproduction steps.
5. Compile and visually check the PDF:

```powershell
.\scripts\publish-note.ps1 -LocalOnly -RenderPages 2
```

6. When the PDF is ready, run the publish script:

```powershell
.\scripts\publish-note.ps1 -Message "Update research note" -RenderPages 2
```

Before running the command, fill `publish.json`. The publish command defaults to
public GitHub plus a complete homepage sync:

```powershell
.\scripts\publish-note.ps1 `
  -Message "Publish project report" `
  -RenderPages 2
```

The script compiles `paper/main.typ`, optionally renders selected pages, publishes
the cleaned project to a public repository, then copies the PDF, upserts
`data/publications.json`, regenerates the homepage, waits for Pages, and checks the
public project and PDF URLs. `-LocalOnly` is a hard no-publish boundary.

Use `-Private` only for an explicitly private repository. Use `-SkipHomepage` only
when the user explicitly asks not to update the personal homepage.

Stop here for most projects.

## What a project should contain

Use this template as a project package, not only as a paper template:

- `README.md`: the front door for humans and coding agents.
- `code/`: the actual implementation.
- `data/`: small data, sample files, or a dataset card.
- `results/`: generated outputs and final figures.
- `paper/`: the default report source and PDF.
- `slides/`: optional Stargazer slide source and PDF.
- `.zenodo.json` and `scripts/zenodo-draft.ps1`: optional DOI workflow.
- `scripts/publish-note.ps1`: local build, GitHub push, homepage PDF sync, and
  public PDF check.

Not every project becomes a paper. A tool project can stop at code plus a PDF
report. A research project can later add versions, slides, discussion links, and
DOI when the result deserves a milestone archive.

## Optional upgrades

Use these only when the project needs them.

### Simple slides

Create a simple Typst/Touying slide deck when the project is paper-like or you
need a lightweight explanation for others. Keep the style restrained, similar to
Touying `stargazer` or another clean default theme. Reuse the PDF's figures and
main claims instead of rebuilding a separate presentation from scratch.

The template slide file is `slides/main.typ`:

```powershell
typst compile slides/main.typ slides/main.pdf --root .
```

### Polished presentation

Create a more polished custom deck only for teacher meetings, defenses, talks,
or other explicit presentation settings. This is not part of the default
workflow.

### DOI and archive

When you want a Zenodo DOI:

1. Edit `.zenodo.json` title, description, creators, and keywords.
2. Create a GitHub Release, for example `v0.1.0`.
3. Let Zenodo archive the release or use the Zenodo API draft workflow below.
4. Copy the DOI into `README.md`, `CITATION.cff`, `.zenodo.json`, and the
   homepage record if one exists.

### Discussion

Post the GitHub repository link in a discussion community such as LessWrong,
Reddit r/MachineLearning, Hugging Face, or GitHub Discussions only when you
actually want outside feedback.

### Homepage entry

Add a homepage entry only when public discovery is useful. The homepage schema
should classify the project as one of:

- `research`: paper-like experiments, evaluations, or research notes.
- `tools`: utilities, datasets, scripts, libraries, or workflow helpers.
- `applications`: demos, apps, dashboards, or applied systems.

Inside each category, show each project as a collapsible box with a short
description and a version timeline. Each version may link to PDF, slides,
GitHub, release, DOI, demo, and discussion. DOI is optional and should be present
only for formal Zenodo milestones.

## Quick local preview

For small edits, do not publish every time. Compile locally and render only the
page you touched:

```powershell
.\scripts\publish-note.ps1 -LocalOnly -RenderPages 2
```

For continuous editing, use Typst watch:

```powershell
typst watch paper/main.typ paper/main.pdf
```

## Zenodo API draft

If you want to reserve a Zenodo DOI without using the GitHub repository toggle,
create a Zenodo personal access token with `deposit:write` and `deposit:actions`,
then set it only in your shell:

```powershell
$env:ZENODO_TOKEN="..."
.\scripts\zenodo-draft.ps1
```

This creates an unpublished Zenodo draft, uploads `paper/main.pdf` and a source
archive, and writes the draft id/URL/reserved DOI to `zenodo-draft.json`.

### Working rule

Use Zenodo as a milestone archive, not as the daily working copy.

- Daily edits: update GitHub and GitHub Pages.
- In-progress public placeholder: keep an unpublished Zenodo draft with a
  reserved DOI.
- Formal milestone: publish the Zenodo record only when explicitly ready.
- Later research stages: keep working in GitHub, then create a new Zenodo version
  when the next stage is ready.

Publishing is intentionally separate:

```powershell
.\scripts\zenodo-draft.ps1 -Publish
```

Only publish when the metadata and files are ready. After publishing, files and
the persistent identifier cannot be modified in-place; use a new version instead.

## Notes

- Google Scholar indexing is not guaranteed. The homepage is only structured to make indexing easier.
- Zenodo is for preservation and DOI, not discussion.
- GitHub Discussions is the default discussion channel for feedback.
- Typst compiles the whole PDF, but it is usually fast. The expensive part is
  rendering and publishing, so the script lets you render only selected pages and
  skip publishing with `-LocalOnly`.
