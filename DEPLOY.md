# Publish the guide for students

The repository already contains the complete working site. Publish the checked-in files directly. The retained ZIP files are historical deliveries and do not need to be extracted over a clone.

## Existing GitHub repository

1. Clone this repository, or download and extract GitHub's repository ZIP. If you are working from an earlier delivered ZIP, extract that package first.
2. Keep the complete site at the repository root. The root should contain `index.html`, `Workflow_Research_Guide.html`, `data`, `code`, and the other folders. Include the hidden `.nojekyll` file so Pages serves the static files without Jekyll processing. If copying into another repository, upload the extracted contents rather than the outer folder or a ZIP alone.
3. Commit the upload to the branch you intend to publish. Do not replace an existing site's `index.html` without first backing it up or choosing a separate repository.
4. In **Settings → Pages**, set **Source** to **Deploy from a branch**, choose your uploaded branch (usually **main**) and **/(root)**, then **Save**. No custom Actions workflow is needed.
5. Use **Visit site** on the Pages settings page and share that address with students. A repository file-view URL is not the interactive website.

GitHub Pages will give a project site an address in this form.

```text
https://YOUR-USERNAME.github.io/YOUR-REPOSITORY/
```

The application uses relative paths. Your repository does not need a particular name and there is no base-URL configuration to edit.

### Upload choice

**GitHub Desktop or Git.** Clone the existing repository and copy any changed site files into its root. Review the changes before committing and pushing them. Keep your existing `.git` directory and preserve the supplied archive files.

**Browser.** Choose **Add file → Upload files**. Select the extracted files and folders rather than the outer wrapper folder or ZIP. Use batches when GitHub's upload limits require them. On macOS, **Command + Shift + .** reveals hidden files such as `.nojekyll`. Alternatively, create an empty `.nojekyll` through **Add file → Create new file**.

GitHub's plan and organization policies determine which repositories can use Pages. Check the site's visibility before publishing and keep private student notes out of the repository.

## Local preview

Run this command from the repository root.

```bash
python3 -m http.server 8000
```

Open `http://localhost:8000/` on that computer. This server is for a local preview only. GitHub Pages hosts the published site; students do not run Python. For an offline copy, open `index.html`; external articles and videos still require internet.

## Updates

Edit and commit the files on the selected publishing branch. The selected branch is the deployment source; there is no separate build step. If a custom Pages Actions workflow already exists, choose one publishing process and adapt that configuration. The supplied `.github/workflows/checks.yml` only validates the site and does not deploy it.

For changes to the supplied editable JS, CSS or JSON assets, run `python3 tools/sync_assets.py` and review the updated HTML pages too. Refresh the checksum manifest with `python3 tools/check_manifest.py --write`, then run the checks in [TESTING.md](TESTING.md). Commit the reviewed source changes with the HTML and manifest. Historic generators in the original reference ZIP remain provenance material; the current maintenance command is `tools/sync_assets.py`.

## Troubleshooting

- **404 at the homepage.** Confirm `index.html` is directly in the configured branch and folder, and that Pages is enabled.
- **A download instead of an app.** Use the Pages address from **Visit site**, not a GitHub raw-file link.
- **A build error.** Confirm `.nojekyll` exists at the published root and inspect the Pages deployment under **Actions**.
- **Some old material appears.** Refresh the browser and confirm the latest commit is on the publishing branch. The guide uses no service worker.
- **A lesson does not play.** Use its official-page fallback. Videos are external and may be blocked by a school network or provider.
- **Notes appear missing.** Exports made from a local copy do not automatically transfer into the website's browser storage. Import the saved notes file.

## Official instructions

Documentation checked for this packaging task on 19 October 2026.

- [Configure a publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [Create a Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)
- [Upload files](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)
