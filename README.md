<HTML>
<HEAD>
<META NAME="generator" CONTENT="http://txt2tags.org">
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=iso-8859-1">
<TITLE>PostGIS Versioning - pgVersion 2.0.0</TITLE>

<!-- CSS include failed for style.css -->

</HEAD>
<BODY>

<DIV CLASS="header" ID="header">
<H1>PostGIS Versioning - pgVersion 2.1</H1>
<H3>Dr. Horst Duester, 2015, horst.duester@sourcepole.ch</H3>
</DIV>

<DIV CLASS="toc">

  <OL>
  <LI><A HREF="#toc1">Change log</A>
  <LI><A HREF="#toc2">TODO</A>
  <LI><A HREF="#toc3">Prerequisits</A>
    <UL>
    <LI><A HREF="#toc4">3.1. Ubuntu</A>
    </UL>
  <LI><A HREF="#toc5">Introduction</A>
  <LI><A HREF="#toc6">Download:</A>
  <LI><A HREF="#toc7">Functions</A>
    <UL>
    <LI><A HREF="#toc8">6.1. pgvsinit</A>
    <LI><A HREF="#toc9">6.2. pgvscommit</A>
    <LI><A HREF="#toc10">6.3. pgvsmerge</A>
    <LI><A HREF="#toc11">6.4. pgvsdrop</A>
    <LI><A HREF="#toc12">6.5. pgvsrevert</A>
    <LI><A HREF="#toc13">6.6. pgvsrevision</A>
    <LI><A HREF="#toc14">6.7. pgvslogview</A>
    <LI><A HREF="#toc15">6.8. pgvsrollback</A>
    </UL>
  <LI><A HREF="#toc16">QGIS Plugin</A>
    <UL>
    <LI><A HREF="#toc17">7.1. Prepare layer for versioning</A>
    <LI><A HREF="#toc18">7.2. Load versioned layer</A>
    <LI><A HREF="#toc19">7.3. Commit changes</A>
    <LI><A HREF="#toc20">7.4. Revert to head revision</A>
    <LI><A HREF="#toc24">7.5. Logview</A>
    <LI><A HREF="#toc21">7.6. Drop versioning from layer</A>
    <LI><A HREF="#toc22">7.7. Help</A>
    </UL>
  <LI><A HREF="#toc23">License</A>
  </OL>

</DIV>
<DIV CLASS="body" ID="body">

<A NAME="toc1"></A>
<H1>1. Change log</H1>

<A NAME="toc2"></A>
<H1>2. TODO</H1>

<UL>
<LI>Branches 
<LI>Merging of branches
</UL>

<A NAME="toc3"></A>
<H1>3. Prerequisits</H1>

<A NAME="toc4"></A>
<H2>3.1. Ubuntu</H2>

<P>
You have to install Qt4SQL  and the Qt4SQL PostgreSQL driver with:
</P>
<P>
<CODE>$ sudo apt-get install libqt4-sql libqt4-sql-psql python-qt4-sql</CODE>
</P>

<A NAME="toc5"></A>
<H1>4. Introduction</H1>

<P>
Versioning of Postgis-Layers will become essential, when more than one person edits the same layer concurrently. To manage concurrencing editing of a single Postgis Layer the pgVersion management system supports your work. The idea is to create a versioning system for editing PostGIS-Layers similar to source code versioning systems like CVS or Subversion.
A <A HREF="http://www.portailsig.org/content/pgversion-le-plugin-de-versionnement-pour-postgis-qgis">french tutorial</A> was created by Nicolas Rochard. 
</P>

<A NAME="toc6"></A>
<H1>5. Download:</H1>

<P>
Download <A HREF="https://github.com/sourcepole/pgversion/blob/master/docs/extension/pgversion--2.0.0.sql">createFunctions.sql</A>
</P>

<A NAME="toc7"></A>
<H1>6. Functions</H1>

<P>
To create the new <CODE>pgvs</CODE> functions you should run the SQL-Script:
</P>

<div class="code"><PRE>
psql -d &lt;databasename&gt; -U &lt;username&gt; -h &lt;hostname&gt; \
     -f &lt;Path to&gt;/createFunctions.sql
</PRE></div>

<P>
After running this command, a new schema is created:
</P>

<div class="code"><PRE>
versions
</PRE></div>

<P>
and some new functions have been created in the schema <CODE>versions</CODE>:
</P>

<div class="code"><PRE>
pgvsinit()
pgvscommit()
pgvsmerge()
pgvsdrop()
pgvsrevert()
pgvsrevision()
pgvslogview()
pgvsrollback()
</PRE></div>

<P>
This schema contains all information which are neccessary to manage the versioned tables. I highly advise that you should not make any changes in the schema <CODE>versions</CODE>. Now your database is ready for versioning.
You also have the option to install the <CODE>pgvs</CODE> environment in the <CODE>template1</CODE> database. In this case every new created database will automatically contain the <CODE>pgvs</CODE> environment.
</P>

