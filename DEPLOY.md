# Publish for students

## Existing GitHub repository

1. Extract the delivered ZIP on your computer.
2. Upload the **contents** of `workflow-research-guide` to your repository root. The root should contain `index.html`, `Workflow_Research_Guide.html`, `data`, `code`, and the other folders. Include the hidden `.nojekyll` file. Do not upload only the ZIP and do not nest everything inside another folder.
3. Commit the upload to the branch you intend to publish. Do not replace an existing site's `index.html` without first backing it up or choosing a separate repository.
4. In **Settings → Pages**, set **Source** to **Deploy from a branch**, choose your uploaded branch (usually **main**) and **/(root)**, then **Save**. No custom Actions workflow is needed.
5. Use **Visit site** on the Pages settings page and share that address with students. A repository file-view URL is not the interactive website.

GitHub Pages will give a project site an address in this form:

```text
https://YOUR-USERNAME.github.io/YOUR-REPOSITORY/
```

The application uses relative paths. Your repository does not need a particular name and there is no base-URL configuration to edit.

### Upload choice

**GitHub Desktop or Git**: clone the existing repository, copy these files into its root, review the changes, commit, and push. Keep your existing `.git` directory.

**Browser**: choose **Add file → Upload files**. Select the extracted files and folders, not the outer wrapper folder or ZIP. GitHub accepts at most 100 files per browser upload; use batches if necessary. Every file here is below the 25 MiB browser limit. On macOS, **Command + Shift + .** reveals hidden files such as `.nojekyll`. Alternatively, create an empty `.nojekyll` through **Add file → Create new file**.

With GitHub Free, use a public repository. Other plans have different private-repository support. Do not publish private student notes; ordinary Pages sites are public. Organization policies or repository permissions can prevent enabling Pages.

## Local preview

From the extracted repository folder:

```bash
python3 -m http.server 8000
```

Open `http://localhost:8000/` on that computer. This server is for a local preview only. GitHub Pages hosts the published site; students do not run Python. For an offline copy, open `index.html`; external articles and videos still require internet.

## Updates

Edit and commit the files on the selected publishing branch. The selected branch is the deployment source; there is no separate build step. If a custom Pages Actions workflow already exists in your repository, disable that old workflow or adapt your existing deployment instead of running two competing publishing processes.

For changes to the supplied editable JS, CSS or JSON assets, run `python3 tools/sync_assets.py` and commit the updated HTML pages too. Then run the optional checks in TESTING.md. Historic generators in the original reference ZIP are for provenance, not the production build command.

## Troubleshooting

- **404 at the homepage**: confirm `index.html` is directly in the configured branch and folder, and that Pages is enabled.
- **A download instead of an app**: use the Pages address from **Visit site**, not a GitHub raw-file link.
- **A build error**: confirm `.nojekyll` exists at the published root and inspect the Pages deployment under **Actions**.
- **Some old material appears**: refresh the browser and confirm the latest commit is on the publishing branch. The guide uses no service worker.
- **A lesson does not play**: use its official-page fallback. Videos are external and may be blocked by a school network or provider.
- **Notes appear missing**: exports made from a local copy do not automatically transfer into the website's browser storage. Import the saved notes file.

## Official instructions

Documentation checked for this packaging task on 19 October 2026:

- [Configure a publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [Create a Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)
- [Upload files](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)
