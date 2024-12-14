#ifndef OPERATION_SELECTION_DIALOG_H
#define OPERATION_SELECTION_DIALOG_H

#include <QDialog>
#include <QComboBox>
#include <QVBoxLayout>
#include <QPushButton>
#include <QLabel>

class OperationSelectionDialog : public QDialog {
    Q_OBJECT
public:
    explicit OperationSelectionDialog(QWidget *parent = nullptr);
    QString selectedOperation() const;

signals:
    void operationSelected(const QString &operation);

private slots:
    void onSendClicked();

private:
    QComboBox *operationComboBox;
};

#endif // OPERATION_SELECTION_DIALOG_H
