import joblib

def load_model(path='model/model_random_forest.pkl'):
    return joblib.load(path)

def predict_df(model, df):
    return model.predict(df)
