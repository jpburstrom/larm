/****************************************************************************
** ui.h extension file, included from the uic-generated form implementation.
**
** If you want to add, delete, or rename functions or slots, use
** Qt Designer to update this file, preserving your code.
**
** You should not define a constructor or destructor in this file.
** Instead, write your code in functions called init() and destroy().
** These will automatically be called by the form's constructor and
** destructor.
*****************************************************************************/



void Form::updateLabels(d)
{
#set label[0] as main label
    self.label.setText(d[0])
#recurse through label[1] and set them
    for r in range(len(d[1])):
        for c in range(len(d[1][r])):
            self.canvaslabels.setText(r, c, QString(d[1][r][c]))
}
