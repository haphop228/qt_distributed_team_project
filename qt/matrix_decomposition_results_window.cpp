#include "matrix_decomposition_results_window.h"
#include "ui_matrix_decomposition_results_window.h"

matrix_decomposition_results_window::matrix_decomposition_results_window(QWidget *parent)
    : QDialog(parent)
    , ui(new Ui::matrix_decomposition_results_window)
{
    ui->setupUi(this);
    setWindowTitle("Decomposition Results");
    setWindowFlags(windowFlags() & ~Qt::WindowContextHelpButtonHint);  // Убираем кнопку помощи
}

matrix_decomposition_results_window::~matrix_decomposition_results_window()
{
    delete ui;
}
void matrix_decomposition_results_window::setResults(const QJsonObject &results)
{
    // Очистка текущего layout
    QLayout *currentLayout = layout();
    if (currentLayout) {
        QLayoutItem *item;
        while ((item = currentLayout->takeAt(0)) != nullptr) {
            delete item->widget();
            delete item;
        }
    }

    QVBoxLayout *mainLayout = new QVBoxLayout();

    // Проверка, что results - валидный объект
    if (!results.isEmpty()) {
        qDebug() << "Worker keys:" << results.keys();

        // Перебор всех worker node
        for (const QString &workerKey : results.keys()) {
            if (!results[workerKey].isObject()) {
                qDebug() << "Skipping invalid worker node data for:" << workerKey;
                continue;
            }

            QJsonObject workerData = results[workerKey].toObject();

            // Создаем виджет для worker node
            QWidget *workerWidget = new QWidget(this);
            QVBoxLayout *workerLayout = new QVBoxLayout(workerWidget);

            // Название worker node
            QLabel *workerLabel = new QLabel(workerKey, workerWidget);
            workerLabel->setStyleSheet("font-weight: bold; font-size: 16px;");
            workerLayout->addWidget(workerLabel);

            // Читаем статус
            QString status = workerData.value("status").toString();
            if (status.isEmpty()) {
                qDebug() << "No status provided for:" << workerKey;
                continue;
            }

            // Алгоритм и время выполнения
            QString algorithm = workerData.value("algorithm").toString("N/A");
            double timeTaken = workerData.value("time_taken").toDouble(0.0);

            QLabel *algorithmLabel = new QLabel("Algorithm: " + algorithm, workerWidget);
            QLabel *timeLabel = new QLabel("Time taken: " + QString::number(timeTaken) + " seconds", workerWidget);
            workerLayout->addWidget(algorithmLabel);
            workerLayout->addWidget(timeLabel);

            if (status == "success") {
                // Обработка успешного результата
                if (workerData.contains("result") && workerData["result"].isArray()) {
                    QJsonArray resultArray = workerData["result"].toArray();
                    for (const QJsonValue &matrix : resultArray) {
                        if (matrix.isArray()) {
                            QString matrixString;
                            for (const QJsonValue &row : matrix.toArray()) {
                                QStringList rowStrings;
                                for (const QJsonValue &val : row.toArray()) {
                                    rowStrings << QString::number(val.toDouble(), 'f', 2);
                                }
                                matrixString += rowStrings.join(" ") + "\n";
                            }

                            QPlainTextEdit *matrixDisplay = new QPlainTextEdit(workerWidget);
                            matrixDisplay->setPlainText(matrixString);
                            matrixDisplay->setReadOnly(true);
                            matrixDisplay->setStyleSheet("font-size: 12px;");
                            workerLayout->addWidget(matrixDisplay);
                        }
                    }
                }
            } else if (status == "error") {
                // Обработка ошибки
                QString errorMessage = workerData.value("message").toString("Unknown error");
                QLabel *errorLabel = new QLabel("Error: " + errorMessage, workerWidget);
                errorLabel->setStyleSheet("color: red; font-size: 12px;");
                workerLayout->addWidget(errorLabel);
            }

            // Добавляем worker layout в основной layout
            mainLayout->addWidget(workerWidget);
        }
    } else {
        qDebug() << "Results object is empty or invalid!";
    }

    // Устанавливаем layout
    this->setLayout(mainLayout);
}
