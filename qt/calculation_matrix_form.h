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

namespace Ui {
class calculation_matrix_form;
}

class calculation_matrix_form : public QMainWindow
{
    Q_OBJECT

public:
    explicit calculation_matrix_form(QWidget *parent = nullptr);
    ~calculation_matrix_form();

private slots:
    void on_add_file_button_clicked();
    void on_decomposite_button_clicked();
    void longRunningOperation();

private:
    Ui::calculation_matrix_form *ui;
    void setup_ui();

    QPushButton *add_file_button;
    QPushButton *decomposite_button;

    QLineEdit *file_path_line_edit;

    QLabel *add_file_label;
    QLabel *your_matrix_label;

    QTableWidget *matrix_viewer;

    Loading *loadingDialog;
};

#endif // CALCULATION_MATRIX_FORM_H
