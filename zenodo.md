---
tags:
- technical
- research
- science
---

Zenodo is a free open repository run by CERN and funded through OpenAIRE that mints a permanent, citable [DOI](https://www.doi.org/) for anything you upload — a dataset, a paper, a poster, a software release, a set of benchmark tables. No affiliation, no peer review, no editorial gate. Upload, fill in the metadata, publish, and the numbers become citable the same day.

## What a DOI buys you

A DOI is a permanent identifier that resolves to your record even if your site, repo, or vault moves or dies. That is the whole product: **citability without a venue**. A journal or workshop acceptance adds a review trail and a line on a CV, but it does not make numbers more quotable than a DOI already does — so if the goal is "other work can point at this result," the repository step alone finishes it, and everything queued behind an acceptance is solving a different problem.

Zenodo metadata is pushed to [DataCite](https://datacite.org/) and OpenAIRE, so records are machine-findable and resolve in reference managers. Coverage in Google Scholar is inconsistent and shouldn't be assumed.

## Versioning

Publishing creates two DOIs:

- **Concept DOI** — always resolves to the newest version. Cite this when you mean "the dataset" as an ongoing thing.
- **Version DOI** — pins one exact snapshot. Cite this in a paper, so the reader gets the numbers you actually ran against.

New versions are added, never swapped in. A published record cannot be deleted or have its files replaced, which is what makes the identifier trustworthy — decide what is in the upload before pressing publish.

## Practical details

- **Reserve the DOI before publishing** so you can write it into the PDF, README, or note that the record contains.
- **GitHub integration** — flip a repo on in Zenodo's settings, and every tagged release is archived with its own version DOI automatically. The standard way to make code citable.
- **50 GB per record** by default, more on request. Any file type.
- **Access levels** — open, embargoed until a date, restricted behind a request form, or closed. Metadata stays public either way.
- **Communities** — topic collections you can submit a record into for visibility; curation is per-community and light.
- **License is required** on open records; [CC BY](https://creativecommons.org/licenses/by/4.0/) for data and text, an [OSI license](https://opensource.org/licenses) for code.

## Where it sits against the alternatives

[[publishing independent research]] covers the full menu. Short version: Zenodo for datasets, code, and any result you want citable now; OSF Preprints for behavioral and cognitive studies, and for pre-registering a protocol before you collect data; arXiv for a paper you want read by a field, noting it needs an endorsement in most categories. These stack rather than compete — a Zenodo record for the data, cited by a preprint elsewhere, is the normal shape.

## Related notes
- [[publishing independent research]] — venues, study structure, and ethics for research without an institution
- [[research]] — empirical observation and comparative analysis
- [[data]] — structuring raw observations and datasets
