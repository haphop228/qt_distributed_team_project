#ifndef REGISTRATION_FORM_H
#define REGISTRATION_FORM_H

#include <QDialog>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include <QNetworkReply>
#include <QJsonObject>
#include <QJsonDocument>
#include <QUrl>
#include <QCryptographicHash>
#include <QMessageBox>
#include <QLineEdit>
#include <QPushButton>

namespace Ui {
class registration_form;
}

class registration_form : public QDialog
{
    Q_OBJECT

public:
    explicit registration_form(QWidget *parent = nullptr);
    ~registration_form();

private:
    Ui::registration_form *ui;
    void setup_ui();

    QLineEdit *name_input;
    QLineEdit *email_input;
    QLineEdit *login_input;
    QLineEdit *password_input;
    QPushButton *register_button;


private slots:
    void on_reg_clicked();


};
#endif // REGISTRATION_FORM_H
