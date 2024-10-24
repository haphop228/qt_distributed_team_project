#include "download_files_form.h"
#include "ui_download_files_form.h"
#include <QVBoxLayout>
#include <QLabel>
#include <QSpacerItem>

download_files_form::download_files_form(QWidget *parent)
    : QWidget(parent)
    , ui(new Ui::download_files_form)
{
    ui->setupUi(this);
    setup_ui();
}

void download_files_form::setup_ui()
{
    // Создаем вертикальный компоновщик
    QVBoxLayout *mainLayout = new QVBoxLayout(this);

    // Заголовок
    QLabel *titleLabel = new QLabel("Скачивание файлов", this);
    titleLabel->setStyleSheet("font-size: 18px");
    mainLayout->addWidget(titleLabel, 0, Qt::AlignCenter); // Центрируем заголовок

    // Кнопка скачивания
    download_button = new QPushButton("Скачать файлы с разложениями", this);
    download_button->setStyleSheet("padding: 10px; font-size: 16px;");
    mainLayout->addWidget(download_button, 0, Qt::AlignCenter); // Центрируем кнопку

    // Добавляем отступы снизу
    QSpacerItem *spacer = new QSpacerItem(20, 40, QSizePolicy::Minimum, QSizePolicy::Expanding);
    mainLayout->addItem(spacer);

    // Устанавливаем компоновку для виджета
    setLayout(mainLayout);

    // Подключаем сигнал к слоту
    connect(download_button, &QPushButton::clicked, this, &download_files_form::on_download_button_clicked);
}

void download_files_form::on_download_button_clicked()
{
    QMessageBox::information(this, "Информация", "Всё");
}

download_files_form::~download_files_form()
{
    delete ui;
}
