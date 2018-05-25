# Review System
A tool for peer review in an organization.
Can give editable ratings, reviews to other people anonymously.

Can see analysis of previous reviews and ratings for each individual.

## Installation
First clone the repository using ```git clone``` . Then run by any of the methods.

1. Using Anaconda :

```
$ conda create -n rvs python=3
$ source activate rvs
$ pip install -r requirements.txt
```

2. Using Virtualenv :

Open the ReviewSystem-master folder then type:
```
$ virtualenv ReviewSystem
$ . ReviewSystem/bin/activate
$ pip install -r requirements.txt
$ touch review_project/ratings/migrations/__init__.py
```


# Features

Registration and Login for each user.
Users can view one another using the 'Leaderboard' tab
Leaderboard also works as a gateway to access all other profiles.
User can rate and review for all users except himself.
Rating is given from 1 to 10.
Opening one's own profile shows the username, name current rating and reviews.
One can view his/her own rating only after rating every other person.
One can publicise his/her contribution by adding "works" on own's profile.

# To-Do

1. Group data into lesser forms. Currently work form can only add the data and not delete it.

2. Adding histograms to see the cumulative ratings of users across sessions

3. Toggle between Log-out and Register buttons once the user has logged in. If the user hasn't logged in, don't display the Log-Out button.

4. Changing the current rating system to that of a system defined value of integers that the user can choose from.

5. Encrypting senstive data so that even the superuser can't view it.

6. Returning clearer and more objective oriented messages in case user enters a field wrongly.

7. Having a trustworthy review system if a user is unhappy with a particular rating.

8. Send a prompt if login fails.

9. Adding a considerable amount of "works" makes the individual fields non-readable. Need to have dynamic blocks which change dimensions according to the text.
