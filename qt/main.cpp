#include "login_form.h"
#include <QApplication>

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);
    login_form login;
    login.show();
    return a.exec();
}
