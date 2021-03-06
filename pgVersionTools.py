# -*- coding: utf-8 -*-
"""
/***************************************************************************
Tools for Database Management
------------------------------------------------------------------------------------------------------------------
begin                 : 2010-07-31
copyright           : (C) 2010 by Dr. Horst Duester
email                 :  horst.duester@sourcepole.ch
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtSql import *
from qgis.gui import *
from qgis.core import *
from forms.Ui_dbVersionCheck import DbVersionCheckDialog 
from datetime import datetime
from .dbtools.dbTools import *
import time,  sys
import apicompat

class PgVersionTools:
    
# Konstruktor 
  def __init__(self,  iface):
      self.pgvsRevision = '1.8.4'
      self.iface = iface
      pass

     
  def layerDB(self, connectionName,  layer):
      
      myUri = QgsDataSourceURI(layer.source())
      
      # If username and password are not saved in the DB settings
      if myUri.username() == '':
          connectionInfo = myUri.connectionInfo()
          (success,  user,  password) =  QgsCredentials.instance().get(connectionInfo, None, None)
          QgsCredentials.instance().put( connectionInfo, user, password )
          myUri.setPassword(password)
          myUri.setUsername(user)
      
      try:
          myDb = DbObj(pluginname=connectionName,typ='pg',hostname=myUri.host(),port=myUri.port(),dbname=myUri.database(),username=myUri.username(), passwort=myUri.password())
          return myDb
      except:
          QMessageBox.information(None, QCoreApplication.translate('PgVersionTools','Error'), QCoreApplication.translate('PgVersionTools','No Database Connection Established.'))
          return None
    
      if not self.tools.checkPGVSRevision(myDb):
        return
     
        
  def setConfTable(self,  theLayer):
      provider = theLayer.dataProvider()
      uri = provider.dataSourceUri() 
      myDb = layerDB('setConfTable',  theLayer)
      mySchema = QgsDataSourceURI(uri).schema()
      myTable = QgsDataSourceURI(uri).table()
      if len(mySchema) == 0:
          mySchema = 'public'

      myTable = myTable.remove("_version")
      sql = "select versions.pgvscommit('"+mySchema+"."+myTable+"')"
      result = myDb.read(sql)
      myDb.close()
      


  def isModified(self, myLayer=None):
    
        myLayerUri = QgsDataSourceURI(myLayer.source())

        myDb = self.layerDB('isModified',  myLayer)
        
        if myDb == None:
            return None
    
        if len(myLayerUri.schema()) == 1:
          schema = 'public'
        else:
          schema = myLayerUri.schema()
        
    
        sql = 'select count(project) \
          from versions.\"'+schema+'_'+myLayerUri.table()+'_log\" \
          where project = \''+myDb.dbUser()+'\' and not commit'
#        QMessageBox.information(None, '', sql)
        result = myDb.read(sql)
        myDb.close()
        
#        try:
        if int(result["COUNT"][0]) == 0:
          return False
        else:
          return True      
#        except:
#            pass
      
  def setModified(self, myLayer=None,  unsetModified=False):
      
    if myLayer==None:
      myLayer = self.iface.mapCanvas().currentLayer()
        
    if self.isModified(myLayer):
      if '(modified)' not in myLayer.name():
        myLayer.setLayerName(myLayer.name()+' (modified)')
    elif unsetModified:
      myLayer.setLayerName(myLayer.name().replace(' (modified)', ''))      
      
# Return QgsVectorLayer from a layer name ( as string )
  def vectorLayerExists(self,   myName ):
     layermap = QgsMapLayerRegistry.instance().mapLayers()
     for name, layer in layermap.iteritems():
         if layer.type() == QgsMapLayer.VectorLayer and layer.name() == myName:
             if layer.isValid():
                 return True
             else:
                 return False



  def versionExists(self,layer):
  
      myDb = self.layerDB('versionExists',  layer)
      provider = layer.dataProvider()
      uri = provider.dataSourceUri()    
  
      try: 
          myTable = QgsDataSourceURI(uri).table()       
          mySchema = QgsDataSourceURI(uri).schema()
          
          if mySchema == '':
              mySchema = 'public'
          
          sql = "select version_table_schema as schema, version_table_name as table \
           from versions.version_tables \
           where (version_view_schema = '"+mySchema+"' and version_view_name = '"+myTable+"') \
              or (version_table_schema = '"+mySchema+"' and version_table_name = '"+myTable+"')"
            
          result  = myDb.read(sql)
          myDb.close()
          
          if len(result["SCHEMA"]) > 1:
            QMessageBox.information(None, '', QCoreApplication.translate('PgVersionTools','Table ')+mySchema+'.'+myTable+QCoreApplication.translate('PgVersionTools',' is already versionized'))
            return True
          else:
            return False
      except:
            QMessageBox.information(None, '', QCoreApplication.translate('PgVersionTools','pgvs is not installed in your database \n\n Please download the pgvs functions from \n\n http://www.sourcepole.ch/pgtools/pgversion/createFunctions.sql\n\n and install them as mentioned in help') )
            return True

  def createGridView(self, tabView, tabData, headerText, colWidth, rowHeight):
    
    numCols = len(headerText)
    startVal = 0
      
    numRows = len(tabData[headerText[0].upper()])
   
    tabView.clear()
    tabView.setColumnCount(numCols)
    
    tabView.setRowCount(numRows)
      
    tabView.sortItems(2)
    col = startVal
    
    i = 0
    for text in headerText:
      headerItem = QTableWidgetItem()
      headerItem.setData(Qt.DisplayRole,pystring(text))
      tabView.setHorizontalHeaderItem(i,headerItem)
      i = i+1
    
    
    for i in range(0,numRows):
      
      col = startVal


      for text in headerText:
        myItem = QTableWidgetItem()
        myItem.setData(Qt.DisplayRole,pystring(tabData[text.upper()][i]))   
        tabView.setItem(i,col,myItem)
        myItem.setSelected(False)
        col = col + 1
    return
           
  def confRecords(self, theLayer):
      confRecords = []
      provider = theLayer.dataProvider()
      uri = provider.dataSourceUri()    
      myDb = self.layerDB('getConfRecord',  theLayer)
      mySchema = QgsDataSourceURI(uri).schema()
      myTable = QgsDataSourceURI(uri).table()
      if len(mySchema) == 0:
          mySchema = 'public'
            
      sql =    "select version_table_schema as schema, version_table_name as table "
      sql += "from versions.version_tables "
      sql += "where version_view_schema = '"+mySchema+"' and version_view_name = '"+myTable+"'"
      result  = myDb.read(sql)
      
      if len(result["SCHEMA"]) == 0:
        QMessageBox.information(None, '', QCoreApplication.translate('PgVersionTools','Table {0} is not versionized').format(self.mySchema+'.'+self.myTable))
        return None
      else:
        sql = "select count(myuser) from versions.pgvscheck('"+result["SCHEMA"][0]+"."+result["TABLE"][0]+"')"
#        QMessageBox.information(None, '',  sql)
        check = myDb.read(sql)
      
      if check["COUNT"][0] <> "0":    
          sql = "select * from versions.pgvscheck('"+result["SCHEMA"][0]+"."+result["TABLE"][0]+"') order by objectkey"
          result = myDb.read(sql)
          myDb.close()        

          for i in range(len(result["CONFLICT_USER"])):
              resString = result["OBJECTKEY"][i]+" - "+result["MYUSER"][i].strip()+" - "+datetime.strftime(datetime.fromtimestamp(float(result["MYSYSTIME"][i])/1000.0), "%x %H:%M:%S")
              confRecords.append(resString)
              resString = result["OBJECTKEY"][i]+" - "+result["CONFLICT_USER"][i].strip()+" - "+datetime.strftime(datetime.fromtimestamp(float(result["CONFLICT_SYSTIME"][i])/1000.0), "%x %H:%M:%S")
              confRecords.append(resString)

#          confRecords =list(set(confRecords))
          confRecords.insert(0, QCoreApplication.translate('PgVersionTools','select Candidate'))          
          return confRecords
      else:
          return None
      
  def tableRecords(self,  theLayer):      
      provider = theLayer.dataProvider()
      uri = provider.dataSourceUri()    
      myDb = self.layerDB('tableRecords',  theLayer)
      mySchema = QgsDataSourceURI(uri).schema()
      myTable = QgsDataSourceURI(uri).table()
      if len(mySchema) == 0:
          mySchema = 'public'
          
      sql =   "select * from versions.version_tables "
      sql += "where version_view_schema = '"+mySchema+"' and version_view_name = '"+myTable+"'"
      layer = myDb.read(sql)              
          
      sql = "select objectkey, myversion_log_id, conflict_version_log_id from versions.pgvscheck('"+mySchema+"."+myTable.replace("_version", "")+"')"
      result = myDb.read(sql)          
      timeListString = ''
      keyString = ''

      for i in range(len(result["OBJECTKEY"])):
          timeListString += result["MYVERSION_LOG_ID"][i]+","+result["CONFLICT_VERSION_LOG_ID"][i]+","
          keyString += result["OBJECTKEY"][i]+","

      timeListString = timeListString[0:len(timeListString)-1]
      keyString = keyString[0:len(keyString)-1]
      
      sql = "select * "
      sql += "from versions.\""+mySchema+"_"+myTable.replace("_version", "")+"_version_log\" "
      sql += "where version_log_id in ("+timeListString+")"
      sql += "order by "+layer["VERSION_VIEW_PKEY"][0]
      
      result = myDb.read(sql)
      
      cols = myDb.cols(sql)
      
      sql = "select f_geometry_column as geocol "
      sql += "from geometry_columns "
      sql += "where f_table_schema = '"+mySchema+"' "
      sql += "  and f_table_name = '"+myTable+"' "
      
      geomCol = myDb.read(sql)
      
      cols.remove('ACTION')
      cols.remove('SYSTIME')
      cols.remove('COMMIT')
      cols.remove(geomCol["GEOCOL"][0].upper())
      
      cols.insert(0, cols.pop(-1))
      cols.insert(0, cols.pop(-1))
      cols.insert(0, cols.pop(-1))
      
      resultArray = []
      resultArray.append(result)
      resultArray.append(cols)
      
      myDb.close()
      return resultArray
      
      

  def conflictLayer(self,  theLayer):
        provider = theLayer.dataProvider()
        uri = provider.dataSourceUri()    
        myDb = self.layerDB('getConflictLayer',  theLayer)
        mySchema = QgsDataSourceURI(uri).schema()
        myTable = QgsDataSourceURI(uri).table()
        if len(mySchema) == 0:
          mySchema = 'public'
            
        sql =   "select * from versions.version_tables "
        sql += "where version_view_schema = '"+mySchema+"' and version_view_name = '"+myTable+"'"
        layer = myDb.read(sql)    
        
        uri = QgsDataSourceURI()
        
#        # set host name, port, database name, username and password
        uri.setConnection(myDb.dbHost(), str(myDb.dbPort()), myDb.dbName(), myDb.dbUser(), myDb.dbPasswd())    
        
        sql = "select * from versions.pgvscheck('"+mySchema+"."+myTable.replace("_version", '')+"')"
        result = myDb.read(sql)
        myFilter = ''
        for i in range(len(result["OBJECTKEY"])):
            key = result["OBJECTKEY"][i]
            myproject = result["MYUSER"][i]
            mysystime = result["MYSYSTIME"][i]
            project = result["CONFLICT_USER"][i]
            systime = result["CONFLICT_SYSTIME"][i]
            myFilter += "("+layer["VERSION_VIEW_PKEY"][0]+"="+key+" and systime = "+systime+") or ("+layer["VERSION_VIEW_PKEY"][0]+"="+key+" and systime = "+mysystime+") or "

        if len(myFilter) > 0:
           myFilter = myFilter[0:len(myFilter)-4]  
           uri.setDataSource("versions", mySchema+"_"+myTable+"_log", layer["VERSION_VIEW_GEOMETRY_COLUMN"][0], myFilter,  layer["VERSION_VIEW_PKEY"][0])
           layerName = myTable+"_conflicts"
           vLayer = QgsVectorLayer(uri.uri(), layerName, "postgres")
           userPluginPath = QFileInfo(QgsApplication.qgisUserDbFilePath()).path()+"/python/plugins/pgversion"  
           vLayer.setRendererV2(None)
           vLayer.loadNamedStyle(userPluginPath+"/tools/conflict.qml")   
           myDb.close()
           if vLayer.isValid():
               return vLayer    
           else:
               return None
       
       
  def createPolygon(self, geometry, geometryType):      
            
    self.mRubberBand.reset()
#    project = QgsProject.instance()
    
    color = QColor(255,0,0)
    self.mRubberBand.setColor(color)
    self.mRubberBand.setWidth(5)
    self.mRubberBand.show()
    
    g = QgsGeometry.fromWkt(geometry)
    
#    self.mRubberBand.setToGeometry(g,  None)
    
    if geometryType == "MULTIPOLYGON":
      for i in g.asMultiPolygon():
        index = 0
        for n in i:
          for k in n: 
            self.mRubberBand.addPoint(k,  False,  index)
          index = index + 1

#    if geometryType == "MULTILINESTRING":
#      for i in g.asPolyline():
#        for k in i: 
#          self.mRubberBand.addPoint(k)

    elif geometryType == "POLYGON":
      for i in g.asPolygon():
        for k in i: 
          self.mRubberBand.addPoint(k,  False)
            

    elif geometryType == "POINT":
      gBuffer = g.buffer(25, 100)
      for i in gBuffer.asPolygon():
        for k in i: 
          self.mRubberBand.addPoint(k)

    return 0                      
    
    
# Check the revision of the DB-Functions
  def checkPGVSRevision(self,  myDb):      
#      try:
          check = pystring(myDb.runError('select pgvsrevision from versions.pgvsrevision()'))
          print "Check: "+str(check)+"  len "+ str(len(check))
          if len(check) > 1:
                self.vsCheck = DbVersionCheckDialog(myDb,  '0.0.0')
                revisionMessage =QCoreApplication.translate('PgVersionTools', 'pgvs is not installed in the selected DB.\n\nPlease contact your DB-administrator to install the DB-functions from the file:\n\n<Plugin-Directory>/pgversion/tools/createFunctions.sql\n\nIf you have appropriate DB permissions you can install the DB functions directly with click on Install pgvs.')
                self.vsCheck.messageTextEdit.setText(revisionMessage)
                self.vsCheck.btnUpdate.setText('Install pgvs')
                self.vsCheck.show()
                return False
          else:  
            result = myDb.read('select pgvsrevision from versions.pgvsrevision()')
            if self.pgvsRevision != result["PGVSREVISION"][0]:
                self.vsCheck = DbVersionCheckDialog(myDb,  result["PGVSREVISION"][0])              
                revisionMessage =QCoreApplication.translate('PgVersionTools', 'The Plugin expects pgvs revision ')+self.pgvsRevision+QCoreApplication.translate('PgVersionTools', ' but DB-functions revision ')+result["PGVSREVISION"][0]+QCoreApplication.translate('PgVersionTools', ' are installed.\n\nPlease contact your DB-administrator to update the DB-functions from the file:\n\n<Plugin-Directory>/pgversion/tools/updateFunctions.sql\n\nIf you have appropriate DB permissions you can update the DB directly with click on DB-Update.')
                self.vsCheck.messageTextEdit.setText(revisionMessage)
                self.vsCheck.show()
                return False
            else:
              return True
#      except:
#          self.vsCheck = DbVersionCheckDialog(myDb,  '0.0.0')
#          revisionMessage = QCoreApplication.translate('PgVersionTools','Please upgrade the DB-functions from the file:\n\n<Plugin-Directory>/pgversion/tools/updateFunctions.sql\n\nIf you have appropriate DB permissions you can update the DB directly with click on DB-Update.')
#          self.vsCheck.messageTextEdit.setText(revisionMessage)
#          self.vsCheck.show()          
#          return False    

    
#Get the Fieldnames of a Vector Layer
#Return: List of Fieldnames
  def getFieldNames(self, vLayer):
#    provider = vLayer.dataProvider()      
    myList = self.getFieldList(vLayer)

    fieldList = []    
    for (k,attr) in myList.iteritems():
       fieldList.append(unicode(attr.name(),'latin1'))

    return fieldList

#Get the List of Fields
#Return: QGsFieldMap
  def getFieldList(self, vlayer):
    fProvider = vlayer.dataProvider()

#    feat = QgsFeature()
    allAttrs = fProvider.attributeIndexes()

# start data retrieval: all attributes for each feature
#    fProvider.select(allAttrs, QgsRectangle(), False)

# retrieve every feature with its attributes
    myFields = fProvider.fields().toList()
      
    return myFields
        
