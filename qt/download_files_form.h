#ifndef DOWNLOAD_FILES_FORM_H
#define DOWNLOAD_FILES_FORM_H

#include "qpushbutton.h"
#include <QWidget>
#include <QMessageBox>
#include <QJsonArray> // Для использования QJsonArray
#include <QPlainTextEdit>

namespace Ui {
class download_files_form;
}

class download_files_form : public QWidget
{
    Q_OBJECT

public:
    explicit download_files_form(QWidget *parent = nullptr);
    ~download_files_form();

    // Метод для установки матрицы
    void setInverseMatrix(const QJsonArray &matrix);

private slots:
    void on_download_button_clicked();

private:
    Ui::download_files_form *ui;
    void setup_ui();

    QPushButton *download_button;

    // Поле для хранения матрицы
    QJsonArray inverseMatrix;
};

#endif // DOWNLOAD_FILES_FORM_H
