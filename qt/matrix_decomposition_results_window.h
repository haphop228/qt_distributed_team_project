#ifndef MATRIX_DECOMPOSITION_RESULTS_WINDOW_H
#define MATRIX_DECOMPOSITION_RESULTS_WINDOW_H

#include <QDialog>  // Используем QDialog для окна
#include <QMessageBox>
#include <QJsonObject> // Для использования QJsonObject
#include <QJsonDocument>
#include <QJsonArray>
#include <QPlainTextEdit>
#include <QLayout>
#include <QLabel>

namespace Ui {
class matrix_decomposition_results_window;
}

class matrix_decomposition_results_window : public QDialog  // Изменено на QDialog
{
    Q_OBJECT

public:
    explicit matrix_decomposition_results_window(QWidget *parent = nullptr);
    ~matrix_decomposition_results_window();

    // Метод для установки матрицы
    void setResults(const QJsonObject &results);

private:
    Ui::matrix_decomposition_results_window *ui;

    QJsonObject results;
};

#endif // MATRIX_DECOMPOSITION_RESULTS_WINDOW_H
