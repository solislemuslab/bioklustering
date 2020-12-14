# Machine learning tools for mycoviral data


# Steps to run this website locally

1. Clone this repository
   
   git clone https://github.com/solislemuslab/bioklustering
2. Create and activate a [python virtual environment](https://docs.python.org/3/tutorial/venv.html). In the directory:

```
python3 -m venv tutorial-env
source tutorial-env/bin/activate
```
   
3. In the virtual environment, install the packages by
   
   pip3 install -r requirements.txt

A list of packages in requirements.txt:
    
    numpy~=1.19.4
    
    pandas~=1.1.5
    
    bio~=0.2.3
    
    scikit-learn~=0.23.2
    
    plotly~=4.14.1
    
    Django~=3.1.2
    
    django-crispy-forms~=1.9.2
    
    django-plotly-dash~=1.4.2
    
    channels~=2.4.0
    
    channels-redis~=3.1.0
        
    django-redis~=4.12.1
    
    daphne~=2.5.0
    
    redis~=3.5.3
    
    psutil~=5.7.3

4. You might also need to install plotly-orca which is for writing and saving the static plotly images to local
   
   https://plotly.com/python/orca-management/
5. Run the website by
   
   python3 manage.py runserver
6. Note: We recommend you use Google Chrome to render the website because different browsers might result in different interface and functioinality
