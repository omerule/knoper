#to load ntfs directory/file access control entry (ace) data into Neo4j
#this file is created with: https://technet.microsoft.com/en-us/sysinternals/accessenum.aspx
#This program should run by someone with enough accessrights on the NTFS filesystem.
#the outputfile of this program contains the dir and ace with read/write/denied and accountname "domain\user"  
#This data I want to load in the Neo4j database to get insite who can acces what.
#To fill de Neo4j these steps:
#       1) the users from active directory are loaded (see...)
#       2) load the directorys/files in Neo4j these directorys/files are at the first column of outputfile (awk $1)
#       3) get the unique users from the outputfile (with awk)
#       4) create missing users in Neo4j (match if not create... with unique constrained in Neo4j)
#We now have to parts in the Neo4j DB: 
#       the dir/files and users.
#the outputfile also contains the Neo4j relationtype:
#        (user)-[read,write..]->(dir/file)
#
#[dir] [read, user1,user2...] [write, user2,user3] [denied, user5...]
#to 
#[dir] [read]  [user1]
#[dir] [read]  [user1]
#[dir] [write] [user2]
#and a list containing only unique directory ($1) in the file 
~                                                               
