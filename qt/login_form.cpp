#include "login_form.h"
#include "ui_login_form.h"
#include "mainwindow.h"
#include "calculation_matrix_form.h"
#include "registration_form.h"
#include <QMessageBox>
#include <QVBoxLayout>
#include <QLabel>
#include <iostream>

login_form::login_form(QWidget *parent)
    : QDialog(parent)
    , ui(new Ui::login_form)
{
    ui->setupUi(this);
    setup_ui();  // Вызов функции настройки UI
}

void login_form::on_login_clicked()
{
    QString userlogin = login_input->text().trimmed();
    QString password = password_input->text().trimmed();
    QByteArray passwordHash = QCryptographicHash::hash(password.toUtf8(), QCryptographicHash::Sha256);
    QString hashedPassword = passwordHash.toHex();

    QMessageBox::information(this, "Успех", "Вход выполнен успешно!");
    calculation_matrix_form *calculation_matrix_form = new class calculation_matrix_form();
    calculation_matrix_form->show();
    this->hide(); // Скрываем окно входа
}


void login_form::on_registration_clicked()
{
    std::cout << "reg clicked";
    registration_form *reg_form = new registration_form(this);
    reg_form->exec(); // Показываем окно регистрации модально
}

void login_form::setup_ui()
{
    this->resize(400, 200);
    this->setWindowTitle("Форма входа");


    welcomeLabel = new QLabel("Добро пожаловать!");
    instructionLabel = new QLabel("Введите логин и пароль");
    login_input = new QLineEdit(this);
    password_input = new QLineEdit(this);
    button_login = new QPushButton("Войти", this);
    registration_button = new QPushButton("Зарегистрироваться", this);

    // Настройка полей ввода
    login_input->setPlaceholderText("логин");
    password_input->setPlaceholderText("пароль");
    password_input->setEchoMode(QLineEdit::Password);

    // Создание и настройка вертикального компоновщика
    QVBoxLayout *layout = new QVBoxLayout();

    // Добавление виджетов в компоновщик
    layout->addWidget(welcomeLabel);
    layout->addWidget(instructionLabel);
    layout->addWidget(login_input);
    layout->addWidget(password_input);
    layout->addWidget(button_login);
    //registration_button
    layout->addWidget(registration_button);
    // Установка отступов и промежутков
    layout->setContentsMargins(50, 50, 50, 50); // Отступы от краев окна
    layout->setSpacing(20); // Расстояние между виджетами
    layout->setAlignment(Qt::AlignCenter); // Центрирование элементов

    // Установка компоновщика в качестве основного для формы
    this->setLayout(layout);

    // Подключение сигнала нажатия кнопки к слоту
    connect(button_login, &QPushButton::clicked, this, &login_form::on_login_clicked);
    connect(registration_button, &QPushButton::clicked, this, &login_form::on_registration_clicked);
}

login_form::~login_form()
{
    delete ui;
}
