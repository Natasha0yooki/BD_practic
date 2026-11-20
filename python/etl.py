import pandas as pd
import os
from tqdm import tqdm

CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'accepted_2007_to_2018Q4.csv')

def get_data_chunks(file_path, chunk_size=100000):
    """
    Генератор, который читает огромный CSV по кускам, не забивая оперативную память.
    """
    print("Начинаем чтение файла чанками...")
    # Читаем только нужные колонки, когда аналитик их пришлет. Пока читаем все.
    reader = pd.read_csv(file_path, chunksize=chunk_size, low_memory=False)
    
    for chunk in tqdm(reader, desc="Обработка чанков"):
        # Здесь будет очистка данных (удаление мусора, приведение типов)
        yield chunk

# Тест генератора (запусти и посмотри, как идёт прогресс)
if __name__ == "__main__":
    count = 0
    for chunk_data in get_data_chunks(CSV_PATH, chunk_size=50000):
        count += len(chunk_data)
        # Раскомментируй, чтобы посмотреть на структуру первого чанка
        # if count == 50000: print(chunk_data.head())
    print(f" Всего обработано строк: {count}")