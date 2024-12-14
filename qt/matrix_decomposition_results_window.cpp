#include "matrix_decomposition_results_window.h"
#include <QDebug>

matrix_decomposition_results_window::matrix_decomposition_results_window(QWidget *parent)
    : QDialog(parent),
    mainLayout(new QVBoxLayout(this)),
    algorithmLabel(new QLabel(this)),
    timeLabel(new QLabel(this)),
    matrixTextOutput(new QTextEdit(this))
{
    // Настройка окна
    setWindowTitle("Результаты разложения матрицы");
    resize(800, 600);

    // Настройка текстового вывода
    matrixTextOutput->setReadOnly(true);
    matrixTextOutput->setTextInteractionFlags(Qt::TextBrowserInteraction);

    // Добавление меток и области вывода
    mainLayout->addWidget(algorithmLabel);
    mainLayout->addWidget(timeLabel);
    mainLayout->addWidget(matrixTextOutput);

    setLayout(mainLayout);
}

matrix_decomposition_results_window::~matrix_decomposition_results_window() = default;

void matrix_decomposition_results_window::setResults(const QJsonObject &results, const QString &selectedKey)
{
    // Отладочный вывод для проверки данных
    qDebug() << "Полученный JSON: " << results;
    qDebug() << "Выбранный ключ: " << selectedKey;

    // Очистка текстового вывода
    matrixTextOutput->clear();

    // Установка алгоритма и времени выполнения
    QString algorithm = results["algorithm"].toString();
    double timeTaken = results["time_taken"].toDouble();

    algorithmLabel->setText("Алгоритм: " + algorithm);
    timeLabel->setText("Время выполнения: " + QString::number(timeTaken, 'f', 6) + " сек");

    // Проверяем наличие ключа "result"
    if (!results.contains("blocks")) {
        qDebug() << "Ключ 'blocks' отсутствует!";
        return;
    }

    QJsonArray resultArray = results["blocks"].toArray();
    if (resultArray.isEmpty()) {
        qDebug() << "Массив 'blocks' пуст!";
        return;
    }

    qDebug() << "Массив 'blocks': " << resultArray;

    // В зависимости от типа разложения выводим соответствующие матрицы
    if (selectedKey.toLower() == "lu") {
        addMatrixTextOutput(resultArray.at(0).toArray(), "Матрица L");
        addMatrixTextOutput(resultArray.at(1).toArray(), "Матрица U");
    } else if (selectedKey.toLower() == "qr") {
        addMatrixTextOutput(resultArray.at(0).toArray(), "Матрица Q");
        addMatrixTextOutput(resultArray.at(1).toArray(), "Матрица R");
    } else {
        qDebug() << "Неизвестный тип разложения: " << selectedKey;
    }
}

void matrix_decomposition_results_window::addMatrixTextOutput(const QJsonArray &matrixData, const QString &title)
{
    qDebug() << "matrix_data: " <<  matrixData << '\n';
    if (matrixData.isEmpty()) {
        qDebug() << "Матрица для отображения пуста!";
        return;
    }

    // Заголовок матрицы
    QString matrixText = title + ":\n";

    int rows = matrixData.size();
    int columns = matrixData[0].toArray().size();

    qDebug() << "Количество строк: " << rows << ", столбцов: " << columns;

    // Формирование текста для матрицы
    for (int i = 0; i < rows; ++i) {
        QJsonArray row = matrixData[i].toArray();
        QStringList rowText;
        for (int j = 0; j < columns; ++j) {
            rowText.append(QString::number(row[j].toDouble(), 'f', 6));
        }
        matrixText.append(rowText.join(" ") + "\n");
    }

    qDebug() << "Текст матрицы:\n" << matrixText;

    // Добавление текста матрицы в QTextEdit
    matrixTextOutput->append(matrixText);
}
