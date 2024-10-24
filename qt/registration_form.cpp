#include "registration_form.h"
#include "ui_registration_form.h"

registration_form::registration_form(QWidget *parent) :
    QDialog(parent),
    ui(new Ui::registration_form)
{
    ui->setupUi(this);
    setup_ui();
}

void registration_form::on_reg_clicked()
{
    // Получаем значения полей из UI
    QString user_login = login_input->text().trimmed();
    QString user_name = name_input->text().trimmed();
    QString user_email = email_input->text().trimmed();
    QString user_password = password_input->text().trimmed();

    // Проверка на пустые поля
    if (user_login.isEmpty() || user_name.isEmpty() || user_email.isEmpty() || user_password.isEmpty()) {
        QMessageBox::warning(this, "Input Error", "All fields must be filled.");
        return;
    }

    // Проверка на корректность почты с использованием регулярного выражения
    QRegularExpression email_regex(R"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)");
    QRegularExpressionMatch match = email_regex.match(user_email);
    if (!match.hasMatch()) {
        QMessageBox::warning(this, "Input Error", "Invalid email address.");
        return;
    }
}

void registration_form::setup_ui(){

    this->setWindowTitle("Регистрация");
    this->resize(200, 400);

    // Установка полей ввода
    name_input = new QLineEdit(this);
    email_input = new QLineEdit(this);
    login_input = new QLineEdit(this);
    password_input = new QLineEdit(this);
    register_button = new QPushButton("Регистрация", this);

    // Настраиваем виджеты
    name_input->setPlaceholderText("Имя");
    email_input->setPlaceholderText("Электронная почта");
    login_input->setPlaceholderText("Логин");
    password_input->setPlaceholderText("Пароль");
    password_input->setEchoMode(QLineEdit::Password);

    // Создание и настройка вертикального компоновщика
    QVBoxLayout *layout = new QVBoxLayout();
    QLabel *welcomeLabel = new QLabel("Регистрация нового пользователя");
    QLabel *instructionLabel = new QLabel("Заполните все поля!");

    layout->addWidget(welcomeLabel);
    layout->addWidget(instructionLabel);
    layout->addWidget(name_input);
    layout->addWidget(email_input);
    layout->addWidget(login_input);
    layout->addWidget(password_input);
    layout->addWidget(register_button);
    layout->setContentsMargins(50, 50, 50, 50); // Отступы от краев окна
    layout->setSpacing(20); // Расстояние между виджетами
    layout->setAlignment(Qt::AlignCenter); // Центрирование элементов

    this->setLayout(layout);

    connect(register_button, &QPushButton::clicked, this, &registration_form::on_reg_clicked);
}

registration_form::~registration_form()
{
    delete ui;
}
