import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import execute_values
import os
from tqdm import tqdm

CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'accepted_2007_to_2018Q4.csv')
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'lending_club',
    'user': 'postgres',
    'password': 'postgres'
}

def clean_date(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == '' or value.lower() in ['nan', 'none', 'null']:
            return None
    try:
        result = pd.to_datetime(value, format='%b-%Y')
        if pd.isna(result):
            return None
        return result.strftime('%Y-%m-%d')
    except Exception:
        return None

def clean_term(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == '' or value.lower() in ['nan', 'none', 'null']:
            return None
    try:
        return int(str(value).replace(' months', '').strip())
    except Exception:
        return None

def clean_percentage(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == '' or value.lower() in ['nan', 'none', 'null']:
            return None
    try:
        return float(str(value).replace('%', '').strip())
    except Exception:
        return None

def clean_numeric(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == '' or value.lower() in ['nan', 'none', 'null']:
            return None
    try:
        return float(value)
    except Exception:
        return None

def clean_string(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    result = str(value).strip()
    if result == '' or result.lower() in ['nan', 'none', 'null', 'n/a']:
        return None
    return result

def clean_fico(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    try:
        val = int(float(value))
        if val < 300 or val > 850:
            return None
        return val
    except Exception:
        return None

def clean_emp_length(value):
    valid_values = [
        '< 1 year', '1 year', '2 years', '3 years', '4 years',
        '5 years', '6 years', '7 years', '8 years', '9 years', '10+ years'
    ]
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == '' or value.lower() in ['nan', 'none', 'null', 'n/a']:
            return None
    if value in valid_values:
        return value
    return None

def clean_dti(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    try:
        val = float(value)
        if val < 0:
            return None
        return val
    except Exception:
        return None

TABLE_MAPPING = {
    'loan_application': [
        ('application_id', 'id', clean_numeric),
        ('loan_amnt', 'loan_amnt', clean_numeric),
        ('term', 'term', clean_term),
        ('purpose', 'purpose', clean_string),
        ('title', 'title', clean_string),
        ('application_type', 'application_type', clean_string),
        ('issue_date', 'issue_d', clean_date),
        ('description', 'desc', clean_string),
        ('url', 'url', clean_string)
    ],
    'applicant_profile': [
        ('application_id', 'id', clean_numeric),
        ('emp_title', 'emp_title', clean_string),
        ('emp_length', 'emp_length', clean_emp_length),
        ('home_ownership', 'home_ownership', clean_string),
        ('annual_inc', 'annual_inc', clean_numeric),
        ('verification_status', 'verification_status', clean_string),
        ('addr_state', 'addr_state', clean_string),
        ('zip_code', 'zip_code', clean_string)
    ],
    'credit_profile': [
        ('application_id', 'id', clean_numeric),
        ('dti', 'dti', clean_dti),
        ('delinq_2yrs', 'delinq_2yrs', clean_numeric),
        ('earliest_cr_line', 'earliest_cr_line', clean_date),
        ('fico_range_low', 'fico_range_low', clean_fico),
        ('fico_range_high', 'fico_range_high', clean_fico),
        ('inq_last_6mths', 'inq_last_6mths', clean_numeric),
        ('open_acc', 'open_acc', clean_numeric),
        ('pub_rec', 'pub_rec', clean_numeric),
        ('revol_bal', 'revol_bal', clean_numeric),
        ('revol_util', 'revol_util', clean_numeric),
        ('total_acc', 'total_acc', clean_numeric)
    ],
    'loan': [
        ('loan_id', 'id', clean_numeric),
        ('application_id', 'id', clean_numeric),
        ('funded_amnt', 'funded_amnt', clean_numeric),
        ('funded_amnt_inv', 'funded_amnt_inv', clean_numeric),
        ('int_rate', 'int_rate', clean_percentage),
        ('installment', 'installment', clean_numeric),
        ('grade', 'grade', clean_string),
        ('sub_grade', 'sub_grade', clean_string),
        ('loan_status', 'loan_status', clean_string),
        ('pymnt_plan', 'pymnt_plan', clean_string),
        ('initial_list_status', 'initial_list_status', clean_string)
    ],
    'loan_performance': [
        ('loan_id', 'id', clean_numeric),
        ('total_pymnt', 'total_pymnt', clean_numeric),
        ('total_pymnt_inv', 'total_pymnt_inv', clean_numeric),
        ('total_rec_prncp', 'total_rec_prncp', clean_numeric),
        ('total_rec_int', 'total_rec_int', clean_numeric),
        ('total_rec_late_fee', 'total_rec_late_fee', clean_numeric),
        ('recoveries', 'recoveries', clean_numeric),
        ('collection_recovery_fee', 'collection_recovery_fee', clean_numeric),
        ('last_pymnt_d', 'last_pymnt_d', clean_date),
        ('last_pymnt_amnt', 'last_pymnt_amnt', clean_numeric),
        ('next_pymnt_d', 'next_pymnt_d', clean_date),
        ('out_prncp', 'out_prncp', clean_numeric),
        ('out_prncp_inv', 'out_prncp_inv', clean_numeric),
        ('last_credit_pull_d', 'last_credit_pull_d', clean_date),
        ('last_fico_range_low', 'last_fico_range_low', clean_fico),
        ('last_fico_range_high', 'last_fico_range_high', clean_fico)
    ]
}

LOAD_ORDER = ['loan_application', 'loan', 'applicant_profile', 'credit_profile', 'loan_performance']

def prepare_chunk_for_table(chunk, table_mapping):
    chunk = chunk.astype(object).where(pd.notnull(chunk), None)
    processed_cols = {}
    for db_col, csv_col, clean_func in table_mapping:
        if csv_col in chunk.columns:
            if clean_func:
                processed_cols[db_col] = chunk[csv_col].apply(clean_func)
            else:
                processed_cols[db_col] = chunk[csv_col]
        else:
            processed_cols[db_col] = [None] * len(chunk)
    df_processed = pd.DataFrame(processed_cols)
    first_col = table_mapping[0][0]
    df_processed = df_processed[df_processed[first_col].notna()]
    if len(df_processed) == 0:
        return []
    return [tuple(None if (isinstance(x, float) and np.isnan(x)) else x for x in row) 
            for row in df_processed.to_numpy()]

def load_table_chunk(conn, table_name, table_mapping, chunk):
    columns = [db_col for db_col, _, _ in table_mapping]
    columns_str = ', '.join(columns)
    data = prepare_chunk_for_table(chunk, table_mapping)
    if not data:
        return 0
    query = f"INSERT INTO credit.{table_name} ({columns_str}) VALUES %s"
    with conn.cursor() as cur:
        execute_values(cur, query, data, page_size=5000)
    return len(data)

def process_chunk(conn, chunk):
    total_loaded = 0
    for table_name in LOAD_ORDER:
        if table_name in TABLE_MAPPING:
            count = load_table_chunk(conn, table_name, TABLE_MAPPING[table_name], chunk)
            total_loaded += count
    return total_loaded

def main():
    print(f"Запуск. Источник: {CSV_PATH}")
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        chunk_size = 50000
        reader = pd.read_csv(CSV_PATH, chunksize=chunk_size, low_memory=False)
        total_rows = 0
        chunk_num = 0
        for chunk in tqdm(reader, desc="Загрузка чанков"):
            chunk_num += 1
            try:
                loaded = process_chunk(conn, chunk)
                conn.commit()
                total_rows += loaded
                if chunk_num % 5 == 0:
                    print(f"Чанк {chunk_num}: загружено {loaded}, всего: {total_rows}")
            except Exception as e:
                conn.rollback()
                print(f"Ошибка в чанке {chunk_num}: {e}")
                continue
        print(f"Загрузка завершена. Всего строк: {total_rows}")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
    finally:
        conn.close()


main()