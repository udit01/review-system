from . import models
from . import encryption
import json
#Helper functions to add/retrieve/edit ratings along with encryption/decryption




'''return a list of ratings given by user '''
def getRatingsGiven(userid,priv_key):
    user = models.Profile.objects.get(userid = userid)
    ratings_given=encryption.decrypt(user.ratings_given,priv_key)
    if '[' in ratings_given :
        print("RATINGS-",ratings_given)
        ratings_given=json.loads(ratings_given)
    else:
        ratings_given=[]
    return ratings_given

'''updates list of ratings given by user '''
def updateRatingsGiven(userid,ratingsGiven):
    user = models.Profile.objects.get(userid = userid)
    user.ratings_given=encryption.encrypt( json.dumps(ratingsGiven),user.public_key )
    user.save()
    return 


'''add rating to db (user1 rates user2)'''
def addRating(user1_id, user2_id, rating, review, priv_key): 

    #retreive users from db
    user1 = models.Profile.objects.get(userid = user1_id)
    user2 = models.Profile.objects.get(userid = user2_id)
    
    #encrypt data for both users
    review_enc_1=encryption.encrypt(review,user1.public_key)
    review_enc_2=encryption.encrypt(review,user2.public_key)

    #add rating to db

    rating=models.Rating(user2=user2,rating=rating,
         review=review_enc_1, review2=review_enc_2 )
    rating.save()

    #update ratingsGiven for user1
    ratingsGiven=getRatingsGiven(user1_id,priv_key)
    ratingsGiven.append(rating.id)
    updateRatingsGiven(user1_id,ratingsGiven)
    return  


'''delete rating with specified id'''
def deleteRating(rating_id,userid,priv_key):
    if rating_id in getRatingsGiven(userid,priv_key):
        rating=models.Rating.objects.get(id=rating_id)
        rating.delete()

        #update ratingsGiven for user
        ratingsGiven=getRatingsGiven(user1_id,priv_key)
        ratingsGiven.remove(rating_id)
        updateRatingsGiven(userid,ratingsGiven)
        return True
    
    else:
        #if rating does not belong to user
        return False
    return

'''update rating with specified id'''
def editRating(rating_id,userid, rating, review):
    if rating_id in getRatingsGiven(userid,priv_key):
        rating=models.Rating.objects.get(id=rating_id)
        #retreive users from db
        user1 = models.Profile.objects.get(userid = userid)
        user2 = rating.user2
        
        #encrypt data for both users
        rating.rating=rating
        rating.review = encryption.encrypt(review,user1.public_key)
        rating.review2 = encryption.encrypt(review,user2.public_key)

        rating.save()
        return True
    else:
        #if rating does not belong to user
        return False
    return

    





