#!/usr/bin/env python3
########################################
#                                      #
# (ActiveDirectory)-[:Python]->(Neo4j) #
#                                      #
# Version: "First Make it work 2.6     #
#                                      #
########################################
#The flow of the program is: 
#Get all group, computer, and person objects from Active Directory,
#and put them in the Neo4j GraphDatabase.
#Then create a relation between group and there members.
#Then you can explore these relationships with Neo4j.
#You need Active Directory, Python with python-ldap3 and Neo4j
import datetime
from enum import IntFlag
#You can install ldap3 with $pip3 install ldap3
from ldap3 import Server, Connection, ALL, NTLM, SUBTREE 
#You can install neo4j.driver with $pip3 install neo4j-driver
from neo4j import GraphDatabase
import logging
from sys import stdout
import getpass
import cmd

#################################################################
#                   Begin User Space                            #
#     Adjust these variable for your own environment            #
#################################################################

domain_ip = "domaincontroller ipaddress" #The IPv4 address of the DomainController
domain_name = "contoso.com" #example domain.local
ldap_pers_scope = "DC=contoso,DC=com" #example OU=Users,DC=domain,DC=local
ldap_comp_scope = "DC=contoso,DC=com" #example OU=Computers,DC=domain,DC=local
ldap_group_scope = "DC=contoso,DC=com" #example DC=domain,DC=local

#You can add extra Active Directory Attributes of you need more.
#Some notes:
#Person, Computer and Group Attributes will be added to the Graph Node as Property and there Value
#Warning: The Attributes must exist in the ActiveDirectory please check before use.
#Note: Empty AD Attribute values will NOT create a Neo4j Property.
#Note: AD Attributes Names are Case Sensitive see: 
#   https://docs.microsoft.com/en-us/windows/desktop/ADSchema/a-accountexpires 
#   When you find a attribute see field: use the "Ldap-Display-Name" notation.
#Warning: Attribute Names with a hyphen "-" don't work.
#Warning: Not all Attributes will work with the LDAP python driver.
person_attributes = [
"givenName"
,"cn"
,"sAMAccountName"
,"objectGUID"
,"objectSid"
,"userAccountControl"
,"uSNCreated"
,"whenCreated"
,"whenChanged"
,"canonicalName"
,"description"
,"info"
]

computer_attributes = [
"cn"
,"sAMAccountName"
,"objectGUID"
,"objectSid"
,"userAccountControl"
,"uSNCreated"
,"whenCreated"
,"whenChanged"
,"canonicalName"
,"operatingSystem"
,"dNSHostName"
,"description"
,"info"
,"managedBy"
]

group_attributes = [
"cn"
,"sAMAccountName"
,"objectGUID"
,"objectSid"
,"userAccountControl"
,"uSNCreated"
,"whenCreated"
,"whenChanged"
,"canonicalName"
,"description"
,"info"
,"managedBy"
,"groupType"
]

#################################################################
#                         End User Space                        # 
#################################################################

#User input for connecting with AD and Neo4j
domain_user = input("domain account name: ") #your domain login account
domain_pass = getpass.getpass("password domain user: ") #domain password
neo4j_user = input("Neo4j loginname: ") #default user
neo4j_pass = getpass.getpass("password Neo4j user: ") #neo4j password

#Mandatory ActiveDirectory Attributes for merging the relations
mandatory_person_attr = ["primaryGroupID","distinguishedName","objectCategory","name"]
mandatory_computer_attr = ["primaryGroupID","distinguishedName","objectCategory","name"]
mandatory_group_attr = ["primaryGroupToken","distinguishedName","member","objectCategory","name"]

#And Merge the Attributes from "user space"  with the above Mandatory Attributes
person_attributes = list(set(person_attributes + mandatory_person_attr))
computer_attributes = list(set(computer_attributes + mandatory_computer_attr))
group_attributes = list(set(group_attributes + mandatory_group_attr))

#Make a connection with Active Directory
server = Server(domain_ip, get_info=ALL) 
conn = Connection(server, user="{}\\{}".format(domain_name,domain_user), password=domain_pass, authentication=NTLM, read_only=True)
conn.bind()

#Make a connection with the Neo4j database
driver = GraphDatabase.driver("bolt://localhost:7687", auth=(neo4j_user, neo4j_pass), encrypted=False)

#First some cleanup and Preparation of the Neo4j GraphDB
session = driver.session()
session.run("MATCH (x) WHERE EXISTS(x.extra_info) DETACH DELETE x;")
session.run("CREATE CONSTRAINT ON (p:person) ASSERT p.distinguishedName IS UNIQUE;")
session.run("CREATE CONSTRAINT ON (c:computer) ASSERT c.distinguishedName IS UNIQUE;")
session.run("CREATE CONSTRAINT ON (g:group) ASSERT g.distinguishedName IS UNIQUE;")
session.run("CREATE INDEX ON :group(primaryGroupToken);")
session.run("CREATE INDEX ON :computer(primaryGroupID);")
session.run("CREATE INDEX ON :person(primaryGroupID);")

