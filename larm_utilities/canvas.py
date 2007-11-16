# Copyright 2007 Johannes Burström, <johannes@ljud.org>
__version__ = "$Revision$"
# -*- coding: utf-8 -*-

import sys
from qt import *
from qtcanvas import *
import random


True = 1
False = 0
butterfly_fn = QString.null
butterflyimg = []
logo_fn = QString.null
logoimg = []
bouncy_logo = None
views = []


class ImageItem(QCanvasRectangle):
    def __init__(self,img,canvas):
        QCanvasRectangle.__init__(self,canvas)
        self.imageRTTI=984376
        self.image=img
        self.pixmap=QPixmap()
        self.setSize(self.image.width(), self.image.height())
        self.pixmap.convertFromImage(self.image, Qt.OrderedAlphaDither);

    def rtti(self):
        return self.imageRTTI

    def hit(self,p):
        ix = p.x()-self.x()
        iy = p.y()-self.y()
        if not self.image.valid( ix , iy ):
            return False
        self.pixel = self.image.pixel( ix, iy )
        return  (qAlpha( self.pixel ) != 0)

    def drawShape(self,p):
        p.drawPixmap( self.x(), self.y(), self.pixmap )


class NodeItem(QCanvasEllipse):
    def __init__(self,canvas):
        QCanvasEllipse.__init__(self,6,6,canvas)
        self.__inList=[]
        self.__outList=[]
        self.setPen(QPen(Qt.black))
        self.setBrush(QBrush(Qt.red))
        self.setZ(128)

    def addInEdge(self,edge):
        self.__inList.append(edge)

    def addOutEdge(self,edge):
        self.__outList.append(edge)

    def moveBy(self,dx,dy):
        QCanvasEllipse.moveBy(self,dx,dy)
        for each_edge in self.__inList:
            each_edge.setToPoint( int(self.x()), int(self.y()) )
        for each_edge in self.__outList:
            each_edge.setFromPoint( int(self.x()), int(self.y()) )

class EdgeItem(QCanvasLine):
    __c=0
    def __init__(self,fromNode, toNode,canvas):
        QCanvasLine.__init__(self,canvas)
        self.__c=self.__c+1
        self.setPen(QPen(Qt.black))
        self.setBrush(QBrush(Qt.red))
        fromNode.addOutEdge(self)
        toNode.addInEdge(self)
        self.setPoints(int(fromNode.x()),int(fromNode.y()), int(toNode.x()), int(toNode.y()))
        self.setZ(127)

    def setFromPoint(self,x,y):
        self.setPoints(x,y,self.endPoint().x(),self.endPoint().y())

    def setToPoint(self,x,y):
        self.setPoints(self.startPoint().x(), self.startPoint().y(),x,y)

    def count(self):
        return self.__c

    def moveBy(self,dx,dy):
        pass


class FigureEditor(QCanvasView):
    def __init__(self,c,parent,name,f):
        QCanvasView.__init__(self,c,parent,name,f)
        self.__moving=0
        self.__moving_start= 0

    def contentsMousePressEvent(self,e): # QMouseEvent e
        point = self.inverseWorldMatrix().map(e.pos())
        ilist = self.canvas().collisions(point) #QCanvasItemList ilist
        for each_item in ilist:
            if each_item.rtti()==984376:
                if not each_item.hit(point):
                    continue
            self.__moving=each_item
            self.__moving_start=point
            return
        self.__moving=0

    def clear(self):
        ilist = self.canvas().allItems()
        for each_item in ilist:
            if each_item:
                each_item.setCanvas(None)
                del each_item
        self.canvas().update()

    def contentsMouseMoveEvent(self,e):
        if  self.__moving :
            point = self.inverseWorldMatrix().map(e.pos());
            self.__moving.moveBy(point.x() - self.__moving_start.x(),point.y() - self.__moving_start.y())
            self.__moving_start = point
        self.canvas().update()


