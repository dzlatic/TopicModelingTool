# Project: Item Catalog @ Udacity Full Stack Nanodegree
# "Catalog App" web application

This project is a web application "Catalog App" in Flask that provides a
general purpose catalog of items. Users can review catalog items without
signing in. Users can also add new items, as well as edit and delete the
items they have created upon sign-in in using Google OAuth.

Catalog is organized per categories of items. Before accessing data about
items, users select the category. Categories are under control of web
administrator only, so users cannot create, delete or change categories
using "Catalog App" web application.

To load new categories, or to initialize database, authorized user can edit
and run teh file  /var/www/CatalogApp/CatalogApp/load_categories.py.

Besides real categories, web users also have on their disposal two helper
categories:

"Latest Items" showing the last 10 items created in the application by
all users, and

"My Items" showing the list of items currently logged in user owns.


## Deployment target on AWS:


Ubuntu-1GB-Frankfurt-1;
1 GB RAM, 1 vCPU, 40 GB SSD;
Ubuntu 16.04;
Frankfurt, Zone A (eu-central-1a)



## Summary of performed configuration tasks on top of VM provided by AWS:


- Users "grader" has been created to be used for deployment review;
- User "grader" is added to sudoers;
- "sudo" password for "grader" it is the same as user name;
- Configured Ubuntu firewall per spec below;
- Installed missing packages per table below;
- Updated & Upgraded system packages;
- Updated AWS configuration to reflect te same ports opening as on Ubuntu;
- Updated Google credentials with validated domain (used meta tag method).


## Deployment Details

| Parameter | Value |
| ------ | ------ |
| IP Address of the server | 35.157.7.133 |
| SSH port | 2200 |
| URL of the web application | http://35.157.7.133.xip.io/catalog |
| Application: | /var/www/CatalogApp |
| Apache/WSGI conf | /etc/apache2/sites-available/CatalogApp.conf |


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
- Added new file "catalog.wsgi" on the level above project files;
- Adjusted paths to .json files with secrets.


## Summary of Configuration tasks:

- Users "grader" has been created to be used for deployment review;
- User "grader" is added to sudoers;
- "sudo" password for "grader" it is the same as user name;
- Configured Ubuntu firewall;
- Installed missing packages;
- Updated & Upgraded system packages;
- Updated AWS configuration to reflect te same ports opening as on Ubuntu;
- Updated Google credentials with validated domain (used meta tag method).


## Files included in Git repository:

| File | Comment |
| ------ | ------ |
| database_setup.py | application that creates database |
| load_categories.py | application that loads categories into database |
| application.py | main application that runs Flask web server |
| README.md | this file |
| templates/main.html | main html template; all others extends this one  |
| templates/catalog.html | catalog template, main app navigation page  |
| templates/item.html | item template that shows catalog item  |
| templates/newItem.html | template that allows creating new item  |
| templates/editItem.html | template that allows edditing an item  |
| templates/deleteItem.html | template that allows delleting an item  |
| static/styles.css | CSS file, addition to Bootstrap invoked in main.html |
| static/favicon.ico | Web app icon, required by browsers |


## Files necessary bit not included in Git repository:
(transfer to server was done using scp, as best practice for sensitive data)

| File | Comment |
| ------ | ------ |
| client_secrets.json | Google OAuth web app client secrets  |
| db_secrets.json | PostgreSQL database credentials   |

## Dependencies

| Software | Version | Download |
| ------ | ------ | ------ |
| Python | Python 3.5.2 | [link](https://www.python.org/downloads/release/python-352/) |
| Flask | 1.0.2 | [link](http://flask.pocoo.org/docs/1.0/installation/) |
| PostgreSQL | 9.5 | [link](https://www.postgresql.org/download/) |


## Useful links:

[Apache on Ubuntu](http://manpages.ubuntu.com/manpages/xenial/man8/a2ensite.8.html)

[Flask on Ubuntu](https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-application-on-an-ubuntu-vps)

[PostgreSQL on Ubuntu](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-16-04)

[Ubuntu firewall](https://help.ubuntu.com/community/UFW)

[WSGI on Apache](http://flask.pocoo.org/docs/1.0/deploying/mod_wsgi/)

