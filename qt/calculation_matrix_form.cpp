#include "calculation_matrix_form.h"
#include "ui_calculation_matrix_form.h"
#include "download_files_form.h"
#include "matrix_decomposition_results_window.h"
#include <QtCore/qjsonobject.h>
#include "operation_selection_dialog.h"


// Используйте эту строку, если поднимаете с помощью docker compose
// main server http://localhost:8002

// Если вы поднимаете кластер с помощью Minikube, то пропишите в терминале "minikube ip" и вставьте "http://<minikube ip>:30001"
const QString MAIN_SERVER_URL("http://localhost:8002");


calculation_matrix_form::calculation_matrix_form(const QString &userlogin, QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::calculation_matrix_form)
    , m_userlogin(userlogin)
{
    ui->setupUi(this);
    setup_ui();
}

void calculation_matrix_form::on_add_and_upload_file_button_clicked() {
    // Шаг 1: Открываем диалог выбора файла
    QString fileName = QFileDialog::getOpenFileName(this, tr("Open Matrix File"), "", tr("Matrix Market (*.mtx);;All Files (*.*)"));
    if (fileName.isEmpty()) return;

    // Устанавливаем путь к файлу в QLineEdit
    file_path_line_edit->setText(fileName);

    // Отображаем название файла в QLabel
    your_matrix_label->setText("Loaded Matrix: " + QFileInfo(fileName).fileName());

    // Загружаем файл на сервер
    QFile file(fileName);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) {
        QMessageBox::warning(this, tr("Error"), tr("Could not open file"));
        return;
    }

    // Шаг 2: Отправляем файл на сервер
    QString filePath = fileName; // Используем выбранный путь к файлу
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
    loginPart.setBody(m_userlogin.toUtf8());
    multiPart->append(loginPart);

    // Параметр "matrix_file" (сам файл)
    QFile *uploadFile = new QFile(filePath);
    if (!uploadFile->open(QIODevice::ReadOnly)) {
        QMessageBox::warning(this, "Ошибка", "Не удалось открыть файл.");
        delete multiPart;
        delete uploadFile;
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


    QHttpPart filePart;
    filePart.setHeader(QNetworkRequest::ContentDispositionHeader, QVariant("form-data; name=\"matrix_file\"; filename=\"" + uploadFile->fileName() + "\""));
    filePart.setBodyDevice(uploadFile);  // Указываем файл как источник данных
    uploadFile->setParent(multiPart);    // Удаление файла вместе с multiPart

    multiPart->append(filePart);

    // Отправляем POST-запрос
    QNetworkReply *reply = networkManager->post(request, multiPart);
    multiPart->setParent(reply); // Удаление multiPart вместе с reply

    // Обрабатываем ответ сервера
    connect(reply, &QNetworkReply::finished, this, [reply, this]() {
        if (reply->error() == QNetworkReply::NoError) {
            QByteArray responseData = reply->readAll();
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


void calculation_matrix_form::on_inverse_button_clicked()
{
    QString filePath = file_path_line_edit->text();
    if (filePath.isEmpty()) {
        QMessageBox::warning(this, "Ошибка", "Выберите файл для загрузки.");
        return;
    }

    // Извлекаем имя матрицы из пути к файлу (например, последние части пути)
    QFileInfo fileInfo(filePath);
    QString matrixName = fileInfo.fileName();
    qDebug() << "Matrix Name:" << matrixName;

    // Создаем объект QNetworkAccessManager для отправки запроса
    QNetworkAccessManager *networkManager = new QNetworkAccessManager(this);

    // URL для отправки запроса
    QUrl url(MAIN_SERVER_URL + "/calculate_invertible_matrix_by_matrix_name");
    QNetworkRequest request(url);

    // Создаем JSON с именем матрицы
    QJsonObject json;
    json["matrix_name"] = matrixName;

    // Преобразуем в QJsonDocument
    QJsonDocument doc(json);
    QByteArray data = doc.toJson();

    // Устанавливаем заголовки
    request.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");

    // Отправляем POST-запрос
    QNetworkReply *reply = networkManager->post(request, data);

    // Обработка ответа
    connect(reply, &QNetworkReply::finished, this, [reply, this]() {
        if (reply->error() == QNetworkReply::NoError) {
            // Если запрос успешен, получаем ответ
            QByteArray response = reply->readAll();
            QJsonDocument responseDoc = QJsonDocument::fromJson(response);

            if (responseDoc.isObject()) {
                QJsonObject responseObject = responseDoc.object();
                // Обработка данных из ответа
                QJsonArray originalMatrix = responseObject["original_matrix"].toArray();
                QJsonArray inverseMatrix = responseObject["inverse_matrix"].toArray();

                // Выводим матрицы для проверки
                qDebug() << "Original Matrix:" << originalMatrix;
                qDebug() << "Inverse Matrix:" << inverseMatrix;

                // Передаем матрицу в окно download_files_form
                download_files_form *downloadForm = new download_files_form();
                downloadForm->setInverseMatrix(inverseMatrix); // Передаем матрицу
                downloadForm->show();


                // Здесь можно обработать матрицы, например, отобразить их в UI или отправить дальше
            }
        } else {
            // Обработка ошибки
            QString errorMessage = reply->errorString();
            QMessageBox::warning(this, "Ошибка", "Ошибка запроса: " + errorMessage);
        }
        reply->deleteLater();
    });
}


void calculation_matrix_form::on_decompositions_button_clicked() {
    // Проверяем, выбран ли файл
    QString filePath = file_path_line_edit->text();
    if (filePath.isEmpty()) {
        QMessageBox::warning(this, "Ошибка", "Выберите файл для загрузки.");
        return;
    }

    // Извлекаем имя матрицы из пути к файлу
    QFileInfo fileInfo(filePath);
    QString matrixName = fileInfo.fileName();

    // Открываем диалог выбора операции
    OperationSelectionDialog *dialog = new OperationSelectionDialog(this);
    connect(dialog, &OperationSelectionDialog::operationSelected, this, [this, matrixName](const QString &operation) {
        QString endpoint;
        if (operation == "inverse") {
            endpoint = "/calculate_invertible_matrix_by_matrix_name";
        } else {
            endpoint = "/calculate_decomposition_of_matrix_by_matrix_name";
        }

        // Формируем URL для запроса
        QUrl url(MAIN_SERVER_URL + endpoint);
        QNetworkRequest request(url);

        // Создаем JSON с именем матрицы и операцией
        QJsonObject json;
        json["matrix_name"] = matrixName;
        if (operation != "inverse") {
            json["algorithm"] = operation; // Передаем выбранный алгоритм
        }

        QJsonDocument doc(json);
        QByteArray data = doc.toJson();

        // Устанавливаем заголовки
        request.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");

        // Отправляем POST-запрос
        QNetworkAccessManager *networkManager = new QNetworkAccessManager(this);
        QNetworkReply *reply = networkManager->post(request, data);

        // Обрабатываем ответ
        connect(reply, &QNetworkReply::finished, this, [this, reply, operation]() {
            if (reply->error() == QNetworkReply::NoError) {
                // Если запрос успешен, получаем ответ
                QByteArray response = reply->readAll();
                QJsonDocument responseDoc = QJsonDocument::fromJson(response);
                QJsonObject responseObject = responseDoc.object();

                // Выводим полный ответ сервера для проверки
                qDebug() << "Server response:" << responseDoc.toJson(QJsonDocument::Indented);

                if (responseObject.contains("result")) {
                    QJsonArray resultArray = responseObject["result"].toArray(); // Получаем массив результата
                    QString algorithm = responseObject["algorithm"].toString(); // Название алгоритма
                    double timeTaken = responseObject["time_taken"].toDouble(); // Время выполнения

                    // Формируем данные для передачи в окно
                    QJsonObject results;
                    results["algorithm"] = algorithm;
                    results["time_taken"] = timeTaken;
                    results["blocks"] = resultArray; // Добавляем блоки результата

                    // Открываем окно с результатами
                    matrix_decomposition_results_window *resultsWindow = new matrix_decomposition_results_window(this);
                    resultsWindow->setResults(results, operation); // Передаем результаты и выбранный ключ
                    resultsWindow->exec(); // Отображаем окно в модальном режиме
                } else {
                    QMessageBox::warning(this, "Ошибка", "No data found for the selected decomposition.");
                }
            } else {
                // Обработка ошибки
                QString errorMessage = reply->errorString();
                QMessageBox::critical(this, "Ошибка", "Ошибка выполнения операции: " + errorMessage);
            }
            reply->deleteLater();
        });
    });

    dialog->exec(); // Запускаем диалоговое окно выбора операции
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

    add_and_upload_file_button = new QPushButton("Добавить и загрузить файл", this);
    //inverse_button = new QPushButton("Вычислить обратную матрицу", this);
    decompositions_button = new QPushButton("Разложить матрицу LU/QR/LDL", this);
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
    mainLayout->addWidget(add_and_upload_file_button);
    mainLayout->addWidget(your_matrix_label);
    mainLayout->addWidget(matrix_viewer);

    // Создаем горизонтальный компоновщик для кнопок
    QHBoxLayout *buttonLayout = new QHBoxLayout;
    buttonLayout->addWidget(inverse_button);
    buttonLayout->addWidget(decompositions_button);

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
    connect(inverse_button, &QPushButton::clicked, this, &calculation_matrix_form::on_inverse_button_clicked);
    connect(decompositions_button, &QPushButton::clicked, this, &calculation_matrix_form::on_decompositions_button_clicked);
    connect(add_and_upload_file_button, &QPushButton::clicked, this, &calculation_matrix_form::on_add_and_upload_file_button_clicked);

}


calculation_matrix_form::~calculation_matrix_form()
{
    delete ui;
}