class BouncyLogo(QCanvasSprite):
    def __init__(self,canvas):
        # Make sure the logo exists.
        global bouncy_logo
        if bouncy_logo is None:
            bouncy_logo=QCanvasPixmapArray("qt-trans.xpm")

        QCanvasSprite.__init__(self,None,canvas)
        self.setSequence(bouncy_logo)
        self.setAnimated(True)
        self.initPos()
        self.logo_rtti=1234

    def rtti(self):
        return self.logo_rtti

    def initPos(self):
        self.initSpeed()
        trial=1000
        self.move(random.random()%self.canvas().width(), random.random()%self.canvas().height())
        self.advance(0)
        trial=trial-1
        while (trial & (self.xVelocity()==0 )& (self.yVelocity()==0)):
            elf.move(random.random()%self.canvas().width(), random.random()%self.canvas().height())
            self.advance(0)
            trial=trial-1

    def initSpeed(self):
        speed=4.0
        d=random.random()%1024/1024.0
        self.setVelocity(d*speed*2-speed, (1-d)*speed*2-speed)

    def advance(self,stage):
        if stage==0:
            vx=self.xVelocity()
            vy=self.yVelocity()
            if (vx==0.0) & (vy==0.0):
                self.initSpeed()
                vx=self.xVelocity()
                vy=self.yVelocity()

            nx=self.x()+vx
            ny=self.y()+vy

            if (nx<0) | (nx >= self.canvas().width()):
                vx=-vx
            if (ny<0) | (ny >= self.canvas().height()):
                vy=-vy

            for bounce in [0,1,2,3]:
                l=self.collisions(False)
                for hit in l:
                    if (hit.rtti()==1234) & (hit.collidesWith(self)):
                        if bounce==0:
                            vx=-vx
                        elif bounce==1:
                            vy=-vy
                            vx=-vx
                        elif bounce==2:
                            vx=-vx
                        elif bounce==3:
                            vx=0
                            vy=0
                        self.setVelocity(vx,vy)
                        break

            if (self.x()+vx < 0) | (self.x()+vx >= self.canvas().width()):
                vx=0
            if (self.y()+vy < 0) | (self.y()+vy >= self.canvas().height()):
                vy=0

            self.setVelocity(vx,vy)
        elif stage==1:
            QCanvasItem.advance(self,stage)


