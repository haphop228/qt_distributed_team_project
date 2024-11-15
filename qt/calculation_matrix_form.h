#ifndef CALCULATION_MATRIX_FORM_H
#define CALCULATION_MATRIX_FORM_H

#include <QMainWindow>
#include <QDialog>
#include <QPushButton>
#include <QLineEdit>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QTableWidget>
#include <QTableWidgetItem>
#include <QVBoxLayout>
#include <QWidget>
#include <QMainWindow>
#include <QFileDialog>
#include "loading.h"
#include <QThread>
#include <QFileDialog>
#include <QHttpMultiPart>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QMessageBox>
#include <QtCore/qjsondocument.h>
#include <QJsonArray>

namespace Ui {
class calculation_matrix_form;
}

class calculation_matrix_form : public QMainWindow
{
    Q_OBJECT

public:
    explicit calculation_matrix_form(const QString &userlogin = nullptr, QWidget *parent = nullptr);
    ~calculation_matrix_form();

signals:
    void loadingFinished();

private slots:
    void on_add_file_button_clicked();
    void on_decomposite_button_clicked();
    void on_load_file_to_server_button();
    void longRunningOperation();

private:
    Ui::calculation_matrix_form *ui;
    void setup_ui();

    QString m_userlogin;

    QPushButton *add_file_button;
    QPushButton *decomposite_button;
    QPushButton *load_file_to_server_button;

    QLineEdit *file_path_line_edit;

    QLabel *add_file_label;
    QLabel *your_matrix_label;

    QTableWidget *matrix_viewer;

    Loading *loadingDialog;
};

#endif // CALCULATION_MATRIX_FORM_H
