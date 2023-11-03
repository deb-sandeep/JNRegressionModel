import util.jndb as db
import pandas as pd 

def get_enriched_card_ratings():
    # Load the raw card ratings from the database.
    ratings = db.get_card_ratings()
    
    # For a card consider only the first attempt within a session.
    ratings.drop_duplicates( subset=['session_id','card_id'], inplace=True )
    
    # Drop the session_id column. We won't need it any further
    ratings.drop( 'session_id', axis=1, inplace=True )    
    
    # Load the card master data
    cards = db.get_cards_meta()
    
    # Load the chapter master data
    chapters = db.get_chapters()
    
    # Associate the chapter information along with the card.
    cards = cards.merge( chapters, how='inner', on='chapter_id' )
    
    # Merge the ratings and cards to create a flat data frame
    ratings = ratings.merge( cards, how='inner', on='card_id' )

    # Remove all the exercise cards and drop the is_exercise_bank column
    ratings = ratings[ratings.is_exercise_bank!=1]
    ratings = ratings.drop( 'is_exercise_bank', axis=1 )
    
    # Drop the cards belonging to Class-[1-6]
    ratings = ratings[ ratings['syllabus_name'].isin( ['Class-8','Class-9'] ) ]
    
    # Drop the cards which are voice2text, etc. 
    # Keep on the below types.
    ratings = ratings[ ratings.card_type.isin( [ 
        'fib', 
        'matching', 
        'multi_choice', 
        'question_answer',
        'image_label',
        'true_false' 
    ] ) ]
    
    # Drop the cards in which time spent is zero and also drop the outliers
    ratings = ratings.loc[(ratings.time_spent > 0) & (ratings.time_spent < 300)]
    
    # Rearrange the columns
    ratings = ratings[[\
        'syllabus_name',\
        'subject_name',\
        'chapter_id',\
        'chapter_name',\
        'card_id',\
        'card_type',\
        'difficulty_level',\
        'timestamp',\
        'time_spent',\
        'rating'\
    ]]
    
    # Sort the frame and reset the index
    ratings = ratings.sort_values( ['syllabus_name','subject_name','chapter_id','card_id'] )
    ratings = ratings.reset_index( drop=True )

    # Update datatype of timestamp column
    ratings['timestamp'] = pd.to_datetime( ratings['timestamp'] )

    # Logic to compute derived fields.
    ratings = _compute_enriched_rating_derived_fields( ratings )

    # Convert many of the columns to categories
    for col in ['syllabus_name', 'subject_name', 'card_type', 'rating', 'rating_num', 'is_correct' ]:
        ratings[col] = ratings[col].astype('category')
    
    return ratings

def _abs_le( ratings, card_id, timestamp ):
    abs_le = 0
    prior_ratings = ratings[ (ratings.card_id == card_id) & (ratings.timestamp < timestamp) ].rating
    for rating in prior_ratings:
        abs_le += 100 if rating == 'E' else \
                   75 if rating == 'A' else \
                   25 if rating == 'P' else \
                    0

    return 0 if len(prior_ratings) == 0 else abs_le/len( prior_ratings )
    
def _compute_enriched_rating_derived_fields( ratings ):
    prior_le                     = 0
    last_card_id                 = 0
    attempt_number               = 0
    last_attempt_time            = None
    duration_since_first_attempt = 0
    
    num_attempts   = []
    gap_duration   = []
    total_duration = []
    prior_le       = []
    
    for idx, rating in ratings.iterrows():
        if( rating.card_id != last_card_id ):
            attempt_number = 0
            last_card_id = rating.card_id
            last_attempt_time = rating.timestamp
            duration_since_first_attempt = 0
    
        attempt_number += 1
        days_since_last_attempt = ( rating.timestamp - last_attempt_time ).days
        duration_since_first_attempt += days_since_last_attempt

        prior_le.append( _abs_le( ratings, rating.card_id, rating.timestamp ) )
        num_attempts.append( attempt_number )
        gap_duration.append( days_since_last_attempt ) 
        total_duration.append( duration_since_first_attempt )

    ratings[ 'prior_le'      ] = prior_le
    ratings[ 'rating_num'    ] = ratings.rating.map( { 'E':1, 'A':2, 'P':3, 'H': 4 } )
    ratings[ 'is_correct'    ] = ratings.rating.map( { 'E':1, 'A':1, 'P':0, 'H': 0 } )
    ratings[ 'attempt_num'   ] = num_attempts
    ratings[ 'gap_duration'  ] = gap_duration
    ratings[ 'total_duration'] = total_duration
    ratings[ 'subject_num'   ] = ratings.subject_name.map( {
        'Biology'         : 1,
        'Chemistry'       : 2,
        'Civics'          : 3,
        'English'         : 4,
        'English Grammar' : 5,
        'Geography'       : 6,
        'Hindi'           : 7,
        'History'         : 8,
        'Mathematics'     : 9,
        'Physics'         : 10,
        'Rapid Reader'    : 11,
        'Computers'       : 12
    } )

    return ratings