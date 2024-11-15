#include "calculation_matrix_form.h"
#include "ui_calculation_matrix_form.h"
#include "download_files_form.h"
#include <QtCore/qjsonobject.h>


const QString MAIN_SERVER_URL("http://localhost:8002");

calculation_matrix_form::calculation_matrix_form(const QString &userlogin, QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::calculation_matrix_form)
    , m_userlogin(userlogin)
{
    ui->setupUi(this);
    setup_ui();
}

void calculation_matrix_form::on_add_file_button_clicked() {
    // TODO : пофиксить показ матриц у которых другие типы (не  matrix array integer general)
    QString fileName = QFileDialog::getOpenFileName(this, tr("Open Matrix File"), "", tr("Matrix Market (*.mtx);;All Files (*.*)"));
    if (fileName.isEmpty()) return;

    // Устанавливаем путь к файлу в QLineEdit
    file_path_line_edit->setText(fileName);

    // Отображаем название файла в QLabel
    your_matrix_label->setText("Loaded Matrix: " + QFileInfo(fileName).fileName());

    QFile file(fileName);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) {
        QMessageBox::warning(this, tr("Error"), tr("Could not open file"));
        return;
    }

    QTextStream in(&file);
    QString line;
    bool isPattern = false;
    bool isCoordinate = false;
    bool isArray = false;
    bool isInteger = false;
    bool isReal = false;

    // Читаем заголовок формата
    while (!in.atEnd()) {
        line = in.readLine();
        if (line.startsWith("%%MatrixMarket")) {
            isPattern = line.contains("pattern"); // TODO // Проверяем, является ли формат "pattern"
            isCoordinate = line.contains("coordinate"); // TODO  // Проверяем на координатный формат
            isArray = line.contains("array");  // Проверяем на массивный формат
            isInteger = line.contains("integer");  // Проверяем на целочисленный формат
            isReal = line.contains("real");
        }
        if (!line.startsWith("%")) break;  // Пропускаем комментарии
    }

    // Читаем размер матрицы и количество элементов
    QStringList sizeData = line.split(' ', Qt::SkipEmptyParts);
    if (sizeData.size() < 2) {
        QMessageBox::warning(this, tr("Error"), tr("Invalid Matrix Market format"));
        return;
    }

    int rows = sizeData[0].toInt();
    int columns = sizeData[1].toInt();

    // Устанавливаем размер таблицы в QTableWidget
    matrix_viewer->setRowCount(rows);
    matrix_viewer->setColumnCount(columns);

    // Устанавливаем фиксированный размер ячеек для равной ширины и высоты
    int cellSize = 50;
    for (int i = 0; i < rows; ++i) {
        matrix_viewer->setRowHeight(i, cellSize);
    }
    for (int j = 0; j < columns; ++j) {
        matrix_viewer->setColumnWidth(j, cellSize);
    }

    // Обработка элементов матрицы в зависимости от типа
    int count = 0;
    while (!in.atEnd()) {
        line = in.readLine();
        if (line.isEmpty()) continue;

        QStringList elements = line.split(' ', Qt::SkipEmptyParts);
        if (elements.size() < 1) continue;

        double value = 0.0;
        if (isArray) {
            if (isInteger) {
                // Для целочисленных значений
                if (elements.size() < 1) continue;
                value = elements[0].toInt();
            } else if (isReal){
                // Для вещественных значений
                if (elements.size() < 1) continue;
                value = elements[0].toDouble();
            }
        }

        int row = count / columns;
        int col = count % columns;

        // Заполняем таблицу значениями
        QTableWidgetItem *item = new QTableWidgetItem(QString::number(value));
        item->setTextAlignment(Qt::AlignCenter);
        matrix_viewer->setItem(row, col, item);

        count++;
    }

    file.close();
}


