# Structure of the Code

## Quick overview
- Requirements to run the code are in `requirements.txt`
- Automatic test functions can be found in `mlmodel/tests.py`
- Python scripts for the ML models can be found in xxxx
- HTML files for the website can be found in `templates`

## Detailed description of files

The main code for the web app is stored in 5 folders:

- `BioKlustering` which contains settings and urls
- `media` which contains images and user files
   - There are 4 folders:
      - `images`: plots generated after making predition
      - `models/images`: plots shown in description
      - `resultfiles`: csv and txt files generated after making predition
      - `userfiles`: fasta and csv files uploaded by users
   - The naming of files is userId + filename, e.g. if the userId is 6 you may see 6results.zip, 6params.txt in above folders
   - Note: don't modify files under this directory
- `mlmodel` which contains the core files that make the website function, i.e. the Django app folder
   - `migrations`: Django files that record the migrations or changes to the database
   - `parser`: scripts that are used to run the prediction and make updates to the website
      - scripts of machine learning models. They are modified to accommodate with the website. The original scripts can be found [here](https://github.com/solislemuslab/bioklustering/tree/master/manuscript/scripts).
         - `kmeans.py`
         - `GMM.py`
         - `spectralClustering.py`
      - `helpers.py`: helper script that is used to accommodate updates like saving plots and parameters for the website.
   - `templatetags`: custom filters for Django template
   - files that are common to all Django admin application:
      - `admin.py`: registering the models in `models.py`
      - `apps.py`: configuration file
      - `forms.py`: custom forms that are used to render the website
      - `models.py`: models that are used to manage data
      - `tests.py`: test file (no automatic tests at the moment)
      - `views.py`: views that render the website
- `static` which contains js and css files
- `templates` which contains html files
   - `email` with files for email template
   - `mlmodel` with files for home page, result page and FAQ
   - `registration` with files for welcome page, sign in and sign up
   - `widgets` with files for Django form field widgets with custom styles

In addition, the file `manage.py` is a common file in Django admin application. We use this file to run the website locally via the command `python3 manage.py runserver` or make a migration when there is a change in the database via the comman `python3 manage.py migrate`

For more information, refer to the [Django Documentation](https://docs.djangoproject.com/en).


## References

Our web app is built using the following resources:

- [Django](https://www.djangoproject.com/start/overview/)
- [Plotly Dashboard](https://django-plotly-dash.readthedocs.io/en/latest/)
- [Bootstrap](https://getbootstrap.com/)