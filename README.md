# Israel — LawCodex (ספר החוקים של מדינת ישראל)

Israeli legislation as plain Markdown, in Hebrew (the language in which statutes are
enacted). Part of [LawCodex](https://github.com/LawCodex): one repository per jurisdiction.

> **Unofficial consolidations.** The texts come from the
> [**Open Law Book** (ספר החוקים הפתוח)](https://he.wikisource.org/wiki/ויקיטקסט:ספר_החוקים_הפתוח)
> on Hebrew Wikisource: volunteers keep up-to-date consolidated versions of Israeli laws, and
> each amendment is linked to its Reshumot (Official Gazette) publication. Israel has no free,
> official, consolidated legislation database. Check the official publications (linked
> from each file) before you rely on a text. Nothing here is translated or summarised.

- Retrieved: **2026-10-12** (current Wikisource revision of each page; the revision id is
  recorded in the front matter)
- Version: each law as currently consolidated by the Open Law Book, including amendments that
  its editors have already incorporated.

## Coverage

| Directory | Contents | Files | of which flagged `repealed` |
| --- | --- | ---: | ---: |
| `he/basic-laws/` | חוקי יסוד: Basic Laws (Israel's constitutional statutes) | 18 | 1 |
| `he/laws/<year>/` | חוקים: Knesset laws (1,097); פקודות: Mandate-era ordinances still in force (122); Orders in Council and Ottoman laws (11) | 1,230 | 10 |
| `he/regulations/<year>/` | תקנות, כללים, תקנונים: regulations and rules (secondary legislation) | 3,549 | 49 |
| `he/orders/<year>/` | צווים: orders (secondary legislation) | 975 | 23 |
| `he/other/<year>/` | proclamations (אכרזות, הכרזות, מנשרים), notices (הודעות), permits, agreements, procedures, government decisions, and the Declaration of Independence | 397 | 16 |
| **Total** | | **6,169** | **99** |

The set is every page in the Open Law Book's bot-maintained category
[קטגוריה:בוט חוקים](https://he.wikisource.org/wiki/קטגוריה:בוט_חוקים) and in
[קטגוריה:חוקי יסוד](https://he.wikisource.org/wiki/קטגוריה:חוקי_יסוד) (6,170 pages; one page
had no law markup and was skipped).

The Basic Laws are Knesset, Government, President, State Economy, Army, Jerusalem, Judiciary,
State Comptroller, Human Dignity and Liberty, Freedom of Occupation (1994; the 1992 version is
also here, flagged repealed), Israel Lands, Referendum, Nation State and Torah Study. The set
also has the temporary budget Basic Laws (2009–2016, 2017–2018) and a temporary amendment to
the State Economy Basic Law.

### Status

`status: in_force` is the default. A file is `repealed` only when the Open Law Book puts an
editorial note at the top of the page saying that the instrument itself was repealed, replaced
or expired (בוטל / הוחלף / פקע). That note is copied to `status_note`. The check is
heuristic:

- Some temporary provisions (הוראת שעה) whose period has ended may still be marked `in_force`.
- Some partly repealed instruments are marked `repealed`.

### Not covered / known gaps

- **Completeness.** The Open Law Book is a volunteer project. It covers nearly all Knesset laws
  in force and many regulations, but it may lack some laws, and some consolidations may trail
  recent amendments. Each file's `consolidation_date` is the date of the last edit to its
  Wikisource page.
- **Knesset National Legislation Database / OData API not used.** `main.knesset.gov.il`,
  `knesset.gov.il/Odata/ParliamentInfo.svc` and `fs.knesset.gov.il` are geo-blocked from the
  network this was built on: every request was redirected to `maintenance-page-geo`. Laws
  are still linked to the Knesset database by their **Knesset law id**
  (`knesset_law_id`, from the Open Law Book's `{{ח:מאגר}}` template). The links point to the
  Knesset law page and to the Reshumot PDFs.
- **Secondary legislation is incomplete.** Regulations and orders are included only where the
  Open Law Book has them, which is a fraction of all Israeli secondary legislation. Municipal
  by-laws (חוקי עזר) are not included.
- **English translations** of the Basic Laws (Knesset site) are not included. The Knesset site
  is unreachable from here, and the translations are unofficial and often out of date.
- **Images** (a few diagrams and forms) are not copied. They are replaced by a marker
  `[תמונה: <file name>]` naming the Wikimedia Commons / Wikisource file.
- **Editorial content.** The Open Law Book's tables of contents and navigation boxes are
  dropped. Its editorial notes (`ח:הערה`, e.g. "(בוטל)", cross-references) are kept in
  *italics*. A few pages also show pending amendments with their explanatory notes (דברי
  הסבר), which are kept in italics too.
- **Year directory.** The year comes from the year in the title, otherwise from the date of
  adoption or signature, otherwise from the first gazette citation. 58 instruments have none of
  these and are filed under `undated/`. Most are Mandate-era ordinances and Ottoman laws.

## Structure

```
he/basic-laws/<knesset-id>-<slug>.md          e.g. he/basic-laws/2000037-hok-ysod-hknst.md   חוק־יסוד: הכנסת
he/laws/<year>/<id>-<slug>.md                 e.g. he/laws/1977/2000479-hok-honshin.md        חוק העונשין, התשל״ז–1977
he/regulations/<year>/<id>-<slug>.md
he/orders/<year>/<id>-<slug>.md
he/other/<year>/<id>-<slug>.md
```

- `<id>` is the Knesset law id when the page records one. Otherwise it is `ws<pageid>`, the
  Hebrew Wikisource page id.
- `<slug>` is a rough consonantal transliteration of the Hebrew title, for readability only.
  The Hebrew title is in the front matter and in the H1.
- `<year>` is the Gregorian year of the law (see above).

### File format

```markdown
---
title: "חוק־יסוד: הכנסת"
identifier: "2000037"
knesset_law_id: "2000037"
type: basic-law            # basic-law | law | ordinance | order-in-council | regulation | order | other
jurisdiction: il
language: he
date: 1958-02-12           # adoption by the Knesset / signature date (from the signature block)
year: 1958
consolidation_date: 2026-08-09   # last edit of the Wikisource page
status: in_force
source: "https://he.wikisource.org/wiki/חוק-יסוד:_הכנסת"
source_revision: "https://he.wikisource.org/w/index.php?oldid=…"
official_record: "https://main.knesset.gov.il/Activity/Legislation/Laws/Pages/LawPrimary.aspx?lawitemid=2000037"
consolidation: unofficial
license: "CC BY-SA 4.0 (Wikisource contributors); statutory text public domain (Copyright Act 2007 s.6)"
retrieved: 2026-10-12
---
```

Body layout:

- **Citations paragraph.** The body opens with the list of publications in Sefer HaHukim
  (ס״ח), Kovetz HaTakanot (ק״ת), Iton Rishmi (ע״ר) and similar. Each citation links to the
  official scanned PDF, and the link title names the amending act.
- **Preamble (מבוא)**, if any.
- **Parts, chapters and signs** (חלק / פרק / סימן) become headings. Each section (סעיף) becomes
  a heading `N. marginal title`, with its amendment history `*(תיקון: …)*` below.
  Sub-sections keep their labels ((א), (1), …) as separate paragraphs.
- **Schedules (תוספות)** follow the same structure. Tables are kept as HTML.
- **Signature block** at the end, after a rule (`---`).

## Sources

| Source | URL | Used for |
| --- | --- | --- |
| Hebrew Wikisource, Open Law Book (ספר החוקים הפתוח) | https://he.wikisource.org/ (MediaWiki Action API `w/api.php`) | all texts |
| Knesset National Legislation Database | https://main.knesset.gov.il/Activity/Legislation/Laws/ | ids and links only (geo-blocked, not fetched) |
| Reshumot PDFs (Knesset, olaw.org.il) | https://fs.knesset.gov.il/ … | linked from each file, not fetched |

Nevo and other commercial databases were not used.

**Access.** The texts were fetched through the MediaWiki Action API, as the Wikimedia API
etiquette allows: serial requests, 50 pages per request, a 1 s pause, `maxlag=5`, and a
descriptive User-Agent. That came to about 250 requests in total. Wikimedia's `robots.txt`
disallows `/w/` to generic HTML crawlers. It does not cover the documented API for tools, and
no HTML pages were scraped. For a fully offline refresh you could adapt the converter to the
public XML dump (`dumps.wikimedia.org/hewikisource/`).

## Licence / copyright

- **Statutory texts.** Under the Israeli Copyright Act 2007, s. 6, there is no copyright in
  statutes, regulations, Knesset Protocols or judicial decisions. The texts of laws are in the
  public domain.
- **Open Law Book.** The consolidation work, markup and editorial notes are by Wikisource
  contributors. They are under the
  [Creative Commons Attribution-ShareAlike 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
  licence. Attribution: *"ספר החוקים הפתוח", Hebrew Wikisource contributors*. The page history
  and authors are at each file's `source` URL. Derived files in this repository are shared
  under the same licence (CC BY-SA 4.0).

## Regenerate

```sh
python -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
.venv/bin/python scripts/il_fetch.py   ../_raw/il      # caches pages/<pageid>.json; re-runs only fetch changed revisions
.venv/bin/python scripts/il_convert.py ../_raw/il .    # writes he/...
```

The converter reads the Open Law Book wikitext markup directly (the `ח:` templates). It does
not scrape rendered HTML, because rendering hits MediaWiki's template-expansion limits on
the largest laws.