// Реализация функции загрузки файла на сервер
void calculation_matrix_form::on_load_file_to_server_button()
{
    QString filePath = file_path_line_edit->text();
    if (filePath.isEmpty()) {
        QMessageBox::warning(this, "Ошибка", "Выберите файл для загрузки.");
        return;
    }

    // Создаем объект QNetworkAccessManager для отправки запроса
    QNetworkAccessManager *networkManager = new QNetworkAccessManager(this);

    // URL для отправки запроса
    QUrl url(MAIN_SERVER_URL + "/save_matrix");
    QNetworkRequest request(url);

    // Создаем многочастный запрос (multipart) для передачи файла и логина
    QHttpMultiPart *multiPart = new QHttpMultiPart(QHttpMultiPart::FormDataType);

    // Параметр "login"
    QHttpPart loginPart;
    loginPart.setHeader(QNetworkRequest::ContentDispositionHeader, QVariant("form-data; name=\"login\""));
    loginPart.setBody(m_userlogin.toUtf8());  // Установка логина как QByteArray
    multiPart->append(loginPart);

    // Параметр "matrix_file" (сам файл)
    QFile *file = new QFile(filePath);
    if (!file->open(QIODevice::ReadOnly)) {
        QMessageBox::warning(this, "Ошибка", "Не удалось открыть файл.");
        delete multiPart;
        delete file;
        return;
    }

    QHttpPart filePart;
    filePart.setHeader(QNetworkRequest::ContentDispositionHeader, QVariant("form-data; name=\"matrix_file\"; filename=\"" + file->fileName() + "\""));
    filePart.setBodyDevice(file);  // Указываем файл как источник данных
    file->setParent(multiPart);    // Удаление файла вместе с multiPart

    multiPart->append(filePart);

    // Отправляем POST-запрос
    QNetworkReply *reply = networkManager->post(request, multiPart);
    multiPart->setParent(reply); // Удаление multiPart вместе с reply

    // Обрабатываем ответ сервера
    connect(reply, &QNetworkReply::finished, this, [reply, this]() {
        if (reply->error() == QNetworkReply::NoError) {
            QByteArray responseData = reply->readAll();
            // Парсим ответ (ожидается JSON)
            QJsonDocument jsonResponse = QJsonDocument::fromJson(responseData);
            QJsonObject jsonObject = jsonResponse.object();

            if (jsonObject.contains("message")) {
                QString message = jsonObject["message"].toString();
                QMessageBox::information(this, "Успех", message);
            } else {
                QMessageBox::information(this, "Успех", "Матрица успешно загружена.");
            }
        } else {
            QMessageBox::warning(this, "Ошибка", "Ошибка загрузки матрицы на сервер: " + reply->errorString());
        }
        reply->deleteLater();
    });
}

void calculation_matrix_form::on_decomposite_button_clicked()
{
    // Создаем и показываем окно загрузки
    loadingDialog = new Loading(this);
    loadingDialog->setAttribute(Qt::WA_DeleteOnClose); // Удаление виджета после закрытия
    loadingDialog->show();

    download_files_form *downloadFilesForm = new download_files_form();
    // Запускаем длительную операцию в отдельном потоке
    QThread *thread = QThread::create([=]() {
        longRunningOperation(); // Вызов длительной операции

        // Закрытие окна загрузки после завершения операции
        QMetaObject::invokeMethod(loadingDialog, "close");
        this->hide();
    });

    connect(thread, &QThread::finished, thread, &QThread::deleteLater); // Удаление потока после завершения
    thread->start();

    downloadFilesForm->show();
}

// Функция "затычка"
void calculation_matrix_form::longRunningOperation()
{
    // Эмулируем длительную операцию
    for (int i = 0; i <= 3; ++i) {
        QThread::sleep(1); // Заменить это на реальную операцию
    }
}


void calculation_matrix_form::setup_ui()
{
    add_file_label = new QLabel("Укажите файл, содержащий матрицу");
    your_matrix_label = new QLabel("Ваша матрица выглядит так:");

    // Создаем QLineEdit для ввода пути к файлу
    file_path_line_edit = new QLineEdit;
    file_path_line_edit->setPlaceholderText("Введите путь к файлу..."); // Устанавливаем текст-подсказку

    add_file_button = new QPushButton("Добавить файл", this);
    load_file_to_server_button = new QPushButton("Загрузить файл на сервер", this);
    decomposite_button = new QPushButton("Разложить матрицу", this);

    matrix_viewer = new QTableWidget;
    QStringList headers;
    headers << "Column 1" << "Column 2" << "Column 3" << "Column 4" << "Column 5";
    matrix_viewer->setHorizontalHeaderLabels(headers);
    matrix_viewer->setRowCount(5);
    matrix_viewer->setColumnCount(5);

    // Создаем вертикальный компоновщик для основного окна
    QVBoxLayout *mainLayout = new QVBoxLayout;

    // Добавляем элементы к вертикальному компоновщику
    mainLayout->addWidget(add_file_label);
    mainLayout->addWidget(file_path_line_edit);
    mainLayout->addWidget(add_file_button);
    mainLayout->addWidget(load_file_to_server_button);
    mainLayout->addWidget(your_matrix_label);
    mainLayout->addWidget(matrix_viewer);

    // Создаем горизонтальный компоновщик для кнопок
    QHBoxLayout *buttonLayout = new QHBoxLayout;
    buttonLayout->addWidget(decomposite_button);

    // Добавляем горизонтальный компоновщик к основному
    mainLayout->addLayout(buttonLayout);

    // Устанавливаем компоновку для главного окна
    QWidget *centralWidget = new QWidget(this); // Создаем центральный виджет
    centralWidget->setLayout(mainLayout); // Устанавливаем компоновку для центрального виджета
    setCentralWidget(centralWidget); // Устанавливаем центральный виджет для QMainWindow

    // Устанавливаем размер окна
    this->resize(600, 400);

    // Показываем окно
    this->show();

    // Подключаем сигналы к слоту
    connect(decomposite_button, &QPushButton::clicked, this, &calculation_matrix_form::on_decomposite_button_clicked);
    connect(add_file_button, &QPushButton::clicked, this, &calculation_matrix_form::on_add_file_button_clicked);
    connect(load_file_to_server_button, &QPushButton::clicked, this, &calculation_matrix_form::on_load_file_to_server_button);
}


calculation_matrix_form::~calculation_matrix_form()
{
    delete ui;
}