<A NAME="toc8"></A>
<H2>6.1. pgvsinit</H2>

<P>
The <CODE>pgvsinit()</CODE> function initializes the versioning environment for a single geometry layer.
</P>
<P>
The init command:
</P>

<div class="code"><PRE>
select * from versions.pgvsinit('&lt;schema&gt;.&lt;tablename&gt;');
</PRE></div>

<P>
The initialisation process works in 3 steps:
</P>

 <UL>
 <LI>creating a view with the name <CODE>&lt;tablename&gt;_version</CODE>. This view has the same structure as the origional table.
 <LI>creating of some rules and triggers for the new view
 <LI>add a record to the meta table <CODE>versions.version_tables</CODE>
 </UL>

<P>
All future editings have to be done on the view <CODE>&lt;tablename&gt;_version</CODE>. If you want to change the geometry or an attribute value of a versioned PostGIS-Layer you can do this in the same way like you would edit a real table. After saving of changes on the Layer, you will see all changes you made. But your changes are only visible for you, they are saved in a temporary state. To make your changes available for the rest of the world, you have to commit your changes to the database.
</P>
<P>
It is not possible to change the structure of the underlaying table. If you want to do this, you have to drop the versioning system from the table like described later. Than you can make your changes. As the last step you have to initialize the versioning system for the table again.
</P>

<A NAME="toc9"></A>
<H2>6.2. pgvscommit</H2>

<P>
When you finish your editings after a while, you have to commit your editings to the main PostGIS-Layer table. In this way you make your editings available for the rest of the world.
</P>
<P>
The commit command:
</P>