class Main (QMainWindow):
    def __init__(self,c,parent,name,f=0):
        QMainWindow.__init__(self,parent,name,f)
        self.editor=FigureEditor(c,self,name,f)
        self.printer=QPrinter()
        self.dbf_id=0
        self.canvas=c
        self.mainCount=0
        file=QPopupMenu(self.menuBar())
        file.insertItem("&Fill canvas", self.init, Qt.CTRL+Qt.Key_F)
        file.insertItem("&Erase canvas", self.clear, Qt.CTRL+Qt.Key_E)
        file.insertItem("&New view", self.newView, Qt.CTRL+Qt.Key_N)
        file.insertSeparator();
        file.insertItem("&Print", self._print, Qt.CTRL+Qt.Key_P)
        file.insertSeparator()
        file.insertItem("E&xit", qApp, SLOT("quit()"), Qt.CTRL+Qt.Key_Q)
        self.menuBar().insertItem("&File", file)

        edit = QPopupMenu(self.menuBar() )
        edit.insertItem("Add &Circle",  self.addCircle, Qt.ALT+Qt.Key_C)
        edit.insertItem("Add &Hexagon",  self.addHexagon, Qt.ALT+Qt.Key_H)
        edit.insertItem("Add &Polygon",  self.addPolygon, Qt.ALT+Qt.Key_P)
        edit.insertItem("Add Spl&ine", self.addSpline, Qt.ALT+Qt.Key_I)
        edit.insertItem("Add &Text", self.addText, Qt.ALT+Qt.Key_T)
        edit.insertItem("Add &Line", self.addLine, Qt.ALT+Qt.Key_L)
        edit.insertItem("Add &Rectangle", self.addRectangle, Qt.ALT+Qt.Key_R)
        edit.insertItem("Add &Sprite", self.addSprite, Qt.ALT+Qt.Key_S)
        edit.insertItem("Create &Mesh", self.addMesh, Qt.ALT+Qt.Key_M )
        edit.insertItem("Add &Alpha-blended image", self.addButterfly, Qt.ALT+Qt.Key_A)
        self.menuBar().insertItem("&Edit", edit)

        view = QPopupMenu(self.menuBar() );
        view.insertItem("&Enlarge", self.enlarge, Qt.SHIFT+Qt.CTRL+Qt.Key_Plus);
        view.insertItem("Shr&ink", self.shrink, Qt.SHIFT+Qt.CTRL+Qt.Key_Minus);
        view.insertSeparator();
        view.insertItem("&Rotate clockwise", self.rotateClockwise, Qt.CTRL+Qt.Key_PageDown);
        view.insertItem("Rotate &counterclockwise", self.rotateCounterClockwise, Qt.CTRL+Qt.Key_PageUp);
        view.insertItem("&Zoom in", self.zoomIn, Qt.CTRL+Qt.Key_Plus);
        view.insertItem("Zoom &out", self.zoomOut, Qt.CTRL+Qt.Key_Minus);
        view.insertItem("Translate left", self.moveL, Qt.CTRL+Qt.Key_Left);
        view.insertItem("Translate right", self.moveR, Qt.CTRL+Qt.Key_Right);
        view.insertItem("Translate up", self.moveU, Qt.CTRL+Qt.Key_Up);
        view.insertItem("Translate down", self.moveD, Qt.CTRL+Qt.Key_Down);
        view.insertItem("&Mirror", self.mirror, Qt.CTRL+Qt.Key_Home);
        self.menuBar().insertItem("&View", view)

        self.options = QPopupMenu( self.menuBar() );
        self.dbf_id = self.options.insertItem("Double buffer", self.toggleDoubleBuffer)
        self.options.setItemChecked(self.dbf_id, True)
        self.menuBar().insertItem("&Options",self.options)

        self.menuBar().insertSeparator();

        help = QPopupMenu( self.menuBar() )
        help.insertItem("&About", self.help, Qt.Key_F1)
        help.insertItem("&About Qt", self.aboutQt, Qt.Key_F2)
        help.setItemChecked(self.dbf_id, True)
        self.menuBar().insertItem("&Help",help)

        self.statusBar()

        self.setCentralWidget(self.editor)

        self.printer = 0
        self.tb=0
        self.tp=0

        self.init()

    def init(self):
        self.clear()
        r=24
        r=r+1
        random.seed(r)
        for i in range(self.canvas.width()/56):
            self.addButterfly()
        for j in range(self.canvas.width()/85):
            self.addHexagon()
        for k in range(self.canvas.width()/128):
            self.addLogo()

    def newView(self):
        m=Main(self.canvas,None,"new windiw",Qt.WDestructiveClose)
        qApp.setMainWidget(m)
        m.show()
        qApp.setMainWidget(None)
        views.append(m)

    def clear(self):
        self.editor.clear()

    def help(self):
        QMessageBox.information(None, "PyQt Canvas Example",
            "<h3>The PyQt QCanvas classes example</h3><hr>"
            "<p>This is the PyQt implementation of "
            "Qt canvas example.</p> by Sadi Kose "
            "<i>(kose@nuvox.net)</i><hr>"
            "<ul>"
            "<li> Press ALT-S for some sprites."
            "<li> Press ALT-C for some circles."
            "<li> Press ALT-L for some lines."
            "<li> Drag the objects around."
            "<li> Read the code!"
            "</ul>","Dismiss")

    def aboutQt(self):
        QMessageBox.aboutQt(self,"PyQt Canvas Example")

    def toggleDoubleBuffer(self):
        s = not self.options.isItemChecked(self.dbf_id)
        self.options.setItemChecked(self.dbf_id,s)
        self.canvas.setDoubleBuffering(s)

    def enlarge(self):
        self.canvas.resize(self.canvas.width()*4/3, self.canvas.height()*4/3)

    def shrink(self):
        self.canvas.resize(self.canvas.width()*3/4, self.canvas.height()*3/4)

    def rotateClockwise(self):
        m = self.editor.worldMatrix()
        m.rotate( 22.5 )
        self.editor.setWorldMatrix( m )

    def rotateCounterClockwise(self):
        m = self.editor.worldMatrix()
        m.rotate( -22.5 )
        self.editor.setWorldMatrix( m )

    def zoomIn(self):
        m = self.editor.worldMatrix()
        m.scale( 2.0, 2.0 )
        self.editor.setWorldMatrix( m )

    def zoomOut(self):
        m = self.editor.worldMatrix()
        m.scale( 0.5, 0.5 )
        self.editor.setWorldMatrix( m )

    def mirror(self):
        m = self.editor.worldMatrix()
        m.scale( -1, 1 )
        self.editor.setWorldMatrix( m )

    def moveL(self):
        m = self.editor.worldMatrix()
        m.translate( -16, 0 )
        self.editor.setWorldMatrix( m )

    def moveR(self):
        m = self.editor.worldMatrix()
        m.translate( +16, 0 )
        self.editor.setWorldMatrix( m )

    def moveU(self):
        m = self.editor.worldMatrix()
        m.translate( 0, -16 )
        self.editor.setWorldMatrix( m )

    def moveD(self):
        m = self.editor.worldMatrix();
        m.translate( 0, +16 );
        self.editor.setWorldMatrix( m )

    def _print(self):
        if not self.printer:
            self.printer = QPrinter()
        if  self.printer.setup(self) :
            pp=QPainter(self.printer)
        self.canvas.drawArea(QRect(0,0,self.canvas.width(),self.canvas.height()),pp,False)

    def addSprite(self):
        i = BouncyLogo(self.canvas)
        i.setZ(256*random.random()%256);
        i.show();

    def addButterfly(self):
        if butterfly_fn.isEmpty():
            return
        if not butterflyimg:
            butterflyimg.append(QImage())
            butterflyimg[0].load(butterfly_fn)
            butterflyimg.append(QImage())
            butterflyimg[1] = butterflyimg[0].smoothScale( int(butterflyimg[0].width()*0.75),
                int(butterflyimg[0].height()*0.75) )
            butterflyimg.append(QImage())
            butterflyimg[2] = butterflyimg[0].smoothScale( int(butterflyimg[0].width()*0.5),
                int(butterflyimg[0].height()*0.5) )
            butterflyimg.append(QImage())
            butterflyimg[3] = butterflyimg[0].smoothScale( int(butterflyimg[0].width()*0.25),
                int(butterflyimg[0].height()*0.25) )

        i = ImageItem(butterflyimg[int(4*random.random()%4)],self.canvas)
        i.move((self.canvas.width()-butterflyimg[0].width())*random.random()%(self.canvas.width()-butterflyimg[0].width()),
            (self.canvas.height()-butterflyimg[0].height())*random.random()%(self.canvas.height()-butterflyimg[0].height()))
        i.setZ(256*random.random()%256+250);
        i.show()

    def addLogo(self):
        if logo_fn.isEmpty():
            return;
        if not logoimg:
            logoimg.append(QImage())
            logoimg[0].load( logo_fn )
            logoimg.append(QImage())
            logoimg[1] = logoimg[0].smoothScale( int(logoimg[0].width()*0.75),
                int(logoimg[0].height()*0.75) )
            logoimg.append(QImage())
            logoimg[2] = logoimg[0].smoothScale( int(logoimg[0].width()*0.5),
                int(logoimg[0].height()*0.5) )
            logoimg.append(QImage())
            logoimg[3] = logoimg[0].smoothScale( int(logoimg[0].width()*0.25),
                int(logoimg[0].height()*0.25) );

        i = ImageItem(logoimg[int(4*random.random()%4)],self.canvas)
        i.move((self.canvas.width()-logoimg[0].width())*random.random()%(self.canvas.width()-logoimg[0].width()),
            (self.canvas.height()-logoimg[0].width())*random.random()%(self.canvas.height()-logoimg[0].width()))
        i.setZ(256*random.random()%256+256)
        i.show()

    def addCircle(self):
        i = QCanvasEllipse(50,50,self.canvas)
        i.setBrush( QBrush(QColor(256*random.random()%32*8,256*random.random()%32*8,256*random.random()%32*8) ))
        i.move(self.canvas.width()*random.random()%self.canvas.width(),self.canvas.width()*random.random()%self.canvas.height())
        i.setZ(256*random.random()%256)
        i.show()

    def addHexagon(self):
        i = QCanvasPolygon(self.canvas)
        size = canvas.width() / 25
        pa=QPointArray(6)
        pa.setPoint(0,QPoint(2*size,0))
        pa.setPoint(1,QPoint(size,-size*173/100))
        pa.setPoint(2,QPoint(-size,-size*173/100))
        pa.setPoint(3,QPoint(-2*size,0))
        pa.setPoint(4,QPoint(-size,size*173/100))
        pa.setPoint(5,QPoint(size,size*173/100))
        i.setPoints(pa)
        i.setBrush( QBrush(QColor(256*random.random()%32*8,256*random.random()%32*8,256*random.random()%32*8) ))
        i.move(self.canvas.width()*random.random()%self.canvas.width(),self.canvas.width()*random.random()%self.canvas.height())
        i.setZ(256*random.random()%256)
        i.show()

    def addPolygon(self):
        i = QCanvasPolygon(self.canvas)
        size = self.canvas.width()/2
        pa=QPointArray(6)
        pa.setPoint(0, QPoint(0,0))
        pa.setPoint(1, QPoint(size,size/5))
        pa.setPoint(2, QPoint(size*4/5,size))
        pa.setPoint(3, QPoint(size/6,size*5/4))
        pa.setPoint(4, QPoint(size*3/4,size*3/4))
        pa.setPoint(5, QPoint(size*3/4,size/4))

        i.setPoints(pa)
        i.setBrush(QBrush( QColor(256*random.random()%32*8,256*random.random()%32*8,256*random.random()%32*8)) )
        i.move(self.canvas.width()*random.random()%self.canvas.width(),self.canvas.width()*random.random()%self.canvas.height())
        i.setZ(256*random.random()%256)
        i.show()

    def addSpline(self):
        i = QCanvasSpline(self.canvas)
        size = canvas.width()/6
        pa=QPointArray(12)
        pa.setPoint(0,QPoint(0,0))
        pa.setPoint(1,QPoint(size/2,0))
        pa.setPoint(2,QPoint(size,size/2))
        pa.setPoint(3,QPoint(size,size))
        pa.setPoint(4,QPoint(size,size*3/2))
        pa.setPoint(5,QPoint(size/2,size*2))
        pa.setPoint(6,QPoint(0,size*2))
        pa.setPoint(7,QPoint(-size/2,size*2))
        pa.setPoint(8,QPoint(size/4,size*3/2))
        pa.setPoint(9,QPoint(0,size))
        pa.setPoint(10,QPoint(-size/4,size/2))
        pa.setPoint(11,QPoint(-size/2,0))
        i.setControlPoints(pa)
        i.setBrush( QBrush(QColor(256*random.random()%32*8,256*random.random()%32*8,256*random.random()%32*8) ))
        i.move(self.canvas.width()*random.random()%self.canvas.width(),self.canvas.width()*random.random()%self.canvas.height())
        i.setZ(256*random.random()%256)
        i.show()

    def addText(self):
        i = QCanvasText(self.canvas)
        i.setText("QCanvasText")
        i.move(self.canvas.width()*random.random()%self.canvas.width(),self.canvas.width()*random.random()%self.canvas.height())
        i.setZ(256*random.random()%256)
        i.show()

    def addLine(self):
        i = QCanvasLine(self.canvas);
        i.setPoints( self.canvas.width()*random.random()%self.canvas.width(), self.canvas.width()*random.random()%self.canvas.height(),
                self.canvas.width()*random.random()%self.canvas.width(), self.canvas.width()*random.random()%self.canvas.height() )
        i.setPen( QPen(QColor(256*random.random()%32*8,256*random.random()%32*8,256*random.random()%32*8), 6) )
        i.setZ(256*random.random()%256)
        i.show()

    def ternary(self,exp,x,y):
        if exp:
            return x
        else:
            return y

    def addMesh(self):
        x0 = 0;
        y0 = 0;

        if not self.tb:
            self.tb = QBrush( Qt.red )
        if not self.tp:
            self.tp = QPen( Qt.black )

        nodecount = 0;

        w = self.canvas.width()
        h = self.canvas.height()

        dist = 30
        rows = h / dist
        cols = w / dist

        #ifndef QT_NO_PROGRESSDIALOG
        #progress=QProgressDialog( "Creating mesh...", "Abort", rows,
        #         self, "progress", True );
        #endif

        lastRow=[]
        for c in range(cols):
            lastRow.append(NodeItem(self.canvas))
        for j in range(rows):
            n = self.ternary(j%2 , cols-1 , cols)
            prev = 0;
            for i in range(n):
                el = NodeItem( self.canvas )
                nodecount=nodecount+1
                r = 20*20*random.random()
                xrand = r %20
                yrand = (r/20) %20
                el.move( xrand + x0 + i*dist + self.ternary(j%2 , dist/2 , 0 ),
                    yrand + y0 + j*dist );

                if  j > 0 :
                    if  i < cols-1 :
                        EdgeItem( lastRow[i], el, self.canvas ).show()
                    if  j%2 :
                        EdgeItem( lastRow[i+1], el, self.canvas ).show()
                    elif i > 0 :
                        EdgeItem( lastRow[i-1], el, self.canvas ).show()
                if  prev:
                    EdgeItem( prev, el, self.canvas ).show()

                if  i > 0 :
                    lastRow[i-1] = prev
                prev = el
                el.show()

            lastRow[n-1]=prev
            #ifndef QT_NO_PROGRESSDIALOG
            #progress.setProgress( j )
            #if  progress.wasCancelled() :
            #   break
            #endif

        #ifndef QT_NO_PROGRESSDIALOG
        #progress.setProgress( rows )
        #endif
        #// qDebug( "%d nodes, %d edges", nodecount, EdgeItem::count() );

    def addRectangle(self):
        i = QCanvasRectangle( self.canvas.width()*random.random()%self.canvas.width(),
            self.canvas.width()*random.random()%self.canvas.height(),
            self.canvas.width()/5,self.canvas.width()/5,self.canvas)
        z = 256*random.random()%256
        i.setBrush( QBrush(QColor(z,z,z) ))
        i.setPen( QPen(QColor(self.canvas.width()*random.random()%32*8,
            self.canvas.width()*random.random()%32*8,
            self.canvas.width()*random.random()%32*8), 6) )
        i.setZ(z)
        i.show()


if __name__=='__main__':
    app=QApplication(sys.argv)

    if len(sys.argv) > 1:
        butterfly_fn=QString(sys.argv[1])
    else:
        butterfly_fn=QString("butterfly.png")

    if len(sys.argv) > 2:
        logo_fn = QString(sys.argv[2])
    else:
        logo_fn=QString("qtlogo.png")

    canvas=QCanvas(800,600)
    canvas.setAdvancePeriod(30)
    m=Main(canvas,None,"pyqt canvas example")
    m.resize(m.sizeHint())

    qApp.setMainWidget(m)
    m.setCaption("Qt Canvas Example ported to PyQt")
    if QApplication.desktop().width() > m.width() + 10 and QApplication.desktop().height() > m.height() + 30:
        m.show()
    else:
        m.showMaximized()

    m.show();
    #//    m.help();
    qApp.setMainWidget(None);

    QObject.connect( qApp, SIGNAL("lastWindowClosed()"), qApp, SLOT("quit()") )

    app.exec_loop()

    # We need to explicitly delete the canvas now (and, therefore, the main
    # window beforehand) to make sure that the sprite logo doesn't get garbage
    # collected first.
    views = []
    del m
    del canvas
