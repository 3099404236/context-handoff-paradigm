# Agent Brief: Start or Update a Research Note

This repository is a reusable template for lightweight research notes. Use it
for small AI experiments that should be more formal than a blog post but less
formal than a conference paper.

## Default deliverable policy

Keep the default workflow small. For a normal new project, the required output is
only:

1. A GitHub repository with code, data notes, figures, and reproducible results.
2. A simple formal PDF report compiled from `paper/main.typ`.

Everything else is optional:

- Slides are not part of the default project output.
- Use a simple Typst/Touying slide deck only when the project is paper-like or
  the user explicitly needs to explain it to others.
- Use a polished custom presentation only for teacher meetings, defenses,
  talks, or other explicit presentation scenarios.
- Zenodo DOI is a milestone archive step, not part of day-to-day project work.

Build the code and PDF first. If the user asks only for local output, stop there.
If the user says upload or publish, the personal default is a public GitHub
repository plus a complete homepage sync: PDF, project metadata, generated detail
page, and public code link. Only keep the repository private or skip the homepage
when the user explicitly requests that exception.

## What the user should provide

For a new project, ask the user for these inputs if they are not obvious from
the workspace:

1. Project title.
2. Short research idea or draft notes.
3. Source folder for code, data, figures, and results.
4. GitHub repository name.
5. Whether the user wants local-only output or publication. For publication,
   infer public visibility and homepage sync unless the user says otherwise.

Do not ask for DOI at the start. Zenodo DOI comes after a GitHub Release.
Do not ask for slides unless the user mentions a talk, teacher meeting, defense,
presentation, or paper-like writeup.

## Files to edit

- `paper/main.typ`: main research note source.
- `paper/refs.bib`: references.
- `paper/figures/`: figures used by the note.
- `slides/main.typ`: optional simple Stargazer slide deck.
- `README.md`: public project summary and reproduction steps.
- `.zenodo.json`: Zenodo metadata before creating a release.
- `CITATION.cff`: citation metadata.
- `data/`, `code/`, `results/`: project artifacts.

## New project setup

For a new project, make sure the package is understandable before adding optional
publishing layers:

1. Put the implementation under `code/`.
2. Put sample data or dataset notes under `data/`.
3. Put generated tables, logs, and figures under `results/`.
4. Write the default report in `paper/main.typ`.
5. Compile `paper/main.pdf`.
6. Update `README.md` so a reader knows what to run and what to read.

Only after that, decide whether the project needs:

- `slides/main.typ` and `slides/main.pdf` for a simple Stargazer explanation.
- a homepage category under `research`, `tools`, or `applications`; this entry is
  part of the default publish flow, but not part of a local-only build.
- an unpublished Zenodo draft with a reserved DOI.
- a formal Zenodo publish step.

## Local preview

For quick edits, do not publish. Compile and render only the page that changed:

```powershell
.\scripts\publish-note.ps1 -LocalOnly -RenderPages 2
```

Use `-RenderAll` only when layout changes affect many pages.

## GitHub publish

After the note looks correct locally:

```powershell
.\scripts\publish-note.ps1 -Message "Update research note" -RenderPages 2
```

This command is for publication, not local preview. Publication defaults to a
public GitHub repository and homepage sync. Fill `publish.json` first; use
`-Private` or `-SkipHomepage` only when the user explicitly requests that exception:

```powershell
.\scripts\publish-note.ps1 `
  -Message "Publish project report" `
  -RenderPages 2
```

The script will:

1. Compile `paper/main.typ` to `paper/main.pdf`.
2. Optionally render selected PDF pages to PNG under `.workbuddy/publish-render`.
3. Create or verify a public GitHub repository and push this project.
4. Wait for GitHub Actions to verify the PDF build.
5. Copy the PDF and upsert the project record in the homepage repository.
6. Rebuild and push the homepage project list and detail page.
7. Wait for GitHub Pages deployment.
8. Verify both the public project page and PDF URL.

This is still just the normal PDF publication path. It does not imply Zenodo
publication or slide creation.

## Optional homepage model

The personal homepage should group work into three collapsible categories:

- `research`: paper-like studies and experiments.
- `tools`: utilities, workflow helpers, datasets, or libraries.
- `applications`: demos, apps, dashboards, or applied systems.

Each project can contain multiple versions. A version may have PDF, slides,
GitHub, release, DOI, demo, and discussion links. Missing DOI or missing slides
is expected for many projects.

## Important workflow decision

GitHub Actions should validate the PDF build but should not commit generated PDF
files back to the repository. The PDF should be compiled locally and committed
with the source changes. This avoids bot commits and rebase noise.

## Typography notes

Chinese fonts are configured at the top of `paper/main.typ`:

```typst
#let zh-serif = ("Noto Serif SC", "Noto Serif CJK SC", "STSong", "SimSun")
#let zh-sans = ("Noto Sans SC", "Noto Sans CJK SC", "Microsoft YaHei")
```

Use `zh-serif` for paper-like body text and `zh-sans` for headings. If a user
wants a different Chinese style, update these two lines first.

## Formula caution

Avoid ambiguous Typst math such as:

```typst
1 / |P| sum_(p in P) s(m, p, d)
```

Write explicit fractions instead:

```typst
(sum_(p in P) s(m, p, d)) / abs(P)
```

Always render the page containing changed formulas before publishing.

## After GitHub Release

When the user wants a DOI:

1. Create a GitHub Release.
2. Confirm Zenodo archives the release.
3. Copy the Zenodo DOI into `README.md`, `CITATION.cff`, `.zenodo.json`, and the
   homepage publication record.
4. Re-run the publish script.

## Zenodo API draft

If the user provides a Zenodo personal access token, do not write it to any file.
Set it only in the current shell as `ZENODO_TOKEN`, then run:

```powershell
.\scripts\zenodo-draft.ps1
```

This creates an unpublished Zenodo draft, uploads `paper/main.pdf` plus a source
archive, and saves non-secret draft metadata to `zenodo-draft.json`. Use
`-Publish` only after explicit confirmation because published files and DOI
cannot be modified in-place.

Default policy:

- Ordinary edits should update GitHub and GitHub Pages only.
- Zenodo should be treated as a milestone archive, not as the working copy.
- It is acceptable to maintain an unpublished Zenodo draft with a reserved DOI
  while the work is still changing.
- Do not publish a Zenodo record unless the user explicitly says something like
  "正式发布", "publish to Zenodo", or "release v1".
- Once published, that version's files remain permanently available. Later work
  should continue in GitHub and become a new Zenodo version only at the next
  milestone.
