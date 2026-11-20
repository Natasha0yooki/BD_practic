import pandas as pd
import os

CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'accepted_2007_to_2018Q4.csv')

print(" Начинаем анализ датасета...")
# low_memory=False отключает предупреждения pandas о смешанных типах данных
df_sample = pd.read_csv(CSV_PATH, nrows=100000, low_memory=False)

print(f" Прочитано строк: {len(df_sample)}, колонок: {len(df_sample.columns)}")

# Ищем колонки, где больше 50% пропусков
missing_ratio = df_sample.isnull().mean()
bad_columns = missing_ratio[missing_ratio > 0.5].sort_values(ascending=False)

print(f" Найдено колонок с пропусками > 50%: {len(bad_columns)}")
print(bad_columns.head(10))

# Сохраняем полный список колонок в CSV, чтобы отправить аналитику
out_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'available_columns.csv')
pd.DataFrame(df_sample.columns, columns=['column_name']).to_csv(out_path, index=False)
print(f" Полный список из {len(df_sample.columns)} колонок сохранен в docs/available_columns.csv")