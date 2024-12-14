#ifndef MATRIX_DECOMPOSITION_RESULTS_WINDOW_H
#define MATRIX_DECOMPOSITION_RESULTS_WINDOW_H

#include <QDialog>
#include <QVBoxLayout>
#include <QLabel>
#include <QTextEdit>
#include <QJsonObject>
#include <QJsonArray>
#include <QString>

class matrix_decomposition_results_window : public QDialog
{
    Q_OBJECT

public:
    explicit matrix_decomposition_results_window(QWidget *parent = nullptr);
    ~matrix_decomposition_results_window();

    void setResults(const QJsonObject &results, const QString &selectedKey);

private:
    QVBoxLayout *mainLayout;
    QLabel *algorithmLabel;
    QLabel *timeLabel;
    QTextEdit *matrixTextOutput;

    void addMatrixTextOutput(const QJsonArray &matrixData, const QString &title);
};

#endif // MATRIX_DECOMPOSITION_RESULTS_WINDOW_H
