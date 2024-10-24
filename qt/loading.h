#ifndef LOADING_H
#define LOADING_H

#include <QDialog>
#include <QLabel>
#include <QVBoxLayout>
#include <QProgressBar>

class Loading : public QDialog {
    Q_OBJECT

public:
    explicit Loading(QWidget *parent = nullptr);

    void setProgress(int value);

private:
    QProgressBar *progressBar;
};

#endif // LOADING_H
