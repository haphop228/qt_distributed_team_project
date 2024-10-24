#include "loading.h"

Loading::Loading(QWidget *parent)
    : QDialog(parent)
{
    setWindowTitle("Загрузка...");
    QVBoxLayout *layout = new QVBoxLayout(this);

    QLabel *label = new QLabel("Пожалуйста, подождите...", this);
    layout->addWidget(label);

    progressBar = new QProgressBar(this);
    progressBar->setRange(0, 0); // Неизвестный прогресс
    layout->addWidget(progressBar);

    setLayout(layout);
    setModal(true);
    resize(300, 100);
}

void Loading::setProgress(int value) {
    progressBar->setValue(value);
}
