#ifndef LOGIN_FORM_H
#define LOGIN_FORM_H

#include <QDialog>
#include <QPushButton>
#include <QLineEdit>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>

namespace Ui {
class login_form;
}

class login_form : public QDialog
{
    Q_OBJECT

public:
    explicit login_form(QWidget *parent = nullptr);
    ~login_form();

private slots:
    void on_login_clicked();
    void on_registration_clicked();

private:
    Ui::login_form *ui;
    void setup_ui();

    QLabel *welcomeLabel;
    QLabel *instructionLabel;

    QLineEdit *login_input;
    QLineEdit *password_input;

    QPushButton *button_login;
    QPushButton *registration_button;
};

#endif // LOGIN_FORM_H
