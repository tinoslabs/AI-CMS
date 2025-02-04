# Django Docker Deploment

## Check List
- [ ] Copy following files & folder to root folder of the project.
  - [.gitignore](.gitignore)
  - [Dockerfile](Dockerfile)
  - [docker-compose.yml](docker-compose.yml)
  - [.dockerignore](.dockerignore)
  - [entrypoint.sh](entrypoint.sh)
  - [requirements.txt](requirements.txt)
  - [sample.env](sample.env)
  - [nginx](nginx) (folder & contents)
- [ ] Copy [django_project/prod_settings.py](django_project/prod_settings.py) to the django project folder.
- [ ] Make sure requirements.txt have all dependencies with latest compatible version.
- [ ] Remove any unwanted dependencies and its reference in the code.

    Example: whitenoise package specified in the requirements.txt and its corresponding django settings
- [ ] Make sure static files like image have compressed to size < 200 kb