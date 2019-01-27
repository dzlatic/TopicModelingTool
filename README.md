# Project: Topic Modeling Tool @ Cisco Libe Barcelona 2019 BRKCCT-2510
#

This project is contains three parts:

1. Jyputer Notebook file "TopicModelingTool-BRKCCT-2510.ipynb" used for row data import
and LDA model building 
2. TopicModelingTool Web appliocation providing REST API and Admin for Topic model
access
3. Procedure for importing model developed and saved in Jyputer Notebook into 
TopicModelingTool Web appliocation server - load-models.py.

## Deployment target on AWS:

Ubuntu-1GB-Frankfurt-1;
1 GB RAM, 1 vCPU, 40 GB SSD;
Ubuntu 16.04;
Frankfurt, Zone A (eu-central-1a)

## Summary of performed configuration tasks on top of VM provided by AWS:

- Configured Ubuntu firewall per spec below;
- Installed missing packages per table below;
- Updated & Upgraded system packages;
- Updated AWS configuration to reflect te same ports opening as on Ubuntu;
- Updated Google credentials with validated domain (used meta tag method).

## Deployment Details

| Parameter | Value |
| ------ | ------ |
| IP Address of the server | 3.121.213.222 |
| SSH port | 2200 |
| URL of the web application home page | http://3.121.213.222.xip.io |
| Application: | /var/www/TopicModelingTool |
| Apache/WSGI conf | /etc/apache2/sites-available/TopicModelingTool.conf |


## Important Notes:

1. Remote login with password has been disabled. You can only access the server
with SHH if you have private key. You can change this configuration
by changing values n the "/etc/ssh/sshd_config" file:
    #### "PubkeyAuthentication yes"
    #### "PasswordAuthentication no"


2. This server is configured so that only open ports are:

| Port | tcp/udp | purpose |
| ------ | ------ | ------ |
| 2200 | tcp | SSH |
| 80 | tcp | HTTP |
| 123 | udp | NTP |

Please note that default SSH port is disabled! Validate configuration with command:

    #### sudo ufw status verbose


## Summary of code adjustments:

- Added support for PostgreSQL;
- Adjusted code so that new directory structure is considered;
- Added new file "tiopicmodelingtool.wsgi" on the level above project files;
- Adjusted paths to .json files with secrets.


## Files included in Git repository:

| File | Comment |
| ------ | ------ |
| database_setup.py | application that creates database |
| load_models.py | application that loads model into database |
| application.py | main application that runs Flask web server |
| README.md | this file |
| templates/index.html | home page, with REST definitions and links to admin page  |
| templates/editTopics.html | admin page for model visualization and assigning aliases and actions to topics |
| static/styles.css | CSS file, addition to Bootstrap invoked in main.html |
| static/favicon.ico | Web app icon, required by browsers |


## Files necessary bit not included in Git repository:
(transfer to server was done using scp, as best practice for sensitive data)

| File | Comment |
| ------ | ------ |
| client_secrets.json | web app client secrets  |
| db_secrets.json | PostgreSQL database credentials   |

## Dependencies

| Software | Version | Download |
| ------ | ------ | ------ |
| Python | Python 3.6.6 | [link](https://www.python.org/downloads/release/python-368/) |
| Flask | 1.0.2 | [link](http://flask.pocoo.org/docs/1.0/installation/) |
| PostgreSQL | 9.5 | [link](https://www.postgresql.org/download/) |


## Useful links:

[Apache on Ubuntu](http://manpages.ubuntu.com/manpages/xenial/man8/a2ensite.8.html)

[Flask on Ubuntu](https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-application-on-an-ubuntu-vps)

[PostgreSQL on Ubuntu](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-16-04)

[Ubuntu firewall](https://help.ubuntu.com/community/UFW)

[WSGI on Apache](http://flask.pocoo.org/docs/1.0/deploying/mod_wsgi/)

