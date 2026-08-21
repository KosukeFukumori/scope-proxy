# Instructions for scope-proxy

## Language of code comments

- This repository is public, so **write comments in source code in English**.
  - Chat responses, commit messages, and `README.ja.md` should still be in Japanese.
  - Only comments inside code (`//`, `#`, docstrings, etc.) need to be in English.
- If you come across existing Japanese comments, feel free to rewrite them in English while making other edits.

## Being mindful that this is a public repository

- This repository is **published publicly on GitHub**. When changing code, commit messages, or documentation, always keep the following in mind:
  - Never include sensitive information such as API keys, passwords, tokens, or private keys in code, config files, commit messages, or commit history.
  - Never include real personal information (email addresses, names, internal system URLs, etc.). Use a dummy domain such as `example.com` when a test needs an email address.
  - Be careful not to accidentally `git add` sensitive files that are excluded via `.gitignore`, such as `.env` or DB files.
  - If you're unsure whether a change is safe to publish, confirm with the user before committing or pushing.

## Managing the README

- `README.md` is the **source of truth** in **English** (since this is a public repository).
- Keep `README.ja.md` as the **Japanese translation** with the same content.
- When `README.md` is updated, reflect the same change in `README.ja.md` (and vice versa) to keep them in sync.
- Keep the mutual links (`[English](./README.md)` / `[日本語](./README.ja.md)`) at the top of both files.
