# Review System
A tool for peer review in an organization.
Can give editable ratings, reviews to other people anonymously.

Can see analysis of previous reviews and ratings for each individual.

## Installation
First clone the repository using ```git clone``` . Then run by any of the methods.

1. Using Anaconda :

```
$ conda create -n ReviewSystem python=3
$ source activate ReviewSystem
$ pip install -r requirements.txt
```


2. Using Virtualenv :
Open the ReviewSystem-master folder then type:
```
$ virtualenv -p python=3 ReviewSystem
$ . ReviewSystem/bin/activate
$ pip install -r requirements.txt
```
After pip installs the requirements, a folder 'migrations' is created in the app 'ratings' and an empty file '__init__.py' is added. 

## Running the app for the first time

Open the review_project folder and execute the following commands 

```
$ touch ratings/migrations/__init__.py
$ python manage.py makemigrations
$ python manage.py migrate
$ python manage.py runserver
```

## Features

1. Registration and Login for each user.
2. Users can view one another using the 'Leaderboard' tab
3. Leaderboard also works as a gateway to access all other profiles.
4. User can rate and review for all users except himself.
5. Rating is given from 1 to 10.
6. Opening one's own profile shows the username, name current rating and reviews.
7. One can view his/her own rating only after rating every other person.
8. One can publicise his/her contribution by adding "works" on own's profile.


## To-Do

- [x] Group data into lesser forms. Currently work form can only add the data and not delete it.

- [ ] Adding histograms to see the cumulative ratings of users across sessions

- [x] Toggle between Log-out and Register buttons once the user has logged in. If the user hasn't logged in, don't display the Log-Out button.

- [x] Changing the current rating system to that of a system defined value of integers that the user can choose from.

- [x] Encrypting senstive data so that even the superuser can't view it.

- [ ] Having a trustworthy review system if a user is unhappy with a particular rating.

- [x] Send a prompt if login fails.

- [x] Adding a considerable amount of "works" makes the individual fields non-readable. Need to have dynamic blocks which change dimensions according to the text.