class uac(IntFlag):
    ACCOUNT_DISABLE = 2
    HOMEDIR_REQUIRED = 8
    LOCKOUT = 16
    PASSWD_NOTREQD = 32
    PASSWD_CANT_CHANGE = 64
    ENCRYPTED_TEXT_PASSWORD_ALLOWED = 128
    NORMAL_ACCOUNT = 512
    INTERDOMAIN_TRUST_ACCOUNT = 2048
    WORKSTATION_TRUST_ACCOUNT = 4096
    SERVER_TRUST_ACCOUNT = 8192
    DONT_EXPIRE_PASSWD = 65536
    MNS_LOGON_ACCOUNT = 131072 
    SMARTCARD_REQUIRED = 262144 
    TRUSTED_FOR_DELEGATION = 524288 
    NOT_DELEGATED = 1048576
    USE_DES_KEY_ONLY = 2097152
    DONT_REQUIRE_PREAUTH = 4194304
    PASSWORD_EXPIRED = 8388608
    TRUSTED_TO_AUTHENTICATE_FOR_DELEGATION = 16777216 
    NO_AUTH_DATA_REQUIRED = 33554432 
    PARTIAL_SECRETS_ACCOUNT = 67108864 

def welder(ad_attr,node_label):
    """
    I try to make a welder for AD attributes for Neo4j attributes as 
    cypher string
    This will return a "Cypher" plus "$" string like:
    CREATE (a:{label} SET a.{AD attribute name} = ${AD attribute name}
    """
    comma = False 
    cypher = "CREATE (a:{}) SET ".format(node_label)
    for x in ad_attr:
        if not comma:
            cypher = cypher + "a.{} = ${} \n".format(x,x)        
            comma = True
        else:
            cypher = cypher + ", a.{} = ${} \n".format(x,x)        
    return cypher 

def ad2neo4j(adfilter, adattr, adobject, adscope):
    """
    This function will read the Objects from Active Directory and put them in de Neo4j GraphDB. 
    """
    #Get the objects form Active Directory
    conn.extend.standard.paged_search(search_base = adscope,
                            search_filter = adfilter,
                            search_scope = SUBTREE,
                            attributes = adattr,
                            paged_size = 5,
                            generator=False)

    print(str(len(conn.entries)) + " " + adobject)
    
    session = driver.session()
    tx = session.begin_transaction()

    #Make the Nodes in Neo4j
    for x in conn.entries:          
        #Create a dict with the AD attributes as "keys" and there value extracted from AD.
        neo_advalues_dict = {}    
        for y in adattr:
            #There some converting Neo4j Python issue with datatime values 
            #so the "datetime" values collected from AD like
            # "whenCreated" or "whenChanged" will be converted to "string".
            if isinstance(x[y].value, datetime.date):
                neo_advalues_dict[y] = str(x[y].value)
            else:
                neo_advalues_dict[y] = x[y].value
        
            #enumaration of userAccountControl
            if y == "userAccountControl" and adobject == "person":
                #Not sure howto check for "null" values within Python
                try:
                    neo_advalues_dict["uac"] = str(uac(x[y].value))
                except:
                    pass

        #This label should be better
        neo_advalues_dict["extra_info"] = "hello world!"

        tx.run(welder(neo_advalues_dict.keys(), adobject), neo_advalues_dict)
    
    tx.commit()
    print(adobject + "s are made...")

ad2neo4j('(&(objectCategory=person)(objectClass=user))', person_attributes, 'person', ldap_pers_scope)
ad2neo4j('(objectCategory=computer)', computer_attributes, 'computer', ldap_comp_scope)
ad2neo4j('(objectCategory=group)', group_attributes, 'group', ldap_group_scope)

#Next make relation between Persons/Computers/Groups and Groups
#And PrimaryGroupID for Persons and Computers 
#The idea is to have all indexes be ready before using them.
#Not sure if this will work:
session.run("CALL db.awaitIndexes(600);")
#Now make the relations with members of group
#First the "special" relation with persons and computers and there primaryGroupID
session = driver.session()
tx = session.begin_transaction()
tx.run("""MATCH (x) WHERE EXISTS(x.extra_info) AND EXISTS(x.primaryGroupID) 
            WITH x, x.primaryGroupID AS pgid 
            MATCH (g:group) WHERE g.primaryGroupToken = pgid 
            MERGE (g)-[:member]->(x);""")
tx.commit()
print("Person/Computer primarygroup relation is made.")
#And create a relation between (group)-[:member]->(group,computer,person)
session = driver.session()
tx = session.begin_transaction()
tx.run("""MATCH (g:group) WHERE EXISTS(g.member) 
            WITH g, g.member AS mem UNWIND mem AS memfx 
            MATCH (p:person) WHERE p.distinguishedName = memfx 
            MERGE (g)-[:member]->(p);""")
tx.commit()
print("Person relation with Group is made.")
session = driver.session()
tx = session.begin_transaction()
tx.run("""MATCH (g:group) WHERE EXISTS(g.member) 
            WITH g, g.member AS mem UNWIND mem AS memfx 
            MATCH (c:computer) WHERE c.distinguishedName = memfx 
            MERGE (g)-[:member]->(c);""")
tx.commit()
print("Computer relation with Group is made.")
session = driver.session()
tx = session.begin_transaction()
tx.run("""MATCH (g:group) WHERE EXISTS(g.member) 
            WITH g, g.member AS mem UNWIND mem AS memfx 
            MATCH (gg:group) WHERE gg.distinguishedName = memfx 
            MERGE (g)-[:member]->(gg);""")
tx.commit()
print("Group relation with Group is made.")
#close the Connection with Neo4j
print(session.close())
#Close the Connection with ActiveDirectory
print(conn.unbind())
print("finished")
exit()
