import numpy as np
from scipy.io import mmwrite, mmread

def generate_random_integer_matrix(rows, cols, density=0.1, min_val=1, max_val=100, seed=None):
    """
    Генерирует случайную целочисленную разреженную матрицу с заданными параметрами.
    
    Args:
        rows (int): Количество строк матрицы.
        cols (int): Количество столбцов матрицы.
        density (float): Плотность матрицы (доля ненулевых элементов).
        min_val (int): Минимальное значение для целочисленных элементов.
        max_val (int): Максимальное значение для целочисленных элементов.
        seed (int): Сид для генератора случайных чисел (опционально).
    
    Returns:
        np.ndarray: Сгенерированная разреженная матрица в формате CSR.
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Генерируем случайные целые числа в диапазоне от min_val до max_val
    matrix = np.random.randint(min_val, max_val + 1, size=(rows, cols))
    
    # Генерация маски для ненулевых элементов
    mask = np.random.rand(rows, cols) < density  # Маска для ненулевых значений
    matrix *= mask  # Применяем маску
    
    return matrix

def save_matrix_to_mtx(matrix, filename):
    """
    Сохраняет матрицу в файл в формате Matrix Market (.mtx).
    
    Args:
        matrix (np.ndarray): Матрица для сохранения.
        filename (str): Путь к файлу, в который будет сохранена матрица.
    """
    # Сохраняем в формате Matrix Market (.mtx)
    mmwrite(filename, matrix)

def load_matrix_from_mtx(filename):
    """
    Загружает матрицу из файла в формате Matrix Market (.mtx) и возвращает её как numpy массив.
    
    Args:
        filename (str): Путь к файлу, который содержит матрицу в формате .mtx.
    
    Returns:
        np.ndarray: Загруженная матрица.
    """
    # Загружаем матрицу из Matrix Market файла
    matrix = mmread(filename)
    return matrix

def main():
    # Параметры матрицы
    rows = 6  # Количество строк
    cols = 6 # Количество столбцов
    density = 0.99  # Плотность матрицы (10% ненулевых элементов)
    matrix_name = "docker_servers/main_server/tests/" + "generated_integer_matrix" + str(np.random.randint(1, 10000)) + ".mtx"  # Имя файла для сохранения
    min_val = 1  # Минимальное значение для чисел в матрице
    max_val = 25  # Максимальное значение для чисел в матрице


    # Генерация случайной целочисленной матрицы
    matrix = generate_random_integer_matrix(rows, cols, density=density, min_val=min_val, max_val=max_val)
    print(matrix)
    print(f'Matrix DET = {np.linalg.det(matrix)}')
    # Сохранение матрицы в файл
    save_matrix_to_mtx(matrix, matrix_name)
    
    print(f"Матрица успешно сохранена в файл: {matrix_name}")

    # Загрузка матрицы из файла
    loaded_matrix = load_matrix_from_mtx(matrix_name)
    
    print("\nЗагруженная матрица:")
    print(loaded_matrix)

    

if __name__ == "__main__":
    main()
