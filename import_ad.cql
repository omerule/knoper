//even wat voorwerk
MATCH (x) DETACH DELETE x;
CREATE CONSTRAINT ON (p:persoon) ASSERT p.GUID IS UNIQUE;
CREATE CONSTRAINT ON (g:groep) ASSERT g.GUID IS UNIQUE;
CREATE CONSTRAINT ON (c:computer) ASSERT c.GUID IS UNIQUE;
//laad de personen in de DB
LOAD CSV WITH HEADERS FROM "file:///bron.csv" AS personen FIELDTERMINATOR ';' CREATE (:persoon {guid:personen.GUID, dn:personen.distinguishedName, cn: personen.cn});
//laad de groepen in de DB
LOAD CSV WITH HEADERS FROM "file:///groepen.csv" AS groep FIELDTERMINATOR ';' CREATE (:groep {guid:groep.GUID, dn:groep.distinguishedName, cn: groep.cn});
//inde erop
LOAD CSV WITH HEADERS FROM "file:///computers.csv" AS computer FIELDTERMINATOR ';' CREATE (:computer {guid:computer.GUID, dn:computer.distinguishedName, cn:computer.cn});
//inde erop
LOAD CSV WITH HEADERS FROM "file:///groep2members.csv" AS gknoop FIELDTERMINATOR ';' MATCH (g:groep{guid:gknoop.GUID}),(m:groep{guid:gknoop.GUID_member}) MERGE (m)-[l:lid_van]->(g);
//knoop de groepen en users
LOAD CSV WITH HEADERS FROM "file:///groep2members.csv" AS pknoop FIELDTERMINATOR ';' MATCH (gg:groep{guid:pknoop.GUID}),(p:persoon{guid:pknoop.GUID_member}) MERGE (p)-[l:lid_van]->(gg);
//knoop de groepen en computers
LOAD CSV WITH HEADERS FROM "file:///groep2members.csv" AS cknoop FIELDTERMINATOR ';' MATCH (gc:groep{guid:cknoop.GUID}),(c:computer{guid:cknoop.GUID_member}) MERGE (c)-[l:lid_van]->(gc);
//voeg een extra tag toe aan de groepen: applicaties, lokaal
MATCH (ag:groep) WHERE ag.dn CONTAINS 'OU=Application,OU=Groups,OU=NZA,DC=nza,DC=local' SET ag:applicatie;
MATCH (lg:groep) WHERE lg.dn CONTAINS 'OU=Local,OU=Resource,OU=Groups,OU=NZA,DC=nza,DC=local' SET lg:lokaal;
//de directory
MATCH (x) DETACH DELETE x;
CREATE CONSTRAINT ON (d:dir) ASSERT d.locatie IS UNIQUE;
CREATE CONSTRAINT ON (p:persoon) ASSERT p.user IS UNIQUE;
LOAD CSV WITH HEADERS FROM 'file:///klaar.txt' AS lijn FIELDTERMINATOR ';'
MERGE (x:persoon{user:TRIM(lijn.user)})
MERGE (y:dir{locatie:TRIM(lijn.dir)})
CREATE (x) - [r:rechten{soort:lijn.rechten}] -> (y)
;

