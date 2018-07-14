from . import models
import json
#Helper functions to add/retrieve/edit ratings along with encryption/decryption


def encrypt(pub_key, plainText):
    pass

def decrypt(priv_key, cipherText):
    pass


'''return a list of ratings given by user '''
def getRatingsGiven(userid,priv_key):
    user = models.Profile.objects.get(userid = userid)
    ratings_given=json.loads(decrypt(priv_key,user.ratings_given))
    return ratings_given

'''updates list of ratings given by user '''
def updateRatingsGiven(userid,ratingsGiven):
    user = models.Profile.objects.get(userid = userid)
    user.ratings_given=encrypt( user.pub_key,json.dumps(ratingsGiven) )
    user.save()
    return 


'''add rating to db (user1 rates user2)'''
def addRating(user1_id, user2_id, rating, review, priv_key): 

    #retreive users from db
    user1 = models.Profile.objects.get(userid = user1_id)
    user2 = models.Profile.objects.get(userid = user2_id)
    
    #encrypt data for both users
    rating_enc_1=encrypt(user1.public_key,rating)
    rating_enc_2=encrypt(user2.public_key,rating)
    review_enc_1=encrypt(user1.public_key,review)
    review_enc_2=encrypt(user2.public_key,review)

    #add rating to db
    rating=models.Rating(user2=user2,rating=rating_enc_1,
        rating2=rating_enc_2, review=review_enc_1,
        review2=review_enc_2 )
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

'''update rating with specified id'''
def editRating(rating_id,userid, rating, review):
    if rating_id in getRatingsGiven(userid,priv_key):
        rating=models.Rating.objects.get(id=rating_id)
        #retreive users from db
        user1 = models.Profile.objects.get(userid = userid)
        user2 = rating.user2
        
        #encrypt data for both users and update record
        rating.rating=encrypt(user1.public_key,rating)
        rating.rating2=encrypt(user2.public_key,rating)
        rating.review=encrypt(user1.public_key,review)
        rating.review2=encrypt(user2.public_key,review)

        rating.save()
        return True
    else:
        #if rating does not belong to user
        return False


    





