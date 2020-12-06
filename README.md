# UBI Center analysis template
Template for UBI Center analyses, including Jupyter-Book and GitHub Action files.

Instructions:
* Replace `reponame` with the name of the repo in `environment.yml`, `jb/_config.yml`, and the files in `.github/workflows/*`.
* Add data generation `.py` script and data files to `jb/data` folder.
Store files in `.csv.gz` format and load them as local files in analysis notebooks.
* Add all necessary packages to `environment.yml`.
* Use pull requests to make changes; the workflows will trigger and alert you of any errors.
