# YPPF

## How to run it
It is recommended to run it with [docker](https://www.docker.com/),
docker-compose and vscode devcontainer.

Within the devcontainer, run the following code to start!

```bash
bash scripts/default_config.sh
python3 manage.py makemigrations # Add new app here if necessary
python3 manage.py migrate
python3 manage.py fill_devdb
python3 manage.py runserver
```

Then, you can access the website from "http://localhost:8000".

Inspect code in *dm/management/fake_records.py* for accounts info.

If you want to test with scheduler job,
edit the config file and change `use_scheduler` to `true`.
Then, open a new terminal and start the scheduler:

```bash
python3 manage.py runscheduler
```




## Project Structure
TODO

## Contribute
Fork the repo, modify on develop branch of your replica.

Reference 

Before open a pull request, run `python3 manage.py test` to check whether your
modification affects other functionality.