<div class="code"><PRE>
select * from versions.psvscommit('&lt;schema&gt;.&lt;tablename&gt;','&lt;log-message&gt;';
</PRE></div>

<P>
Sometimes it happens, that two or more different users edit the same table record. In this case <CODE>pgvscommit()</CODE>
lists the conflicting records. The conflicting objects are not saved to the database. Please contact the user mentioned in the error message to discuss, which change should be committed to the database.
</P>

<A NAME="toc10"></A>
<H2>6.3. pgvsmerge</H2>

<P>
To solve conflicts user the command:
</P>

<div class="code"><PRE>
select * from versions.pgvsmerge('&lt;schema&gt;.&lt;tablename&gt;',&lt;record-id&gt;,'&lt;username&gt;');
</PRE></div>

<A NAME="toc11"></A>
<H2>6.4. pgvsdrop</H2>

<P>
To remove the versioning system from a specific table, you can use the command:
</P>

<div class="code"><PRE>
select * from versions.pgvsdrop('&lt;tablename&gt;');
</PRE></div>

<P>
Than all versioning stuff will be removed from the PostGIS-Layer table. You only can drop versioning from a table when all changes of all users are committed. Don't worry, the command <CODE>pgvsdrop('&lt;tablename&gt;');</CODE> only removes the versioning system. The main PostGIS-Layer table with all former committs still exists of course!
</P>

<A NAME="toc12"></A>
<H2>6.5. pgvsrevert</H2>

<P>
The pgvsrevert function gives you the option to remove all your uncommitted editings and set back your data to the HEAD revision.
The revision number of the HEAD revision will be returned.
</P>

<div class="code"><PRE>
select * from versions.pgvsrevert('&lt;tablename&gt;');
</PRE></div>

<A NAME="toc13"></A>
<H2>6.6. pgvsrevision</H2>

<P>
The pgvsrevision function returns the installed revison of pgvs:
</P>

<div class="code"><PRE>
select * from versions.pgvsrevision();
</PRE></div>

<A NAME="toc14"></A>
<H2>6.7. pgvslogview</H2>

<P>
The pgvslogview function returns all logs of a specific versioned table:
</P>

<div class="code"><PRE>
select * from versions.pgpslogview('&lt;tablename&gt;');
</PRE></div>

<A NAME="toc15"></A>
<H2>6.8. pgvsrollback</H2>

<P>
The pgvsrollback function will push a revision into HEAD revision:
</P>

<div class="code"><PRE>
select * from versions.pgvsrollback('&lt;tablename&gt;',revision integer);
</PRE></div>

<P>
This function will work reliable since pgvs db-version 1.8.4 and QGIS-Plugin version 2.0.2. All prior created revisions of the layer are not ready to rollback.
</P>

<A NAME="toc16"></A>
<H1>7. QGIS Plugin</H1>

<P>
To make your life easier, the pgversion plugin for QGIS supports you by the use of <CODE>pgvs</CODE>. 
</P>

<A NAME="toc17"></A>
<H2>7.1. Prepare layer for versioning</H2>

<P>
<IMG ALIGN="middle" SRC="docs/images/qgis_001.png" BORDER="0" ALT="">
</P>
<P>
With this option you start the versioning for a PostGIS layer. You have to do this once for every layer versioning should be available. Select the layer and the versioning system will be available for this layer. After this step you have to remove the layer from QGIS. To work with the versioned layer you have to do the next step.
</P>

<A NAME="toc18"></A>
<H2>7.2. Load versioned layer</H2>

<P>
<IMG ALIGN="middle" SRC="docs/images/qgis_002.png" BORDER="0" ALT="">
</P>
<P>
Now you can select the versioned layer from your database. In fact the corresponding layer view is loaded. Select your QGIS-PostGIS-Connection. You also will see the connected user. Than select the versioned layer from the list. The layer will be loaded to the QGIS Mapcanvas and you can start with editing.
</P>
<P>
<IMG ALIGN="middle" SRC="docs/images/qgis_005.png" BORDER="0" ALT="">
</P>

<A NAME="toc19"></A>
<H2>7.3. Commit changes</H2>

<P>
<IMG ALIGN="middle" SRC="docs/images/qgis_003.png" BORDER="0" ALT="">
</P>
<P>
When you have finished your editings you can commit your changes to the database. 
When no conflicts between your editings and editings of an other user have been detected you get a dialog to enter a log message. 
After a successful commit you will see this message.
</P>
<P>
<IMG ALIGN="middle" SRC="docs/images/qgis_006.png" BORDER="0" ALT="">
</P>
<P>
In the case that a different editor has changed one or more objects you edited as well, a new window will appear to support the merging of concurrent objects.
</P>
<P>
<IMG ALIGN="middle" SRC="docs/images/qgis_007.png" BORDER="0" ALT="">
</P>
<P>
The conflicting objects are shown up in red with and labled with the  corresponding username.
</P>
<P>
To hightlight the object of a single record from the table below the map, click a row and the corresponding object will be hightlighted in blue color.
</P>
<P>
<IMG ALIGN="middle" SRC="docs/images/qgis_013.png" BORDER="0" ALT="">
</P>
<P>
Now you can select the object to commit from the select box.
</P>
<P>
<IMG ALIGN="middle" SRC="docs/images/qgis_008.png" BORDER="0" ALT="">
</P>
<P>
Click <IMG ALIGN="middle" SRC="docs/images/qgis_009.png" BORDER="0" ALT=""> to complete merging for this single object.
</P>

<A NAME="toc20"></A>
<H2>7.4. Revert to head revision</H2>

<P>
<IMG ALIGN="middle" SRC="docs/images/qgis_010.png" BORDER="0" ALT="">
</P>
<P>
Sometimes you like to remove your non committed changes. That means that you can set your view back to the HEAD revision. In this case all of your editings will be removed.
To revert your editings activate the corresponding layer in the legend and select the menue "Revert to head revision"
</P>

<A NAME="toc24"></A>
<H2>7.5. Logview</H2>
<P>
The Logview Dialog gives you the option to get an overview over the changes of a single layer. You also are able rollback to a  specific release. The rollback will be loaded to QGIS. As the result you will lose all possible changes you made before. If you want to keep this changes, you have to commit them. After the loading of the rollback your layer will be named as modified. That means only you can see this rollback. If you like to make it persistent, you have to commit it.
</P>

<A NAME="toc21"></A>
<H2>7.6. Drop versioning from layer</H2>

<P>
<IMG ALIGN="middle" SRC="docs/images/qgis_011.png" BORDER="0" ALT="">
</P>
<P>
Drop versioning from layer does not drop the main layer itself. It only drops the versioning environment of the layer. 
This is necessary in the case you changed the model of the main table or you don't want to use the versioning environment in the future.
To drop versioning from layer activate the corresponding layer in the legend and select "Drop versioning from layer" in the menue.
</P>

<A NAME="toc22"></A>
<H2>7.7. Help</H2>

<P>
<IMG ALIGN="middle" SRC="docs/images/qgis_004.png" BORDER="0" ALT="">
</P>
<P>
You will get this help.
</P>

<A NAME="toc23"></A>
<H1>8. License</H1>

<P>
LICENSING INFORMATION:
</P>
<P>
pgvs Postgres-Functions and PgVersion QGIS Plugin is copyright (C) 2010  Dr. Horst Duester / Sourcepole AG, Zurich
</P>
<P>
<A HREF="mailto:horst.duester@sourcepole.ch">horst.duester@sourcepole.ch</A>
</P>
<P>
QGIS-Plugin icons is copyright (C) 2010 Robert Szczepanek
</P>
<P>
<A HREF="mailto:robert@szczepanek.pl">robert@szczepanek.pl</A>
</P>
<P>
Licensed under the terms of GNU GPL 2
</P>
<P>
This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
</P>
</DIV>

<!-- html code generated by txt2tags 2.6 (http://txt2tags.org) -->
<!-- cmdline: txt2tags -i help.t2t -o ../help.html -t html -->
</BODY></HTML>
