# ResearchSub
A categorization system for new research publications to enable enthusiasts to stay upto date in each field. Two different styles were tested as shown above (one as a research network, one as predefined category groups). The HistoryNodes branch contains the former version (which displays all research papers in nodes as they relate to one another).
Developed in Django/Python, using MySQL and the CrossRef API.

## Setup
In order to run the web app, the MySQL database must be started. By running the dbgenerator, on startup it will format an empty database with the correct fields. The dbgenerator uses the CrossRef API. Also, make sure you have  To do this run:
> python scrape.py

## Run Server
Once setup is complete and the desired papers have been categorized, start the server by entering the django directory and navigating to the project folder "researchsub_web". Then type:
> python manage.py runserver

In order to run this, make sure you have the "mysql.connector" package installed.

The web app will now be accessible at *127.0.0.1:8000*

For deployment:
Within the django folder, the deployment version shows an example of how to configure the web app to run through WSGI on an apache configuration. The configuration is based on the recommended WSGI deployment settings.

## Use
Pulls information from the CrossRef API, requires human input (for now) to categorize each paper into a category, using the dbgenerator 
Clicking on each category allows one to narrow the field of interest and be aware of any major updates in any specific field of science
