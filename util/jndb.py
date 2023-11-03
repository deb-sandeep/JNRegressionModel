import os
import pandas as pd

def _load_csv( file_name ):
    return pd.read_csv( f'data/{file_name}.csv' )

def get_card_learning_summary():
    return _load_csv( 'card_learning_summary' )

def get_card_ratings_ex():
    return _load_csv( 'card_ratings_ex' )

def get_card_ratings():
    return _load_csv( 'card_ratings' )

def get_cards_meta():
    return _load_csv( 'cards_meta' )

def get_chapters():
    return _load_csv( 'chapters' )
