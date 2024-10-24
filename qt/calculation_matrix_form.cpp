#include "calculation_matrix_form.h"
#include "ui_calculation_matrix_form.h"
#include "download_files_form.h"

calculation_matrix_form::calculation_matrix_form(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::calculation_matrix_form)
{
    ui->setupUi(this);
    setup_ui();
}


void calculation_matrix_form::on_add_file_button_clicked()
{
    QString fileName = QFileDialog::getOpenFileName(this, tr("Open File"), "",
                                                    tr("All Files (*.*);;Text Files (*.txt);;Images (*.png *.xpm *.jpg)"));

    if (!fileName.isEmpty()) {
        // Записываем путь к файлу в текстовое поле
        file_path_line_edit->setText(fileName);
    }
}

void calculation_matrix_form::on_decomposite_button_clicked()
{
    // Создаем и показываем окно загрузки
    loadingDialog = new Loading(this);
    loadingDialog->setAttribute(Qt::WA_DeleteOnClose); // Удаление виджета после закрытия
    loadingDialog->show();

    download_files_form *download_files_form = new class download_files_form();
    // Запускаем длительную операцию в отдельном потоке
    QThread *thread = QThread::create([=]() {
        longRunningOperation(); // Вызов длительной операции

        // Закрытие окна загрузки после завершения операции
        QMetaObject::invokeMethod(loadingDialog, "close");
        this->hide();



    });

    thread->start();

    download_files_form->show();

}

// Функция "затычка"
void calculation_matrix_form::longRunningOperation() {
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
    decomposite_button = new QPushButton("Разложить матрицу", this);

    QTableWidget *matrix_viewer = new QTableWidget;
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

}


calculation_matrix_form::~calculation_matrix_form()
{
    delete ui;
}
