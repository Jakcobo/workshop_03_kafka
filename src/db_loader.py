import sqlalchemy

def save_prediction(df, db_url):
    engine = sqlalchemy.create_engine(db_url)
    df.to_sql('predictions', engine, if_exists='append', index=False)
