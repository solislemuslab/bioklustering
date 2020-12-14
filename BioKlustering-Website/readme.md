# Structure of the Code

## Quick overview
- Requirements to run the code are in `requirements.txt`
- Automatic test functions can be found in `mlmodel/tests.py`
- Python scripts for the ML models can be found in xxxx
- HTML files for the website can be found in `templates`

## Detailed description of files

The main code for the web app is stored in 5 folders:

- `BioKlustering` which contains files related to xxxx
- `media` which contains files related to xxxx
- `mlmodel` which contains files related to xxxx and divide on
   - `migrations`: xxxx
   - `parser`: xxxxx
   - `templatetags`: xxxx
   - Among other important files, there are:
      - `admin.py` for xxxx
      - `apps.py` for xxxx
      - `forms.py` for xxxx
      - `models.py` for xxxx
      - `tests.py` for automatic testing (still empty)
      - `views.py` for xxxx
- `static` which contains files related to xxx
- `templates` which contains file related to xxxx further categorized in 4 subfolders:
   - `email` with files for xxxx
   - `mlmodel` with files for xxx
   - `registration` with files for xxx
   - `widgets` with files for xxx

In addition, the file `manage.py` runs the website locally via the command `python3 manage.py runserver` (xxxx other descrption of this file?)

## References

Our web app is built using the following resources:

- Django (xxx add link)
- Plotly Dashboard (xxx add link)
- Bootstrap (xxx add link)
- xxxx