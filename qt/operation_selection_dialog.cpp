#include "operation_selection_dialog.h"

OperationSelectionDialog::OperationSelectionDialog(QWidget *parent)
    : QDialog(parent)
{
    setWindowTitle("Выбор операции");

    QVBoxLayout *layout = new QVBoxLayout(this);

    QLabel *label = new QLabel("Выберите операцию:", this);
    layout->addWidget(label);

    operationComboBox = new QComboBox(this);
    operationComboBox->addItem("Обратная матрица", "inverse");
    operationComboBox->addItem("LU разложение", "lu");
    operationComboBox->addItem("QR разложение", "qr");
    operationComboBox->addItem("LDL разложение", "ldl");
    layout->addWidget(operationComboBox);

    QPushButton *sendButton = new QPushButton("Отправить", this);
    layout->addWidget(sendButton);

    connect(sendButton, &QPushButton::clicked, this, &OperationSelectionDialog::onSendClicked);
}

QString OperationSelectionDialog::selectedOperation() const {
    return operationComboBox->currentData().toString();
}

void OperationSelectionDialog::onSendClicked() {
    emit operationSelected(selectedOperation());
    accept();
}
