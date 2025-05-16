import os
from dotenv import load_dotenv

load_dotenv()  # carga variables de .env

DB_USER        = os.getenv('DB_USER')
DB_PASS        = os.getenv('DB_PASS')
DB_NAME        = os.getenv('DB_NAME')
DB_HOST        = os.getenv('DB_HOST', 'postgres')
DB_PORT        = os.getenv('DB_PORT', '5432')
DB_URL         = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

KAFKA_BOOTSTRAP = os.getenv('KAFKA_BOOTSTRAP', 'kafka:9092')
TOPIC           = os.getenv('TOPIC', 'happiness_features')

COMBINED_CSV    = os.getenv('COMBINED_CSV', 'data/combined_happiness.csv')
